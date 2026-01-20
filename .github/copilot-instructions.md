# MCA-Risk-Model AI Coding Guidelines

## Project Overview

**MCA-Risk-Model** is a production-ready Python library for Merchant Cash Advance (MCA) underwriting. It performs bank statement parsing, cash flow analysis, and comprehensive risk scoring using a **layered three-tier architecture**.

**Core Purpose**: Score MCA deals with 100-point composite scores, assign letter grades (A+ to F), and provide risk tiers with underwriting recommendations.

---

## Architecture: Three-Tier Separation of Concerns

### Layer 1: **Parsing** (`parsing/`)
- **Responsibility**: Extract raw financial data from bank statement PDFs
- **Key Files**: `bank_statement_parser.py` (main), `bank_templates.py` (bank-specific patterns)
- **Deliverable**: `ParsingResult` with transactions, balances, and metadata
- **Key Pattern**: Template-based bank detection; each bank has regex patterns for transactions and balances
- **When to Update**: New bank support, transaction classification rules, or balance extraction logic
- **Common Pitfall**: Regex patterns must be tested against real bank statement text. If a bank memo pattern doesn't match, add to `revenue_patterns.json`, not inline to parser.

### Layer 2: **Analytics** (`analytics/`)
- **Responsibility**: Calculate financial metrics from parsed transactions
- **Key File**: `cashflow_analyzer.py`
- **Inputs**: Transaction lists from Parser
- **Deliverable**: `CashFlowSummary` with trailing averages (3/6/12-month), trends, NSF counts, ADB
- **Key Pattern**: Self-contained metric calculators; no side effects
- **When to Update**: New financial metrics, volatility formulas, or classification rules
- **Important**: All metrics must be based on 90-day or specified windows. Never mix timeframes (e.g., don't average 90-day revenue with 180-day NSF).

### Layer 3: **Scoring** (`scoring/`)
- **Responsibility**: Produce risk scores, letter grades, and deal recommendations
- **Key Files**: `mca_scorecard.py` (main engine), `letter_grader.py`, `industry_scorer.py`
- **Inputs**: Application data + Analytics results
- **Deliverable**: `ScoringResult` with 100-point score, letter grade, recommended factor, max advance
- **Key Pattern**: Weighted component scoring; weights loaded from `data/scoring_weights.json`
- **When to Update**: Score weights, new scoring components, or tier classifications
- **Critical Pre-Check**: Scoring validates minimum thresholds (FICO, business age, revenue) before component scoring. See `_pre_check()` logic.

---

## Data Models: The Common Language

All layers communicate through shared models in `models/`:
- **`ApplicationData`**: Merchant info (name, industry, FICO, TIB)
- **`BankAnalytics`**: Calculated metrics (revenue, ADB, NSF, variance)
- **`ScoringResult`**: Final output (score, grade, factor, max_advance)
- **`Transaction`**: Individual transaction with type, amount, flags
- **`CashFlowSummary`**: Analytics summary (30/90/180-day averages, trends)

**Important**: Update models in `models/` before adding fields to any layer. All new data flows through these types.

---

## Working with Configuration Files

### Structure: `data/` Directory
All configuration files are JSON and loaded at module initialization (not runtime):

```
data/
  scoring_weights.json       # 11-component weights (100 total points)
  revenue_patterns.json      # Regex patterns for transaction classification
  mca_lender_list.json       # 50+ MCA lender names with aliases
  letter_grade_thresholds.json  # Score ranges for A+ through F grades
  industry_risk_db.json      # Industry codes mapped to 5-tier risk levels
  deal_tier_thresholds.json  # Deal sizing rules (document requirements)
```

### Key Workflows
**Adding a new MCA lender?** → Edit `mca_lender_list.json` under `"lenders"` section. Add company name as key, list of aliases as value. No code change needed.

**Adjusting scoring weights?** → Edit `data/scoring_weights.json`. Weights must sum to 100 points. Test impact with `examples/complete_scoring.py` before committing.

**Adding transaction classification rule?** → Edit `revenue_patterns.json`. Add pattern to `true_revenue_patterns` or `non_true_revenue_patterns` array. Use `test_real_pdf.py` with real PDFs to validate.

---

## Key Development Workflows

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_integration.py -v

# Filter by name
pytest -k "test_zelle" -v
```

### Manual Testing
```bash
# Quick smoke test (see README.md for full example)
python examples/quick_start.py

# Complete scoring workflow
python examples/complete_scoring.py

# Test specific parser feature
python -c "from parsing.bank_statement_parser import BankStatementParser; ..."
```

### Adding Bank Support
1. Add template to `bank_templates.py` with bank name, detection patterns, and regex
2. Update `BANK_TEMPLATES` dict
3. Add test PDF to `data/` with name matching bank
4. Run `test_real_pdf.py` to validate

### Updating Scoring Weights
1. Edit `data/scoring_weights.json` (points per component)
2. Run `examples/complete_scoring.py` to verify impact
3. Update test expectations in `tests/test_integration.py`

---

## Coding Conventions

### Style & Structure
- **Indentation**: 4 spaces (Python standard)
- **Imports**: Group by standard library, third-party (pandas, numpy), local
- **Type Hints**: Use `from typing import Dict, List, Optional` for function signatures
- **Docstrings**: Triple-quoted for modules/classes; include Author and Version in parsing/scoring modules

### Naming & Patterns
- **Classes**: PascalCase (`BankStatementParser`, `MCAScoringModel`)
- **Functions**: snake_case (`calculate_trailing_average`, `extract_balance_info`)
- **Constants**: UPPER_SNAKE_CASE (`SCORING_WEIGHTS`, `MIN_ADB`)
- **Data Fields**: Reflect financial domain (`monthly_true_revenue`, `nsf_count_90d`, not `rev` or `nsf_cnt`)

### Composability Over Inlining
- **Parser layer**: Separate methods for `_extract_transactions()`, `_extract_balance_info()`, `_extract_mca_positions()`
- **Analytics**: Reuse existing calculators; add new methods rather than duplicating logic
- **Scoring**: Use component scorers (`_score_revenue()`, `_score_adb()`) instead of monolithic logic

---

## Critical Integration Points

### Parser → Analytics Flow
- Parser outputs `ParsingResult.transactions` list + `CashFlowSummary` stub
- Analytics uses `CashFlowAnalyzer` to enrich `CashFlowSummary` with metrics
- **Bridge**: `_generate_summary()` in parser populates initial summary; analyzer refines it

### Analytics → Scoring Flow
- Scorecard reads `BankAnalytics` (calculated metrics) + `ApplicationData` (application info)
- Both must be set before calling `score()`
- **Bridge**: Method chaining pattern (`.set_bank_analytics().score()`)

### Transaction Classification
- Parser classifies each transaction as `TRUE_REVENUE`, `TRANSFER`, `LOAN`, `P2P`, `MCA_PAYMENT`, etc.
- Analytics uses classifications to filter revenue, identify Zelle transfers, flag NSF
- Scoring consumes aggregated metrics (doesn't re-classify)

---

## Common Patterns & Idioms

### Method Chaining (Fluent API)
```python
result = (MCAScoringModel()
    .set_application(...)
    .set_bank_analytics(...)
    .score(requested_amount=50000))
```
Pattern: All setters return `self` for chaining.

### Template-Based Flexibility
Parser uses bank templates for extensibility:
- **Detection**: Regex finds bank name in statement
- **Parsing**: Bank-specific patterns extract transactions
- **Fallback**: Generic template handles unknown banks

### Weighted Component Scoring
Scorecard loads weights from JSON, applies per-component scorers:
```python
SCORING_WEIGHTS = {
    'revenue_stability': 15,
    'cash_flow_depth': 12,
    'adb_strength': 10,
    # ... 8 more components totaling 100
}
```

### Flag-Based Metadata
Transactions carry flags for downstream handling:
```python
# In parser
transaction.flags = ['P2P_REVIEW_REQUIRED']  # Added to all P2P

# In analytics/scoring
if 'P2P_REVIEW_REQUIRED' in transaction.flags:
    manual_review_required = True
```

---

## Edge Cases & Advanced Patterns

### Multi-Bank Scenarios
- Parser auto-detects bank from statement text using `detect_bank()` → checks `bank_templates.py` patterns
- If bank not recognized, falls back to `GENERIC` template with flexible regex
- **Best practice**: Test new banks with `test_bank_detection.py` and `test_real_pdf.py`

### Revenue Classification Complexity
Three classification layers (order matters):
1. **MCA Payment check** → Transaction classified as `MCA_PAYMENT` (not revenue)
2. **P2P detection** → Zelle/Venmo marked `TRUE_REVENUE` + flagged `P2P_REVIEW_REQUIRED`
3. **Pattern matching** → Use `true_revenue_patterns` and `non_true_revenue_patterns` from JSON

**Gotcha**: A transaction can be `TRUE_REVENUE` AND flagged. Flags don't change classification, they add metadata.

### Scoring Pre-Checks Before Scoring
Before any component scoring happens, `MCAScoringModel` runs `_pre_check()`:
- FICO score < 500? → Blocker
- Time in business < 3 months? → Blocker
- Monthly true revenue < $10k? → Blocker
- NSF count > 10 in 90 days? → Blocker

**Result**: If blockers exist, `ScoringResult.pre_check.passed = False` and no components are scored. Use `result.pre_check.blockers` list for underwriter feedback.

### Handling Missing Analytics Data
When setting `bank_analytics`:
- All fields optional (default to 0)
- Scoring adapts: 0 ADB → component receives 0 points (not penalty)
- **Recommendation**: Always populate at minimum: `monthly_true_revenue`, `average_daily_balance`, `nsf_count_90d`, `negative_days_90d`, `deposit_variance`

---

## Security & Configuration

### No Hard-Coded Paths
- Bank detection: Parses statement text, not file paths
- Scoring: All data passed via method parameters, not files
- **Exception**: `data/scoring_weights.json` is shipped with library; immutable configuration

### Sensitive Data Handling
- PDFs processed in-memory; no temp files cached
- Transactions sanitized before logging (omit amounts, merchant names in debug output)
- **Test Data**: Use anonymized `example-fw9.pdf` for smoke tests; keep real client PDFs outside repo

---

## When to Refactor vs. Extend

### Extend (Add New Component)
- New scoring metric → Add to `scoring/` with weighted component method
- New bank → Add template to `bank_templates.py`
- New analytics calculation → Add method to `CashFlowAnalyzer`

### Refactor (Improve Existing)
- Parser line count >500 lines → Split `bank_statement_parser.py` into modules (e.g., `transaction_extractor.py`)
- Scoring weights frequently changing → Move to external config file with reload support
- Duplicate metric logic in analytics → Extract to shared utility

### When in Doubt
- Check if change affects the **contract** between layers (model fields)
- If contract changes, update `models/` **first**
- Run `pytest` to catch breaks in integration tests

---

## Debugging & Troubleshooting

### Common Issues & Solutions
**Parser not detecting bank?** → Check `bank_templates.py` for detection patterns. Use `detect_bank(text)` in REPL to debug.

**Transactions not classified?** → Verify `revenue_patterns.json` contains the memo text. Add new patterns to `true_revenue_patterns` or `non_true_revenue_patterns`.

**Scoring result doesn't match expected?** → Check `scoring_weights.json` for weight values. Each component weight affects proportionally. Use `result.component_scores` dict to debug individual pieces.

**P2P transactions missing flags?** → Ensure `bank_templates.py` includes Zelle/Venmo patterns. Check transaction memo against `zelle_venmo_patterns` in JSON.

### Testing Specific Features
```bash
# Test parser with real PDF
python test_real_pdf.py

# Test Zelle detection
pytest -k "test_zelle" -v

# Test balance extraction
python test_balance_extraction.py

# Test bank detection
python test_bank_detection.py
```

---

## Immediate Productivity Checklist

**First task in this codebase?**
1. Run `pytest` to verify environment
2. Read `README.md` Quick Start section (method chaining example)
3. Review `models/scoring.py` to understand `ScoringResult` fields
4. Run `examples/complete_scoring.py` to see full workflow
5. Check `IMPLEMENTATION_SUMMARY.md` for latest enhancements (P2P flagging, balance extraction, multi-bank support)

**Modifying an existing component?**
1. Identify which layer: Parsing / Analytics / Scoring
2. Check affected models in `models/`
3. Review existing tests in `tests/`
4. Add tests **before** implementation
5. Run full test suite to catch integration breaks

---

## Environment Setup (Windows)

```bash
# 1. Navigate to project
cd C:\Dev\Trusted\MCA-Risk-Model

# 2. Create and activate venv (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify setup
pytest --co -q  # Show test collection without running
```

