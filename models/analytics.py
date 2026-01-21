"""
Analytics Data Models

Data classes for cash flow analysis, deposit categorization, and balance tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import date


class DepositCategory(Enum):
    """Categories for deposit classification"""
    CASH = "cash"
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    CARD_PROCESSING = "card_processing"
    MOBILE_PAYMENT = "mobile_payment"
    TRANSFER = "transfer"
    OTHER = "other"


@dataclass
class MonthlyData:
    """
    Monthly summary data for cash flow analysis.

    Attributes:
        period: Month period (YYYY-MM format)
        year: Year
        month: Month (1-12)
        beginning_balance: Starting balance
        ending_balance: Ending balance
        total_deposits: Sum of all deposits
        total_withdrawals: Sum of all withdrawals
        deposit_count: Number of deposit transactions
        withdrawal_count: Number of withdrawal transactions
        net_cash_flow: Net change (deposits - withdrawals)
        avg_deposit: Average deposit amount
        max_deposit: Largest single deposit
        min_deposit: Smallest deposit
        average_balance: Average balance for the month
        nsf_count: Number of NSF fees
        negative_days: Days with negative balance
    """
    period: str
    year: int
    month: int
    beginning_balance: float = 0.0
    ending_balance: float = 0.0
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    deposit_count: int = 0
    withdrawal_count: int = 0
    net_cash_flow: float = 0.0
    avg_deposit: float = 0.0
    max_deposit: float = 0.0
    min_deposit: float = 0.0
    average_balance: float = 0.0
    nsf_count: int = 0
    negative_days: int = 0

    @property
    def deposit_variance(self) -> float:
        """Calculate variance as (max - min) / avg if available"""
        if self.avg_deposit > 0 and self.max_deposit > 0:
            return (self.max_deposit - self.min_deposit) / self.avg_deposit
        return 0.0


@dataclass
class BalanceMetrics:
    """
    Balance tracking metrics.

    Attributes:
        average_daily_balance: Average daily balance over period
        min_balance: Lowest balance observed
        max_balance: Highest balance observed
        negative_days: Number of days with negative balance
        below_threshold_days: Days below critical threshold
        balance_trend: Trend direction (increasing, stable, decreasing)
        volatility: Balance volatility measure (std dev / mean)
    """
    average_daily_balance: float = 0.0
    min_balance: float = 0.0
    max_balance: float = 0.0
    negative_days: int = 0
    below_threshold_days: int = 0
    balance_trend: str = "stable"
    volatility: float = 0.0

    @property
    def is_healthy(self) -> bool:
        """Returns True if balance metrics are healthy"""
        return (
            self.negative_days == 0 and
            self.average_daily_balance > 0 and
            self.volatility < 1.0
        )


@dataclass
class CashFlowSummary:
    """
    Comprehensive cash flow analysis summary.

    Attributes:
        period_start: Analysis start date
        period_end: Analysis end date
        true_revenue_90d: True revenue over 90 days
        monthly_true_revenue: Average monthly true revenue
        total_deposits_90d: Total deposits (90 days)
        total_withdrawals_90d: Total withdrawals (90 days)
        average_daily_balance: ADB over period
        nsf_count: NSF fees detected
        negative_days: Days with negative balance
        mca_payment_total: Total MCA payments detected
        deposit_consistency: Deposit consistency score (0-1)
        cash_flow_margin: Available cash flow margin
        trailing_3mo_avg: 3-month trailing average
        trailing_6mo_avg: 6-month trailing average
        trailing_12mo_avg: 12-month trailing average
        trend: Cash flow trend (increasing, stable, declining)
        red_flags: List of identified issues
        warnings: List of warning conditions
    """
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    true_revenue_90d: float = 0.0
    monthly_true_revenue: float = 0.0
    total_deposits_90d: float = 0.0
    total_withdrawals_90d: float = 0.0
    average_daily_balance: float = 0.0
    nsf_count: int = 0
    negative_days: int = 0
    mca_payment_total: float = 0.0
    deposit_consistency: float = 0.0
    cash_flow_margin: float = 0.0
    trailing_3mo_avg: Optional[float] = None
    trailing_6mo_avg: Optional[float] = None
    trailing_12mo_avg: Optional[float] = None
    trend: str = "stable"
    red_flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def net_cash_flow(self) -> float:
        """Calculate net cash flow"""
        return self.total_deposits_90d - self.total_withdrawals_90d

    @property
    def has_red_flags(self) -> bool:
        """Returns True if any red flags present"""
        return len(self.red_flags) > 0

    @property
    def cfcr(self) -> float:
        """
        Calculate Cash Flow Coverage Ratio.
        (Deposits - Withdrawals - MCA Payments) / Deposits
        """
        if self.total_deposits_90d > 0:
            available = self.total_deposits_90d - self.total_withdrawals_90d - self.mca_payment_total
            return available / self.total_deposits_90d
        return 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'period_start': str(self.period_start) if self.period_start else None,
            'period_end': str(self.period_end) if self.period_end else None,
            'true_revenue_90d': self.true_revenue_90d,
            'monthly_true_revenue': self.monthly_true_revenue,
            'total_deposits_90d': self.total_deposits_90d,
            'total_withdrawals_90d': self.total_withdrawals_90d,
            'average_daily_balance': self.average_daily_balance,
            'nsf_count': self.nsf_count,
            'negative_days': self.negative_days,
            'mca_payment_total': self.mca_payment_total,
            'deposit_consistency': self.deposit_consistency,
            'cash_flow_margin': self.cash_flow_margin,
            'net_cash_flow': self.net_cash_flow,
            'cfcr': self.cfcr,
            'trend': self.trend,
            'red_flags': self.red_flags,
            'warnings': self.warnings,
        }
