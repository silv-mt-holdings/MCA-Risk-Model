"""
Scoring Data Models

Data classes for MCA risk scoring, application data, and scoring results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date


@dataclass
class BankAnalytics:
    """
    Bank statement analytics for scoring.

    This is the primary input from cash flow analysis. All values should be
    based on the most recent 90-day period unless otherwise specified.

    Attributes:
        monthly_true_revenue: Average monthly true revenue
        average_daily_balance: Average daily balance (90 days)
        nsf_count_90d: NSF count over 90 days
        negative_days_90d: Days with negative balance (90 days)
        deposit_variance: Deposit consistency (CV or variance measure)
        total_deposits_90d: Total deposits (all types)
        total_withdrawals_90d: Total withdrawals
        mca_positions: List of identified MCA positions
        cash_flow_margin: Cash flow coverage ratio (CFCR)
        trailing_3mo_avg: 3-month trailing average revenue
        trailing_6mo_avg: 6-month trailing average revenue
        trailing_12mo_avg: 12-month trailing average revenue
    """
    monthly_true_revenue: float = 0.0
    average_daily_balance: float = 0.0
    nsf_count_90d: int = 0
    negative_days_90d: int = 0
    deposit_variance: float = 0.0
    total_deposits_90d: float = 0.0
    total_withdrawals_90d: float = 0.0
    mca_positions: List[str] = field(default_factory=list)
    cash_flow_margin: Optional[float] = None
    trailing_3mo_avg: Optional[float] = None
    trailing_6mo_avg: Optional[float] = None
    trailing_12mo_avg: Optional[float] = None

    @property
    def net_cash_flow(self) -> float:
        """Calculate net cash flow"""
        return self.total_deposits_90d - self.total_withdrawals_90d

    @property
    def position_count(self) -> int:
        """Number of existing MCA positions"""
        return len(self.mca_positions)


@dataclass
class MerchantData:
    """
    Merchant processing data.

    Attributes:
        monthly_volume: Average monthly card processing volume
        tenure_months: Months with current processor
        processor_name: Processor name (e.g., "Square", "Stripe")
        chargeback_count: Number of chargebacks (if available)
        chargeback_ratio: Chargeback ratio (if available)
    """
    monthly_volume: float = 0.0
    tenure_months: int = 0
    processor_name: str = "unknown"
    chargeback_count: Optional[int] = None
    chargeback_ratio: Optional[float] = None

    @property
    def is_available(self) -> bool:
        """Returns True if merchant data is available"""
        return self.monthly_volume > 0


@dataclass
class ApplicationData:
    """
    Application and business profile data.

    Attributes:
        business_name: Legal business name
        dba_name: DBA name if different
        ein: Employer Identification Number
        entity_type: Entity type (LLC, Corp, Sole Prop, etc.)
        industry: Industry classification
        fico_score: Self-reported FICO score
        time_in_business_months: Time in business (months)
        owner_name: Owner name
        state: Business state
        monthly_merchant_volume: Monthly card volume (from merchant data)
        merchant_tenure_months: Merchant tenure (from merchant data)
        requested_amount: Funding amount requested
    """
    business_name: str = ""
    dba_name: str = ""
    ein: str = ""
    entity_type: str = ""
    industry: str = ""
    fico_score: int = 0
    time_in_business_months: int = 0
    owner_name: str = ""
    state: str = ""
    monthly_merchant_volume: float = 0.0
    merchant_tenure_months: int = 0
    requested_amount: float = 0.0

    @property
    def has_merchant_data(self) -> bool:
        """Returns True if merchant data is present"""
        return self.monthly_merchant_volume > 0


@dataclass
class PreCheckResult:
    """
    Pre-check validation result.

    Identifies blockers and warnings before scoring.

    Attributes:
        passed: True if no blockers found
        blockers: List of blocking issues (must be resolved)
        warnings: List of warning conditions (proceed with caution)
        message: Summary message
    """
    passed: bool = True
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    message: str = ""

    def add_blocker(self, message: str):
        """Add a blocking issue"""
        self.blockers.append(message)
        self.passed = False

    def add_warning(self, message: str):
        """Add a warning condition"""
        self.warnings.append(message)

    @property
    def has_warnings(self) -> bool:
        """Returns True if warnings present"""
        return len(self.warnings) > 0


@dataclass
class ScoringResult:
    """
    Comprehensive MCA scoring result.

    Attributes:
        total_score: Total score (0-100)
        letter_grade: Letter grade (A+ through F)
        tier: Risk tier (1-5)
        component_scores: Dict of individual component scores
        recommended_factor: Recommended factor rate
        max_advance_pct: Maximum advance percentage
        max_advance: Maximum advance amount (dollar)
        term_months_range: Recommended term range (min, max)
        pre_check: Pre-check result
        industry_note: Industry-specific notes
        warnings: List of warnings
        metadata: Additional metadata
        scored_at: Timestamp of scoring
    """
    total_score: float = 0.0
    letter_grade: str = "F"
    tier: int = 5
    component_scores: Dict[str, float] = field(default_factory=dict)
    recommended_factor: float = 1.50
    max_advance_pct: float = 0.05
    max_advance: float = 0.0
    term_months_range: tuple = (2, 4)
    pre_check: Optional[PreCheckResult] = None
    industry_note: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    scored_at: Optional[date] = None

    @property
    def is_approvable(self) -> bool:
        """Returns True if score is approvable (≥40 points)"""
        return self.total_score >= 40

    @property
    def is_tier_1(self) -> bool:
        """Returns True if tier 1 (A paper)"""
        return self.tier == 1

    @property
    def has_blockers(self) -> bool:
        """Returns True if pre-check has blockers"""
        return self.pre_check is not None and not self.pre_check.passed

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'total_score': round(self.total_score, 2),
            'letter_grade': self.letter_grade,
            'tier': self.tier,
            'component_scores': {k: round(v, 2) for k, v in self.component_scores.items()},
            'recommended_factor': round(self.recommended_factor, 2),
            'max_advance_pct': round(self.max_advance_pct, 4),
            'max_advance': round(self.max_advance, 2),
            'term_months_range': self.term_months_range,
            'is_approvable': self.is_approvable,
            'industry_note': self.industry_note,
            'warnings': self.warnings,
            'metadata': self.metadata,
        }

    def __str__(self) -> str:
        """String representation"""
        return f"ScoringResult(grade={self.letter_grade}, score={self.total_score:.1f}, factor={self.recommended_factor:.2f})"
