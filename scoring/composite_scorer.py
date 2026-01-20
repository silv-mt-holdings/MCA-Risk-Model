"""
Composite Scorer
================
Calculate weighted composite scores from multiple categories.

Default Weights:
- bank_metrics: 40%
- credit_metrics: 25%
- industry_metrics: 20%
- deal_metrics: 15%
"""

from dataclasses import dataclass
from typing import Dict, List
import json


@dataclass
class CategoryScore:
    """Score for a single category"""
    name: str
    score: float
    max_score: float = 100.0
    weight: float = 0.0
    weighted_score: float = 0.0
    components: Dict = None

    def __post_init__(self):
        if self.components is None:
            self.components = {}
        if self.weighted_score == 0 and self.weight > 0:
            self.weighted_score = self.score * self.weight


# Default category weights
DEFAULT_WEIGHTS = {
    'bank_metrics': 0.40,
    'credit_metrics': 0.25,
    'industry_metrics': 0.20,
    'deal_metrics': 0.15,
}


class CompositeScorer:
    """
    Calculate weighted composite scores.

    Usage:
        scorer = CompositeScorer()
        scorer.add_score('bank_metrics', 75)
        scorer.add_score('credit_metrics', 80)
        composite = scorer.calculate()
    """

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.scores: Dict[str, CategoryScore] = {}

    def load_weights(self, config_path: str):
        """Load weights from JSON config"""
        try:
            with open(config_path) as f:
                data = json.load(f)
            self.weights = data.get('weights', self.weights)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def add_score(self, category: str, score: float, components: Dict = None):
        """
        Add a category score.

        Args:
            category: Category name
            score: Score value (0-100)
            components: Optional breakdown of score components
        """
        weight = self.weights.get(category, 0)
        self.scores[category] = CategoryScore(
            name=category,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            components=components or {},
        )

    def calculate(self) -> float:
        """
        Calculate composite score.

        Returns:
            Weighted composite score (0-100)
        """
        if not self.scores:
            return 0.0

        total = sum(cat.weighted_score for cat in self.scores.values())
        return round(total, 2)

    def get_breakdown(self) -> Dict[str, CategoryScore]:
        """Get score breakdown by category"""
        return self.scores

    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = sum(self.weights.values())
        return abs(total - 1.0) < 0.001
