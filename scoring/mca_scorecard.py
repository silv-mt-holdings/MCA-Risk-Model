"""
MCA Scorecard
=============
Main scoring orchestrator for MCA risk assessment.

Combines metrics from all categories into a composite score
and assigns a letter grade.

Usage:
    scorecard = MCAScorecard()
    scorecard.set_bank_metrics(...)
    scorecard.set_credit_metrics(...)
    result = scorecard.calculate()
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from .composite_scorer import CompositeScorer, CategoryScore
from .letter_grader import LetterGrader, LetterGrade, grade_from_score
from .credit_scoring import CreditScorer, bucket_from_fico
from .industry_scorer import IndustryScorer


@dataclass
class ScoringResult:
    """Complete scoring result"""
    score: float = 0.0
    letter_grade: str = 'F'
    grade_info: Optional[LetterGrade] = None
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)
    recommendation: str = ''

    def summary(self) -> str:
        """Return formatted summary string"""
        lines = [
            f"Score: {self.score:.1f}/100",
            f"Grade: {self.letter_grade}",
            f"Risk Level: {self.grade_info.risk_level if self.grade_info else 'Unknown'}",
            "",
            "Category Breakdown:",
        ]
        for name, cat in self.category_scores.items():
            lines.append(f"  {name}: {cat.score:.1f}/{cat.max_score} ({cat.weight*100:.0f}%)")

        if self.risk_flags:
            lines.append("")
            lines.append("Risk Flags:")
            for flag in self.risk_flags:
                lines.append(f"  - {flag}")

        return "\n".join(lines)


class MCAScorecard:
    """
    Main MCA scoring orchestrator.

    Collects metrics from all sources, calculates weighted composite score,
    and assigns letter grade with recommendations.
    """

    def __init__(self):
        self.bank_metrics: Dict = {}
        self.credit_metrics: Dict = {}
        self.industry: str = ''
        self.deal_metrics: Dict = {}
        self.risk_flags: List[str] = []

        # Component scorers
        self.composite_scorer = CompositeScorer()
        self.grader = LetterGrader()
        self.credit_scorer = CreditScorer()
        self.industry_scorer = IndustryScorer()

    def set_bank_metrics(
        self,
        trailing_avg_3mo: float = 0,
        trailing_avg_6mo: float = 0,
        trend: str = 'stable',
        volatility: float = 0,
        nsf_count: int = 0,
        avg_daily_balance: float = 0,
    ):
        """Set bank statement metrics"""
        self.bank_metrics = {
            'trailing_avg_3mo': trailing_avg_3mo,
            'trailing_avg_6mo': trailing_avg_6mo,
            'trend': trend,
            'volatility': volatility,
            'nsf_count': nsf_count,
            'avg_daily_balance': avg_daily_balance,
        }
        return self

    def set_credit_metrics(
        self,
        fico_score: int = 0,
        credit_utilization: float = 0,
    ):
        """Set credit metrics"""
        self.credit_metrics = {
            'fico_score': fico_score,
            'credit_utilization': credit_utilization,
        }
        return self

    def set_industry(self, industry: str):
        """Set industry for risk tier scoring"""
        self.industry = industry
        return self

    def set_deal_metrics(
        self,
        position_count: int = 0,
        funding_amount: float = 0,
        time_in_business_months: int = 0,
    ):
        """Set deal-specific metrics"""
        self.deal_metrics = {
            'position_count': position_count,
            'funding_amount': funding_amount,
            'time_in_business_months': time_in_business_months,
        }
        return self

    def add_risk_flag(self, flag: str):
        """Add a risk flag"""
        self.risk_flags.append(flag)
        return self

    def load_metrics(self, metrics: Dict):
        """Load metrics from a dictionary (e.g., from analytics module)"""
        if 'bank' in metrics:
            self.set_bank_metrics(**metrics['bank'])
        if 'credit' in metrics:
            self.set_credit_metrics(**metrics['credit'])
        if 'industry' in metrics:
            self.set_industry(metrics['industry'])
        if 'deal' in metrics:
            self.set_deal_metrics(**metrics['deal'])
        return self

    def calculate(self) -> ScoringResult:
        """
        Calculate composite score and assign letter grade.

        Returns:
            ScoringResult with score, grade, and breakdown
        """
        # Calculate category scores
        bank_score = self._score_bank_metrics()
        credit_score = self._score_credit_metrics()
        industry_score = self._score_industry()
        deal_score = self._score_deal_metrics()

        # Build category scores dict
        category_scores = {
            'bank_metrics': bank_score,
            'credit_metrics': credit_score,
            'industry_metrics': industry_score,
            'deal_metrics': deal_score,
        }

        # Calculate composite
        total_score = sum(cat.weighted_score for cat in category_scores.values())

        # Get letter grade
        grade_info = grade_from_score(total_score)

        # Check for auto-fail conditions
        self._check_risk_flags()

        return ScoringResult(
            score=round(total_score, 1),
            letter_grade=grade_info.grade,
            grade_info=grade_info,
            category_scores=category_scores,
            risk_flags=self.risk_flags,
            recommendation=self._get_recommendation(grade_info.grade),
        )

    def _score_bank_metrics(self) -> CategoryScore:
        """Score bank metrics (40% weight)"""
        # TODO: Implement detailed scoring logic
        base_score = 70  # Placeholder
        return CategoryScore(
            name='bank_metrics',
            score=base_score,
            max_score=100,
            weight=0.40,
            weighted_score=base_score * 0.40,
        )

    def _score_credit_metrics(self) -> CategoryScore:
        """Score credit metrics (25% weight)"""
        fico = self.credit_metrics.get('fico_score', 0)
        bucket = bucket_from_fico(fico)
        score = bucket.score if bucket else 50

        return CategoryScore(
            name='credit_metrics',
            score=score,
            max_score=100,
            weight=0.25,
            weighted_score=score * 0.25,
        )

    def _score_industry(self) -> CategoryScore:
        """Score industry risk (20% weight)"""
        tier_result = self.industry_scorer.score(self.industry)

        return CategoryScore(
            name='industry_metrics',
            score=tier_result['score'],
            max_score=100,
            weight=0.20,
            weighted_score=tier_result['score'] * 0.20,
        )

    def _score_deal_metrics(self) -> CategoryScore:
        """Score deal metrics (15% weight)"""
        # TODO: Implement detailed scoring logic
        base_score = 75  # Placeholder
        return CategoryScore(
            name='deal_metrics',
            score=base_score,
            max_score=100,
            weight=0.15,
            weighted_score=base_score * 0.15,
        )

    def _check_risk_flags(self):
        """Check for automatic risk flags"""
        if self.bank_metrics.get('nsf_count', 0) > 5:
            self.risk_flags.append('High NSF activity (>5 in period)')

        if self.credit_metrics.get('fico_score', 700) < 500:
            self.risk_flags.append('Very low FICO score (<500)')

        if self.deal_metrics.get('position_count', 0) > 4:
            self.risk_flags.append('Heavy stacking (>4 positions)')

    def _get_recommendation(self, grade: str) -> str:
        """Get recommendation based on grade"""
        recommendations = {
            'A': 'Approve - Low risk, standard terms',
            'B': 'Approve - Moderate risk, consider adjusted terms',
            'C': 'Review - Standard risk, manual review recommended',
            'D': 'Caution - High risk, require additional documentation',
            'F': 'Decline - Very high risk',
        }
        return recommendations.get(grade, 'Manual review required')
