# MCA-Risk-Model

**Clean, modular MCA (Merchant Cash Advance) risk scoring and underwriting library**

A production-ready Python library for MCA underwriting with bank statement parsing, cash flow analysis, and comprehensive risk scoring. Built with a layered architecture separating parsing, analytics, and scoring concerns.

## Features

### 🔍 Parsing Layer
- **Bank Statement Parser**: Extract transactions, balances, and metrics from bank statements
- **MCA Detection**: Identify existing MCA positions from 50+ lenders
- **Revenue Classification**: Distinguish true revenue from transfers, loans, and other non-operational deposits
- **Wire Transfer Analysis**: Classify and validate wire transfers
- **Treasury Payment Validation**: Identify legitimate government payments

### 📊 Analytics Layer
- **Cash Flow Analyzer**: Trailing averages (3/6/12 month), trend analysis, volatility metrics
- **Deposit Categorizer**: ACH, wire, cash, card processing classification
- **NSF Analyzer**: NSF count, overdraft detection, negative day analysis
- **Balance Tracker**: Average daily balance (ADB), balance trends
- **MCA Position Detector**: Identify and track existing MCA obligations

### 🎯 Scoring Layer
- **MCA Scorecard**: 100-point composite risk score with 11 weighted components
- **Letter Grader**: 13-grade system (A+ through F) with pricing and term recommendations
- **Industry Scorer**: 5-tier industry risk segmentation (60+ industries)
- **Deal Tier Classifier**: Micro/Small/Mid/Large/Jumbo classification with document requirements
- **Component Scorers**: Modular scoring for revenue, cash flow, ADB, NSF, FICO, TIB, etc.

## Installation

```bash
cd MCA-Risk-Model
pip install -r requirements.txt
```

## Quick Start

### Complete Example: Score a Deal

The simplest way to score a deal using method chaining:

```python
from scoring.mca_scorecard import MCAScoringModel

# Score a deal with method chaining
result = (MCAScoringModel()
    .set_application(
        business_name="Joe's Pizza",
        industry="restaurant",
        fico_score=680,
        time_in_business_months=36,
        monthly_merchant_volume=38000,
        merchant_tenure_months=24
    )
    .set_bank_analytics(
        monthly_true_revenue=45000,
        average_daily_balance=15000,
        nsf_count_90d=1,
        negative_days_90d=0,
        deposit_variance=0.18,
        total_deposits_90d=135000,
        total_withdrawals_90d=128000,
        mca_positions=[]
    )
    .score(requested_amount=50000))

# Display results
print(f"\n{'='*70}")
print(f"SCORING RESULT")
print(f"{'='*70}\n")
print(f"Total Score: {result.total_score:.1f}/100")
print(f"Letter Grade: {result.letter_grade} (Tier {result.tier})")
print(f"Recommended Factor: {result.recommended_factor:.2f}")
print(f"Max Advance: ${result.max_advance:,.0f}")
print(f"Max Advance %: {result.max_advance_pct*100:.0f}%")
print(f"Term Range: {result.term_months_range[0]}-{result.term_months_range[1]} months")
print(f"Approvable: {'Yes' if result.is_approvable else 'No'}")

# Component scores breakdown
print(f"\n{'='*70}")
print(f"COMPONENT SCORES")
print(f"{'='*70}\n")
for component, score in result.component_scores.items():
    print(f"  {component:25s}: {score:6.2f} pts")

# Pre-check validation
if result.pre_check.blockers:
    print(f"\nBlockers:")
    for blocker in result.pre_check.blockers:
        print(f"  [X] {blocker}")

if result.warnings:
    print(f"\nWarnings:")
    for warning in result.warnings:
        print(f"  [!] {warning}")
```

### Example: Parse Bank Statement

```python
from parsing.bank_statement_parser import BankStatementParser

parser = BankStatementParser()

# Parse PDF or text
with open('bank_statement.pdf', 'rb') as f:
    result = parser.parse(f.read(), 'statement.pdf')

# Access parsed data
print(f"True Revenue (90d): ${result.summary.true_revenue_90d:,.2f}")
print(f"Monthly True Revenue: ${result.summary.monthly_true_revenue:,.2f}")
print(f"Average Daily Balance: ${result.summary.average_daily_balance:,.2f}")
print(f"NSF Count: {result.summary.nsf_count}")
print(f"Negative Days: {result.summary.negative_days_90d}")
print(f"Deposit Variance: {result.summary.deposit_variance:.2%}")

# MCA positions detected
print(f"\nMCA Positions Found: {len(result.mca_positions)}")
for position in result.mca_positions:
    print(f"  - {position.mca_name}: ${position.payment_amount:,.2f}/payment")
    print(f"    Est. Monthly: ${position.avg_monthly_payment:,.2f}")

# Transactions
print(f"\nTotal Transactions: {len(result.transactions)}")
true_revenue_txns = [t for t in result.transactions if t.is_true_revenue]
print(f"True Revenue Transactions: {len(true_revenue_txns)}")
```

