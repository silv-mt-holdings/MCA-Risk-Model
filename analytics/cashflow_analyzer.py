"""
Cash Flow Analyzer
==================
Calculate cash flow metrics: trailing averages, trends, volatility.

Usage:
    analyzer = CashFlowAnalyzer(transactions)
    metrics = analyzer.calculate_metrics()
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from datetime import date
import statistics


class TrendDirection(Enum):
    """Cash flow trend direction"""
    INCREASING = 'increasing'
    STABLE = 'stable'
    DECREASING = 'decreasing'
    VOLATILE = 'volatile'


@dataclass
class CashFlowMetrics:
    """Calculated cash flow metrics"""
    trailing_avg_3mo: float = 0.0
    trailing_avg_6mo: float = 0.0
    trailing_avg_12mo: float = 0.0
    trend: TrendDirection = TrendDirection.STABLE
    trend_pct: float = 0.0
    volatility: float = 0.0
    highest_month: float = 0.0
    lowest_month: float = 0.0
    revenue_deposits: float = 0.0
    non_revenue_deposits: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'trailing_avg_3mo': self.trailing_avg_3mo,
            'trailing_avg_6mo': self.trailing_avg_6mo,
            'trailing_avg_12mo': self.trailing_avg_12mo,
            'trend': self.trend.value,
            'trend_pct': self.trend_pct,
            'volatility': self.volatility,
            'highest_month': self.highest_month,
            'lowest_month': self.lowest_month,
            'revenue_deposits': self.revenue_deposits,
            'non_revenue_deposits': self.non_revenue_deposits,
        }


class CashFlowAnalyzer:
    """
    Analyze cash flow from transaction data.

    Calculates trailing averages, trends, and volatility metrics.
    """

    def __init__(self, transactions: List = None, monthly_totals: List[float] = None):
        self.transactions = transactions or []
        self.monthly_totals = monthly_totals or []
        self.metrics: Optional[CashFlowMetrics] = None

    def set_monthly_deposits(self, deposits: List[float]):
        """Set monthly deposit totals directly"""
        self.monthly_totals = deposits

    def calculate_metrics(self) -> CashFlowMetrics:
        """
        Calculate all cash flow metrics.

        Returns:
            CashFlowMetrics object with calculated values
        """
        if not self.monthly_totals and self.transactions:
            self._aggregate_monthly()

        if not self.monthly_totals:
            return CashFlowMetrics()

        totals = self.monthly_totals

        # Trailing averages
        avg_3mo = statistics.mean(totals[-3:]) if len(totals) >= 3 else statistics.mean(totals)
        avg_6mo = statistics.mean(totals[-6:]) if len(totals) >= 6 else statistics.mean(totals)
        avg_12mo = statistics.mean(totals) if totals else 0

        # Trend calculation
        trend, trend_pct = self._calculate_trend(totals)

        # Volatility (coefficient of variation)
        volatility = 0.0
        if len(totals) > 1 and avg_12mo > 0:
            volatility = statistics.stdev(totals) / avg_12mo

        self.metrics = CashFlowMetrics(
            trailing_avg_3mo=round(avg_3mo, 2),
            trailing_avg_6mo=round(avg_6mo, 2),
            trailing_avg_12mo=round(avg_12mo, 2),
            trend=trend,
            trend_pct=round(trend_pct, 2),
            volatility=round(volatility, 4),
            highest_month=max(totals) if totals else 0,
            lowest_month=min(totals) if totals else 0,
        )
        return self.metrics

    def _aggregate_monthly(self):
        """Aggregate transactions into monthly totals"""
        # Group by month and sum deposits
        monthly = {}
        for txn in self.transactions:
            if hasattr(txn, 'amount') and txn.amount > 0:
                key = (txn.date.year, txn.date.month)
                monthly[key] = monthly.get(key, 0) + txn.amount

        # Sort by date and extract values
        sorted_months = sorted(monthly.keys())
        self.monthly_totals = [monthly[k] for k in sorted_months]

    def _calculate_trend(self, values: List[float]) -> tuple:
        """Calculate trend direction and percentage"""
        if len(values) < 2:
            return TrendDirection.STABLE, 0.0

        # Compare recent 3 months to prior 3 months
        if len(values) >= 6:
            recent = statistics.mean(values[-3:])
            prior = statistics.mean(values[-6:-3])
        else:
            recent = values[-1]
            prior = values[0]

        if prior == 0:
            return TrendDirection.STABLE, 0.0

        pct_change = ((recent - prior) / prior) * 100

        if pct_change > 10:
            return TrendDirection.INCREASING, pct_change
        elif pct_change < -10:
            return TrendDirection.DECREASING, pct_change
        else:
            return TrendDirection.STABLE, pct_change
