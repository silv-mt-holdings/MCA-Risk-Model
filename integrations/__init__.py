"""
Integrations Module
===================
Third-party API integrations for business verification.

Components:
- GooglePlacesClient: Business lookup, address validation, industry classification
"""

from .google_places import (
    GooglePlacesClient,
    PlaceResult,
    AddressComponent,
    BusinessVerification,
    verify_business,
    validate_address,
    lookup_industry,
)

__all__ = [
    'GooglePlacesClient',
    'PlaceResult',
    'AddressComponent',
    'BusinessVerification',
    'verify_business',
    'validate_address',
    'lookup_industry',
]