### Example: Analyze Cash Flow Trends

```python
from analytics.cashflow_analyzer import BankCashFlowAnalyzer

analyzer = BankCashFlowAnalyzer()

# Add 6 months of data
months_data = [
    (7,  2025, 10000, 12000, 45000, 42000),
    (8,  2025, 12000, 13000, 47000, 44000),
    (9,  2025, 13000, 15000, 50000, 46000),
    (10, 2025, 15000, 14000, 48000, 45000),
    (11, 2025, 14000, 16000, 52000, 48000),
    (12, 2025, 16000, 17000, 54000, 50000),
]

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
trailing = analyzer.calculate_trailing_averages()
print(f"3-Month Avg Deposits: ${trailing['avg_3_month_deposits']:,.2f}")
print(f"6-Month Avg Deposits: ${trailing['avg_6_month_deposits']:,.2f}")
print(f"Trend: {trailing['trend'].upper()}")

# Calculate trends
trends = analyzer.calculate_monthly_trends()
print(f"\nDeposit Trends:")
print(f"  Direction: {trends['trend_direction'].upper()}")
print(f"  Volatility (CV): {trends['volatility_cv']:.1f}%")
print(f"  High Volatility: {'Yes' if trends['high_volatility'] else 'No'}")

# Generate underwriting summary
summary = analyzer.generate_underwriting_summary()
print(f"\nUnderwriting Summary:")
print(f"  Red Flags: {len(summary['red_flags'])}")
print(f"  Warnings: {len(summary['warnings'])}")

if summary['red_flags']:
    print("\nRed Flags:")
    for flag in summary['red_flags']:
        print(f"  [X] {flag}")

if summary['warnings']:
    print("\nWarnings:")
    for warning in summary['warnings']:
        print(f"  [!] {warning}")
```

### Example: Letter Grader Usage

```python
from scoring.letter_grader import LetterGrader, get_letter_grade

grader = LetterGrader()

# Get letter grade from score
score = 85
grade = grader.get_grade(score)  # Returns 'A-'

# Get comprehensive grade summary
summary = grader.get_grade_summary(score)
print(f"Score: {summary['score']}/100")
print(f"Letter Grade: {summary['letter_grade']}")
print(f"Tier: {summary['tier']}")
print(f"Factor Range: {summary['factor_range'][0]:.2f} - {summary['factor_range'][1]:.2f}")
print(f"Recommended Factor: {summary['recommended_factor']:.2f}")
print(f"Max Advance %: {summary['max_advance_pct']*100:.0f}%")
print(f"Term Range: {summary['term_months_range'][0]}-{summary['term_months_range'][1]} months")
print(f"Approvable: {'Yes' if summary['is_approvable'] else 'No'}")
print(f"Tier 1 (A tier): {'Yes' if summary['is_tier_1'] else 'No'}")

# Calculate max advance
monthly_revenue = 50000
max_advance = grader.calculate_max_advance(grade, monthly_revenue)
print(f"\nMax Advance: ${max_advance:,.0f}")

# Convenience function
grade = get_letter_grade(85)  # Returns 'A-'
```

### Example: Industry Risk Assessment

```python
from scoring.industry_scorer import IndustryScorer, get_industry_risk

scorer = IndustryScorer()

# Get industry risk summary
industry = "restaurant"
summary = scorer.get_industry_summary(industry)

print(f"Industry: {industry.replace('_', ' ').title()}")
print(f"Tier: {summary['tier']} - {summary['tier_name']}")
print(f"Score Adjustment: {summary['adjustment']:+.0f} points")
print(f"Factor Modification: {summary['factor_mod']:+.3f}")
print(f"Note: {summary['note']}")

# Compare multiple industries
industries = ['dental', 'restaurant', 'trucking', 'cannabis']
print(f"\n{'Industry':<25} {'Tier':<5} {'Adjustment':<12} {'Factor Mod'}")
print("-" * 65)

for ind in industries:
    risk = scorer.get_industry_risk(ind)
    if risk:
        print(f"{ind.replace('_', ' ').title():<25} {risk['tier']:<5} "
              f"{risk['adjustment']:+6.0f} pts   {risk['factor_mod']:+.3f}")

# Search for industries
results = scorer.search_industries('medical')
print(f"\nFound medical industries: {', '.join(results)}")

# Convenience function
risk = get_industry_risk('restaurant')  # Returns dict or None
```

