"""
Industry Scorer
===============
Score industry risk based on tier classification.

Tiers:
- Tier 1 (Preferred): Low risk industries
- Tier 2 (Standard): Average risk
- Tier 3 (Non-Preferred): Above average risk
- Tier 4 (High Risk): High risk industries
- Tier 5 (Prohibited): Do not fund
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import json
from pathlib import Path


class IndustryTier(Enum):
    """Industry risk tier classification"""
    PREFERRED = 1
    STANDARD = 2
    NON_PREFERRED = 3
    HIGH_RISK = 4
    PROHIBITED = 5


@dataclass
class IndustryInfo:
    """Industry information"""
    name: str
    tier: IndustryTier
    score: float
    notes: str = ''


# Default industry mappings
DEFAULT_INDUSTRIES = {
    # Tier 1 - Preferred
    'medical': IndustryInfo('Medical/Healthcare', IndustryTier.PREFERRED, 100),
    'dental': IndustryInfo('Dental', IndustryTier.PREFERRED, 100),
    'veterinary': IndustryInfo('Veterinary', IndustryTier.PREFERRED, 100),
    'accounting': IndustryInfo('Accounting', IndustryTier.PREFERRED, 95),
    'legal': IndustryInfo('Legal Services', IndustryTier.PREFERRED, 95),

    # Tier 2 - Standard
    'restaurant': IndustryInfo('Restaurant', IndustryTier.STANDARD, 75),
    'retail': IndustryInfo('Retail', IndustryTier.STANDARD, 75),
    'construction': IndustryInfo('Construction', IndustryTier.STANDARD, 70),
    'trucking': IndustryInfo('Trucking', IndustryTier.STANDARD, 70),
    'auto_repair': IndustryInfo('Auto Repair', IndustryTier.STANDARD, 75),

    # Tier 3 - Non-Preferred
    'bar': IndustryInfo('Bar/Nightclub', IndustryTier.NON_PREFERRED, 50),
    'gas_station': IndustryInfo('Gas Station', IndustryTier.NON_PREFERRED, 50),
    'salon': IndustryInfo('Salon/Spa', IndustryTier.NON_PREFERRED, 55),

    # Tier 4 - High Risk
    'firearms': IndustryInfo('Firearms', IndustryTier.HIGH_RISK, 25),
    'tobacco': IndustryInfo('Tobacco', IndustryTier.HIGH_RISK, 25),
    'pawn': IndustryInfo('Pawn Shop', IndustryTier.HIGH_RISK, 30),

    # Tier 5 - Prohibited
    'gambling': IndustryInfo('Gambling', IndustryTier.PROHIBITED, 0, 'Prohibited'),
    'marijuana': IndustryInfo('Cannabis/Marijuana', IndustryTier.PROHIBITED, 0, 'Prohibited'),
    'adult': IndustryInfo('Adult Entertainment', IndustryTier.PROHIBITED, 0, 'Prohibited'),
}


class IndustryScorer:
    """
    Score industry risk based on classification.

    Usage:
        scorer = IndustryScorer()
        result = scorer.score('restaurant')
    """

    def __init__(self, config_path: str = None):
        self.industries = DEFAULT_INDUSTRIES.copy()

        # Load custom config if provided
        if config_path:
            self._load_config(config_path)

    def _load_config(self, path: str):
        """Load industry config from JSON"""
        try:
            with open(path) as f:
                data = json.load(f)
            # TODO: Parse and merge config
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def score(self, industry: str) -> Dict:
        """
        Score an industry.

        Args:
            industry: Industry name or code

        Returns:
            Dict with score and tier info
        """
        # Normalize input
        key = industry.lower().replace(' ', '_').replace('-', '_')

        # Look up industry
        info = self.industries.get(key)

        if not info:
            # Try partial match
            for k, v in self.industries.items():
                if key in k or k in key:
                    info = v
                    break

        if not info:
            # Default to standard tier
            info = IndustryInfo(
                name=industry,
                tier=IndustryTier.STANDARD,
                score=70,
                notes='Unknown industry - defaulting to Standard'
            )

        return {
            'industry': info.name,
            'tier': info.tier.value,
            'tier_name': info.tier.name,
            'score': info.score,
            'notes': info.notes,
            'prohibited': info.tier == IndustryTier.PROHIBITED,
        }

    def get_tier(self, industry: str) -> IndustryTier:
        """Get industry tier only"""
        result = self.score(industry)
        return IndustryTier(result['tier'])
