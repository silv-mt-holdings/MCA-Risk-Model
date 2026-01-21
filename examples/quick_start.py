"""
MCA-Risk-Model Quick Start Example

Demonstrates basic usage of the library:
- Letter grading
- Industry risk assessment
- Bank statement parsing
- Cash flow analysis
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.letter_grader import LetterGrader, get_letter_grade
from scoring.industry_scorer import IndustryScorer, get_industry_risk
from models.analytics import MonthlyData, CashFlowSummary
from analytics.cashflow_analyzer import BankCashFlowAnalyzer


def demo_letter_grader():
    """Demonstrate letter grading"""
    print("\n" + "="*70)
    print("  LETTER GRADER DEMO")
    print("="*70 + "\n")

    grader = LetterGrader()

    # Example: Score a deal
    test_scores = [95, 85, 75, 60, 45]

    for score in test_scores:
        grade = grader.get_grade(score)
        min_f, max_f = grader.get_factor_range(grade)
        max_adv_pct = grader.get_max_advance_pct(grade)
        tier = grader.get_tier(grade)

        print(f"Score: {score}/100")
        print(f"  Grade: {grade} (Tier {tier})")
        print(f"  Factor Range: {min_f:.2f} - {max_f:.2f}")
        print(f"  Max Advance: {max_adv_pct*100:.0f}% of monthly revenue")
        print(f"  Approvable: {'Yes' if grader.is_approvable(score) else 'No'}")
        print()

    # Calculate max advance for specific scenario
    print("Example: $50,000 monthly revenue, Score 85 (Grade A-)")
    max_advance = grader.calculate_max_advance('A-', 50000)
    print(f"  Maximum Advance: ${max_advance:,.2f}")
    print(f"  Factor: 1.15 - 1.20")
    print(f"  Term: 3-6 months")


def demo_industry_scorer():
    """Demonstrate industry risk scoring"""
    print("\n" + "="*70)
    print("  INDUSTRY RISK SCORER DEMO")
    print("="*70 + "\n")

    scorer = IndustryScorer()

    # Example industries
    test_industries = [
        'medical_practice',   # Tier 1 - Preferred
        'restaurant',         # Tier 3 - Elevated risk
        'trucking',          # Tier 4 - High risk
        'cannabis'           # Tier 5 - Specialty
    ]

    for industry in test_industries:
        summary = scorer.get_industry_summary(industry)

        print(f"Industry: {industry.replace('_', ' ').title()}")
        print(f"  Tier: {summary['tier']} - {summary['tier_name']}")
        print(f"  Score Impact: {summary['adjustment']:+.0f} points")
        print(f"  Factor Impact: {summary['factor_mod']:+.3f}")
        print(f"  Note: {summary['note']}")
        print()

    # Search for industries
    print("Searching for 'medical' industries:")
    results = scorer.search_industries('medical')
    print(f"  Found: {', '.join(results)}")


def demo_cash_flow_analyzer():
    """Demonstrate cash flow analysis"""
    print("\n" + "="*70)
    print("  CASH FLOW ANALYZER DEMO")
    print("="*70 + "\n")

    analyzer = BankCashFlowAnalyzer()

    # Add 6 months of data
    months_data = [
        (12, 2024, 10000, 12000, 45000, 42000),
        (1,  2025, 12000, 13000, 47000, 44000),
        (2,  2025, 13000, 15000, 50000, 46000),
        (3,  2025, 15000, 14000, 48000, 45000),
        (4,  2025, 14000, 16000, 52000, 48000),
        (5,  2025, 16000, 17000, 54000, 50000),
    ]

    print("Adding 6 months of bank data...")
    for month, year, beg_bal, end_bal, deposits, withdrawals in months_data:
        analyzer.add_monthly_summary(
            month=month,
            year=year,
            beginning_balance=beg_bal,
            ending_balance=end_bal,
            total_deposits=deposits,
            total_withdrawals=withdrawals
        )

    # Calculate trailing averages
    print("\nTrailing Averages:")
    trailing = analyzer.calculate_trailing_averages()
    print(f"  3-Month Average: ${trailing.get('avg_3_month_deposits', 0):,.2f}/month")
    print(f"  6-Month Average: ${trailing.get('avg_6_month_deposits', 0):,.2f}/month")
    print(f"  Trend: {trailing.get('trend', 'N/A').upper()}")

    # Calculate trends
    print("\nDeposit Trends:")
    trends = analyzer.calculate_monthly_trends()
    print(f"  Direction: {trends.get('trend_direction', 'N/A').upper()}")
    print(f"  Volatility (CV): {trends.get('volatility_cv', 0):.1f}%")
    print(f"  High Volatility: {'Yes' if trends.get('high_volatility') else 'No'}")

    # Check for red flags
    print("\nUnderwriting Summary:")
    summary = analyzer.generate_underwriting_summary()
    print(f"  Red Flags: {len(summary.get('red_flags', []))}")
    print(f"  Warnings: {len(summary.get('warnings', []))}")

    if summary.get('warnings'):
        for warning in summary['warnings']:
            print(f"    ⚠ {warning}")


def demo_complete_scenario():
    """Demonstrate a complete underwriting scenario"""
    print("\n" + "="*70)
    print("  COMPLETE UNDERWRITING SCENARIO")
    print("="*70 + "\n")

    print("Business Profile:")
    print("  Name: Joe's Pizza")
    print("  Industry: Restaurant")
    print("  Monthly Revenue: $45,000")
    print("  Time in Business: 36 months")
    print("  Requested Funding: $50,000")
    print()

    # Industry risk
    industry_scorer = IndustryScorer()
    industry_summary = industry_scorer.get_industry_summary('restaurant')

    print(f"Industry Risk Assessment:")
    print(f"  Tier: {industry_summary['tier']} - {industry_summary['tier_name']}")
    print(f"  Score Adjustment: {industry_summary['adjustment']:+.0f} points")
    print(f"  Note: {industry_summary['note']}")
    print()

    # Assume we have a composite score
    base_score = 70  # B- grade
    adjusted_score = base_score + industry_summary['adjustment']  # 70 + (-8) = 62

    print(f"Scoring:")
    print(f"  Base Score: {base_score}/100")
    print(f"  Industry Adjustment: {industry_summary['adjustment']:+.0f}")
    print(f"  Final Score: {adjusted_score}/100")
    print()

    # Letter grade
    grader = LetterGrader()
    grade_summary = grader.get_grade_summary(adjusted_score)

    print(f"Letter Grade: {grade_summary['letter_grade']} (Tier {grade_summary['tier']})")
    print(f"  Factor Range: {grade_summary['factor_range'][0]:.2f} - {grade_summary['factor_range'][1]:.2f}")
    print(f"  Recommended Factor: {grade_summary['recommended_factor']:.2f}")
    print(f"  Max Advance %: {grade_summary['max_advance_pct']*100:.0f}%")
    print()

    # Calculate offer
    monthly_revenue = 45000
    max_advance = grader.calculate_max_advance(grade_summary['letter_grade'], monthly_revenue)
    requested = 50000

    print(f"Offer Calculation:")
    print(f"  Monthly Revenue: ${monthly_revenue:,.0f}")
    print(f"  Max Advance (based on grade): ${max_advance:,.0f}")
    print(f"  Amount Requested: ${requested:,.0f}")

    if requested <= max_advance:
        approved_amount = requested
        print(f"  [APPROVED]: ${approved_amount:,.0f}")
    else:
        approved_amount = max_advance
        print(f"  [COUNTER-OFFER]: ${approved_amount:,.0f} (requested exceeds max)")

    # Terms
    factor = grade_summary['recommended_factor']
    payback = approved_amount * factor
    min_term, max_term = grade_summary['term_months_range']

    print(f"\nProposed Terms:")
    print(f"  Advance: ${approved_amount:,.0f}")
    print(f"  Factor: {factor:.2f}")
    print(f"  Payback: ${payback:,.0f}")
    print(f"  Term: {min_term}-{max_term} months")
    print(f"  Approvable: {'Yes' if grade_summary['is_approvable'] else 'No'}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  MCA-RISK-MODEL LIBRARY - QUICK START EXAMPLES")
    print("="*70)

    demo_letter_grader()
    demo_industry_scorer()
    demo_cash_flow_analyzer()
    demo_complete_scenario()

    print("\n" + "="*70)
    print("  END OF DEMO")
    print("="*70 + "\n")