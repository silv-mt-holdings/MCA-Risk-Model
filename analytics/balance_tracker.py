"""
Balance Tracker
===============
Track daily balances and calculate average daily balance (ADB).

Metrics:
- Average Daily Balance
- Low balance days (< threshold)
- Negative balance days
- Balance volatility
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date, timedelta
import statistics


@dataclass
class BalanceMetrics:
    """Balance tracking metrics"""
    average_daily_balance: float = 0.0
    lowest_balance: float = 0.0
    highest_balance: float = 0.0
    negative_days: int = 0
    low_balance_days: int = 0  # Days below threshold
    low_balance_threshold: float = 1000.0
    volatility: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'average_daily_balance': self.average_daily_balance,
            'lowest_balance': self.lowest_balance,
            'highest_balance': self.highest_balance,
            'negative_days': self.negative_days,
            'low_balance_days': self.low_balance_days,
            'low_balance_threshold': self.low_balance_threshold,
            'volatility': self.volatility,
        }


class BalanceTracker:
    """
    Track and analyze daily balances.

    Usage:
        tracker = BalanceTracker(transactions)
        tracker.set_threshold(500)  # $500 low balance threshold
        metrics = tracker.calculate()
    """

    def __init__(self, transactions: List = None):
        self.transactions = transactions or []
        self.daily_balances: Dict[date, float] = {}
        self.low_threshold = 1000.0
        self.metrics: Optional[BalanceMetrics] = None

    def set_threshold(self, threshold: float):
        """Set the low balance threshold"""
        self.low_threshold = threshold

    def set_daily_balances(self, balances: Dict[date, float]):
        """Set daily balances directly"""
        self.daily_balances = balances

    def calculate(self) -> BalanceMetrics:
        """
        Calculate balance metrics.

        Returns:
            BalanceMetrics with calculated values
        """
        if not self.daily_balances and self.transactions:
            self._build_daily_balances()

        if not self.daily_balances:
            return BalanceMetrics()

        balances = list(self.daily_balances.values())

        # Calculate metrics
        adb = statistics.mean(balances)
        negative_days = sum(1 for b in balances if b < 0)
        low_days = sum(1 for b in balances if 0 <= b < self.low_threshold)

        volatility = 0.0
        if len(balances) > 1 and adb > 0:
            volatility = statistics.stdev(balances) / adb

        self.metrics = BalanceMetrics(
            average_daily_balance=round(adb, 2),
            lowest_balance=min(balances),
            highest_balance=max(balances),
            negative_days=negative_days,
            low_balance_days=low_days,
            low_balance_threshold=self.low_threshold,
            volatility=round(volatility, 4),
        )
        return self.metrics

    def _build_daily_balances(self):
        """Build daily balance map from transactions"""
        if not self.transactions:
            return

        # Sort by date
        sorted_txns = sorted(self.transactions, key=lambda t: t.date)

        # Get date range
        start_date = sorted_txns[0].date
        end_date = sorted_txns[-1].date

        # Build daily balances (forward fill)
        current_balance = sorted_txns[0].balance - sorted_txns[0].amount
        txn_idx = 0

        current_date = start_date
        while current_date <= end_date:
            # Apply all transactions for this date
            while txn_idx < len(sorted_txns) and sorted_txns[txn_idx].date == current_date:
                current_balance = sorted_txns[txn_idx].balance
                txn_idx += 1

            self.daily_balances[current_date] = current_balance
            current_date += timedelta(days=1)
