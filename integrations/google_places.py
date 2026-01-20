"""
Google Places API Integration
=============================
Business verification, address validation, and industry lookup using Google Places API.

Setup:
    1. Get API key from Google Cloud Console
    2. Enable Places API (New) and Geocoding API
    3. Set GOOGLE_PLACES_API_KEY environment variable or pass to client

Usage:
    from integrations import GooglePlacesClient

    client = GooglePlacesClient()
    result = client.find_business("Joe's Pizza", "123 Main St, New York, NY")
    print(result.verified, result.industry_type)
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None  # type: ignore


logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

PLACES_API_BASE = "https://places.googleapis.com/v1/places"
GEOCODING_API_BASE = "https://maps.googleapis.com/maps/api/geocode/json"

# Google Place Types to MCA Industry mapping
PLACE_TYPE_TO_INDUSTRY = {
    # Tier 1 - Preferred
    "doctor": "medical",
    "dentist": "dental",
    "veterinary_care": "veterinary",
    "hospital": "medical",
    "pharmacy": "pharmacy",
    "physiotherapist": "medical",
    "accounting": "accounting",
    "lawyer": "legal",
    "insurance_agency": "insurance",

    # Tier 2 - Standard
    "restaurant": "restaurant",
    "cafe": "restaurant",
    "bakery": "restaurant",
    "meal_takeaway": "restaurant",
    "meal_delivery": "restaurant",
    "bar": "bar",
    "night_club": "bar",
    "store": "retail",
    "clothing_store": "retail",
    "shoe_store": "retail",
    "jewelry_store": "retail",
    "electronics_store": "retail",
    "furniture_store": "retail",
    "home_goods_store": "retail",
    "hardware_store": "retail",
    "pet_store": "retail",
    "florist": "retail",
    "supermarket": "grocery",
    "grocery_or_supermarket": "grocery",
    "convenience_store": "convenience",
    "car_repair": "auto_repair",
    "car_dealer": "auto_dealer",
    "car_wash": "auto_service",
    "gas_station": "gas_station",
    "general_contractor": "construction",
    "electrician": "construction",
    "plumber": "construction",
    "roofing_contractor": "construction",
    "moving_company": "trucking",
    "storage": "storage",
    "gym": "fitness",
    "spa": "salon",
    "beauty_salon": "salon",
    "hair_care": "salon",
    "nail_salon": "salon",
    "laundry": "laundry",
    "lodging": "hotel",
    "real_estate_agency": "real_estate",
    "travel_agency": "travel",

    # Tier 3+ / Needs Review
    "casino": "gambling",
    "liquor_store": "liquor",
    "pawn_shop": "pawn",
}

# Address component type mappings
ADDRESS_COMPONENT_TYPES = {
    "street_number": "street_number",
    "route": "street_name",
    "locality": "city",
    "administrative_area_level_1": "state",
    "administrative_area_level_2": "county",
    "postal_code": "zip_code",
    "country": "country",
    "subpremise": "suite",
}


class VerificationStatus(Enum):
    """Business verification status"""
    VERIFIED = "verified"
    PARTIAL_MATCH = "partial_match"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"
    ERROR = "error"


class OperationalStatus(Enum):
    """Business operational status from Google"""
    OPERATIONAL = "operational"
    CLOSED_TEMPORARILY = "closed_temporarily"
    CLOSED_PERMANENTLY = "closed_permanently"
    UNKNOWN = "unknown"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AddressComponent:
    """Parsed address component"""
    street_number: str = ""
    street_name: str = ""
    suite: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county: str = ""
    country: str = "US"

    @property
    def street_address(self) -> str:
        """Full street address line"""
        parts = []
        if self.street_number:
            parts.append(self.street_number)
        if self.street_name:
            parts.append(self.street_name)
        if self.suite:
            parts.append(f"#{self.suite}")
        return " ".join(parts)

    @property
    def city_state_zip(self) -> str:
        """City, State ZIP format"""
        return f"{self.city}, {self.state} {self.zip_code}".strip()

    @property
    def full_address(self) -> str:
        """Complete formatted address"""
        return f"{self.street_address}, {self.city_state_zip}"

    def to_dict(self) -> Dict:
        return {
            "street_number": self.street_number,
            "street_name": self.street_name,
            "suite": self.suite,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "county": self.county,
            "country": self.country,
            "street_address": self.street_address,
            "full_address": self.full_address,
        }


@dataclass
class BusinessHours:
    """Business operating hours"""
    day: str
    open_time: str
    close_time: str
    is_open: bool = True

    def to_dict(self) -> Dict:
        return {
            "day": self.day,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "is_open": self.is_open,
        }


@dataclass
class PlaceResult:
    """Google Places API result"""
    place_id: str
    name: str
    formatted_address: str
    address_components: AddressComponent
    phone_number: str = ""
    website: str = ""
    google_maps_url: str = ""
    rating: float = 0.0
    review_count: int = 0
    price_level: int = 0
    business_status: OperationalStatus = OperationalStatus.UNKNOWN
    types: List[str] = field(default_factory=list)
    hours: List[BusinessHours] = field(default_factory=list)
    latitude: float = 0.0
    longitude: float = 0.0

    # Derived fields
    primary_type: str = ""
    industry_type: str = ""

    def __post_init__(self):
        if self.types and not self.primary_type:
            self.primary_type = self.types[0] if self.types else ""
        if not self.industry_type:
            self.industry_type = self._map_industry()

    def _map_industry(self) -> str:
        """Map Google place types to MCA industry"""
        for place_type in self.types:
            if place_type in PLACE_TYPE_TO_INDUSTRY:
                return PLACE_TYPE_TO_INDUSTRY[place_type]
        return "unknown"

    @property
    def is_operational(self) -> bool:
        return self.business_status == OperationalStatus.OPERATIONAL

    def to_dict(self) -> Dict:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "formatted_address": self.formatted_address,
            "address_components": self.address_components.to_dict(),
            "phone_number": self.phone_number,
            "website": self.website,
            "google_maps_url": self.google_maps_url,
            "rating": self.rating,
            "review_count": self.review_count,
            "price_level": self.price_level,
            "business_status": self.business_status.value,
            "is_operational": self.is_operational,
            "types": self.types,
            "primary_type": self.primary_type,
            "industry_type": self.industry_type,
            "hours": [h.to_dict() for h in self.hours],
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass
class BusinessVerification:
    """Business verification result"""
    status: VerificationStatus
    confidence_score: float  # 0.0 - 1.0
    place_result: Optional[PlaceResult] = None

    # Verification details
    name_match: bool = False
    name_similarity: float = 0.0
    address_match: bool = False
    address_similarity: float = 0.0
    phone_match: bool = False

    # Flags
    is_operational: bool = False
    industry_type: str = ""
    risk_flags: List[str] = field(default_factory=list)

    # Timestamps
    verified_at: datetime = field(default_factory=datetime.now)

    @property
    def is_verified(self) -> bool:
        return self.status == VerificationStatus.VERIFIED

    @property
    def needs_review(self) -> bool:
        return self.status == VerificationStatus.PARTIAL_MATCH or len(self.risk_flags) > 0

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "is_verified": self.is_verified,
            "needs_review": self.needs_review,
            "name_match": self.name_match,
            "name_similarity": self.name_similarity,
            "address_match": self.address_match,
            "address_similarity": self.address_similarity,
            "phone_match": self.phone_match,
            "is_operational": self.is_operational,
            "industry_type": self.industry_type,
            "risk_flags": self.risk_flags,
            "verified_at": self.verified_at.isoformat(),
            "place_result": self.place_result.to_dict() if self.place_result else None,
        }


# =============================================================================
# Google Places Client
# =============================================================================

class GooglePlacesClient:
    """
    Google Places API client for business verification.

    Usage:
        client = GooglePlacesClient(api_key="your-api-key")
        # or set GOOGLE_PLACES_API_KEY environment variable

        # Find a business
        result = client.find_business("Joe's Pizza", "123 Main St, New York, NY")

        # Verify business details
        verification = client.verify_business(
            business_name="Joe's Pizza",
            address="123 Main St, New York, NY 10001",
            phone="212-555-1234"
        )

        # Validate address
        validated = client.validate_address("123 Main St, New York, NY")

        # Lookup industry
        industry = client.lookup_industry("restaurant", "123 Main St, NYC")
    """

    def __init__(self, api_key: str = None):
        if requests is None:
            raise ImportError("requests library required: pip install requests")

        self.api_key = api_key or os.environ.get("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Places API key required. "
                "Set GOOGLE_PLACES_API_KEY environment variable or pass api_key parameter."
            )

        self.session = requests.Session()

    # -------------------------------------------------------------------------
    # Core API Methods
    # -------------------------------------------------------------------------

    def text_search(
        self,
        query: str,
        location: str = None,
        radius_meters: int = 5000,
        max_results: int = 5,
    ) -> List[PlaceResult]:
        """
        Search for places using text query.

        Args:
            query: Search text (e.g., "Joe's Pizza New York")
            location: Optional location bias (address or lat,lng)
            radius_meters: Search radius in meters
            max_results: Maximum number of results

        Returns:
            List of PlaceResult objects
        """
        url = f"{PLACES_API_BASE}:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.addressComponents,places.nationalPhoneNumber,"
                "places.internationalPhoneNumber,places.websiteUri,"
                "places.googleMapsUri,places.rating,places.userRatingCount,"
                "places.priceLevel,places.businessStatus,places.types,"
                "places.regularOpeningHours,places.location"
            ),
        }

        body = {
            "textQuery": query,
            "maxResultCount": max_results,
            "languageCode": "en",
        }

        if location:
            # Try to geocode location for better results
            coords = self._geocode_address(location)
            if coords:
                body["locationBias"] = {
                    "circle": {
                        "center": {"latitude": coords[0], "longitude": coords[1]},
                        "radius": float(radius_meters),
                    }
                }

        try:
            response = self.session.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for place in data.get("places", []):
                result = self._parse_place_result(place)
                if result:
                    results.append(result)

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Places API text search error: {e}")
            return []

    def get_place_details(self, place_id: str) -> Optional[PlaceResult]:
        """
        Get detailed information about a place by ID.

        Args:
            place_id: Google Place ID

        Returns:
            PlaceResult or None if not found
        """
        url = f"{PLACES_API_BASE}/{place_id}"

        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "id,displayName,formattedAddress,addressComponents,"
                "nationalPhoneNumber,internationalPhoneNumber,websiteUri,"
                "googleMapsUri,rating,userRatingCount,priceLevel,"
                "businessStatus,types,regularOpeningHours,location"
            ),
        }

        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_place_result(data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Places API details error: {e}")
            return None

    def _geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode an address to coordinates"""
        url = GEOCODING_API_BASE
        params = {
            "address": address,
            "key": self.api_key,
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK" and data.get("results"):
                location = data["results"][0]["geometry"]["location"]
                return (location["lat"], location["lng"])

        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding error: {e}")

        return None

    # -------------------------------------------------------------------------
    # Business Verification
    # -------------------------------------------------------------------------

    def find_business(
        self,
        business_name: str,
        address: str = None,
        max_results: int = 3,
    ) -> List[PlaceResult]:
        """
        Find a business by name and optional address.

        Args:
            business_name: Business name to search
            address: Optional address for location bias
            max_results: Maximum results to return

        Returns:
            List of matching PlaceResult objects
        """
        query = business_name
        if address:
            query = f"{business_name} {address}"

        return self.text_search(query, location=address, max_results=max_results)

    def verify_business(
        self,
        business_name: str,
        address: str,
        phone: str = None,
        strict: bool = False,
    ) -> BusinessVerification:
        """
        Verify a business exists and matches provided details.

        Args:
            business_name: Expected business name
            address: Expected business address
            phone: Optional phone number to verify
            strict: If True, require exact matches

        Returns:
            BusinessVerification result
        """
        # Search for the business
        results = self.find_business(business_name, address, max_results=5)

        if not results:
            return BusinessVerification(
                status=VerificationStatus.NOT_FOUND,
                confidence_score=0.0,
                risk_flags=["Business not found in Google Places"],
            )

        # Find best match
        best_match = None
        best_score = 0.0

        for result in results:
            name_sim = self._string_similarity(
                business_name.lower(),
                result.name.lower()
            )
            addr_sim = self._address_similarity(address, result.formatted_address)

            # Weighted score
            score = (name_sim * 0.6) + (addr_sim * 0.4)

            if score > best_score:
                best_score = score
                best_match = result

        if not best_match:
            return BusinessVerification(
                status=VerificationStatus.NOT_FOUND,
                confidence_score=0.0,
            )

        # Calculate verification details
        name_sim = self._string_similarity(
            business_name.lower(),
            best_match.name.lower()
        )
        addr_sim = self._address_similarity(address, best_match.formatted_address)
        phone_match = self._phone_matches(phone, best_match.phone_number) if phone else True

        # Determine status
        risk_flags = []

        if name_sim < 0.5:
            risk_flags.append(f"Name mismatch: '{best_match.name}' vs '{business_name}'")

        if addr_sim < 0.5:
            risk_flags.append("Address mismatch")

        if phone and not phone_match:
            risk_flags.append("Phone number mismatch")

        if not best_match.is_operational:
            risk_flags.append(f"Business status: {best_match.business_status.value}")

        # Determine verification status
        if strict:
            threshold = 0.85
        else:
            threshold = 0.6

        if best_score >= threshold and not risk_flags:
            status = VerificationStatus.VERIFIED
        elif best_score >= 0.4:
            status = VerificationStatus.PARTIAL_MATCH
        else:
            status = VerificationStatus.MISMATCH

        return BusinessVerification(
            status=status,
            confidence_score=best_score,
            place_result=best_match,
            name_match=name_sim >= 0.8,
            name_similarity=name_sim,
            address_match=addr_sim >= 0.7,
            address_similarity=addr_sim,
            phone_match=phone_match,
            is_operational=best_match.is_operational,
            industry_type=best_match.industry_type,
            risk_flags=risk_flags,
        )

    # -------------------------------------------------------------------------
    # Address Validation
    # -------------------------------------------------------------------------

    def validate_address(self, address: str) -> Optional[AddressComponent]:
        """
        Validate and standardize an address using Google Geocoding.

        Args:
            address: Address string to validate

        Returns:
            AddressComponent with parsed/validated components, or None
        """
        url = GEOCODING_API_BASE
        params = {
            "address": address,
            "key": self.api_key,
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK" or not data.get("results"):
                return None

            result = data["results"][0]
            return self._parse_address_components(result.get("address_components", []))

        except requests.exceptions.RequestException as e:
            logger.error(f"Address validation error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Industry Lookup
    # -------------------------------------------------------------------------

    def lookup_industry(
        self,
        business_name: str,
        address: str = None,
    ) -> Optional[str]:
        """
        Look up industry type for a business.

        Args:
            business_name: Business name
            address: Optional address for better matching

        Returns:
            Industry type string or None
        """
        results = self.find_business(business_name, address, max_results=1)

        if results:
            return results[0].industry_type

        return None

    def get_industry_from_place_types(self, place_types: List[str]) -> str:
        """
        Map Google Place types to MCA industry classification.

        Args:
            place_types: List of Google Place type strings

        Returns:
            MCA industry type
        """
        for place_type in place_types:
            if place_type in PLACE_TYPE_TO_INDUSTRY:
                return PLACE_TYPE_TO_INDUSTRY[place_type]
        return "unknown"

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _parse_place_result(self, data: Dict) -> Optional[PlaceResult]:
        """Parse API response into PlaceResult"""
        if not data:
            return None

        # Parse address components
        addr_components = self._parse_address_components(
            data.get("addressComponents", [])
        )

        # Parse business status
        status_str = data.get("businessStatus", "").upper()
        status_map = {
            "OPERATIONAL": OperationalStatus.OPERATIONAL,
            "CLOSED_TEMPORARILY": OperationalStatus.CLOSED_TEMPORARILY,
            "CLOSED_PERMANENTLY": OperationalStatus.CLOSED_PERMANENTLY,
        }
        business_status = status_map.get(status_str, OperationalStatus.UNKNOWN)

        # Parse hours
        hours = []
        opening_hours = data.get("regularOpeningHours", {})
        for period in opening_hours.get("periods", []):
            day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            open_info = period.get("open", {})
            close_info = period.get("close", {})

            day_idx = open_info.get("day", 0)
            day_name = day_names[day_idx] if 0 <= day_idx < 7 else "Unknown"

            hours.append(BusinessHours(
                day=day_name,
                open_time=f"{open_info.get('hour', 0):02d}:{open_info.get('minute', 0):02d}",
                close_time=f"{close_info.get('hour', 0):02d}:{close_info.get('minute', 0):02d}",
                is_open=True,
            ))

        # Get coordinates
        location = data.get("location", {})

        # Extract place types
        types = data.get("types", [])

        return PlaceResult(
            place_id=data.get("id", ""),
            name=data.get("displayName", {}).get("text", ""),
            formatted_address=data.get("formattedAddress", ""),
            address_components=addr_components,
            phone_number=data.get("nationalPhoneNumber", "") or data.get("internationalPhoneNumber", ""),
            website=data.get("websiteUri", ""),
            google_maps_url=data.get("googleMapsUri", ""),
            rating=data.get("rating", 0.0),
            review_count=data.get("userRatingCount", 0),
            price_level=data.get("priceLevel", 0) if isinstance(data.get("priceLevel"), int) else 0,
            business_status=business_status,
            types=types,
            hours=hours,
            latitude=location.get("latitude", 0.0),
            longitude=location.get("longitude", 0.0),
        )

    def _parse_address_components(self, components: List[Dict]) -> AddressComponent:
        """Parse Google address components into AddressComponent"""
        addr = AddressComponent()

        for comp in components:
            comp_types = comp.get("types", [])
            long_name = comp.get("longText", comp.get("long_name", ""))
            short_name = comp.get("shortText", comp.get("short_name", ""))

            for gtype, attr in ADDRESS_COMPONENT_TYPES.items():
                if gtype in comp_types:
                    # Use short_name for state, long_name for others
                    value = short_name if attr == "state" else long_name
                    setattr(addr, attr, value)

        return addr

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (0.0 - 1.0)"""
        if not s1 or not s2:
            return 0.0

        # Normalize strings
        s1 = re.sub(r'[^\w\s]', '', s1.lower()).strip()
        s2 = re.sub(r'[^\w\s]', '', s2.lower()).strip()

        if s1 == s2:
            return 1.0

        # Simple word overlap similarity
        words1 = set(s1.split())
        words2 = set(s2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _address_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate address similarity"""
        if not addr1 or not addr2:
            return 0.0

        # Normalize addresses
        def normalize_addr(addr: str) -> str:
            addr = addr.lower()
            # Common abbreviations
            replacements = {
                r'\bstreet\b': 'st',
                r'\bavenue\b': 'ave',
                r'\broad\b': 'rd',
                r'\bdrive\b': 'dr',
                r'\blane\b': 'ln',
                r'\bboulevard\b': 'blvd',
                r'\bnorth\b': 'n',
                r'\bsouth\b': 's',
                r'\beast\b': 'e',
                r'\bwest\b': 'w',
                r'\bapartment\b': 'apt',
                r'\bsuite\b': 'ste',
            }
            for pattern, repl in replacements.items():
                addr = re.sub(pattern, repl, addr)
            return re.sub(r'[^\w\s]', '', addr).strip()

        n1 = normalize_addr(addr1)
        n2 = normalize_addr(addr2)

        return self._string_similarity(n1, n2)

    def _phone_matches(self, phone1: str, phone2: str) -> bool:
        """Check if two phone numbers match (digits only)"""
        if not phone1 or not phone2:
            return False

        # Extract digits only
        digits1 = re.sub(r'\D', '', phone1)
        digits2 = re.sub(r'\D', '', phone2)

        # Handle country code
        if len(digits1) == 11 and digits1.startswith('1'):
            digits1 = digits1[1:]
        if len(digits2) == 11 and digits2.startswith('1'):
            digits2 = digits2[1:]

        return digits1 == digits2


# =============================================================================
# Convenience Functions
# =============================================================================

def verify_business(
    business_name: str,
    address: str,
    phone: str = None,
    api_key: str = None,
) -> BusinessVerification:
    """
    Quick business verification function.

    Args:
        business_name: Business name to verify
        address: Business address
        phone: Optional phone number
        api_key: Optional API key (uses env var if not provided)

    Returns:
        BusinessVerification result
    """
    client = GooglePlacesClient(api_key=api_key)
    return client.verify_business(business_name, address, phone)


def validate_address(address: str, api_key: str = None) -> Optional[AddressComponent]:
    """
    Quick address validation function.

    Args:
        address: Address to validate
        api_key: Optional API key

    Returns:
        Validated AddressComponent or None
    """
    client = GooglePlacesClient(api_key=api_key)
    return client.validate_address(address)


def lookup_industry(
    business_name: str,
    address: str = None,
    api_key: str = None,
) -> Optional[str]:
    """
    Quick industry lookup function.

    Args:
        business_name: Business name
        address: Optional address
        api_key: Optional API key

    Returns:
        Industry type string or None
    """
    client = GooglePlacesClient(api_key=api_key)
    return client.lookup_industry(business_name, address)


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python google_places.py <business_name> [address]")
        print("\nExample:")
        print('  python google_places.py "Starbucks" "New York, NY"')
        sys.exit(1)

    business_name = sys.argv[1]
    address = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        client = GooglePlacesClient()

        print(f"Searching for: {business_name}")
        if address:
            print(f"Near: {address}")
        print("-" * 50)

        results = client.find_business(business_name, address)

        if not results:
            print("No results found")
        else:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.name}")
                print(f"   Address: {result.formatted_address}")
                print(f"   Phone: {result.phone_number or 'N/A'}")
                print(f"   Industry: {result.industry_type}")
                print(f"   Rating: {result.rating} ({result.review_count} reviews)")
                print(f"   Status: {result.business_status.value}")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nSet GOOGLE_PLACES_API_KEY environment variable:")
        print("  Windows: set GOOGLE_PLACES_API_KEY=your-api-key")
        print("  Linux/Mac: export GOOGLE_PLACES_API_KEY=your-api-key")
