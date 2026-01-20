# Risk-Model-01 Architecture

> **Modular MCA Underwriting System** - Functional Core (Toolkits) + Imperative Shell (Product)

## Design Pattern: Functional Core, Imperative Shell

This architecture separates **pure business logic** (toolkits) from **application concerns** (database, CLI, integrations).

```
┌─────────────────────────────────────────────────────────┐
│          IMPERATIVE SHELL (Risk-Model-01)               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  CLI, MSSQL, Integrations, Reports, Orchestrator │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                              │
│                          ▼                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │           FUNCTIONAL CORE (Toolkits)              │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Stateless, Pure Logic, Database-Agnostic   │  │  │
│  │  │  - bankstatement-parser-toolkit             │  │  │
│  │  │  - transaction-classifier-toolkit           │  │  │
│  │  │  - cashflow-analytics-toolkit               │  │  │
│  │  │  - mca-position-tracker-toolkit             │  │  │
│  │  │  - mca-scoring-toolkit                      │  │  │
│  │  │  - mca-pricing-toolkit                      │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Why This Separation?

| Concern | Functional Core (Toolkits) | Imperative Shell (Risk-Model-01) |
|---------|---------------------------|----------------------------------|
| **State** | Stateless, pure functions | Stateful (MSSQL, env vars) |
| **Database** | Database-agnostic | MSSQL-specific |
| **Testing** | Unit tests, no mocks | Integration tests |
| **Reusability** | Can be used by other apps | App-specific orchestration |
| **Deployment** | Versioned packages | Application deployment |
| **Change Frequency** | Low (stable algorithms) | High (features, schema changes) |

## Functional Core: Toolkits

### 1. [bankstatement-parser-toolkit](https://github.com/silv-mt-holdings/bankstatement-parser-toolkit)
**Input**: PDF bytes
**Output**: `StatementResult` (transactions, balances, detected bank)
**No database**, **No external APIs**

```python
from parser.statement_parser import BankStatementParser

parser = BankStatementParser()
result = parser.parse(pdf_bytes, filename="statement.pdf")
# Pure function: same input = same output
```

---

### 2. [transaction-classifier-toolkit](https://github.com/silv-mt-holdings/transaction-classifier-toolkit)
**Input**: `List[Transaction]`
**Output**: `List[ClassifiedTransaction]` (revenue type, MCA detection)
**No database**

**Depends on**: bankstatement-parser-toolkit (for Transaction model)

---

### 3. [cashflow-analytics-toolkit](https://github.com/silv-mt-holdings/cashflow-analytics-toolkit)
**Input**: `List[ClassifiedTransaction]`
**Output**: `CashFlowSummary` (trends, volatility, NSF, ADB)
**No database**

**Depends on**: transaction-classifier-toolkit

---

### 4. [mca-position-tracker-toolkit](https://github.com/silv-mt-holdings/mca-position-tracker-toolkit)
**Input**: `List[ClassifiedTransaction]`
**Output**: `StackingAnalysis` (MCA positions, stacking risk)
**No database**

**Depends on**: transaction-classifier-toolkit

---

### 5. [mca-scoring-toolkit](https://github.com/silv-mt-holdings/mca-scoring-toolkit)
**Input**: `CashFlowSummary`, `StackingAnalysis`, FICO, industry
**Output**: `ScoringResult` (100-pt score, letter grade)
**No database**

**Depends on**: cashflow-analytics-toolkit, mca-position-tracker-toolkit

---

### 6. [mca-pricing-toolkit](https://github.com/silv-mt-holdings/mca-pricing-toolkit)
**Input**: `ScoringResult`, monthly revenue
**Output**: `PricingRecommendation` (factor rate, advance, terms)
**No database**

**Depends on**: mca-scoring-toolkit

---

## Imperative Shell: Risk-Model-01 (This Repo)

**Purpose**: Production MCA underwriting platform with state management

### What Lives Here

```
Risk-Model-01/
├── cli.py                    ← CLI interface, orchestration
├── orchestrator/
│   └── pipeline.py           ← Calls toolkits in sequence
├── integrations/
│   ├── mssql.py              ← MSSQL connection, CRUD operations
│   ├── google_places.py      ← Business verification API
│   └── scraping_toolkit.py   ← SOS, UCC, court records
├── mssql/
│   ├── schema.sql            ← Database schema (CREATE TABLE statements)
│   ├── migrations/           ← Schema migrations
│   └── queries/              ← SQL queries
├── reports/
│   └── pdf_generator.py      ← PDF report generation
├── config/
│   ├── settings.py           ← Environment variables, config
│   └── .env.example          ← Example configuration
├── tests/
│   └── test_integration.py   ← End-to-end tests with DB
└── requirements.txt          ← All toolkit dependencies + MSSQL driver
```

### Why Database Code Stays Here

**❌ DON'T create `underwriting-database-toolkit`**

| Problem | Why It's Bad |
|---------|--------------|
| **Schema changes = 3-step dance** | Update toolkit → Publish toolkit → Update Risk-Model-01 |
| **Tight coupling** | Database schema is specific to this app |
| **YAGNI violation** | No other apps need this exact schema |
| **Migration complexity** | Every schema change requires toolkit versioning |

**✅ DO keep database code in Risk-Model-01**

- Schema changes are local (edit `mssql/schema.sql`, done)
- Fast iteration (no publish/version steps)
- Clear ownership (database = part of the product)
- Easy migrations (Alembic, Flyway, or manual SQL scripts)

---

## Data Flow

```
1. PDF Input
   ↓
2. bankstatement-parser-toolkit
   → StatementResult
   ↓
3. transaction-classifier-toolkit
   → ClassifiedTransactions
   ↓
