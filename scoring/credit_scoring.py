"""
Credit Scoring
==============
FICO-based credit scoring and bucketing.

Buckets:
- Excellent: 750+
- Good: 700-749
- Fair: 650-699
- Poor: 600-649
- Very Poor: <600
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class FICOBucket(Enum):
    """FICO score buckets"""
    EXCELLENT = 'excellent'
    GOOD = 'good'
    FAIR = 'fair'
    POOR = 'poor'
    VERY_POOR = 'very_poor'
    UNKNOWN = 'unknown'


@dataclass
class FICOBucketInfo:
    """FICO bucket information"""
    bucket: FICOBucket
    min_score: int
    max_score: int
    score: float  # Normalized score (0-100)
    description: str


# FICO bucket definitions
FICO_BUCKETS = {
    FICOBucket.EXCELLENT: FICOBucketInfo(
        bucket=FICOBucket.EXCELLENT,
        min_score=750,
        max_score=850,
        score=100,
        description='Excellent credit'
    ),
    FICOBucket.GOOD: FICOBucketInfo(
        bucket=FICOBucket.GOOD,
        min_score=700,
        max_score=749,
        score=80,
        description='Good credit'
    ),
    FICOBucket.FAIR: FICOBucketInfo(
        bucket=FICOBucket.FAIR,
        min_score=650,
        max_score=699,
        score=60,
        description='Fair credit'
    ),
    FICOBucket.POOR: FICOBucketInfo(
        bucket=FICOBucket.POOR,
        min_score=600,
        max_score=649,
        score=40,
        description='Poor credit'
    ),
    FICOBucket.VERY_POOR: FICOBucketInfo(
        bucket=FICOBucket.VERY_POOR,
        min_score=300,
        max_score=599,
        score=20,
        description='Very poor credit'
    ),
}


def bucket_from_fico(fico_score: int) -> Optional[FICOBucketInfo]:
    """
    Get FICO bucket from score.

    Args:
        fico_score: FICO credit score (300-850)

    Returns:
        FICOBucketInfo or None if invalid
    """
    if fico_score < 300 or fico_score > 850:
        return None

    if fico_score >= 750:
        return FICO_BUCKETS[FICOBucket.EXCELLENT]
    elif fico_score >= 700:
        return FICO_BUCKETS[FICOBucket.GOOD]
    elif fico_score >= 650:
        return FICO_BUCKETS[FICOBucket.FAIR]
    elif fico_score >= 600:
        return FICO_BUCKETS[FICOBucket.POOR]
    else:
        return FICO_BUCKETS[FICOBucket.VERY_POOR]


class CreditScorer:
    """
    Score credit metrics.

    Usage:
        scorer = CreditScorer()
        result = scorer.score(fico=680, utilization=0.35)
    """

    def __init__(self):
        self.fico_weight = 0.70
        self.utilization_weight = 0.30

    def score(self, fico: int = 0, utilization: float = 0) -> dict:
        """
        Calculate credit score.

        Args:
            fico: FICO credit score
            utilization: Credit utilization ratio (0-1)

        Returns:
            Dict with score breakdown
        """
        # FICO score component
        bucket = bucket_from_fico(fico)
        fico_score = bucket.score if bucket else 50

        # Utilization score (lower is better)
        if utilization <= 0.10:
            util_score = 100
        elif utilization <= 0.30:
            util_score = 80
        elif utilization <= 0.50:
            util_score = 60
        elif utilization <= 0.75:
            util_score = 40
        else:
            util_score = 20

        # Weighted composite
        composite = (fico_score * self.fico_weight) + (util_score * self.utilization_weight)

        return {
            'composite_score': round(composite, 1),
            'fico_score': fico_score,
            'fico_bucket': bucket.bucket.value if bucket else 'unknown',
            'utilization_score': util_score,
            'utilization_pct': utilization * 100,
        }