## Architecture

```
MCA-Risk-Model/
├── parsing/              # INPUT LAYER
│   ├── bank_statement_parser.py
│   └── statement_templates/
├── analytics/            # PROCESSING LAYER
│   ├── cashflow_analyzer.py
│   ├── deposit_categorizer.py
│   ├── mca_detector.py
│   ├── nsf_analyzer.py
│   └── balance_tracker.py
├── scoring/              # SCORING LAYER
│   ├── mca_scorecard.py
│   ├── letter_grader.py
│   ├── industry_scorer.py
│   └── deal_tier_classifier.py
├── models/               # SHARED DATA CLASSES
│   ├── transactions.py
│   ├── analytics.py
│   └── scoring.py
├── data/                 # REFERENCE DATA (JSON)
│   ├── letter_grade_thresholds.json
│   ├── scoring_weights.json
│   ├── industry_risk_db.json
│   ├── mca_lender_list.json
│   ├── revenue_patterns.json
│   └── deal_tier_thresholds.json
└── tests/                # TEST SUITE
    ├── test_parsing.py
    ├── test_analytics.py
    └── test_scoring.py
```

## Scoring Methodology

### 100-Point Composite Score

| Component | Points | Description |
|-----------|--------|-------------|
| **Bank Analytics** | **55** | |
| True Revenue | 15 | Monthly true revenue volume |
| Cash Flow Margin (CFCR) | 12 | Available cash after obligations |
| Average Daily Balance | 10 | ADB relative to funding |
| NSF/Overdraft | 10 | NSF count + negative days (penalty) |
| Deposit Consistency | 8 | Variance in deposits |
| **Credit** | **12** | |
| FICO Score | 12 | Self-reported (discounted weight) |
| **Merchant Data** | **13** | |
| Merchant Volume | 8 | Card processing volume |
| Merchant Tenure | 5 | Time with processor |
| **Business Profile** | **15** | |
| Time in Business | 8 | TIB in months |
| Industry Risk | 7 | Industry segmentation (5 tiers) |
| **Position Analysis** | **5** | |
| Existing Positions | 5 | MCA stacking analysis |

### Letter Grades (13 Grades)

- **A+ (95-100)**: Factor 1.10-1.15, up to 20% advance
- **A (90-94)**: Factor 1.12-1.18, up to 18% advance
- **A- (85-89)**: Factor 1.15-1.20, up to 16% advance
- **B+ (80-84)**: Factor 1.18-1.25, up to 15% advance
- **B (75-79)**: Factor 1.22-1.28, up to 14% advance
- **B- (70-74)**: Factor 1.25-1.32, up to 12% advance
- **C+ (65-69)**: Factor 1.28-1.35, up to 11% advance
- **C (60-64)**: Factor 1.32-1.38, up to 10% advance
- **C- (55-59)**: Factor 1.35-1.42, up to 9% advance
- **D+ (50-54)**: Factor 1.38-1.45, up to 8% advance
- **D (45-49)**: Factor 1.42-1.48, up to 7% advance
- **D- (40-44)**: Factor 1.45-1.52, up to 6% advance
- **F (0-39)**: Factor 1.50-1.65, up to 5% advance

## Data Files

All configuration data is externalized to JSON for easy customization:

- **letter_grade_thresholds.json**: Letter grade definitions and pricing
- **scoring_weights.json**: Component weights (must sum to 100)
- **industry_risk_db.json**: 60+ industries with risk tiers
- **mca_lender_list.json**: 50+ MCA lenders with AKA names
- **revenue_patterns.json**: True vs non-true revenue patterns
- **deal_tier_thresholds.json**: Deal sizing and document requirements

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_scoring.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Dependencies

- **Core**: Python 3.8+
- **Analytics**: pandas, numpy
- **Parsing**: python-dateutil (optional)
- **Development**: pytest, pytest-cov

## Contributing

This is a standalone library extracted from the UnderwritingToolkit project. To contribute:

1. Maintain separation of concerns (parsing → analytics → scoring)
2. Keep data in JSON files (never hardcode thresholds)
3. Write tests for all new features
4. Follow existing patterns for consistency

## License

Internal use only - IntensiveCapFi / Silv MT Holdings

## Version

**v2.0** - Initial modular extraction (January 2026)

---

**Author**: IntensiveCapFi
**Migrated from**: UnderwritingToolkit (UnderwritingToolkit project)
