"""
Transaction Data Models

Data classes for bank statement transactions, MCA positions, and transaction classification.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import date


class RevenueType(Enum):
    """Classification of transaction revenue type"""
    TRUE_REVENUE = "true_revenue"
    NON_TRUE_REVENUE = "non_true_revenue"
    OUTLIER = "outlier"
    MCA_PAYMENT = "mca_payment"
    NEEDS_REVIEW = "needs_review"


class TransactionType(Enum):
    """Type of bank transaction"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    WIRE = "wire"
    ACH = "ach"
    CHECK = "check"
    CARD = "card"
    FEE = "fee"


class WireType(Enum):
    """Classification of wire transfer types"""
    WIRE_TRANSFER = "wire_transfer"      # ORIG: prefix
    FED_WIRE = "fed_wire"                # ORIG: prefix
    CHIPS_CREDIT = "chips_credit"        # B/O: prefix
    BOOK_TRANSFER = "book_transfer"      # B/O: prefix
    FOREIGN_REMITTANCE = "foreign_remittance"  # NOT True Revenue
    UNKNOWN = "unknown"


@dataclass
class Transaction:
    """
    Represents a single bank statement transaction.

    Attributes:
        date: Transaction date
        description: Transaction description from statement
        amount: Transaction amount (positive for deposits, negative for withdrawals)
        transaction_type: Type of transaction (ACH, wire, check, etc.)
        revenue_type: Classification of revenue (true/non-true/outlier)
        mca_match: MCA lender name if detected
        wire_type: Wire transfer classification if applicable
        flags: List of warning flags or notes
        raw_text: Original raw text from statement
    """
    date: date
    description: str
    amount: float
    transaction_type: TransactionType = TransactionType.ACH
    revenue_type: RevenueType = RevenueType.NEEDS_REVIEW
    mca_match: Optional[str] = None
    wire_type: Optional[WireType] = None
    flags: List[str] = field(default_factory=list)
    raw_text: str = ""

    @property
    def is_deposit(self) -> bool:
        """Returns True if this is a deposit (positive amount)"""
        return self.amount > 0

    @property
    def is_withdrawal(self) -> bool:
        """Returns True if this is a withdrawal (negative amount)"""
        return self.amount < 0

    @property
    def is_true_revenue(self) -> bool:
        """Returns True if classified as true revenue"""
        return self.revenue_type == RevenueType.TRUE_REVENUE

    @property
    def is_mca_payment(self) -> bool:
        """Returns True if identified as an MCA payment"""
        return self.revenue_type == RevenueType.MCA_PAYMENT or self.mca_match is not None


@dataclass
class MCAPosition:
    """
    Represents an identified MCA position from bank statements.

    Attributes:
        mca_name: Official MCA lender name
        aka_name: Name as it appears on bank statement
        payment_amount: Average payment amount
        payment_frequency: Payment frequency (daily, weekly, etc.)
        estimated_balance: Estimated remaining balance
        transaction_count: Number of payments detected
        first_seen: Date of first detected payment
        last_seen: Date of most recent payment
        flags: Any warning flags or notes
    """
    mca_name: str
    aka_name: str
    payment_amount: float = 0.0
    payment_frequency: str = "unknown"
    estimated_balance: Optional[float] = None
    transaction_count: int = 0
    first_seen: Optional[date] = None
    last_seen: Optional[date] = None
    flags: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Returns True if position appears to be active (has recent payments)"""
        return self.transaction_count > 0

    @property
    def avg_monthly_payment(self) -> float:
        """Estimate average monthly payment based on frequency"""
        if self.payment_frequency == "daily":
            return self.payment_amount * 21  # ~21 business days/month
        elif self.payment_frequency == "weekly":
            return self.payment_amount * 4
        else:
            return self.payment_amount
