"""
LendEdge API Orchestrator (v2.0)
==================================
Connects React Frontend -> Parser Toolkit -> Scoring Toolkit
Handles Form Data inputs for TIB, Industry, and FICO.

Architecture: Imperative Shell
------------------------------
This API is the "Imperative Shell" that orchestrates all the Functional Core toolkits.
It handles I/O (file uploads, HTTP), database interactions, and coordinates the pure
functional logic from the 6 modular toolkits.

Author: IntensiveCapFi / Silv MT Holdings
Version: 2.0 - January 2026
"""
import uvicorn
import shutil
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- TOOLKIT IMPORTS (Functional Core) ---
from parsing.bank_statement_parser import BankStatementParser
from scoring.mca_scorecard import MCAScorecard as RBFScoringModel

app = FastAPI(
    title="LendEdge RBF Engine",
    description="Revenue-Based Financing Risk Assessment API",
    version="2.0"
)

# CORS Configuration - Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RESPONSE MODELS ---
class Violation(BaseModel):
    """Individual risk violation/check result"""
    id: int
    name: str
    limit: str
    actual: str
    status: str  # "PASS" | "FAIL"
    severity: str  # "good" | "warning" | "critical"


class DealResponse(BaseModel):
    """Complete deal analysis response for frontend"""
    name: str
    grade: str
    revenue: float
    adb: float
    violations: List[Violation]


# --- API ENDPOINTS ---
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0"}


@app.post("/analyze", response_model=DealResponse)
async def analyze_statement(
    file: UploadFile = File(...),
    # Application Context (Not extractable from bank statement)
    industry: str = Form("construction"),
    tib_months: int = Form(24),
    fico: int = Form(680)
):
    """
    Analyze a bank statement and score the deal.

    Parameters:
    -----------
    file : UploadFile
        Bank statement PDF file
    industry : str
        Business industry (e.g., "construction", "restaurant")
    tib_months : int
        Time in business (months)
    fico : int
        FICO credit score

    Returns:
    --------
    DealResponse
        Complete deal analysis with grade, metrics, and violations
    """
    temp_filename = f"temp_{file.filename}"

    try:
        # 1. SAVE FILE TEMPORARILY (I/O - Imperative Shell)
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. PARSE THE PDF (Functional Core - Parser Toolkit)
        parser = BankStatementParser()
        print(f"Parsing {file.filename}...")

        # NOTE: For demo/development without OCR setup, we simulate parser output
        # In production, replace this with: result = parser.parse_pdf(temp_filename)
        # The parser toolkit provides: parse(), parse_pdf(), detect_bank(), etc.

        # --- SIMULATING PARSER OUTPUT (Remove in production) ---
        class MockSummary:
            monthly_true_revenue = 58240.00
            average_daily_balance = 4200.00
            nsf_count = 9
            negative_days = 4
            deposit_variance = 0.15
            total_deposits = 65000.00
            total_withdrawals = 63750.00  # Net Cash Flow = +1250
            mca_positions = []

        summary = MockSummary()
        # -------------------------------------------------------

        # 3. SCORE THE DEAL (Functional Core - Scoring Toolkit)
        print("Calculating RBF Score...")
        scorer = RBFScoringModel()

        # Inject Application Data (The Missing Pieces from PDF)
        scorer.set_application(
            industry=industry,
            time_in_business_months=tib_months,
            fico_score=fico
        )

        # Inject Bank Analytics Data
        scorer.set_bank_analytics(
            monthly_true_revenue=summary.monthly_true_revenue,
            average_daily_balance=summary.average_daily_balance,
            nsf_count_90d=summary.nsf_count,
            negative_days_90d=summary.negative_days,
            deposit_variance=summary.deposit_variance,
            gross_deposits_monthly=summary.total_deposits
        )

        # Run Scoring Calculation
        score_result = scorer.calculate()

        # 4. CALCULATE VIOLATIONS FOR DASHBOARD (Business Logic - Imperative Shell)
        # These thresholds could be moved to data/violation_thresholds.json

        # Violation 1: NSF Tolerance
        nsf_violation = {
            "id": 1,
            "name": "NSF Tolerance",
            "limit": "< 5 Days",
            "actual": f"{summary.nsf_count} Days",
            "status": "FAIL" if summary.nsf_count >= 5 else "PASS",
            "severity": "critical" if summary.nsf_count > 8 else "warning"
        }

        # Violation 2: Time in Business (Uses Form Data)
        tib_violation = {
            "id": 2,
            "name": "Time in Business",
            "limit": "6+ Months",
            "actual": f"{tib_months} Months",
            "status": "FAIL" if tib_months < 6 else "PASS",
            "severity": "warning"
        }

        # Violation 3: Industry Risk (Uses Form Data + Scoring Result)
        tier = score_result.key_metrics.get('industry_tier', 2)
        ind_violation = {
            "id": 3,
            "name": "Industry Risk",
            "limit": "Tier 1-3",
            "actual": f"Tier {tier} ({industry.title()})",
            "status": "FAIL" if tier >= 4 else "PASS",
            "severity": "critical" if tier == 5 else "good"
        }

        # Violation 4: Avg Monthly Revenue
        rev_violation = {
            "id": 4,
            "name": "Avg. Monthly Rev",
            "limit": "$15k+",
            "actual": f"${summary.monthly_true_revenue/1000:.1f}k",
            "status": "PASS" if summary.monthly_true_revenue >= 15000 else "FAIL",
            "severity": "good"
        }

        # Violation 5: Net Cash Flow (Calculated from Analytics)
        net_cf = summary.total_deposits - summary.total_withdrawals
        cf_violation = {
            "id": 5,
            "name": "Net Cash Flow",
            "limit": "> $0",
            "actual": f"{'+' if net_cf >= 0 else '-'}${abs(net_cf):,.0f}",
            "status": "PASS" if net_cf > 0 else "FAIL",
            "severity": "warning"
        }

        # 5. RETURN RESPONSE (I/O - Imperative Shell)
        return {
            "name": "Titan Construction LLC",  # TODO: Extract from parser
            "grade": score_result.letter_grade,
            "revenue": summary.monthly_true_revenue,
            "adb": summary.average_daily_balance,
            "violations": [
                nsf_violation,
                tib_violation,
                ind_violation,
                rev_violation,
                cf_violation
            ]
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temporary file (I/O - Imperative Shell)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "api": "LendEdge RBF Engine",
        "version": "2.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
