# MCA Risk Scoring Model

Modular risk scoring system for Merchant Cash Advance (MCA) underwriting.

## Architecture

This system follows a **3-layer pipeline** architecture:

```
+-------------------------------------------------------------------------+
|                         MCA RISK MODEL PIPELINE                         |
+-------------------------------------------------------------------------+

  +--------------+      +--------------+      +--------------+
  |   PARSING    | ---> |  ANALYTICS   | ---> |   SCORING    |
  |              |      |              |      |              |
  | - PDF Extract|      | - Cash Flow  |      | - Composite  |
  | - Bank Parse |      | - Deposits   |      | - Industry   |
  | - Templates  |      | - NSF/OD     |      | - Letter     |
  |              |      | - Balances   |      | - Credit     |
  +--------------+      +--------------+      +--------------+
        |                      |                     |
        v                      v                     v
   Transactions           Metrics/KPIs          Risk Score
   (structured)           (calculated)          (A+ to F)
```

## Layer Descriptions

### 1. Parsing Layer (`parsing/`)
Extracts raw data from bank statement PDFs and converts to structured transactions.

- **bank_statement_parser.py** - Core parsing logic for bank statements
- **pdf_extractor.py** - PDF text extraction and table detection
- **statement_templates/** - Bank-specific parsing templates

### 2. Analytics Layer (`analytics/`)
Transforms raw transactions into underwriting metrics and KPIs.

- **cashflow_analyzer.py** - Trailing averages, trends, volatility
- **deposit_categorizer.py** - Revenue classification (true revenue vs transfers)
- **nsf_analyzer.py** - NSF/overdraft detection and scoring
- **balance_tracker.py** - Average daily balance, low balance days

### 3. Scoring Layer (`scoring/`)
Combines metrics into a composite risk score with letter grade output.

- **mca_scorecard.py** - Main scoring orchestrator
- **credit_scoring.py** - FICO bucket scoring
- **industry_scorer.py** - Industry risk tier scoring
- **letter_grader.py** - Score-to-letter-grade conversion
- **composite_scorer.py** - Weighted composite score calculation

## Installation

```bash
git clone https://github.com/silv-mt-holdings/MCA-Risk-Model.git
cd MCA-Risk-Model
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Score

```python
from scoring import MCAScorecard

# Create scorecard with metrics
scorecard = MCAScorecard()
scorecard.set_bank_metrics(
    trailing_avg_3mo=45000,
    trailing_avg_6mo=42000,
    trend='stable',
    nsf_count=2,
    avg_daily_balance=8500
)
scorecard.set_credit_metrics(fico_score=680)
scorecard.set_industry('restaurant')
scorecard.set_deal_metrics(position_count=1, funding_amount=25000)

# Get composite score and letter grade
result = scorecard.calculate()
print(f"Score: {result.score}/100")
print(f"Grade: {result.letter_grade}")
```

### Full Pipeline

```python
from parsing import BankStatementParser
from analytics import CashFlowAnalyzer
from scoring import MCAScorecard

# Parse bank statements
parser = BankStatementParser()
transactions = parser.parse_pdf('statement.pdf')

# Analyze cash flow
analyzer = CashFlowAnalyzer(transactions)
metrics = analyzer.calculate_metrics()

# Score the deal
scorecard = MCAScorecard()
scorecard.load_metrics(metrics)
result = scorecard.calculate()

print(result.summary())
```

### CLI Usage

```bash
# Score from bank statement PDF
python cli.py score statement.pdf --fico 680 --industry restaurant

# Analyze only (no scoring)
python cli.py analyze statement.pdf --output metrics.json
```

## Configuration

Scoring weights and thresholds are configurable via JSON files in `data/`:

- **scoring_weights.json** - Category weight distribution
- **letter_grade_thresholds.json** - Score-to-grade mapping
- **industry_risk_db.json** - Industry risk tier database

## Scoring Categories

| Category | Weight | Components |
|----------|--------|------------|
| Bank Metrics | 40% | Trailing avg, trend, volatility, NSF, ADB |
| Credit Metrics | 25% | FICO score, credit utilization |
| Industry Metrics | 20% | Industry tier, time in business |
| Deal Metrics | 15% | Position count, funding amount |

## Letter Grades

| Grade | Score Range | Risk Level |
|-------|-------------|------------|
| A | 80-100 | Low Risk |
| B | 65-79 | Moderate Risk |
| C | 50-64 | Standard Risk |
| D | 35-49 | High Risk |
| F | 0-34 | Very High Risk |

## Testing

```bash
python -m pytest tests/
```

## Project Structure

```
MCA-Risk-Model/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
│
├── parsing/
│   ├── __init__.py
│   ├── bank_statement_parser.py
│   ├── pdf_extractor.py
│   └── statement_templates/
│       └── __init__.py
│
├── analytics/
│   ├── __init__.py
│   ├── cashflow_analyzer.py
│   ├── deposit_categorizer.py
│   ├── nsf_analyzer.py
│   └── balance_tracker.py
│
├── scoring/
│   ├── __init__.py
│   ├── mca_scorecard.py
│   ├── credit_scoring.py
│   ├── industry_scorer.py
│   ├── letter_grader.py
│   └── composite_scorer.py
│
├── data/
│   ├── industry_risk_db.json
│   ├── scoring_weights.json
│   └── letter_grade_thresholds.json
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_analytics.py
│   └── test_scoring.py
│
└── cli.py
```

## License

Proprietary - Silv MT Holdings
