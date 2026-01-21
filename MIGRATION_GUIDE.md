# Migration Guide: Legacy Risk Model → New Toolkit Architecture

This guide explains how to migrate from the monolithic legacy risk model to the new modular toolkit architecture.

## Overview

**Old Architecture** (MCA-Risk-Model):
- Single repo with all code (parsing, analytics, scoring, pricing)
- Tightly coupled components
- Hard to reuse or test independently

**New Architecture** (Functional Core + Imperative Shell):
- 6 focused toolkits (parser, classifier, analytics, tracker, scoring, pricing)
- 1 orchestration product (Risk-Model-01)
- Clear separation: logic vs state

## Architecture Comparison

### Before (Monolith)
```
MCA-Risk-Model/
├── parsing/
│   ├── bank_statement_parser.py  (parsing + classification mixed)
│   └── bank_templates.py
├── analytics/
│   └── cashflow_analyzer.py      (analytics + scoring mixed)
├── scoring/
│   ├── mca_scorecard.py          (scoring + pricing mixed)
│   └── letter_grader.py
├── models/
├── data/
└── tests/
```

### After (Modular)
```
bankstatement-parser-toolkit/     ← Parsing only
transaction-classifier-toolkit/    ← Classification only
cashflow-analytics-toolkit/        ← Analytics only
rbf-position-tracker-toolkit/      ← RBF detection only
rbf-scoring-toolkit/               ← Scoring only
rbf-pricing-toolkit/               ← Pricing only
Risk-Model-01/                     ← Orchestration + MSSQL + CLI
```

## Migration Status

