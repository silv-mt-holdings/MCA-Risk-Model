"""
MCA-Risk-Model Shared Data Models

Common data classes and enums used across parsing, analytics, and scoring layers.
"""

from .transactions import (
    Transaction,
    MCAPosition,
    RevenueType,
    TransactionType,
    WireType
)

from .analytics import (
    CashFlowSummary,
    DepositCategory,
    BalanceMetrics,
    MonthlyData
)

from .scoring import (
    BankAnalytics,
    MerchantData,
    ApplicationData,
    ScoringResult,
    PreCheckResult
)

__all__ = [
    # Transaction models
    'Transaction',
    'MCAPosition',
    'RevenueType',
    'TransactionType',
    'WireType',

    # Analytics models
    'CashFlowSummary',
    'DepositCategory',
    'BalanceMetrics',
    'MonthlyData',

    # Scoring models
    'BankAnalytics',
    'MerchantData',
    'ApplicationData',
    'ScoringResult',
    'PreCheckResult',
]
