"""
Scoring Module Tests
====================
Tests for risk scoring functionality.
"""

import pytest


class TestMCAScorecard:
    """Tests for MCAScorecard"""

    def test_scorecard_creation(self):
        """Test scorecard initialization"""
        from scoring import MCAScorecard

        scorecard = MCAScorecard()
        assert scorecard.bank_metrics == {}
        assert scorecard.credit_metrics == {}

    def test_set_bank_metrics(self):
        """Test setting bank metrics"""
        from scoring import MCAScorecard

        scorecard = MCAScorecard()
        scorecard.set_bank_metrics(
            trailing_avg_3mo=45000,
            nsf_count=2,
        )
        assert scorecard.bank_metrics['trailing_avg_3mo'] == 45000
        assert scorecard.bank_metrics['nsf_count'] == 2

    def test_calculate_score(self):
        """Test score calculation"""
        from scoring import MCAScorecard

        scorecard = MCAScorecard()
        scorecard.set_credit_metrics(fico_score=720)
        scorecard.set_industry('restaurant')
        result = scorecard.calculate()

        assert result.score > 0
        assert result.letter_grade in ['A', 'B', 'C', 'D', 'F']


class TestCreditScorer:
    """Tests for CreditScorer"""

    def test_fico_buckets(self):
        """Test FICO bucket assignment"""
        from scoring import bucket_from_fico

        assert bucket_from_fico(800).bucket.value == 'excellent'
        assert bucket_from_fico(720).bucket.value == 'good'
        assert bucket_from_fico(680).bucket.value == 'fair'
        assert bucket_from_fico(620).bucket.value == 'poor'
        assert bucket_from_fico(550).bucket.value == 'very_poor'


class TestIndustryScorer:
    """Tests for IndustryScorer"""

    def test_industry_tiers(self):
        """Test industry tier assignment"""
        from scoring import IndustryScorer

        scorer = IndustryScorer()

        medical = scorer.score('medical')
        assert medical['tier'] == 1

        restaurant = scorer.score('restaurant')
        assert restaurant['tier'] == 2

    def test_prohibited_industries(self):
        """Test prohibited industry detection"""
        from scoring import IndustryScorer

        scorer = IndustryScorer()
        result = scorer.score('gambling')
        assert result['prohibited'] == True
        assert result['score'] == 0


class TestLetterGrader:
    """Tests for LetterGrader"""

    def test_grade_thresholds(self):
        """Test grade threshold boundaries"""
        from scoring import grade_from_score

        assert grade_from_score(95).grade == 'A'
        assert grade_from_score(80).grade == 'A'
        assert grade_from_score(79).grade == 'B'
        assert grade_from_score(65).grade == 'B'
        assert grade_from_score(64).grade == 'C'
        assert grade_from_score(50).grade == 'C'
        assert grade_from_score(49).grade == 'D'
        assert grade_from_score(35).grade == 'D'
        assert grade_from_score(34).grade == 'F'
        assert grade_from_score(0).grade == 'F'

    def test_is_passing(self):
        """Test passing grade check"""
        from scoring import LetterGrader

        grader = LetterGrader()
        assert grader.is_passing(75) == True
        assert grader.is_passing(50) == True
        assert grader.is_passing(49) == False


class TestCompositeScorer:
    """Tests for CompositeScorer"""

    def test_weight_validation(self):
        """Test that weights sum to 1.0"""
        from scoring import CompositeScorer

        scorer = CompositeScorer()
        assert scorer.validate_weights() == True

    def test_composite_calculation(self):
        """Test weighted composite calculation"""
        from scoring import CompositeScorer

        scorer = CompositeScorer()
        scorer.add_score('bank_metrics', 80)
        scorer.add_score('credit_metrics', 70)
        scorer.add_score('industry_metrics', 75)
        scorer.add_score('deal_metrics', 60)

        composite = scorer.calculate()
        # 80*0.4 + 70*0.25 + 75*0.2 + 60*0.15 = 32 + 17.5 + 15 + 9 = 73.5
        assert composite == 73.5
