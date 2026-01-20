"""
NSF Analyzer
============
Analyze NSF (Non-Sufficient Funds) and overdraft activity.

Scoring:
- 0 NSF in 12 months: Excellent
- 1-2 NSF: Good
- 3-5 NSF: Fair
- 6+ NSF: Poor
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
import re


class NSFRating(Enum):
    """NSF activity rating"""
    EXCELLENT = 'excellent'
    GOOD = 'good'
    FAIR = 'fair'
    POOR = 'poor'


@dataclass
class NSFMetrics:
    """NSF analysis metrics"""
    total_nsf_count: int = 0
    total_nsf_amount: float = 0.0
    nsf_fees_paid: float = 0.0
    overdraft_days: int = 0
    rating: NSFRating = NSFRating.EXCELLENT
    score: float = 100.0

    def to_dict(self) -> Dict:
        return {
            'total_nsf_count': self.total_nsf_count,
            'total_nsf_amount': self.total_nsf_amount,
            'nsf_fees_paid': self.nsf_fees_paid,
            'overdraft_days': self.overdraft_days,
            'rating': self.rating.value,
            'score': self.score,
        }


# NSF detection patterns
NSF_PATTERNS = [
    r'NSF',
    r'NON.?SUFFICIENT',
    r'INSUFFICIENT',
    r'RETURNED.?ITEM',
    r'RETURN.?CHECK',
    r'OVERDRAFT',
    r'OD FEE',
    r'UNCOLLECTED',
]


class NSFAnalyzer:
    """
    Analyze NSF and overdraft activity.

    Usage:
        analyzer = NSFAnalyzer(transactions)
        metrics = analyzer.analyze()
    """

    def __init__(self, transactions: List = None):
        self.transactions = transactions or []
        self.nsf_patterns = [re.compile(p, re.I) for p in NSF_PATTERNS]
        self.metrics: NSFMetrics = NSFMetrics()

    def analyze(self) -> NSFMetrics:
        """
        Analyze all transactions for NSF activity.

        Returns:
            NSFMetrics with analysis results
        """
        nsf_count = 0
        nsf_amount = 0.0
        fees = 0.0
        od_days = 0

        for txn in self.transactions:
            desc = getattr(txn, 'description', '')
            amount = getattr(txn, 'amount', 0)
            balance = getattr(txn, 'balance', 0)

            # Check for NSF
            if self._is_nsf(desc):
                nsf_count += 1
                nsf_amount += abs(amount)
                if 'FEE' in desc.upper():
                    fees += abs(amount)

            # Track overdraft days
            if balance < 0:
                od_days += 1

        # Calculate rating and score
        rating, score = self._calculate_rating(nsf_count)

        self.metrics = NSFMetrics(
            total_nsf_count=nsf_count,
            total_nsf_amount=nsf_amount,
            nsf_fees_paid=fees,
            overdraft_days=od_days,
            rating=rating,
            score=score,
        )
        return self.metrics

    def _is_nsf(self, description: str) -> bool:
        """Check if description indicates NSF activity"""
        for pattern in self.nsf_patterns:
            if pattern.search(description):
                return True
        return False

    def _calculate_rating(self, nsf_count: int) -> tuple:
        """Calculate NSF rating and score based on count"""
        if nsf_count == 0:
            return NSFRating.EXCELLENT, 100.0
        elif nsf_count <= 2:
            return NSFRating.GOOD, 80.0
        elif nsf_count <= 5:
            return NSFRating.FAIR, 50.0
        else:
            return NSFRating.POOR, 20.0
