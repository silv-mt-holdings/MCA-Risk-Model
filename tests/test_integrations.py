"""
Integration Module Tests
========================
Tests for Google Places API integration.
"""

import pytest
from unittest.mock import Mock, patch


class TestGooglePlacesClient:
    """Tests for GooglePlacesClient"""

    def test_client_requires_api_key(self):
        """Test that client requires API key"""
        from integrations.google_places import GooglePlacesClient

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                GooglePlacesClient()

    def test_client_accepts_api_key_param(self):
        """Test client accepts api_key parameter"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_client_reads_env_var(self):
        """Test client reads from environment variable"""
        from integrations.google_places import GooglePlacesClient

        with patch.dict('os.environ', {'GOOGLE_PLACES_API_KEY': 'env-key'}):
            client = GooglePlacesClient()
            assert client.api_key == "env-key"


class TestPlaceTypeMapping:
    """Tests for place type to industry mapping"""

    def test_restaurant_mapping(self):
        """Test restaurant type maps correctly"""
        from integrations.google_places import PLACE_TYPE_TO_INDUSTRY

        assert PLACE_TYPE_TO_INDUSTRY.get("restaurant") == "restaurant"
        assert PLACE_TYPE_TO_INDUSTRY.get("cafe") == "restaurant"

    def test_medical_mapping(self):
        """Test medical types map correctly"""
        from integrations.google_places import PLACE_TYPE_TO_INDUSTRY

        assert PLACE_TYPE_TO_INDUSTRY.get("doctor") == "medical"
        assert PLACE_TYPE_TO_INDUSTRY.get("dentist") == "dental"

    def test_prohibited_mapping(self):
        """Test prohibited industry types"""
        from integrations.google_places import PLACE_TYPE_TO_INDUSTRY

        assert PLACE_TYPE_TO_INDUSTRY.get("casino") == "gambling"


class TestAddressComponent:
    """Tests for AddressComponent"""

    def test_full_address_formatting(self):
        """Test full address is formatted correctly"""
        from integrations.google_places import AddressComponent

        addr = AddressComponent(
            street_number="123",
            street_name="Main St",
            city="New York",
            state="NY",
            zip_code="10001",
        )

        assert addr.street_address == "123 Main St"
        assert addr.city_state_zip == "New York, NY 10001"
        assert addr.full_address == "123 Main St, New York, NY 10001"

    def test_suite_included(self):
        """Test suite is included in address"""
        from integrations.google_places import AddressComponent

        addr = AddressComponent(
            street_number="456",
            street_name="Broadway",
            suite="200",
            city="New York",
            state="NY",
            zip_code="10013",
        )

        assert addr.street_address == "456 Broadway #200"


class TestBusinessVerification:
    """Tests for BusinessVerification"""

    def test_verified_status(self):
        """Test verified status properties"""
        from integrations.google_places import (
            BusinessVerification,
            VerificationStatus,
        )

        verification = BusinessVerification(
            status=VerificationStatus.VERIFIED,
            confidence_score=0.95,
        )

        assert verification.is_verified is True
        assert verification.needs_review is False

    def test_partial_match_needs_review(self):
        """Test partial match needs review"""
        from integrations.google_places import (
            BusinessVerification,
            VerificationStatus,
        )

        verification = BusinessVerification(
            status=VerificationStatus.PARTIAL_MATCH,
            confidence_score=0.65,
        )

        assert verification.is_verified is False
        assert verification.needs_review is True

    def test_risk_flags_trigger_review(self):
        """Test risk flags trigger review"""
        from integrations.google_places import (
            BusinessVerification,
            VerificationStatus,
        )

        verification = BusinessVerification(
            status=VerificationStatus.VERIFIED,
            confidence_score=0.90,
            risk_flags=["Phone number mismatch"],
        )

        assert verification.needs_review is True


class TestStringSimilarity:
    """Tests for string similarity functions"""

    def test_exact_match(self):
        """Test exact string match"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        similarity = client._string_similarity("Joe's Pizza", "Joe's Pizza")
        assert similarity == 1.0

    def test_partial_match(self):
        """Test partial string match"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        similarity = client._string_similarity("Joe's Pizza", "Joe Pizza Shop")
        assert 0.3 < similarity < 0.8

    def test_no_match(self):
        """Test no string match"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        similarity = client._string_similarity("ABC Company", "XYZ Corporation")
        assert similarity < 0.3


class TestPhoneMatching:
    """Tests for phone number matching"""

    def test_exact_phone_match(self):
        """Test exact phone number match"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        assert client._phone_matches("212-555-1234", "212-555-1234") is True

    def test_formatted_phone_match(self):
        """Test formatted phone numbers match"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        assert client._phone_matches("(212) 555-1234", "212.555.1234") is True

    def test_country_code_match(self):
        """Test phone with country code matches"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        assert client._phone_matches("+1-212-555-1234", "212-555-1234") is True

    def test_phone_mismatch(self):
        """Test phone number mismatch"""
        from integrations.google_places import GooglePlacesClient

        client = GooglePlacesClient(api_key="test")
        assert client._phone_matches("212-555-1234", "212-555-9999") is False
