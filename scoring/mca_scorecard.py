"""
MCA Scoring Model v2.0
Standalone Letter Grade Risk Scoring Engine

Letter Grading: A+, A, A-, B+, B, B-, C+, C, C-, D+, D, D-, F

Data Sources:
- Bank Statement Analytics (manual input or from parsing module)
- Self-Reported FICO (unverified - weighted accordingly)
- Merchant Processing Data
- Industry Risk Segmentation

Author: Silv MT Holdings
Version: 2.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import date, datetime
import re

# Import credit scoring components
from .credit_scoring import (
    bucket_from_fico,
    grade_from_score,
    LetterGrader,
    CreditScorer
)

# Import precheck module for Google Places verification
try:
    from .precheck import run_precheck, precheck_to_score_adjustment, PrecheckResult, PrecheckStatus
    _HAS_PRECHECK = True
except ImportError:
    _HAS_PRECHECK = False

# =============================================================================
# OPTIONAL INTEGRATION: parsing module
# Risk Model can run STANDALONE or integrate with bank_statement_parser
# =============================================================================
try:
    from parsing.bank_statement_parser import (
        BankStatementParser,
        CashFlowSummary,
        MCAPosition,
        RevenueType,
        lookup_mca
    )
    _HAS_BANK_PARSER = True
except ImportError:
    _HAS_BANK_PARSER = False


# =============================================================================
# LETTER GRADE SYSTEM (13 Grades)
# =============================================================================

LETTER_GRADES = {
    'A+': {'min_score': 95, 'max_score': 100, 'tier': 1, 'factor_range': (1.10, 1.15), 'max_advance_pct': 0.20, 'term_months': (3, 6)},
    'A':  {'min_score': 90, 'max_score': 94,  'tier': 1, 'factor_range': (1.12, 1.18), 'max_advance_pct': 0.18, 'term_months': (3, 6)},
    'A-': {'min_score': 85, 'max_score': 89,  'tier': 1, 'factor_range': (1.15, 1.20), 'max_advance_pct': 0.16, 'term_months': (3, 6)},
    'B+': {'min_score': 80, 'max_score': 84,  'tier': 2, 'factor_range': (1.18, 1.25), 'max_advance_pct': 0.15, 'term_months': (4, 8)},
    'B':  {'min_score': 75, 'max_score': 79,  'tier': 2, 'factor_range': (1.22, 1.28), 'max_advance_pct': 0.14, 'term_months': (4, 8)},
    'B-': {'min_score': 70, 'max_score': 74,  'tier': 2, 'factor_range': (1.25, 1.32), 'max_advance_pct': 0.12, 'term_months': (4, 8)},
    'C+': {'min_score': 65, 'max_score': 69,  'tier': 3, 'factor_range': (1.28, 1.35), 'max_advance_pct': 0.11, 'term_months': (4, 6)},
    'C':  {'min_score': 60, 'max_score': 64,  'tier': 3, 'factor_range': (1.32, 1.38), 'max_advance_pct': 0.10, 'term_months': (4, 6)},
    'C-': {'min_score': 55, 'max_score': 59,  'tier': 3, 'factor_range': (1.35, 1.42), 'max_advance_pct': 0.09, 'term_months': (4, 6)},
    'D+': {'min_score': 50, 'max_score': 54,  'tier': 4, 'factor_range': (1.38, 1.45), 'max_advance_pct': 0.08, 'term_months': (3, 5)},
    'D':  {'min_score': 45, 'max_score': 49,  'tier': 4, 'factor_range': (1.42, 1.48), 'max_advance_pct': 0.07, 'term_months': (3, 5)},
    'D-': {'min_score': 40, 'max_score': 44,  'tier': 4, 'factor_range': (1.45, 1.52), 'max_advance_pct': 0.06, 'term_months': (3, 4)},
    'F':  {'min_score': 0,  'max_score': 39,  'tier': 5, 'factor_range': (1.50, 1.65), 'max_advance_pct': 0.05, 'term_months': (2, 4)},
}


# =============================================================================
# SCORING WEIGHTS (100 points total)
# =============================================================================

SCORING_WEIGHTS = {
    'true_revenue':           15,
    'cash_flow_margin':       12,
    'average_daily_balance':  10,
    'nsf_overdraft':          10,
    'deposit_consistency':     8,
    'fico_score':             12,
    'merchant_volume':         8,
    'merchant_tenure':         5,
    'time_in_business':        8,
    'industry_risk':           7,
    'existing_positions':      5,
}

assert sum(SCORING_WEIGHTS.values()) == 100


# =============================================================================
# INDUSTRY SEGMENTATION
# =============================================================================

INDUSTRY_SEGMENTS = {
    # TIER 1 - PREFERRED
    'medical_practice':     {'tier': 1, 'adjustment': +5, 'factor_mod': -0.03, 'note': 'Recession-proof'},
    'dental':               {'tier': 1, 'adjustment': +5, 'factor_mod': -0.03, 'note': 'High margins'},
    'healthcare':           {'tier': 1, 'adjustment': +4, 'factor_mod': -0.02, 'note': 'Essential services'},
    'veterinary':           {'tier': 1, 'adjustment': +4, 'factor_mod': -0.02, 'note': 'Stable demand'},
    'legal_services':       {'tier': 1, 'adjustment': +3, 'factor_mod': -0.02, 'note': 'Established CF'},
    'accounting':           {'tier': 1, 'adjustment': +3, 'factor_mod': -0.02, 'note': 'Recurring revenue'},
    'professional_services':{'tier': 1, 'adjustment': +3, 'factor_mod': -0.02, 'note': 'Low overhead'},
    'it_services':          {'tier': 1, 'adjustment': +3, 'factor_mod': -0.02, 'note': 'High margins'},
    'saas':                 {'tier': 1, 'adjustment': +4, 'factor_mod': -0.02, 'note': 'Recurring MRR'},
    'medical':              {'tier': 1, 'adjustment': +5, 'factor_mod': -0.03, 'note': 'Recession-proof'},

    # TIER 2 - STANDARD
    'manufacturing':        {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Standard risk'},
    'wholesale':            {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Standard risk'},
    'ecommerce':            {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Verify processor'},
    'general_contractor':   {'tier': 2, 'adjustment': -2, 'factor_mod': 0.02, 'note': 'Project-based'},
    'hvac':                 {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Seasonal'},
    'plumbing':             {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Service-based'},
    'electrical':           {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Service-based'},
    'auto_body':            {'tier': 2, 'adjustment': -2, 'factor_mod': 0.02, 'note': 'Insurance dependent'},
    'salon_spa':            {'tier': 2, 'adjustment': 0, 'factor_mod': 0.00, 'note': 'Cash + card mix'},

    # TIER 3 - ELEVATED
    'restaurant':           {'tier': 3, 'adjustment': -8, 'factor_mod': 0.08, 'note': '60% fail in 5 years'},
    'bar_nightclub':        {'tier': 3, 'adjustment': -10, 'factor_mod': 0.10, 'note': 'Cash intensive'},
    'retail':               {'tier': 3, 'adjustment': -6, 'factor_mod': 0.05, 'note': 'E-commerce pressure'},
    'convenience_store':    {'tier': 3, 'adjustment': -5, 'factor_mod': 0.05, 'note': 'Cash intensive'},
    'gas_station':          {'tier': 3, 'adjustment': -6, 'factor_mod': 0.06, 'note': 'Thin margins'},
    'hotel_motel':          {'tier': 3, 'adjustment': -6, 'factor_mod': 0.05, 'note': 'Seasonal'},
    'staffing':             {'tier': 3, 'adjustment': -5, 'factor_mod': 0.05, 'note': 'AR dependent'},
    'landscaping':          {'tier': 3, 'adjustment': -4, 'factor_mod': 0.04, 'note': 'Seasonal'},
    'moving_company':       {'tier': 3, 'adjustment': -5, 'factor_mod': 0.05, 'note': 'Liability'},
    'dry_cleaner':          {'tier': 3, 'adjustment': -4, 'factor_mod': 0.04, 'note': 'Declining'},

    # TIER 4 - HIGH RISK
    'trucking':             {'tier': 4, 'adjustment': -12, 'factor_mod': 0.12, 'note': 'Fuel costs'},
    'transportation':       {'tier': 4, 'adjustment': -12, 'factor_mod': 0.12, 'note': 'High liability'},
    'construction':         {'tier': 4, 'adjustment': -12, 'factor_mod': 0.12, 'note': '25% fail in 1 year'},
    'used_cars':            {'tier': 4, 'adjustment': -15, 'factor_mod': 0.15, 'note': 'Floor plan'},
    'auto_dealer':          {'tier': 4, 'adjustment': -15, 'factor_mod': 0.15, 'note': 'Inventory risk'},
    'jewelry':              {'tier': 4, 'adjustment': -10, 'factor_mod': 0.10, 'note': 'Theft risk'},
    'travel_agency':        {'tier': 4, 'adjustment': -10, 'factor_mod': 0.10, 'note': 'Volatile'},
    'taxi_limo':            {'tier': 4, 'adjustment': -8, 'factor_mod': 0.08, 'note': 'Rideshare competition'},
    'towing':               {'tier': 4, 'adjustment': -6, 'factor_mod': 0.06, 'note': 'Equipment dependent'},

    # TIER 5 - SPECIALTY
    'gambling':             {'tier': 5, 'adjustment': -25, 'factor_mod': 0.20, 'note': 'Specialty'},
    'cannabis':             {'tier': 5, 'adjustment': -50, 'factor_mod': 0.25, 'note': 'Federal banking limits'},
    'cbd':                  {'tier': 5, 'adjustment': -20, 'factor_mod': 0.15, 'note': 'Verify compliance'},
    'adult_entertainment':  {'tier': 5, 'adjustment': -25, 'factor_mod': 0.20, 'note': 'Cash intensive'},
    'firearms':             {'tier': 5, 'adjustment': -20, 'factor_mod': 0.15, 'note': 'Licensing required'},
    'bail_bonds':           {'tier': 5, 'adjustment': -20, 'factor_mod': 0.18, 'note': 'Irregular CF'},
    'check_cashing':        {'tier': 5, 'adjustment': -30, 'factor_mod': 0.22, 'note': 'BSA/AML scrutiny'},
    'pawn_shop':            {'tier': 5, 'adjustment': -18, 'factor_mod': 0.15, 'note': 'Inventory/theft'},
    'crypto':               {'tier': 5, 'adjustment': -30, 'factor_mod': 0.25, 'note': 'Volatility'},
    'mlm':                  {'tier': 5, 'adjustment': -35, 'factor_mod': 0.25, 'note': 'Income instability'},
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BankAnalytics:
    """Parsed bank statement analytics"""
    true_revenue_monthly: float = 0.0
    non_true_revenue_monthly: float = 0.0
    gross_deposits_monthly: float = 0.0
    true_revenue_pct: float = 0.0
    average_daily_balance: float = 0.0
    lowest_balance_90d: float = 0.0
    ending_balance: float = 0.0
    nsf_count_90d: int = 0
    negative_days_90d: int = 0
    overdraft_count_90d: int = 0
    deposit_count_monthly: int = 0
    deposit_variance: float = 0.0
    deposit_trend: str = 'STABLE'
    mca_positions_detected: int = 0
    mca_daily_payments: float = 0.0
    mca_total_balance: float = 0.0
    mca_funders: List[str] = field(default_factory=list)
    statement_months: int = 3
    period_start: date = None
    period_end: date = None


@dataclass
class MerchantData:
    """Card processing data"""
    processor_name: str = ""
    monthly_volume: float = 0.0
    months_processing: int = 0
    chargeback_ratio: float = 0.0
    refund_ratio: float = 0.0
    avg_ticket: float = 0.0
    has_reserves: bool = False
    reserve_balance: float = 0.0


@dataclass
class ApplicationData:
    """Self-reported application data"""
    business_name: str = ""
    dba: str = ""
    entity_type: str = ""
    state: str = ""
    fico_score: int = 0
    time_in_business_months: int = 0
    annual_revenue: float = 0.0
    industry: str = ""
    naics_code: str = ""
    requested_amount: float = 0.0
    use_of_funds: str = ""
    owner_name: str = ""
    ownership_pct: float = 100.0


@dataclass
class CategoryScore:
    """Score for a single category"""
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 0.0
    weighted_score: float = 0.0


@dataclass
class LetterGrade:
    """Letter grade result"""
    grade: str = 'F'
    min_score: int = 0
    max_score: int = 39
    tier: int = 5
    risk_level: str = 'High'


@dataclass
class ScoringResult:
    """Complete scoring output"""
    letter_grade: str = 'F'
    numeric_score: float = 0.0
    tier: int = 5
    approved: bool = False
    max_advance: float = 0.0
    factor_range: Tuple[float, float] = (0.0, 0.0)
    suggested_term_months: Tuple[int, int] = (0, 0)
    score_breakdown: Dict = field(default_factory=dict)
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    risk_flags: List[Dict] = field(default_factory=list)
    decline_reasons: List[str] = field(default_factory=list)
    key_metrics: Dict = field(default_factory=dict)
    grade_info: Optional[LetterGrade] = None

    @property
    def score(self) -> float:
        return self.numeric_score

    def summary(self) -> str:
        lines = [
            f"Grade: {self.letter_grade}",
            f"Score: {self.numeric_score:.1f}/100",
            f"Max Advance: ${self.max_advance:,.0f}",
            f"Factor Range: {self.factor_range[0]:.2f} - {self.factor_range[1]:.2f}",
            f"Term: {self.suggested_term_months[0]}-{self.suggested_term_months[1]} months",
        ]
        if self.risk_flags:
            lines.append(f"Risk Flags: {len(self.risk_flags)}")
        return "\n".join(lines)

    @property
    def recommendation(self) -> str:
        if self.letter_grade.startswith('A'):
            return "Approve - Premium terms"
        elif self.letter_grade.startswith('B'):
            return "Approve - Standard terms"
        elif self.letter_grade.startswith('C'):
            return "Approve - Higher pricing"
        elif self.letter_grade.startswith('D'):
            return "Review - High risk pricing"
        else:
            return "Decline or Specialty pricing"


# =============================================================================
# SCORING ENGINE
# =============================================================================

class MCAScorecard:
    """MCA Underwriting Scoring Model"""

    def __init__(self):
        self.application: Optional[ApplicationData] = None
        self.bank_analytics: Optional[BankAnalytics] = None
        self.merchant_data: Optional[MerchantData] = None
        self.manual_positions: List[Dict] = []
        self.result: Optional[ScoringResult] = None
        self.bank_metrics: Dict = {}
        self.credit_metrics: Dict = {}
        self.deal_metrics: Dict = {}
        self._industry: str = ""
        self.risk_flags: List[str] = []
        self.composite_scorer = CompositeScorer()
        self.grader = LetterGrader()
        self.credit_scorer = CreditScorer()
        self.industry_scorer = IndustryScorer()

    def set_bank_metrics(self, **kwargs) -> 'MCAScorecard':
        self.bank_metrics.update(kwargs)
        return self

    def set_credit_metrics(self, **kwargs) -> 'MCAScorecard':
        self.credit_metrics.update(kwargs)
        if 'fico_score' in kwargs:
            if self.application is None:
                self.application = ApplicationData(fico_score=kwargs['fico_score'])
            else:
                self.application.fico_score = kwargs['fico_score']
        return self

    def set_deal_metrics(self, **kwargs) -> 'MCAScorecard':
        self.deal_metrics.update(kwargs)
        return self

    def set_industry(self, industry: str) -> 'MCAScorecard':
        self._industry = industry
        if self.application is None:
            self.application = ApplicationData(industry=industry)
        else:
            self.application.industry = industry
        return self

    def set_application(self, **kwargs) -> 'MCAScorecard':
        self.application = ApplicationData(**kwargs)
        return self

    def set_bank_analytics(self, **kwargs) -> 'MCAScorecard':
        self.bank_analytics = BankAnalytics(**kwargs)
        return self

    def set_merchant_data(self, **kwargs) -> 'MCAScorecard':
        self.merchant_data = MerchantData(**kwargs)
        return self

    def add_position(self, funder: str, original: float, balance: float,
                     daily_payment: float, factor: float = None) -> 'MCAScorecard':
        self.manual_positions.append({
            'funder': funder,
            'original_amount': original,
            'current_balance': balance,
            'daily_payment': daily_payment,
            'monthly_payment': daily_payment * 22,
            'factor_rate': factor,
            'pct_paid': 1 - (balance / original) if original > 0 else 0,
        })
        return self

    def add_risk_flag(self, flag: str) -> 'MCAScorecard':
        self.risk_flags.append(flag)
        return self

    def from_bank_parser(self, summary) -> 'MCAScorecard':
        if not _HAS_BANK_PARSER:
            raise ImportError("from_bank_parser() requires parsing module.")

        days = (summary.period_end - summary.period_start).days or 1
        months = max(1, days / 30)

        self.bank_analytics = BankAnalytics(
            true_revenue_monthly=summary.true_revenue / months,
            non_true_revenue_monthly=summary.non_true_revenue / months,
            gross_deposits_monthly=summary.total_deposits / months,
            true_revenue_pct=(summary.true_revenue / summary.total_deposits * 100) if summary.total_deposits > 0 else 0,
            mca_positions_detected=len(summary.mca_positions),
            mca_total_balance=sum(pos.total_debited for pos in summary.mca_positions),
            mca_funders=[pos.mca_name for pos in summary.mca_positions],
            period_start=summary.period_start,
            period_end=summary.period_end,
            statement_months=int(months),
        )
        return self

    def _score_true_revenue(self) -> Dict:
        max_pts = SCORING_WEIGHTS['true_revenue']
        revenue = self.bank_analytics.true_revenue_monthly if self.bank_analytics else self.bank_metrics.get('trailing_avg_3mo', 0)

        if revenue >= 150000:
            score, rating = max_pts, 'EXCELLENT'
        elif revenue >= 100000:
            score, rating = max_pts * 0.93, 'VERY STRONG'
        elif revenue >= 75000:
            score, rating = max_pts * 0.85, 'STRONG'
        elif revenue >= 50000:
            score, rating = max_pts * 0.75, 'GOOD'
        elif revenue >= 35000:
            score, rating = max_pts * 0.65, 'ADEQUATE'
        elif revenue >= 25000:
            score, rating = max_pts * 0.50, 'FAIR'
        elif revenue >= 15000:
            score, rating = max_pts * 0.35, 'LOW'
        elif revenue >= 10000:
            score, rating = max_pts * 0.20, 'VERY LOW'
        else:
            score, rating = 0, 'INSUFFICIENT'

        return {'score': round(score, 2), 'max': max_pts, 'value': revenue, 'rating': rating}

    def _score_cash_flow_margin(self) -> Dict:
        max_pts = SCORING_WEIGHTS['cash_flow_margin']
        if not self.bank_analytics and not self.bank_metrics:
            return {'score': max_pts * 0.5, 'max': max_pts, 'value': 0, 'rating': 'NO DATA', 'cfcr': 0}

        true_rev = self.bank_analytics.true_revenue_monthly if self.bank_analytics else self.bank_metrics.get('trailing_avg_3mo', 0)
        existing_daily = self.bank_analytics.mca_daily_payments if self.bank_analytics else 0
        for pos in self.manual_positions:
            existing_daily += pos.get('daily_payment', 0)
        existing_monthly = existing_daily * 22
        requested = self.application.requested_amount if self.application else self.deal_metrics.get('funding_amount', 0)
        proposed_monthly = (requested * 1.35) / 6 if requested else 0
        total_obligations = existing_monthly + proposed_monthly

        cfcr = true_rev / total_obligations if total_obligations > 0 else 10.0

        if cfcr >= 5.0:
            score, rating = max_pts, 'EXCELLENT'
        elif cfcr >= 4.0:
            score, rating = max_pts * 0.92, 'VERY STRONG'
        elif cfcr >= 3.0:
            score, rating = max_pts * 0.83, 'STRONG'
        elif cfcr >= 2.5:
            score, rating = max_pts * 0.75, 'GOOD'
        elif cfcr >= 2.0:
            score, rating = max_pts * 0.60, 'ADEQUATE'
        elif cfcr >= 1.5:
            score, rating = max_pts * 0.45, 'TIGHT'
        elif cfcr >= 1.25:
            score, rating = max_pts * 0.30, 'STRESSED'
        elif cfcr >= 1.0:
            score, rating = max_pts * 0.15, 'MARGINAL'
        else:
            score, rating = 0, 'NEGATIVE'

        return {'score': round(score, 2), 'max': max_pts, 'value': round(cfcr, 2), 'rating': rating, 'cfcr': cfcr}

    def _score_adb(self) -> Dict:
        max_pts = SCORING_WEIGHTS['average_daily_balance']
        adb = self.bank_analytics.average_daily_balance if self.bank_analytics else self.bank_metrics.get('average_daily_balance', 0)
        requested = self.application.requested_amount if self.application else self.deal_metrics.get('funding_amount', 1)
        adb_ratio = (adb / requested) if requested > 0 else 0

        if adb_ratio >= 0.25:
            score, rating = max_pts, 'EXCELLENT'
        elif adb_ratio >= 0.20:
            score, rating = max_pts * 0.90, 'VERY STRONG'
        elif adb_ratio >= 0.15:
            score, rating = max_pts * 0.80, 'STRONG'
        elif adb_ratio >= 0.10:
            score, rating = max_pts * 0.65, 'GOOD'
        elif adb_ratio >= 0.07:
            score, rating = max_pts * 0.50, 'ADEQUATE'
        elif adb_ratio >= 0.05:
            score, rating = max_pts * 0.35, 'LOW'
        elif adb_ratio >= 0.03:
            score, rating = max_pts * 0.20, 'VERY LOW'
        else:
            score, rating = max_pts * 0.10, 'MINIMAL'

        return {'score': round(score, 2), 'max': max_pts, 'value': adb, 'rating': rating}

    def _score_nsf_overdraft(self) -> Dict:
        max_pts = SCORING_WEIGHTS['nsf_overdraft']
        if not self.bank_analytics and not self.bank_metrics:
            return {'score': max_pts * 0.5, 'max': max_pts, 'value': {}, 'rating': 'UNKNOWN'}

        nsf = self.bank_analytics.nsf_count_90d if self.bank_analytics else self.bank_metrics.get('nsf_count', 0)
        neg_days = self.bank_analytics.negative_days_90d if self.bank_analytics else 0
        od = self.bank_analytics.overdraft_count_90d if self.bank_analytics else 0

        score = max_pts
        if nsf > 0:
            if nsf <= 1: score -= 1
            elif nsf <= 2: score -= 2
            elif nsf <= 3: score -= 3
            elif nsf <= 5: score -= 5
            elif nsf <= 7: score -= 7
            else: score -= 10

        if neg_days > 0:
            if neg_days <= 2: score -= 1
            elif neg_days <= 5: score -= 2
            elif neg_days <= 10: score -= 4
            else: score -= 6

        if od > 3: score -= 2
        elif od > 1: score -= 1

        score = max(0, score)

        if score >= 9: rating = 'CLEAN'
        elif score >= 7: rating = 'MINOR'
        elif score >= 5: rating = 'CONCERNS'
        elif score >= 3: rating = 'PROBLEMS'
        else: rating = 'SEVERE'

        return {'score': round(score, 2), 'max': max_pts, 'value': {'nsf': nsf, 'neg_days': neg_days, 'overdrafts': od}, 'rating': rating}

    def _score_deposit_consistency(self) -> Dict:
        max_pts = SCORING_WEIGHTS['deposit_consistency']
        if not self.bank_analytics:
            return {'score': max_pts * 0.5, 'max': max_pts, 'value': 0, 'rating': 'UNKNOWN'}

        variance = self.bank_analytics.deposit_variance
        trend = self.bank_analytics.deposit_trend

        if variance <= 0.10: score, rating = max_pts, 'VERY CONSISTENT'
        elif variance <= 0.15: score, rating = max_pts * 0.88, 'CONSISTENT'
        elif variance <= 0.20: score, rating = max_pts * 0.75, 'STABLE'
        elif variance <= 0.30: score, rating = max_pts * 0.55, 'MODERATE'
        elif variance <= 0.40: score, rating = max_pts * 0.35, 'VARIABLE'
        else: score, rating = max_pts * 0.15, 'ERRATIC'

        if trend == 'UP': score = min(max_pts, score + 1)
        elif trend == 'DOWN': score = max(0, score - 1.5)

        return {'score': round(score, 2), 'max': max_pts, 'value': variance, 'rating': rating}

    def _score_fico(self) -> Dict:
        max_pts = SCORING_WEIGHTS['fico_score']
        fico = self.application.fico_score if self.application else self.credit_metrics.get('fico_score', 0)

        if fico >= 720: score, rating = max_pts, 'EXCELLENT'
        elif fico >= 700: score, rating = max_pts * 0.92, 'VERY GOOD'
        elif fico >= 680: score, rating = max_pts * 0.83, 'GOOD'
        elif fico >= 660: score, rating = max_pts * 0.70, 'FAIR+'
        elif fico >= 640: score, rating = max_pts * 0.58, 'FAIR'
        elif fico >= 620: score, rating = max_pts * 0.45, 'BELOW AVG'
        elif fico >= 600: score, rating = max_pts * 0.33, 'POOR'
        elif fico >= 580: score, rating = max_pts * 0.20, 'VERY POOR'
        elif fico >= 550: score, rating = max_pts * 0.10, 'BAD'
        elif fico >= 500: score, rating = max_pts * 0.05, 'VERY BAD'
        else: score, rating = 0, 'SUBPRIME'

        return {'score': round(score, 2), 'max': max_pts, 'value': fico, 'rating': rating}

    def _score_merchant_volume(self) -> Dict:
        max_pts = SCORING_WEIGHTS['merchant_volume']
        if not self.merchant_data or self.merchant_data.monthly_volume == 0:
            return {'score': max_pts * 0.5, 'max': max_pts, 'value': 0, 'rating': 'N/A'}

        volume = self.merchant_data.monthly_volume
        chargeback = self.merchant_data.chargeback_ratio

        if volume >= 100000: score, rating = max_pts, 'EXCELLENT'
        elif volume >= 75000: score, rating = max_pts * 0.90, 'VERY STRONG'
        elif volume >= 50000: score, rating = max_pts * 0.80, 'STRONG'
        elif volume >= 30000: score, rating = max_pts * 0.65, 'GOOD'
        elif volume >= 15000: score, rating = max_pts * 0.50, 'ADEQUATE'
        elif volume >= 8000: score, rating = max_pts * 0.35, 'LOW'
        else: score, rating = max_pts * 0.20, 'MINIMAL'

        if chargeback > 0.02: score -= 3
        elif chargeback > 0.01: score -= 1.5

        return {'score': round(max(0, score), 2), 'max': max_pts, 'value': volume, 'rating': rating}

    def _score_merchant_tenure(self) -> Dict:
        max_pts = SCORING_WEIGHTS['merchant_tenure']
        if not self.merchant_data or self.merchant_data.months_processing == 0:
            return {'score': max_pts * 0.4, 'max': max_pts, 'value': 0, 'rating': 'N/A'}

        months = self.merchant_data.months_processing

        if months >= 36: score, rating = max_pts, 'ESTABLISHED'
        elif months >= 24: score, rating = max_pts * 0.85, 'MATURE'
        elif months >= 12: score, rating = max_pts * 0.65, 'STANDARD'
        elif months >= 6: score, rating = max_pts * 0.45, 'NEWER'
        elif months >= 3: score, rating = max_pts * 0.25, 'NEW'
        else: score, rating = max_pts * 0.10, 'VERY NEW'

        return {'score': round(score, 2), 'max': max_pts, 'value': months, 'rating': rating}

    def _score_tib(self) -> Dict:
        max_pts = SCORING_WEIGHTS['time_in_business']
        tib = self.application.time_in_business_months if self.application else 0

        if tib >= 60: score, rating = max_pts, 'ESTABLISHED'
        elif tib >= 48: score, rating = max_pts * 0.92, 'MATURE'
        elif tib >= 36: score, rating = max_pts * 0.83, 'SEASONED'
        elif tib >= 24: score, rating = max_pts * 0.70, 'STANDARD'
        elif tib >= 18: score, rating = max_pts * 0.55, 'DEVELOPING'
        elif tib >= 12: score, rating = max_pts * 0.40, 'NEWER'
        elif tib >= 6: score, rating = max_pts * 0.25, 'STARTUP'
        else: score, rating = 0, 'TOO NEW'

        return {'score': round(score, 2), 'max': max_pts, 'value': tib, 'rating': rating}

    def _score_industry(self) -> Dict:
        max_pts = SCORING_WEIGHTS['industry_risk']
        industry = (self.application.industry if self.application else self._industry).lower().replace(' ', '_')
        ind_data = INDUSTRY_SEGMENTS.get(industry, {'tier': 2, 'adjustment': 0, 'factor_mod': 0, 'note': 'Unknown'})
        tier = ind_data['tier']

        if tier == 5: score, rating = 0, 'SPECIALTY'
        elif tier == 4: score, rating = max_pts * 0.25, 'HIGH RISK'
        elif tier == 3: score, rating = max_pts * 0.50, 'ELEVATED'
        elif tier == 2: score, rating = max_pts * 0.75, 'STANDARD'
        else: score, rating = max_pts, 'PREFERRED'

        return {'score': round(score, 2), 'max': max_pts, 'value': industry, 'rating': rating, 'tier': tier, 'adjustment': ind_data['adjustment'], 'factor_mod': ind_data['factor_mod']}

    def _score_positions(self) -> Dict:
        max_pts = SCORING_WEIGHTS['existing_positions']
        detected = self.bank_analytics.mca_positions_detected if self.bank_analytics else 0
        manual = len(self.manual_positions)
        total_positions = max(detected, manual, self.deal_metrics.get('position_count', 0))
        total_balance = (self.bank_analytics.mca_total_balance if self.bank_analytics else 0) + sum(p.get('current_balance', 0) for p in self.manual_positions)
        total_daily = (self.bank_analytics.mca_daily_payments if self.bank_analytics else 0) + sum(p.get('daily_payment', 0) for p in self.manual_positions)

        if total_positions == 0: score, rating = max_pts, 'CLEAN'
        elif total_positions == 1: score, rating = max_pts * 0.70, '1ST POSITION'
        elif total_positions == 2: score, rating = max_pts * 0.40, '2ND POSITION'
        elif total_positions == 3: score, rating = max_pts * 0.20, '3RD POSITION'
        else: score, rating = 0, 'HEAVY STACK'

        return {'score': round(score, 2), 'max': max_pts, 'value': total_positions, 'rating': rating, 'total_balance': total_balance, 'total_daily': total_daily}

    def calculate(self) -> ScoringResult:
        breakdown = {
            'true_revenue': self._score_true_revenue(),
            'cash_flow_margin': self._score_cash_flow_margin(),
            'average_daily_balance': self._score_adb(),
            'nsf_overdraft': self._score_nsf_overdraft(),
            'deposit_consistency': self._score_deposit_consistency(),
            'fico_score': self._score_fico(),
            'merchant_volume': self._score_merchant_volume(),
            'merchant_tenure': self._score_merchant_tenure(),
            'time_in_business': self._score_tib(),
            'industry_risk': self._score_industry(),
            'existing_positions': self._score_positions(),
        }

        base_score = sum(comp['score'] for comp in breakdown.values())
        industry_adj = breakdown['industry_risk'].get('adjustment', 0)
        adjusted_score = max(0, min(100, base_score + industry_adj))

        letter_grade = 'F'
        grade_info = LETTER_GRADES['F']
        for grade, info in LETTER_GRADES.items():
            if adjusted_score >= info['min_score']:
                letter_grade = grade
                grade_info = info
                break

        risk_flags = []
        fico = self.application.fico_score if self.application else self.credit_metrics.get('fico_score', 0)
        tib = self.application.time_in_business_months if self.application else 0
        nsf_data = breakdown['nsf_overdraft']['value']
        cfcr = breakdown['cash_flow_margin'].get('cfcr', 0)
        positions = breakdown['existing_positions']['value']

        if fico > 0 and fico < 550:
            risk_flags.append({'severity': 'HIGH', 'flag': f"Very low FICO: {fico}"})
        elif fico > 0 and fico < 580:
            risk_flags.append({'severity': 'MEDIUM', 'flag': f"Low FICO: {fico}"})
        if tib < 6:
            risk_flags.append({'severity': 'HIGH', 'flag': f"New business: {tib} months"})
        if isinstance(nsf_data, dict):
            if nsf_data.get('nsf', 0) > 10:
                risk_flags.append({'severity': 'HIGH', 'flag': f"Heavy NSFs: {nsf_data['nsf']}"})
            elif nsf_data.get('nsf', 0) > 5:
                risk_flags.append({'severity': 'MEDIUM', 'flag': f"Elevated NSFs: {nsf_data['nsf']}"})
            if nsf_data.get('neg_days', 0) > 5:
                risk_flags.append({'severity': 'HIGH', 'flag': f"Negative days: {nsf_data['neg_days']}"})
        if cfcr < 1.5:
            risk_flags.append({'severity': 'MEDIUM', 'flag': f"Tight cash flow: {cfcr:.2f}x"})
        if positions >= 4:
            risk_flags.append({'severity': 'HIGH', 'flag': f"Heavy stacking: {positions} positions"})
        elif positions >= 3:
            risk_flags.append({'severity': 'MEDIUM', 'flag': f"Multiple positions: {positions}"})
        if breakdown['industry_risk']['tier'] == 5:
            industry_name = self.application.industry if self.application else self._industry
            risk_flags.append({'severity': 'HIGH', 'flag': f"Specialty industry: {industry_name}"})

        true_rev = self.bank_analytics.true_revenue_monthly if self.bank_analytics else self.bank_metrics.get('trailing_avg_3mo', 0)
        advance_pct = grade_info['max_advance_pct']
        base_max = true_rev * advance_pct * 12
        existing_bal = breakdown['existing_positions'].get('total_balance', 0)
        adjusted_max = max(0, base_max - existing_bal)
        requested = self.application.requested_amount if self.application else self.deal_metrics.get('funding_amount', 0)
        max_advance = min(adjusted_max, requested) if requested > 0 else adjusted_max
        factor_mod = breakdown['industry_risk'].get('factor_mod', 0)
        factor_low = grade_info['factor_range'][0] + factor_mod
        factor_high = grade_info['factor_range'][1] + factor_mod

        self.result = ScoringResult(
            letter_grade=letter_grade,
            numeric_score=round(adjusted_score, 1),
            tier=grade_info['tier'],
            approved=True,
            max_advance=round(max_advance, 0),
            factor_range=(round(factor_low, 2), round(factor_high, 2)),
            suggested_term_months=grade_info['term_months'],
            score_breakdown=breakdown,
            risk_flags=risk_flags,
            decline_reasons=[],
            key_metrics={
                'fico': fico,
                'tib_months': tib,
                'true_revenue_monthly': true_rev,
                'adb': self.bank_analytics.average_daily_balance if self.bank_analytics else self.bank_metrics.get('average_daily_balance', 0),
                'nsf_count': nsf_data.get('nsf', 0) if isinstance(nsf_data, dict) else 0,
                'position_count': positions,
                'cfcr': cfcr,
                'industry_tier': breakdown['industry_risk']['tier'],
            }
        )
        return self.result

    def score(self) -> ScoringResult:
        return self.calculate()


# =============================================================================
# SUPPORTING CLASSES
# =============================================================================

class IndustryScorer:
    """Score industry risk"""

    def score(self, industry: str) -> Dict:
        industry_key = industry.lower().replace(' ', '_')
        ind_data = INDUSTRY_SEGMENTS.get(industry_key, {'tier': 2, 'adjustment': 0, 'factor_mod': 0, 'note': 'Unknown'})
        prohibited = ind_data.get('tier', 2) == 5 and ind_data.get('adjustment', 0) <= -25
        tier = ind_data.get('tier', 2)

        if tier == 5: score = 0
        elif tier == 4: score = 25
        elif tier == 3: score = 50
        elif tier == 2: score = 75
        else: score = 100

        return {
            'tier': tier,
            'score': 0 if prohibited else score,
            'prohibited': prohibited,
            'adjustment': ind_data.get('adjustment', 0),
            'factor_mod': ind_data.get('factor_mod', 0),
            'note': ind_data.get('note', ''),
        }


class CompositeScorer:
    """Calculate weighted composite scores"""

    def __init__(self):
        self.scores: Dict[str, float] = {}
        self.weights = {
            'bank_metrics': 0.40,
            'credit_metrics': 0.25,
            'industry_metrics': 0.20,
            'deal_metrics': 0.15,
        }

    def add_score(self, category: str, score: float) -> 'CompositeScorer':
        self.scores[category] = score
        return self

    def validate_weights(self) -> bool:
        return abs(sum(self.weights.values()) - 1.0) < 0.001

    def calculate(self) -> float:
        total = 0.0
        for category, weight in self.weights.items():
            score = self.scores.get(category, 0)
            total += score * weight
        return total


# =============================================================================
# QUICK FUNCTIONS
# =============================================================================

def quick_score(
    true_revenue: float,
    adb: float,
    fico: int = 650,
    tib_months: int = 24,
    nsf: int = 0,
    positions: int = 0,
    industry: str = 'retail',
    requested: float = None,
) -> ScoringResult:
    if requested is None:
        requested = true_revenue * 1.5

    scorecard = MCAScorecard()
    scorecard.set_application(
        business_name="Quick Score",
        fico_score=fico,
        time_in_business_months=tib_months,
        industry=industry,
        requested_amount=requested,
    )
    scorecard.set_bank_analytics(
        true_revenue_monthly=true_revenue,
        average_daily_balance=adb,
        nsf_count_90d=nsf,
        mca_positions_detected=positions,
    )
    return scorecard.calculate()


if __name__ == '__main__':
    result = quick_score(
        true_revenue=65000,
        adb=12000,
        fico=680,
        tib_months=36,
        nsf=1,
        industry='ecommerce',
        requested=75000,
    )
    print(f"\n{result.summary()}")
