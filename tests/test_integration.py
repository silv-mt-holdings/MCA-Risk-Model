"""
Integration Tests for MCA-Risk-Model

Tests the complete scoring workflow from application through final decision.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.mca_scorecard import MCAScoringModel
from models.scoring import BankAnalytics, ApplicationData


class TestScoringIntegration(unittest.TestCase):
    """Test complete scoring workflows"""

    def test_complete_approval_workflow(self):
        """Test a complete approval scenario"""
        model = MCAScoringModel()

        # Set application data
        model.set_application(
            business_name="Test Restaurant",
            industry="restaurant",
            fico_score=680,
            time_in_business_months=36,
            state="NY",
            monthly_merchant_volume=38000,
            merchant_tenure_months=24
        )

        # Set bank analytics
        model.set_bank_analytics(
            monthly_true_revenue=45000,
            average_daily_balance=15000,
            nsf_count_90d=1,
            negative_days_90d=0,
            deposit_variance=0.18,
            total_deposits_90d=135000,
            total_withdrawals_90d=128000,
            mca_positions=[]
        )

        # Score the deal
        result = model.score(requested_amount=50000)

        # Assertions
        self.assertTrue(result.pre_check.passed, "Pre-check should pass")
        self.assertGreater(result.total_score, 0, "Should have positive score")
        self.assertTrue(result.is_approvable, "Should be approvable")
        self.assertIsNotNone(result.letter_grade, "Should have letter grade")
        self.assertGreater(result.recommended_factor, 1.0, "Factor should be > 1.0")
        self.assertGreater(result.max_advance, 0, "Max advance should be positive")

    def test_precheck_blocker_scenario(self):
        """Test that pre-check blockers prevent scoring"""
        model = MCAScoringModel()

        # Below minimum requirements
        model.set_application(
            business_name="New Startup",
            industry="retail",
            fico_score=480,  # Below 500 minimum
            time_in_business_months=2  # Below 3 month minimum
        )

        model.set_bank_analytics(
            monthly_true_revenue=8000,  # Below $10k minimum
            average_daily_balance=1200,
            nsf_count_90d=12,
            negative_days_90d=8,
            deposit_variance=0.75,
            total_deposits_90d=24000,
            total_withdrawals_90d=23500
        )

        result = model.score(requested_amount=25000)

        # Assertions
        self.assertFalse(result.pre_check.passed, "Pre-check should fail")
        self.assertGreater(len(result.pre_check.blockers), 0, "Should have blockers")
        self.assertFalse(result.is_approvable, "Should not be approvable")
        self.assertEqual(result.letter_grade, 'F', "Should get F grade")

    def test_excellent_deal_scoring(self):
        """Test A+ grade deal"""
        model = MCAScoringModel()

        model.set_application(
            business_name="Premium Dental",
            industry="dental",
            fico_score=740,
            time_in_business_months=72,
            monthly_merchant_volume=65000,
            merchant_tenure_months=36
        )

        model.set_bank_analytics(
            monthly_true_revenue=180000,
            average_daily_balance=85000,
            nsf_count_90d=0,
            negative_days_90d=0,
            deposit_variance=0.08,
            total_deposits_90d=540000,
            total_withdrawals_90d=490000,
            cash_flow_margin=0.30,
            mca_positions=[]
        )

        result = model.score(requested_amount=100000)

        # Assertions
        self.assertTrue(result.pre_check.passed)
        self.assertGreaterEqual(result.total_score, 90, "Should score 90+")
        self.assertIn(result.letter_grade, ['A+', 'A'], "Should be A tier")
        self.assertEqual(result.tier, 1, "Should be tier 1")
        self.assertLessEqual(result.recommended_factor, 1.20, "Should have low factor")

    def test_high_risk_deal_scoring(self):
        """Test high-risk deal with warnings"""
        model = MCAScoringModel()

        model.set_application(
            business_name="Freight Co",
            industry="trucking",
            fico_score=580,
            time_in_business_months=18
        )

        model.set_bank_analytics(
            monthly_true_revenue=28000,
            average_daily_balance=3500,
            nsf_count_90d=6,
            negative_days_90d=4,
            deposit_variance=0.55,
            total_deposits_90d=84000,
            total_withdrawals_90d=82000,
            mca_positions=['Rapid Funding', 'Forward Financing']
        )

        result = model.score(requested_amount=35000)

        # Assertions
        self.assertTrue(result.pre_check.passed, "Should pass pre-check")
        # High-risk factors should result in lower score and higher factor
        self.assertLess(result.total_score, 70, "Should be lower score")
        self.assertGreaterEqual(result.recommended_factor, 1.30, "Should have higher factor")
        # Check that high-risk components scored low
        self.assertLess(result.component_scores.get('nsf_overdraft', 10), 5, "NSF should score low")
        self.assertLess(result.component_scores.get('fico_score', 12), 8, "FICO should score low")

    def test_industry_adjustment_impact(self):
        """Test that industry adjustments affect final score"""
        base_app = {
            "fico_score": 650,
            "time_in_business_months": 24
        }

        base_bank = {
            "monthly_true_revenue": 50000,
            "average_daily_balance": 12000,
            "nsf_count_90d": 2,
            "negative_days_90d": 1,
            "deposit_variance": 0.22,
            "total_deposits_90d": 150000,
            "total_withdrawals_90d": 142000,
            "mca_positions": []
        }

        # Test preferred industry (dental)
        model1 = MCAScoringModel()
        model1.set_application(industry="dental", **base_app)
        model1.set_bank_analytics(**base_bank)
        result1 = model1.score(requested_amount=50000)

        # Test high-risk industry (trucking)
        model2 = MCAScoringModel()
        model2.set_application(industry="trucking", **base_app)
        model2.set_bank_analytics(**base_bank)
        result2 = model2.score(requested_amount=50000)

        # Dental should score higher than trucking
        self.assertGreater(
            result1.total_score,
            result2.total_score,
            "Preferred industry should score higher than high-risk"
        )

        # Dental should have better pricing
        self.assertLess(
            result1.recommended_factor,
            result2.recommended_factor,
            "Preferred industry should have lower factor"
        )

    def test_method_chaining(self):
        """Test fluent API with method chaining"""
        result = (MCAScoringModel()
                 .set_application(
                     industry="retail",
                     fico_score=650,
                     time_in_business_months=24
                 )
                 .set_bank_analytics(
                     monthly_true_revenue=35000,
                     average_daily_balance=8000,
                     nsf_count_90d=2,
                     negative_days_90d=1,
                     deposit_variance=0.25,
                     total_deposits_90d=105000,
                     total_withdrawals_90d=98000
                 )
                 .score(requested_amount=30000))

        # Should complete successfully
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.letter_grade)

    def test_max_advance_calculation(self):
        """Test that max advance is calculated correctly"""
        model = MCAScoringModel()

        monthly_revenue = 50000

        model.set_application(
            industry="retail",
            fico_score=720,
            time_in_business_months=48
        )

        model.set_bank_analytics(
            monthly_true_revenue=monthly_revenue,
            average_daily_balance=15000,
            nsf_count_90d=0,
            negative_days_90d=0,
            deposit_variance=0.15,
            total_deposits_90d=150000,
            total_withdrawals_90d=135000
        )

        result = model.score(requested_amount=10000)

        # Max advance should be based on grade and monthly revenue
        self.assertGreater(result.max_advance, 0)
        self.assertGreater(result.max_advance_pct, 0)
        self.assertLessEqual(result.max_advance_pct, 0.20)  # Should not exceed 20%

        # Max advance should equal monthly_revenue * max_advance_pct
        expected_max = monthly_revenue * result.max_advance_pct
        self.assertAlmostEqual(result.max_advance, expected_max, places=0)

    def test_component_scores_sum(self):
        """Test that component scores add up correctly"""
        model = MCAScoringModel()

        model.set_application(
            industry="restaurant",
            fico_score=650,
            time_in_business_months=36
        )

        model.set_bank_analytics(
            monthly_true_revenue=40000,
            average_daily_balance=10000,
            nsf_count_90d=3,
            negative_days_90d=2,
            deposit_variance=0.30,
            total_deposits_90d=120000,
            total_withdrawals_90d=115000
        )

        result = model.score(requested_amount=35000)

        # Component scores should be present
        self.assertGreater(len(result.component_scores), 0)

        # Base component sum (before industry adjustment)
        base_components = {k: v for k, v in result.component_scores.items()
                          if k != 'industry_adjustment'}
        base_sum = sum(base_components.values())

        # Base sum should be reasonable
        self.assertGreater(base_sum, 0)
        self.assertLessEqual(base_sum, 100)

    def test_term_range_assignment(self):
        """Test that term ranges are assigned based on grade"""
        model = MCAScoringModel()

        model.set_application(
            industry="retail",
            fico_score=680,
            time_in_business_months=24
        )

        model.set_bank_analytics(
            monthly_true_revenue=45000,
            average_daily_balance=12000,
            nsf_count_90d=1,
            negative_days_90d=0,
            deposit_variance=0.20,
            total_deposits_90d=135000,
            total_withdrawals_90d=128000
        )

        result = model.score(requested_amount=40000)

        # Term range should be present
        self.assertEqual(len(result.term_months_range), 2)
        min_term, max_term = result.term_months_range

        # Terms should be valid
        self.assertGreater(min_term, 0)
        self.assertGreater(max_term, min_term)
        self.assertLessEqual(max_term, 12)


if __name__ == '__main__':
    unittest.main()
