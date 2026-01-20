"""
Deposit Categorizer
===================
Classify deposits as revenue vs non-revenue.

True Revenue:
- ACH Credits
- Wire transfers (from customers)
- POS/Card deposits
- Merchant processing deposits

Non-Revenue:
- Internal transfers
- Loan proceeds
- Owner contributions
- MCA funding
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import re


class DepositCategory(Enum):
    """Deposit category classification"""
    TRUE_REVENUE = 'true_revenue'
    NON_REVENUE = 'non_revenue'
    TRANSFER = 'transfer'
    MCA_FUNDING = 'mca_funding'
    LOAN_PROCEEDS = 'loan_proceeds'
    OWNER_CONTRIBUTION = 'owner_contribution'
    UNKNOWN = 'unknown'


# Patterns for revenue classification
REVENUE_PATTERNS = [
    r'POS',
    r'CARD',
    r'MERCHANT',
    r'SQUARE',
    r'STRIPE',
    r'PAYPAL',
    r'CLOVER',
    r'TOAST',
    r'CUSTOMER',
    r'SALES',
    r'INVOICE',
]

NON_REVENUE_PATTERNS = [
    r'TRANSFER',
    r'XFER',
    r'LOAN',
    r'ADVANCE',
    r'FUNDING',
    r'CONTRIBUTION',
    r'OWNER',
    r'DEPOSIT\s+FROM\s+SAVINGS',
]

MCA_PATTERNS = [
    r'FORA FINANCIAL',
    r'KAPITUS',
    r'CREDIBLY',
    r'FUNDBOX',
    r'BLUEVINE',
    r'ONDECK',
    r'KABBAGE',
    r'RAPID FINANCE',
    r'CAN CAPITAL',
    r'FORWARD FINANCING',
]


@dataclass
class CategorizationResult:
    """Result of deposit categorization"""
    category: DepositCategory
    confidence: float
    matched_pattern: Optional[str] = None


class DepositCategorizer:
    """
    Categorize deposits as revenue vs non-revenue.

    Usage:
        categorizer = DepositCategorizer()
        result = categorizer.categorize(description, amount)
    """

    def __init__(self):
        self.revenue_patterns = [re.compile(p, re.I) for p in REVENUE_PATTERNS]
        self.non_revenue_patterns = [re.compile(p, re.I) for p in NON_REVENUE_PATTERNS]
        self.mca_patterns = [re.compile(p, re.I) for p in MCA_PATTERNS]

    def categorize(self, description: str, amount: float = 0) -> CategorizationResult:
        """
        Categorize a single deposit.

        Args:
            description: Transaction description
            amount: Transaction amount

        Returns:
            CategorizationResult with category and confidence
        """
        desc_upper = description.upper()

        # Check MCA patterns first
        for pattern in self.mca_patterns:
            if pattern.search(desc_upper):
                return CategorizationResult(
                    category=DepositCategory.MCA_FUNDING,
                    confidence=0.95,
                    matched_pattern=pattern.pattern
                )

        # Check non-revenue patterns
        for pattern in self.non_revenue_patterns:
            if pattern.search(desc_upper):
                return CategorizationResult(
                    category=DepositCategory.NON_REVENUE,
                    confidence=0.85,
                    matched_pattern=pattern.pattern
                )

        # Check revenue patterns
        for pattern in self.revenue_patterns:
            if pattern.search(desc_upper):
                return CategorizationResult(
                    category=DepositCategory.TRUE_REVENUE,
                    confidence=0.80,
                    matched_pattern=pattern.pattern
                )

        # Default to unknown for unclassified deposits
        return CategorizationResult(
            category=DepositCategory.UNKNOWN,
            confidence=0.50,
        )

    def categorize_all(self, transactions: List) -> Dict[str, float]:
        """
        Categorize all transactions and return totals by category.

        Returns:
            Dict mapping category name to total amount
        """
        totals = {cat.value: 0.0 for cat in DepositCategory}

        for txn in transactions:
            if hasattr(txn, 'amount') and txn.amount > 0:
                result = self.categorize(txn.description, txn.amount)
                totals[result.category.value] += txn.amount

        return totals


def categorize_deposit(description: str, amount: float = 0) -> CategorizationResult:
    """Convenience function to categorize a single deposit"""
    categorizer = DepositCategorizer()
    return categorizer.categorize(description, amount)
