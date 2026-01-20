"""
Pre-Check Module
================
Runs verification checks before scoring. Catches red flags early.

Usage:
    from scoring.precheck import run_precheck
    
    result = run_precheck(
        business_name="Joe's Pizza",
        address="123 Main St, Tampa FL",
        stated_industry="restaurant",
        phone="813-555-1234"
    )
    
    if result.block_deal:
        print(f"BLOCKED: {result.block_reason}")
    elif result.flags:
        print(f"Review needed: {result.flags}")
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PrecheckStatus(Enum):
    """Pre-check result status"""
    PASS = "pass"
    FLAG = "flag"  # Proceed with manual review
    BLOCK = "block"  # Do not proceed


# Industries that require immediate decline or heavy restrictions
PROHIBITED_INDUSTRIES = {
    "cannabis", "cbd", "gambling", "firearms", "adult_entertainment",
    "check_cashing", "bail_bonds", "crypto", "money_services"
}

# Industries requiring manual review / elevated pricing
HIGH_RISK_INDUSTRIES = {
    "trucking", "used_cars", "towing", "bar", "hookah", "liquor",
    "pawn", "tobacco", "vape"
}


@dataclass
class PrecheckResult:
    """Pre-check verification result"""
    status: PrecheckStatus
    confidence: float  # 0.0 - 1.0
    
    # Verification results
    business_verified: bool = False
    address_verified: bool = False
    industry_verified: bool = False
    
    # Industry analysis
    stated_industry: str = ""
    detected_industry: str = ""
    industry_match: bool = True
    industry_tier: int = 2  # 1-5, lower is better
    
    # Google Places data
    google_rating: float = 0.0
    google_reviews: int = 0
    operational_status: str = "unknown"
    
    # Flags and blocks
    flags: List[str] = field(default_factory=list)
    block_deal: bool = False
    block_reason: str = ""
    
    # Timestamps
    checked_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "confidence": self.confidence,
            "business_verified": self.business_verified,
            "address_verified": self.address_verified,
            "industry_verified": self.industry_verified,
            "stated_industry": self.stated_industry,
            "detected_industry": self.detected_industry,
            "industry_match": self.industry_match,
            "industry_tier": self.industry_tier,
            "google_rating": self.google_rating,
            "google_reviews": self.google_reviews,
            "operational_status": self.operational_status,
            "flags": self.flags,
            "block_deal": self.block_deal,
            "block_reason": self.block_reason,
            "checked_at": self.checked_at.isoformat(),
        }


def get_industry_tier(industry: str) -> int:
    """
    Get risk tier for industry (1=best, 5=prohibited)
    
    Tier 1 - Preferred: Medical, dental, legal, accounting
    Tier 2 - Standard: Restaurant, retail, construction, salon
    Tier 3 - Elevated: Bar, liquor, convenience, gas station
    Tier 4 - High Risk: Trucking, used cars, towing, pawn
    Tier 5 - Specialty/Prohibited: Cannabis, gambling, firearms
    """
    tier_map = {
        # Tier 1 - Preferred
        "medical": 1, "dental": 1, "veterinary": 1, "pharmacy": 1,
        "accounting": 1, "legal": 1, "insurance": 1,
        
        # Tier 2 - Standard  
        "restaurant": 2, "retail": 2, "grocery": 2, "construction": 2,
        "salon": 2, "fitness": 2, "auto_repair": 2, "auto_dealer": 2,
        "real_estate": 2, "hotel": 2, "laundry": 2, "storage": 2,
        "jewelry": 2,
        
        # Tier 3 - Elevated
        "bar": 3, "convenience": 3, "gas_station": 3, "liquor": 3,
        "auto_service": 3, "travel": 3,
        
        # Tier 4 - High Risk
        "trucking": 4, "used_cars": 4, "towing": 4, "pawn": 4,
        "hookah": 4, "tobacco": 4, "vape": 4,
        
        # Tier 5 - Specialty/Prohibited
        "cannabis": 5, "cbd": 5, "gambling": 5, "firearms": 5,
        "adult_entertainment": 5, "check_cashing": 5, "bail_bonds": 5,
    }
    return tier_map.get(industry, 3)  # Default to Tier 3 if unknown


def run_precheck(
    business_name: str,
    address: str,
    stated_industry: str = None,
    phone: str = None,
    skip_google: bool = False,
) -> PrecheckResult:
    """
    Run pre-check verification on a business.
    
    Args:
        business_name: Legal or DBA name
        address: Business address
        stated_industry: Industry from application
        phone: Business phone (optional)
        skip_google: Skip Google Places lookup (for testing)
    
    Returns:
        PrecheckResult with verification status and flags
    """
    flags = []
    block_deal = False
    block_reason = ""
    
    # Initialize result
    result = PrecheckResult(
        status=PrecheckStatus.PASS,
        confidence=0.0,
        stated_industry=stated_industry or "",
    )
    
    # Skip Google lookup if requested or no API key
    if skip_google or not os.environ.get("GOOGLE_PLACES_API_KEY"):
        result.flags = ["Google Places verification skipped"]
        result.confidence = 0.0
        return result
    
    try:
        from integrations.google_places import GooglePlacesClient
        client = GooglePlacesClient()
        
        # Verify business
        verification = client.verify_business(
            business_name=business_name,
            address=address,
            phone=phone,
        )
        
        result.confidence = verification.confidence_score
        result.business_verified = verification.name_match
        result.address_verified = verification.address_match
        result.detected_industry = verification.industry_type
        result.operational_status = verification.place_result.business_status.value if verification.place_result else "unknown"
        
        if verification.place_result:
            result.google_rating = verification.place_result.rating
            result.google_reviews = verification.place_result.review_count
        
        # Check 1: Business not found
        if verification.status.value == "not_found":
            flags.append("Business not found in Google Places")
        
        # Check 2: Business closed
        if result.operational_status in ["closed_permanently", "closed_temporarily"]:
            flags.append(f"Business status: {result.operational_status}")
            if result.operational_status == "closed_permanently":
                block_deal = True
                block_reason = "Business permanently closed per Google"
        
        # Check 3: Industry mismatch
        if stated_industry and verification.industry_type:
            stated_normalized = stated_industry.lower().replace(" ", "_").replace("-", "_")
            detected = verification.industry_type.lower()
            
            # Check if they match (allow some flexibility)
            industry_aliases = {
                "restaurant": ["restaurant", "cafe", "bakery", "food"],
                "medical": ["medical", "doctor", "health", "clinic"],
                "retail": ["retail", "store", "shop"],
                "construction": ["construction", "contractor", "builder"],
                "auto": ["auto_repair", "auto_dealer", "auto_service", "car"],
            }
            
            match_found = stated_normalized == detected
            if not match_found:
                for base, aliases in industry_aliases.items():
                    if stated_normalized in aliases and detected in aliases:
                        match_found = True
                        break
            
            result.industry_match = match_found
            result.industry_verified = match_found
            
            if not match_found:
                flags.append(f"Industry mismatch: stated [{stated_industry}] vs Google [{detected}]")
        
        # Check 4: Prohibited industry detected
        detected_tier = get_industry_tier(verification.industry_type)
        result.industry_tier = detected_tier
        
        if verification.industry_type in PROHIBITED_INDUSTRIES:
            block_deal = True
            block_reason = f"Prohibited industry detected: {verification.industry_type}"
        elif verification.industry_type in HIGH_RISK_INDUSTRIES:
            flags.append(f"High-risk industry: {verification.industry_type}")
        
        # Check 5: Low rating / few reviews (could indicate new or troubled business)
        if result.google_rating > 0 and result.google_rating < 3.0:
            flags.append(f"Low Google rating: {result.google_rating}")
        if result.google_reviews < 5:
            flags.append(f"Few reviews: {result.google_reviews} (may be new business)")
        
        # Check 6: Address verification issues
        if verification.risk_flags:
            flags.extend(verification.risk_flags)
        
    except ImportError:
        flags.append("Google Places integration not available")
    except Exception as e:
        logger.error(f"Precheck error: {e}")
        flags.append(f"Verification error: {str(e)}")
    
    # Set final status
    result.flags = flags
    result.block_deal = block_deal
    result.block_reason = block_reason
    
    if block_deal:
        result.status = PrecheckStatus.BLOCK
    elif flags:
        result.status = PrecheckStatus.FLAG
    else:
        result.status = PrecheckStatus.PASS
    
    return result


def precheck_to_score_adjustment(precheck: PrecheckResult) -> Dict[str, Any]:
    """
    Convert precheck result to scoring adjustments.
    
    Returns dict with:
        - industry_tier_override: If Google detected different tier
        - point_adjustments: Dict of score component adjustments
        - risk_flags: List of flags to include in memo
    """
    adjustments = {
        "industry_tier_override": None,
        "point_adjustments": {},
        "risk_flags": precheck.flags.copy(),
    }
    
    # If blocked, no adjustments needed - deal won't proceed
    if precheck.block_deal:
        return adjustments
    
    # Industry tier adjustment
    if precheck.detected_industry and precheck.industry_tier:
        adjustments["industry_tier_override"] = precheck.industry_tier
    
    # Point adjustments based on verification
    if not precheck.business_verified:
        adjustments["point_adjustments"]["business_profile"] = -3
    
    if not precheck.address_verified:
        adjustments["point_adjustments"]["business_profile"] = \
            adjustments["point_adjustments"].get("business_profile", 0) - 2
    
    if not precheck.industry_match:
        adjustments["point_adjustments"]["business_profile"] = \
            adjustments["point_adjustments"].get("business_profile", 0) - 5
    
    # Rating/review adjustments
    if precheck.google_rating >= 4.5 and precheck.google_reviews >= 50:
        adjustments["point_adjustments"]["reputation_bonus"] = 2
    elif precheck.google_rating < 3.0:
        adjustments["point_adjustments"]["reputation_penalty"] = -2
    
    return adjustments


# CLI for testing
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    
    if len(sys.argv) < 3:
        print("Usage: python precheck.py <business_name> <address> [stated_industry]")
        print("\nExample:")
        print('  python precheck.py "Starbucks" "Tampa FL" "restaurant"')
        sys.exit(1)
    
    business = sys.argv[1]
    address = sys.argv[2]
    industry = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Running precheck for: {business}")
    print(f"Address: {address}")
    if industry:
        print(f"Stated industry: {industry}")
    print("-" * 50)
    
    result = run_precheck(business, address, industry)
    
    print(f"\nStatus: {result.status.value.upper()}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Business verified: {result.business_verified}")
    print(f"Address verified: {result.address_verified}")
    print(f"Industry: {result.detected_industry} (Tier {result.industry_tier})")
    print(f"Industry match: {result.industry_match}")
    print(f"Google rating: {result.google_rating} ({result.google_reviews} reviews)")
    print(f"Operational: {result.operational_status}")
    
    if result.flags:
        print(f"\nFlags:")
        for flag in result.flags:
            print(f"  - {flag}")
    
    if result.block_deal:
        print(f"\n*** BLOCKED: {result.block_reason} ***")
