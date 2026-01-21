"""
Tests for Letter Grader

Tests the 13-grade letter system and pricing calculations.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.letter_grader import LetterGrader, get_letter_grade


class TestLetterGrader(unittest.TestCase):
    """Test letter grader functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.grader = LetterGrader()

    def test_grade_assignment(self):
        """Test that scores map to correct grades"""
        self.assertEqual(self.grader.get_grade(98), 'A+')
        self.assertEqual(self.grader.get_grade(92), 'A')
        self.assertEqual(self.grader.get_grade(87), 'A-')
        self.assertEqual(self.grader.get_grade(82), 'B+')
        self.assertEqual(self.grader.get_grade(77), 'B')
        self.assertEqual(self.grader.get_grade(72), 'B-')
        self.assertEqual(self.grader.get_grade(67), 'C+')
        self.assertEqual(self.grader.get_grade(62), 'C')
        self.assertEqual(self.grader.get_grade(57), 'C-')
        self.assertEqual(self.grader.get_grade(52), 'D+')
        self.assertEqual(self.grader.get_grade(47), 'D')
        self.assertEqual(self.grader.get_grade(42), 'D-')
        self.assertEqual(self.grader.get_grade(30), 'F')

    def test_grade_boundaries(self):
        """Test grade boundaries"""
        self.assertEqual(self.grader.get_grade(95), 'A+')  # min A+
        self.assertEqual(self.grader.get_grade(100), 'A+')  # max A+
        self.assertEqual(self.grader.get_grade(90), 'A')   # min A
        self.assertEqual(self.grader.get_grade(94), 'A')   # max A
        self.assertEqual(self.grader.get_grade(40), 'D-')  # min D-
        self.assertEqual(self.grader.get_grade(39), 'F')   # max F

    def test_out_of_range_scores(self):
        """Test that out-of-range scores are handled"""
        self.assertEqual(self.grader.get_grade(-10), 'F')
        self.assertEqual(self.grader.get_grade(150), 'A+')

    def test_factor_ranges(self):
        """Test factor range retrieval"""
        min_f, max_f = self.grader.get_factor_range('A+')
        self.assertEqual(min_f, 1.10)
        self.assertEqual(max_f, 1.15)

        min_f, max_f = self.grader.get_factor_range('F')
        self.assertEqual(min_f, 1.50)
        self.assertEqual(max_f, 1.65)

    def test_recommended_factor(self):
        """Test recommended factor calculation"""
        # Mid position
        factor = self.grader.get_recommended_factor('A+', 'mid')
        self.assertAlmostEqual(factor, 1.125, places=3)

        # Low position
        factor = self.grader.get_recommended_factor('B', 'low')
        self.assertEqual(factor, 1.22)

        # High position
        factor = self.grader.get_recommended_factor('B', 'high')
        self.assertEqual(factor, 1.28)

    def test_max_advance_pct(self):
        """Test maximum advance percentage"""
        self.assertEqual(self.grader.get_max_advance_pct('A+'), 0.20)
        self.assertEqual(self.grader.get_max_advance_pct('B'), 0.14)
        self.assertEqual(self.grader.get_max_advance_pct('F'), 0.05)

    def test_max_advance_calculation(self):
        """Test maximum advance amount calculation"""
        # A+ grade with $50k monthly revenue → 20% = $10k max
        max_advance = self.grader.calculate_max_advance('A+', 50000)
        self.assertAlmostEqual(max_advance, 10000, places=2)

        # B grade with $50k monthly revenue → 14% = $7k max
        max_advance = self.grader.calculate_max_advance('B', 50000)
        self.assertAlmostEqual(max_advance, 7000, places=2)

    def test_term_ranges(self):
        """Test term range retrieval"""
        min_term, max_term = self.grader.get_term_range('A+')
        self.assertEqual(min_term, 3)
        self.assertEqual(max_term, 6)

        min_term, max_term = self.grader.get_term_range('F')
        self.assertEqual(min_term, 2)
        self.assertEqual(max_term, 4)

    def test_tier_assignment(self):
        """Test risk tier assignment"""
        self.assertEqual(self.grader.get_tier('A+'), 1)
        self.assertEqual(self.grader.get_tier('A'), 1)
        self.assertEqual(self.grader.get_tier('B+'), 2)
        self.assertEqual(self.grader.get_tier('C'), 3)
        self.assertEqual(self.grader.get_tier('D'), 4)
        self.assertEqual(self.grader.get_tier('F'), 5)

    def test_tier_1_check(self):
        """Test tier 1 identification"""
        self.assertTrue(self.grader.is_tier_1('A+'))
        self.assertTrue(self.grader.is_tier_1('A'))
        self.assertTrue(self.grader.is_tier_1('A-'))
        self.assertFalse(self.grader.is_tier_1('B+'))
        self.assertFalse(self.grader.is_tier_1('F'))

    def test_approvability(self):
        """Test approvability threshold (40 points)"""
        self.assertTrue(self.grader.is_approvable(40))
        self.assertTrue(self.grader.is_approvable(50))
        self.assertTrue(self.grader.is_approvable(100))
        self.assertFalse(self.grader.is_approvable(39))
        self.assertFalse(self.grader.is_approvable(0))

    def test_grade_summary(self):
        """Test comprehensive grade summary"""
        summary = self.grader.get_grade_summary(85)

        self.assertEqual(summary['letter_grade'], 'A-')
        self.assertEqual(summary['score'], 85)
        self.assertEqual(summary['tier'], 1)
        self.assertTrue(summary['is_approvable'])
        self.assertTrue(summary['is_tier_1'])
        self.assertEqual(summary['factor_range'], (1.15, 1.20))
        self.assertEqual(summary['max_advance_pct'], 0.16)

    def test_convenience_function(self):
        """Test convenience function"""
        self.assertEqual(get_letter_grade(85), 'A-')
        self.assertEqual(get_letter_grade(50), 'D+')


if __name__ == '__main__':
    unittest.main()
