"""
Parser Module Tests
===================
Tests for bank statement parsing functionality.
"""

import pytest
from datetime import date


class TestTransaction:
    """Tests for Transaction dataclass"""

    def test_transaction_creation(self):
        """Test creating a transaction"""
        from parsing import Transaction, TransactionType

        txn = Transaction(
            date=date(2024, 1, 15),
            description='ACH DEPOSIT - CUSTOMER PAYMENT',
            amount=5000.00,
            balance=15000.00,
            transaction_type=TransactionType.DEPOSIT,
        )
        assert txn.amount == 5000.00
        assert txn.transaction_type == TransactionType.DEPOSIT

    def test_transaction_to_dict(self):
        """Test transaction serialization"""
        from parsing import Transaction, TransactionType

        txn = Transaction(
            date=date(2024, 1, 15),
            description='Test',
            amount=100.00,
            balance=1000.00,
        )
        d = txn.to_dict()
        assert d['amount'] == 100.00
        assert 'date' in d


class TestBankStatementParser:
    """Tests for BankStatementParser"""

    def test_parser_init(self):
        """Test parser initialization"""
        from parsing import BankStatementParser

        parser = BankStatementParser()
        assert parser.template == 'generic'
        assert parser.transactions == []

    def test_parse_transactions(self):
        """Test transaction parsing from raw data"""
        from parsing import BankStatementParser

        parser = BankStatementParser()
        raw_data = [
            {'date': '01/15/2024', 'description': 'DEPOSIT', 'amount': 1000, 'balance': 5000},
            {'date': '01/16/2024', 'description': 'WITHDRAWAL', 'amount': -500, 'balance': 4500},
        ]
        transactions = parser.parse_transactions(raw_data)
        assert len(transactions) == 2

    def test_get_summary(self):
        """Test summary generation"""
        from parsing import BankStatementParser

        parser = BankStatementParser()
        raw_data = [
            {'date': '01/15/2024', 'description': 'DEPOSIT', 'amount': 1000, 'balance': 5000},
            {'date': '01/16/2024', 'description': 'WITHDRAWAL', 'amount': -500, 'balance': 4500},
        ]
        parser.parse_transactions(raw_data)
        summary = parser.get_summary()
        assert summary.total_deposits == 1000
        assert summary.total_withdrawals == 500