4a. cashflow-analytics-toolkit → CashFlowSummary
4b. mca-position-tracker-toolkit → StackingAnalysis
   ↓
5. mca-scoring-toolkit
   → ScoringResult
   ↓
6. mca-pricing-toolkit
   → PricingRecommendation
   ↓
7. Risk-Model-01 Orchestrator
   ↓
8. integrations/mssql.py
   → Save to database (applications, scores, pricing)
   ↓
9. reports/pdf_generator.py
   → Generate PDF report
```

## Example: CLI Orchestration

```python
# cli.py score command

from parser.statement_parser import BankStatementParser
from classifier.revenue_classifier import TransactionClassifier
from analytics.cashflow_analyzer import CashFlowAnalyzer
from tracker.position_analyzer import PositionTracker
from scoring.mca_scorecard import MCAScoringModel
from pricing.factor_calculator import PricingCalculator
from integrations.mssql import save_application, get_db_connection

# 1. Parse (Functional Core)
parser = BankStatementParser()
statement = parser.parse(pdf_bytes, filename)

# 2. Classify (Functional Core)
classifier = TransactionClassifier()
classified = classifier.classify_all(statement.transactions)

# 3. Analyze (Functional Core)
analytics = CashFlowAnalyzer()
cash_flow = analytics.analyze(classified)

tracker = PositionTracker()
positions = tracker.find_positions(classified)

# 4. Score (Functional Core)
scorer = MCAScoringModel()
score_result = scorer.score(
    cash_flow=cash_flow,
    positions=positions,
    fico=680,
    industry='restaurant'
)

# 5. Price (Functional Core)
pricer = PricingCalculator()
pricing = pricer.calculate(
    grade=score_result.letter_grade,
    monthly_revenue=cash_flow.monthly_true_revenue
)

# 6. Save (Imperative Shell - Risk-Model-01 only)
with get_db_connection() as conn:
    application_id = save_application(
        conn,
        business_name=business_name,
        statement_result=statement,
        score_result=score_result,
        pricing=pricing
    )

# 7. Generate Report (Imperative Shell)
report.generate_pdf(application_id, score_result, pricing)
```

---

## Installation & Setup

### 1. Install Toolkits

```bash
# Option A: Install from GitHub (production)
pip install git+https://github.com/silv-mt-holdings/bankstatement-parser-toolkit.git
pip install git+https://github.com/silv-mt-holdings/transaction-classifier-toolkit.git
pip install git+https://github.com/silv-mt-holdings/cashflow-analytics-toolkit.git
pip install git+https://github.com/silv-mt-holdings/mca-position-tracker-toolkit.git
pip install git+https://github.com/silv-mt-holdings/mca-scoring-toolkit.git
pip install git+https://github.com/silv-mt-holdings/mca-pricing-toolkit.git

# Option B: Clone for development
cd C:\Dev\Trusted
git clone https://github.com/silv-mt-holdings/bankstatement-parser-toolkit.git
cd bankstatement-parser-toolkit && pip install -e . && cd ..
# Repeat for other toolkits...
```

### 2. Setup Risk-Model-01

```bash
cd C:\Dev\Trusted\Risk-Model-01
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with MSSQL connection string, API keys, etc.

# Initialize database
python -m integrations.mssql --init-schema
```

### 3. Run CLI

```bash
python cli.py score statement.pdf --fico 680 --industry restaurant
```

---

## Testing Strategy

### Toolkit Tests (Unit Tests)
```bash
# Test individual toolkit (no database needed)
cd bankstatement-parser-toolkit
pytest tests/test_parser.py

# Fast, isolated, no mocks needed (pure functions)
```

### Risk-Model-01 Tests (Integration Tests)
```bash
# Test full pipeline with database
cd Risk-Model-01
pytest tests/test_integration.py

# Requires test database, environment variables
```

---

## Benefits of This Architecture

| Benefit | Description |
|---------|-------------|
| **Clear Boundaries** | Logic (toolkits) vs State (product) |
| **Easy Testing** | Pure functions = simple unit tests |
| **Reusability** | Toolkits can be used in other apps |
| **Fast Iteration** | Database changes don't require toolkit updates |
| **Flexible Deployment** | Deploy toolkits independently from product |
| **Team Collaboration** | Different teams can own toolkits vs product |

---

## Future Enhancements

### When to Extract Database Code

Create `underwriting-database-toolkit` **ONLY if**:

✅ You build a **second application** (e.g., web portal) that needs the **exact same schema**
✅ You have **shared database migrations** across multiple apps
✅ You need **database-level business logic** (stored procedures, triggers)

Until then: **YAGNI** (You Aren't Gonna Need It)

### When to Extract Other Concerns

- **`underwriting-reporting-toolkit`**: If multiple apps generate the same reports
- **`underwriting-integrations-toolkit`**: If Google Places logic is reused
- **`underwriting-api-toolkit`**: If you build both REST API and GraphQL API

---

## Related Documentation

- [README.md](./README.md) - Product overview and usage
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) - AI coding guidelines
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Original monolith implementation
- [mssql/schema.sql](./mssql/schema.sql) - Database schema

---

## Toolkit Repositories

- [bankstatement-parser-toolkit](https://github.com/silv-mt-holdings/bankstatement-parser-toolkit)
- [transaction-classifier-toolkit](https://github.com/silv-mt-holdings/transaction-classifier-toolkit)
- [cashflow-analytics-toolkit](https://github.com/silv-mt-holdings/cashflow-analytics-toolkit)
- [mca-position-tracker-toolkit](https://github.com/silv-mt-holdings/mca-position-tracker-toolkit)
- [mca-scoring-toolkit](https://github.com/silv-mt-holdings/mca-scoring-toolkit)
- [mca-pricing-toolkit](https://github.com/silv-mt-holdings/mca-pricing-toolkit)
