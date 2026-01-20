"""
Analytics Module
================
Cash flow analytics and metrics calculation.

Components:
- CashFlowAnalyzer: Trailing averages, trends, volatility
- DepositCategorizer: Revenue classification
- NSFAnalyzer: NSF/overdraft scoring
- BalanceTracker: ADB calculation
"""

from .cashflow_analyzer import (
    CashFlowAnalyzer,
    CashFlowMetrics,
    TrendDirection,
)

from .deposit_categorizer import (
    DepositCategorizer,
    DepositCategory,
    categorize_deposit,
)

from .nsf_analyzer import (
    NSFAnalyzer,
    NSFMetrics,
)

from .balance_tracker import (
    BalanceTracker,
    BalanceMetrics,
)

__all__ = [
    'CashFlowAnalyzer',
    'CashFlowMetrics',
    'TrendDirection',
    'DepositCategorizer',
    'DepositCategory',
    'categorize_deposit',
    'NSFAnalyzer',
    'NSFMetrics',
    'BalanceTracker',
    'BalanceMetrics',
]
