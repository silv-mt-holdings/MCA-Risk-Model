"""
Scoring Module
==============
Composite risk scoring and letter grade assignment.

Components:
- MCAScorecard: Main scoring orchestrator
- CreditScorer: FICO-based scoring
- IndustryScorer: Industry risk tier scoring
- LetterGrader: Score-to-grade conversion
- CompositeScorer: Weighted score calculation
"""

from .mca_scorecard import (
    MCAScorecard,
    ScoringResult,
)

from .credit_scoring import (
    CreditScorer,
    FICOBucket,
    bucket_from_fico,
)

from .industry_scorer import (
    IndustryScorer,
    IndustryTier,
)

from .letter_grader import (
    LetterGrader,
    LetterGrade,
    grade_from_score,
)

from .composite_scorer import (
    CompositeScorer,
    CategoryScore,
)

__all__ = [
    'MCAScorecard',
    'ScoringResult',
    'CreditScorer',
    'FICOBucket',
    'bucket_from_fico',
    'IndustryScorer',
    'IndustryTier',
    'LetterGrader',
    'LetterGrade',
    'grade_from_score',
    'CompositeScorer',
    'CategoryScore',
]
