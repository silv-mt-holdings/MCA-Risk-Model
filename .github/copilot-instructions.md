# Risk-Model-01 AI Coding Guidelines

## Project Overview

**Risk-Model-01** is the Imperative Shell and orchestration layer for the RBF (Revenue-Based Financing) risk assessment system.

**Core Purpose**: Orchestrate 6 functional core toolkits, handle I/O (API, database, files), and coordinate the end-to-end underwriting workflow.

**Architecture Pattern**: **Imperative Shell** (I/O + Orchestration)

---

## Architecture: Functional Core + Imperative Shell

This project implements the **Functional Core / Imperative Shell** pattern:

### Functional Core (6 Toolkits - External)
Pure functional libraries with NO I/O:
1. **bankstatement-parser-toolkit** - Extract data from PDFs
2. **transaction-classifier-toolkit** - Classify transaction types
3. **cashflow-analytics-toolkit** - Calculate financial metrics
4. **rbf-position-tracker-toolkit** - Detect RBF positions
5. **rbf-scoring-toolkit** - Calculate risk scores
6. **rbf-pricing-toolkit** - Determine pricing

### Imperative Shell (Risk-Model-01 - This Repo)
Handles I/O and orchestration:
- **api.py** - FastAPI endpoints (file upload, HTTP responses)
- **cli.py** - Command-line interface
- **integrations/** - MSSQL database, Google Places API
- **Orchestration** - Coordinates toolkit workflow

---

## File Structure

```
Risk-Model-01/
├── api.py                      # FastAPI orchestration (NEW)
├── cli.py                      # CLI interface
├── requirements.txt            # All 6 toolkits + FastAPI + MSSQL
├── .env.example                # Environment variables
├── integrations/
│   ├── mssql.py                # Database I/O
│   └── google_places.py        # External API calls
├── examples/
│   ├── complete_scoring.py     # End-to-end example
│   └── quick_start.py          # Quick demo
├── data/                       # Configuration (JSON)
│   ├── scoring_weights.json
│   ├── letter_grade_thresholds.json
│   └── industry_risk_db.json
└── tests/
    └── test_integration.py     # Integration tests
```

---

## Core Workflow: API Orchestration

The `api.py` file is the **bridge** between the React frontend and Python backend:

```python
@app.post("/analyze", response_model=DealResponse)
async def analyze_statement(
    file: UploadFile = File(...),
    industry: str = Form("construction"),
    tib_months: int = Form(24),
    fico: int = Form(680)
):
    # 1. I/O: Save uploaded file temporarily
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. FUNCTIONAL CORE: Parse PDF (Pure function)
    parser = BankStatementParser()
    result = parser.parse(pdf_bytes)

    # 3. FUNCTIONAL CORE: Classify transactions (Pure function)
    classifier = RevenueClassifier()
    classified = classifier.classify_all(result.transactions)

    # 4. FUNCTIONAL CORE: Analyze cash flow (Pure function)
    analyzer = CashFlowAnalyzer()
    cash_flow = analyzer.analyze(classified)

    # 5. FUNCTIONAL CORE: Score deal (Pure function)
    scorer = RBFScoringModel()
    scorer.set_application(industry=industry, tib_months=tib_months, fico=fico)
    scorer.set_bank_analytics(monthly_true_revenue=cash_flow.monthly_revenue, ...)
    score_result = scorer.calculate()

    # 6. FUNCTIONAL CORE: Calculate pricing (Pure function)
    pricer = PricingCalculator()
    pricing = pricer.calculate(grade=score_result.letter_grade, monthly_revenue=cash_flow.monthly_revenue)

    # 7. I/O: Return HTTP response
    return DealResponse(...)
```

**Key Pattern**: I/O happens in the Imperative Shell; pure logic happens in toolkits.

---

## Responsibilities

### What Risk-Model-01 SHOULD Do (Imperative Shell)
- File I/O (read/write files)
- HTTP requests/responses (FastAPI)
- Database operations (MSSQL)
- External API calls (Google Places)
- Orchestrate toolkit workflow
- Handle errors and exceptions
- Logging and monitoring

### What Risk-Model-01 SHOULD NOT Do
- Implement parsing logic (use parser toolkit)
- Implement scoring logic (use scoring toolkit)
- Duplicate functional code (DRY - use toolkits)

---

## Key Development Workflows

### Running the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python api.py

# Server runs at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Running the CLI

```bash
# Score a deal
python cli.py score --fico 680 --industry restaurant --amount 50000

# Analyze statement
python cli.py analyze statement.pdf

# Show config
python cli.py config --show
```

### Testing Integration

```bash
# Run all tests
pytest

# Run integration tests
pytest tests/test_integration.py -v

# With coverage
pytest --cov=. --cov-report=html
```

---

## Integration with Frontend (lendedge-portal)

The React frontend communicates with the API:

```typescript
// Frontend: lendedge-portal/app/page.tsx
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('industry', 'construction');
formData.append('tib_months', '24');
formData.append('fico', '680');

const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
});

const data = await response.json();
// data.grade, data.revenue, data.adb, data.violations
```

---

## Database Integration (MSSQL)

```python
# integrations/mssql.py
from pymssql import connect

def save_application(conn, business_name, score_result, pricing):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (business_name, letter_grade, total_score, max_advance)
        VALUES (%s, %s, %s, %s)
    """, (business_name, score_result.letter_grade, score_result.total_score, pricing.max_advance))
    conn.commit()
    return cursor.lastrowid
```

**Pattern**: Database I/O stays in the Imperative Shell; toolkits never touch the database.

---

## Configuration Data

All configuration files are JSON (no hardcoded thresholds):

```
data/
├── scoring_weights.json         # Component weights (must sum to 100)
├── letter_grade_thresholds.json # Grade definitions
├── industry_risk_db.json        # 60+ industries, 5 tiers
├── mca_lender_list.json         # Known RBF/MCA lenders
├── revenue_patterns.json        # Transaction classification patterns
└── deal_tier_thresholds.json   # Deal sizing rules
```

**Important**: Configuration is loaded at module init, not on every request.

---

## Error Handling

```python
@app.post("/analyze")
async def analyze_statement(...):
    try:
        # Orchestration logic
        ...
    except ParsingError as e:
        raise HTTPException(status_code=400, detail=f"PDF parsing failed: {str(e)}")
    except ScoringError as e:
        raise HTTPException(status_code=422, detail=f"Scoring failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
```

**Pattern**: Handle errors gracefully; always cleanup resources.

---

## Environment Variables

```bash
# .env
MSSQL_CONNECTION_STRING=Server=localhost;Database=lending;User=sa;Password=***
GOOGLE_PLACES_API_KEY=AIza***
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Usage**:
```python
from dotenv import load_dotenv
import os

load_dotenv()
db_connection = os.getenv('MSSQL_CONNECTION_STRING')
```

---

## Coding Conventions

### Style & Structure
- **Type Hints**: Required for API endpoints and public functions
- **Docstrings**: Triple-quoted for all API endpoints
- **Error Handling**: Always use try/except with cleanup in finally
- **Logging**: Use Python logging module (not print statements)

### API Endpoint Pattern

```python
@app.post("/endpoint", response_model=ResponseModel)
async def endpoint_name(
    file: UploadFile = File(...),
    param: str = Form(...)
) -> ResponseModel:
    """
    Endpoint description.

    Args:
        file: Description
        param: Description

    Returns:
        ResponseModel with ...

    Raises:
        HTTPException: 400 if ...
        HTTPException: 500 if ...
    """
    try:
        # 1. I/O operations
        # 2. Functional Core calls
        # 3. I/O response
        return ResponseModel(...)
    except SpecificError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Cleanup
        pass
```

---

## Testing Strategy

### Unit Tests (Toolkits)
Pure function tests in each toolkit (no mocking needed).

### Integration Tests (Risk-Model-01)
Test the orchestration layer:

```python
def test_full_workflow():
    # Mock file upload
    with open('fixtures/sample_statement.pdf', 'rb') as f:
        pdf_bytes = f.read()

    # Call API endpoint
    response = client.post(
        "/analyze",
        files={"file": ("statement.pdf", pdf_bytes, "application/pdf")},
        data={"industry": "construction", "tib_months": 24, "fico": 680}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['grade'] in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']
    assert data['revenue'] > 0
    assert len(data['violations']) == 5
```

---

## Common Patterns & Idioms

### Pattern 1: Toolkit Orchestration

```python
# Step 1: Parse (Functional Core)
parser = BankStatementParser()
statement = parser.parse(pdf_bytes)

# Step 2: Classify (Functional Core)
classifier = RevenueClassifier()
classified = classifier.classify_all(statement.transactions)

# Step 3: Analyze (Functional Core)
analyzer = CashFlowAnalyzer()
cash_flow = analyzer.analyze(classified)

# Step 4: Score (Functional Core)
scorer = RBFScoringModel()
scorer.set_application(industry=industry, tib_months=tib_months, fico=fico)
scorer.set_bank_analytics(**cash_flow.to_dict())
result = scorer.calculate()
```

**Key**: Each toolkit provides a focused API; the shell orchestrates them.

### Pattern 2: Temporary File Handling

```python
temp_filename = f"temp_{uuid.uuid4()}_{file.filename}"
try:
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process file
    result = process_file(temp_filename)
    return result
finally:
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
```

### Pattern 3: Database Transactions

```python
conn = get_db_connection()
try:
    cursor = conn.cursor()
    # Multiple inserts
    cursor.execute("INSERT INTO applications ...")
    cursor.execute("INSERT INTO violations ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

---

## Deployment

### Local Development
```bash
# Terminal 1: Start API
cd Risk-Model-01
python api.py

# Terminal 2: Start Frontend
cd lendedge-portal
npm run dev
```

### Production
- **API**: Deploy FastAPI with Uvicorn/Gunicorn
- **Database**: MSSQL Server (Azure SQL, AWS RDS, or on-prem)
- **Frontend**: Deploy Next.js to Vercel or Netlify

---

## Security & Best Practices

### Sensitive Data Handling
- PDFs processed in-memory; deleted after processing
- Database credentials in environment variables (never committed)
- API keys in `.env` (never committed)
- Input validation on all form data

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting (Production)
```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.client.host)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_statement(...):
    ...
```

---

## Debugging & Troubleshooting

### Common Issues

**Toolkit import errors?**
- Ensure all 6 toolkits are installed: `pip install -r requirements.txt`
- Check that toolkits are pushed to GitHub

**API not responding?**
- Check if port 8000 is available: `lsof -i :8000`
- Verify CORS origins match frontend URL

**Database connection failed?**
- Verify `.env` file exists with correct connection string
- Test connection: `python -c "import pymssql; pymssql.connect(...)"`

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@app.post("/analyze")
async def analyze_statement(...):
    logger.info(f"Analyzing statement: {file.filename}")
    # ...
    logger.debug(f"Score result: {score_result.total_score}")
```

---

## Quick Reference

### API Endpoints
- `GET /health` - Health check
- `POST /analyze` - Analyze bank statement (main endpoint)
- `GET /` - API info

### Running Commands
```bash
python api.py                   # Start FastAPI server
python cli.py score --help      # CLI help
pytest                          # Run tests
pytest --cov=.                  # With coverage
```

### Dependencies
```bash
pip install -r requirements.txt  # Install all toolkits + FastAPI + DB drivers
```

---

## Version

**v2.0** - Imperative Shell with FastAPI (January 2026)

**Author**: IntensiveCapFi / Silv MT Holdings

**Architecture**: Functional Core (6 toolkits) + Imperative Shell (This repo)
