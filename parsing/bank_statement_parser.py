"""
Bank Statement Parser
=====================
Core parsing logic for extracting transactions from bank statements.

Usage:
    parser = BankStatementParser()
    transactions = parser.parse_pdf('statement.pdf')
    summary = parser.get_summary()
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, datetime
from enum import Enum


class TransactionType(Enum):
    """Transaction type classification"""
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'
    FEE = 'fee'
    INTEREST = 'interest'
    NSF = 'nsf'
    UNKNOWN = 'unknown'


@dataclass
class Transaction:
    """Represents a single bank transaction"""
    date: date
    description: str
    amount: float
    balance: float
    transaction_type: TransactionType = TransactionType.UNKNOWN
    category: Optional[str] = None
    is_revenue: bool = False
    mca_funder: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'date': self.date.isoformat(),
            'description': self.description,
            'amount': self.amount,
            'balance': self.balance,
            'type': self.transaction_type.value,
            'category': self.category,
            'is_revenue': self.is_revenue,
            'mca_funder': self.mca_funder,
        }


@dataclass
class StatementSummary:
    """Summary of parsed bank statement"""
    account_number: Optional[str] = None
    statement_period: Optional[str] = None
    beginning_balance: float = 0.0
    ending_balance: float = 0.0
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    deposit_count: int = 0
    withdrawal_count: int = 0
    nsf_count: int = 0
    transactions: List[Transaction] = field(default_factory=list)


class BankStatementParser:
    """
    Parser for bank statement PDFs.

    Extracts transactions and generates summary metrics.
    """

    def __init__(self, template: str = 'generic'):
        self.template = template
        self.transactions: List[Transaction] = []
        self.summary: Optional[StatementSummary] = None

    def parse_pdf(self, pdf_path: str) -> List[Transaction]:
        """
        Parse a bank statement PDF and extract transactions.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of Transaction objects
        """
        # TODO: Implement PDF parsing logic
        # This will use pdf_extractor module
        raise NotImplementedError("PDF parsing not yet implemented")

    def parse_transactions(self, raw_data: List[Dict]) -> List[Transaction]:
        """
        Parse raw transaction data into Transaction objects.

        Args:
            raw_data: List of dicts with transaction data

        Returns:
            List of Transaction objects
        """
        transactions = []
        for row in raw_data:
            txn = Transaction(
                date=self._parse_date(row.get('date')),
                description=row.get('description', ''),
                amount=float(row.get('amount', 0)),
                balance=float(row.get('balance', 0)),
                transaction_type=self._classify_type(row),
            )
            transactions.append(txn)

        self.transactions = transactions
        return transactions

    def get_summary(self) -> StatementSummary:
        """Generate summary from parsed transactions"""
        if not self.transactions:
            return StatementSummary()

        deposits = [t for t in self.transactions if t.amount > 0]
        withdrawals = [t for t in self.transactions if t.amount < 0]
        nsf = [t for t in self.transactions if t.transaction_type == TransactionType.NSF]

        self.summary = StatementSummary(
            beginning_balance=self.transactions[0].balance - self.transactions[0].amount,
            ending_balance=self.transactions[-1].balance,
            total_deposits=sum(t.amount for t in deposits),
            total_withdrawals=abs(sum(t.amount for t in withdrawals)),
            deposit_count=len(deposits),
            withdrawal_count=len(withdrawals),
            nsf_count=len(nsf),
            transactions=self.transactions,
        )
        return self.summary

    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object"""
        if isinstance(date_str, date):
            return date_str
        # Try common formats
        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except (ValueError, TypeError):
                continue
        return date.today()

    def _classify_type(self, row: Dict) -> TransactionType:
        """Classify transaction type based on description"""
        desc = row.get('description', '').upper()
        amount = float(row.get('amount', 0))

        if 'NSF' in desc or 'RETURNED' in desc:
            return TransactionType.NSF
        if 'FEE' in desc or 'SERVICE CHARGE' in desc:
            return TransactionType.FEE
        if 'INTEREST' in desc:
            return TransactionType.INTEREST
        if 'TRANSFER' in desc:
            return TransactionType.TRANSFER
        if amount > 0:
            return TransactionType.DEPOSIT
        if amount < 0:
            return TransactionType.WITHDRAWAL
        return TransactionType.UNKNOWN