| Component | Status | Repo | Notes |
|-----------|--------|------|-------|
| **Parser** | ✅ Complete | [bankstatement-parser-toolkit](https://github.com/silv-mt-holdings/bankstatement-parser-toolkit) | Pushed to GitHub |
| **Classifier** | ✅ Complete | [transaction-classifier-toolkit](https://github.com/silv-mt-holdings/transaction-classifier-toolkit) | Pushed to GitHub |
| **Analytics** | ⏳ Pending | [cashflow-analytics-toolkit](https://github.com/silv-mt-holdings/cashflow-analytics-toolkit) | Repo created |
| **Tracker** | ✅ Complete | [rbf-position-tracker-toolkit](https://github.com/silv-mt-holdings/rbf-position-tracker-toolkit) | Pushed to GitHub |
| **Scoring** | ✅ Complete | [rbf-scoring-toolkit](https://github.com/silv-mt-holdings/rbf-scoring-toolkit) | Pushed to GitHub |
| **Pricing** | ✅ Complete | [rbf-pricing-toolkit](https://github.com/silv-mt-holdings/rbf-pricing-toolkit) | Pushed to GitHub |

## Step-by-Step Migration

### Phase 1: Install Completed Toolkits ✅

```bash
# Install implemented toolkits
pip install git+https://github.com/silv-mt-holdings/bankstatement-parser-toolkit.git
pip install git+https://github.com/silv-mt-holdings/transaction-classifier-toolkit.git
```

### Phase 2: Extract Remaining Components (Next Steps)

**2a. Extract cashflow-analytics-toolkit**

From `MCA-Risk-Model/analytics/cashflow_analyzer.py` extract:
- Average daily balance calculation
- Trailing averages (3/6/12 month)
- Trend analysis (increasing/stable/declining)
- Volatility metrics (coefficient of variation)
- NSF/overdraft detection
- Red flag generation

**2b. Extract rbf-position-tracker-toolkit**

Create new logic for:
- RBF payment frequency detection
- Payment pattern analysis
- Stacking risk calculation
- Estimated balance calculation

**2c. Extract rbf-scoring-toolkit**

From `MCA-Risk-Model/scoring/` extract:
- `mca_scorecard.py` → 100-point composite scoring
- `letter_grader.py` → Letter grade assignment
- `industry_scorer.py` → Industry risk adjustment
- `precheck.py` → Pre-check validation
- `data/scoring_weights.json`
- `data/letter_grade_thresholds.json`
- `data/industry_risk_db.json`

**2d. Extract rbf-pricing-toolkit**

From `MCA-Risk-Model/scoring/` extract:
- Factor rate calculation logic
- Max advance calculation
- Term recommendation logic
- Deal tier classification
- `data/deal_tier_thresholds.json`

### Phase 3: Update Risk-Model-01

**3a. Update requirements.txt**

```txt
# Toolkit dependencies
git+https://github.com/silv-mt-holdings/bankstatement-parser-toolkit.git
git+https://github.com/silv-mt-holdings/transaction-classifier-toolkit.git
git+https://github.com/silv-mt-holdings/cashflow-analytics-toolkit.git
git+https://github.com/silv-mt-holdings/rbf-position-tracker-toolkit.git
git+https://github.com/silv-mt-holdings/rbf-scoring-toolkit.git
git+https://github.com/silv-mt-holdings/rbf-pricing-toolkit.git

# Database
pyodbc>=4.0.0
pymssql>=2.2.0

# Environment
python-dotenv>=1.0.0

# Integrations
googlemaps>=4.10.0
requests>=2.31.0
```

**3b. Create orchestrator/pipeline.py**

```python
"""
Underwriting Pipeline

Orchestrates all toolkits into end-to-end underwriting workflow.
"""

from parser.statement_parser import BankStatementParser
from classifier.revenue_classifier import RevenueClassifier
from analytics.cashflow_analyzer import CashFlowAnalyzer
from tracker.position_analyzer import PositionTracker
from scoring.rbf_scorecard import RBFScoringModel
from pricing.factor_calculator import PricingCalculator
from integrations.mssql import save_application, get_db_connection

class UnderwritingPipeline:
    """
    End-to-end RBF underwriting pipeline.
    """

    def __init__(self):
        self.parser = BankStatementParser()
        self.classifier = RevenueClassifier()
        self.analytics = CashFlowAnalyzer()
        self.tracker = PositionTracker()
        self.scorer = RBFScoringModel()
        self.pricer = PricingCalculator()

    def process(self, pdf_bytes, fico, industry, business_name):
        """
        Process a complete underwriting application.

        Args:
            pdf_bytes: Bank statement PDF
            fico: FICO score
            industry: Industry name/NAICS
            business_name: Business name

        Returns:
            Complete underwriting result with pricing
        """
        # 1. Parse bank statement
        statement = self.parser.parse(pdf_bytes)

        # 2. Classify transactions
        classified = self.classifier.classify_all(statement.transactions)

        # 3. Analyze cash flow
        cash_flow = self.analytics.analyze(classified)

        # 4. Track RBF positions
        positions = self.tracker.find_positions(classified)

        # 5. Score the deal
        score_result = self.scorer.score(
            cash_flow=cash_flow,
            positions=positions,
            fico=fico,
            industry=industry
        )

        # 6. Calculate pricing
        pricing = self.pricer.calculate(
            grade=score_result.letter_grade,
            monthly_revenue=cash_flow.monthly_true_revenue
        )

        # 7. Save to database
        with get_db_connection() as conn:
            application_id = save_application(
                conn,
                business_name=business_name,
                statement_result=statement,
                score_result=score_result,
                pricing=pricing
            )

        return {
            'application_id': application_id,
            'statement': statement,
            'cash_flow': cash_flow,
            'positions': positions,
            'score': score_result,
            'pricing': pricing
        }
```

**3c. Update cli.py**

```python
"""
Risk-Model-01 CLI

Command-line interface for RBF underwriting.
"""

import click
from pathlib import Path
from orchestrator.pipeline import UnderwritingPipeline

@click.group()
def cli():
    """RBF Risk Model CLI"""
    pass

@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('--fico', type=int, required=True, help='FICO score')
@click.option('--industry', required=True, help='Industry name')
@click.option('--business-name', required=True, help='Business name')
def score(pdf_file, fico, industry, business_name):
    """Score an RBF application from bank statement"""

    # Read PDF
    with open(pdf_file, 'rb') as f:
        pdf_bytes = f.read()

    # Process through pipeline
    pipeline = UnderwritingPipeline()
    result = pipeline.process(pdf_bytes, fico, industry, business_name)

    # Display results
    click.echo(f"\n✅ Application #{result['application_id']} processed")
    click.echo(f"\nScore: {result['score'].total_score:.1f}/100")
    click.echo(f"Grade: {result['score'].letter_grade}")
    click.echo(f"Approvable: {'Yes' if result['score'].is_approvable else 'No'}")
    click.echo(f"\nRecommended Factor: {result['pricing'].recommended_factor}")
    click.echo(f"Max Advance: ${result['pricing'].max_advance:,.2f}")

if __name__ == '__main__':
    cli()
```

**3d. Remove Duplicated Code**

Delete from Risk-Model-01:
- `parsing/` (replaced by bankstatement-parser-toolkit)
- `analytics/` (replaced by cashflow-analytics-toolkit)
- `scoring/` (replaced by mca-scoring-toolkit + mca-pricing-toolkit)
- Duplicated data files in `data/` (kept in toolkits)

Keep in Risk-Model-01:
- `integrations/mssql.py` (database code)
- `integrations/google_places.py` (API integrations)
- `cli.py` (command-line interface)
- `orchestrator/` (pipeline orchestration)
- `reports/` (PDF generation)
- `mssql/schema.sql` (database schema)
- `config/settings.py` (application config)

### Phase 4: Testing

**Test individual toolkits:**

```bash
# Test parser
cd bankstatement-parser-toolkit
pytest tests/

# Test classifier
cd transaction-classifier-toolkit
pytest tests/
```

**Test integration:**

```bash
# Test full pipeline
cd Risk-Model-01
pytest tests/test_integration.py
```

### Phase 5: Deployment

**Option A: Development Mode**

```bash
cd C:\Dev\Trusted
cd bankstatement-parser-toolkit && pip install -e . && cd ..
cd transaction-classifier-toolkit && pip install -e . && cd ..
cd cashflow-analytics-toolkit && pip install -e . && cd ..
cd mca-position-tracker-toolkit && pip install -e . && cd ..
cd mca-scoring-toolkit && pip install -e . && cd ..
cd mca-pricing-toolkit && pip install -e . && cd ..
cd Risk-Model-01
pip install -r requirements.txt
```

**Option B: Production Mode**

```bash
cd Risk-Model-01
pip install -r requirements.txt  # Installs all toolkits from GitHub
python cli.py score statement.pdf --fico 680 --industry restaurant --business-name "Joe's Pizza"
```

## Code Mapping

### Old → New Mapping

| Old Location (MCA-Risk-Model) | New Location | Toolkit |
|------------------------------|--------------|---------|
| `parsing/bank_statement_parser.py` (parsing logic) | `parser/statement_parser.py` | bankstatement-parser-toolkit |
| `parsing/bank_templates.py` | `parser/bank_templates.py` | bankstatement-parser-toolkit |
| `parsing/bank_statement_parser.py` (classification) | `classifier/revenue_classifier.py` | transaction-classifier-toolkit |
| `data/mca_lender_list.json` | `data/mca_lender_list.json` | transaction-classifier-toolkit |
| `data/revenue_patterns.json` | `data/revenue_patterns.json` | transaction-classifier-toolkit |
| `analytics/cashflow_analyzer.py` | `analytics/cashflow_analyzer.py` | cashflow-analytics-toolkit |
| `analytics/` (RBF detection) | `tracker/position_analyzer.py` | rbf-position-tracker-toolkit |
| `scoring/rbf_scorecard.py` | `scoring/rbf_scorecard.py` | rbf-scoring-toolkit |
| `scoring/letter_grader.py` | `scoring/letter_grader.py` | rbf-scoring-toolkit |
| `scoring/industry_scorer.py` | `scoring/industry_scorer.py` | rbf-scoring-toolkit |
| `scoring/` (pricing logic) | `pricing/factor_calculator.py` | rbf-pricing-toolkit |
| `data/scoring_weights.json` | `data/scoring_weights.json` | rbf-scoring-toolkit |
| `data/deal_tier_thresholds.json` | `data/deal_tier_thresholds.json` | rbf-pricing-toolkit |

## Benefits of New Architecture

| Benefit | Description |
|---------|-------------|
| **Modularity** | Each toolkit has ONE job |
| **Reusability** | Use parser toolkit in other projects (fraud detection, reporting, etc.) |
| **Testability** | Unit test each toolkit independently |
| **Maintainability** | Easier to find and fix bugs |
| **Collaboration** | Different teams can own different toolkits |
| **Deployment Flexibility** | Install only what you need |
| **Clear Boundaries** | Logic (toolkits) vs State (Risk-Model-01) |

## Troubleshooting

### Import Errors

```python
# If you get: ModuleNotFoundError: No module named 'parser'
# Solution: Install the toolkit
pip install git+https://github.com/silv-mt-holdings/bankstatement-parser-toolkit.git
```

### Data File Not Found

```python
# If classifier can't find mca_lender_list.json
# Solution: Ensure data files are in toolkit's data/ directory
# They're packaged with setup.py's package_data
```

### Database Connection Errors

```python
# Risk-Model-01 specific - check .env file
# Ensure MSSQL_CONNECTION_STRING is set
```

## Next Steps

1. ✅ **Complete toolkit implementations** (cashflow, tracker, scoring, pricing)
2. ✅ **Update Risk-Model-01** requirements.txt and orchestrator
3. ✅ **Test integration** end-to-end
4. ✅ **Delete MCA-Risk-Model** locally (keep as archive if needed)
5. ✅ **Update documentation** in each toolkit README
6. ⏭️ **Optional: Publish to PyPI** for easier installation

## Support

For questions or issues:
- [bankstatement-parser-toolkit issues](https://github.com/silv-mt-holdings/bankstatement-parser-toolkit/issues)
- [transaction-classifier-toolkit issues](https://github.com/silv-mt-holdings/transaction-classifier-toolkit/issues)
- [Risk-Model-01 issues](https://github.com/silv-mt-holdings/Risk-Model-01/issues)

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Functional Core/Imperative Shell pattern
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) - AI coding guidelines
