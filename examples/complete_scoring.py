"""
Complete MCA Scoring Example

Demonstrates the full scoring workflow from start to finish.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.mca_scorecard import MCAScoringModel
from models.scoring import BankAnalytics, ApplicationData


def example_basic_scoring():
    """Example: Basic deal scoring"""
    print("\n" + "="*70)
    print("  EXAMPLE 1: BASIC DEAL SCORING")
    print("="*70 + "\n")

    # Create scoring model
    model = MCAScoringModel()

    # Set application data
    model.set_application(
        business_name="Joe's Pizza",
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
    requested = 50000
    result = model.score(requested_amount=requested)

    # Display results
    print(f"Business: Joe's Pizza")
    print(f"Industry: Restaurant")
    print(f"Amount Requested: ${requested:,.0f}")
    print(f"\n{'='*70}")
    print(f"SCORING RESULT")
    print(f"{'='*70}\n")

    print(f"Total Score: {result.total_score:.1f}/100")
    print(f"Letter Grade: {result.letter_grade} (Tier {result.tier})")
    print(f"Factor Range: {result.recommended_factor:.2f}")
    print(f"Max Advance: ${result.max_advance:,.0f}")
    print(f"Max Advance %: {result.max_advance_pct*100:.0f}%")
    print(f"Term Range: {result.term_months_range[0]}-{result.term_months_range[1]} months")
    print(f"Approvable: {'Yes' if result.is_approvable else 'No'}")

    # Component breakdown
    print(f"\n{'='*70}")
    print(f"COMPONENT SCORES")
    print(f"{'='*70}\n")

    for component, score in result.component_scores.items():
        if component != 'industry_adjustment':
            print(f"  {component:25s}: {score:6.2f} pts")

    if 'industry_adjustment' in result.component_scores:
        adj = result.component_scores['industry_adjustment']
        print(f"\n  Industry Adjustment:          {adj:+.1f} pts")

    # Warnings
    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    return result


def example_aplus_deal():
    """Example: A+ grade deal"""
    print("\n" + "="*70)
    print("  EXAMPLE 2: A+ GRADE DEAL (EXCELLENT)")
    print("="*70 + "\n")

    model = MCAScoringModel()

    # Strong medical practice
    model.set_application(
        business_name="Smith Family Dental",
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

    print(f"Business: Smith Family Dental")
    print(f"Industry: Dental (Tier 1 - Preferred)")
    print(f"\nScore: {result.total_score:.1f}/100 - Grade {result.letter_grade}")
    print(f"Factor: {result.recommended_factor:.2f}")
    print(f"Max Advance: ${result.max_advance:,.0f} ({result.max_advance_pct*100:.0f}% of monthly revenue)")

    return result


def example_high_risk_deal():
    """Example: High-risk deal with warnings"""
    print("\n" + "="*70)
    print("  EXAMPLE 3: HIGH-RISK DEAL WITH WARNINGS")
    print("="*70 + "\n")

    model = MCAScoringModel()

    # Trucking company with issues
    model.set_application(
        business_name="Fast Freight LLC",
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
        mca_positions=['Rapid Funding', 'Forward Financing']  # 2 existing positions
    )

    result = model.score(requested_amount=35000)

    print(f"Business: Fast Freight LLC")
    print(f"Industry: Trucking (Tier 4 - High Risk)")
    print(f"\nScore: {result.total_score:.1f}/100 - Grade {result.letter_grade}")
    print(f"Factor: {result.recommended_factor:.2f}")
    print(f"Max Advance: ${result.max_advance:,.0f}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  [!] {warning}")

    print(f"\nIndustry Note: {result.industry_note}")

    return result


def example_with_blockers():
    """Example: Deal with blocking issues"""
    print("\n" + "="*70)
    print("  EXAMPLE 4: DEAL WITH BLOCKERS (DECLINED)")
    print("="*70 + "\n")

    model = MCAScoringModel()

    # Business below minimums
    model.set_application(
        business_name="New Startup Inc",
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

    print(f"Business: New Startup Inc")
    print(f"Industry: Retail")
    print(f"\nPre-Check Result: {'PASSED' if result.pre_check.passed else 'FAILED'}")

    if result.pre_check.blockers:
        print(f"\nBlockers ({len(result.pre_check.blockers)}):")
        for blocker in result.pre_check.blockers:
            print(f"  [X] {blocker}")

    print(f"\nDecision: DECLINED")
    print(f"Reason: {result.pre_check.message}")

    return result


def compare_industries():
    """Example: Compare same metrics across different industries"""
    print("\n" + "="*70)
    print("  EXAMPLE 5: INDUSTRY COMPARISON")
    print("="*70 + "\n")

    # Same metrics, different industries
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

    industries = [
        ("medical_practice", "Medical Practice"),
        ("manufacturing", "Manufacturing"),
        ("restaurant", "Restaurant"),
        ("trucking", "Trucking")
    ]

    print("Identical metrics applied to different industries:\n")
    print(f"{'Industry':<25} {'Score':<10} {'Grade':<8} {'Factor':<10} {'Max Adv'}")
    print("-" * 70)

    for industry_key, industry_name in industries:
        model = MCAScoringModel()
        model.set_application(industry=industry_key, **base_app)
        model.set_bank_analytics(**base_bank)
        result = model.score(requested_amount=50000)

        print(f"{industry_name:<25} {result.total_score:>6.1f}     {result.letter_grade:<8} {result.recommended_factor:<10.2f} ${result.max_advance:>8,.0f}")

    print("\nConclusion: Industry risk significantly impacts pricing and terms!")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  MCA-RISK-MODEL: COMPLETE SCORING EXAMPLES")
    print("="*70)

    # Run all examples
    example_basic_scoring()
    example_aplus_deal()
    example_high_risk_deal()
    example_with_blockers()
    compare_industries()

    print("\n" + "="*70)
    print("  END OF EXAMPLES")
    print("="*70 + "\n")
