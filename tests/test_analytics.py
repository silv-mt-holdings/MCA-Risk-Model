"""
Analytics Module Tests
======================
Tests for cash flow analytics functionality.
"""

import pytest


class TestCashFlowAnalyzer:
    """Tests for CashFlowAnalyzer"""

    def test_trailing_averages(self):
        """Test trailing average calculations"""
        from analytics import CashFlowAnalyzer

        analyzer = CashFlowAnalyzer()
        analyzer.set_monthly_deposits([30000, 35000, 40000, 38000, 42000, 45000])
        metrics = analyzer.calculate_metrics()

        assert metrics.trailing_avg_3mo > 0
        assert metrics.trailing_avg_6mo > 0

    def test_trend_calculation(self):
        """Test trend direction calculation"""
        from analytics import CashFlowAnalyzer, TrendDirection

        # Increasing trend
        analyzer = CashFlowAnalyzer()
        analyzer.set_monthly_deposits([20000, 22000, 24000, 30000, 35000, 40000])
        metrics = analyzer.calculate_metrics()
        assert metrics.trend == TrendDirection.INCREASING

    def test_volatility(self):
        """Test volatility calculation"""
        from analytics import CashFlowAnalyzer

        analyzer = CashFlowAnalyzer()
        analyzer.set_monthly_deposits([30000, 30000, 30000, 30000])  # Low volatility
        metrics = analyzer.calculate_metrics()
        assert metrics.volatility < 0.1


class TestDepositCategorizer:
    """Tests for DepositCategorizer"""

    def test_revenue_classification(self):
        """Test true revenue classification"""
        from analytics import categorize_deposit, DepositCategory

        result = categorize_deposit('SQUARE INC DEPOSIT')
        assert result.category == DepositCategory.TRUE_REVENUE

    def test_mca_detection(self):
        """Test MCA funding detection"""
        from analytics import categorize_deposit, DepositCategory

        result = categorize_deposit('KAPITUS FUNDING')
        assert result.category == DepositCategory.MCA_FUNDING

    def test_transfer_detection(self):
        """Test internal transfer detection"""
        from analytics import categorize_deposit, DepositCategory

        result = categorize_deposit('TRANSFER FROM SAVINGS')
        assert result.category == DepositCategory.NON_REVENUE


class TestNSFAnalyzer:
    """Tests for NSFAnalyzer"""

    def test_nsf_rating(self):
        """Test NSF rating calculation"""
        from analytics import NSFAnalyzer

        analyzer = NSFAnalyzer()
        # Empty transactions = excellent rating
        metrics = analyzer.analyze()
        assert metrics.score == 100.0


class TestBalanceTracker:
    """Tests for BalanceTracker"""

    def test_average_daily_balance(self):
        """Test ADB calculation"""
        from analytics import BalanceTracker
        from datetime import date

        tracker = BalanceTracker()
        tracker.set_daily_balances({
            date(2024, 1, 1): 10000,
            date(2024, 1, 2): 12000,
            date(2024, 1, 3): 8000,
        })
        metrics = tracker.calculate()
        assert metrics.average_daily_balance == 10000.0
