import os
import tempfile

# Point the app at a throwaway database and upload folder before it is imported.
_TMP = tempfile.mkdtemp(prefix="aharya-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["UPLOAD_DIR"] = f"{_TMP}/uploads"
os.environ["LLM_MODE"] = "offline"

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

from app.main import app

HEADER = [
    "Name : MR. RAVI SHAH                    Collected On : {date}",
    "Lab No : 000001      Age : 42   Sex: MALE     Reported On : {date}",
    "Ref By : Dr. TEST                       Sample Collected At: (Test Pathology)",
    "",
]
BLOOD_ROWS = [
    "HAEMOGLOBIN                  14.2          g/dL          13.0 - 17.0",
    "W.B.C Count                  7200          /cumm         4000 - 11000",
    "Platelet Count               2.4           lakhs/cumm    1.5 - 4.5",
    "W.B.C Morphology             Normal",
    "Fasting Blood Sugar          112           mg/dL         70 - 100",
    "LDL Cholesterol              148           mg/dL         < 100",
    "HDL Cholesterol              38            mg/dL         > 40",
    "Triglycerides                210           mg/dL         < 150",
    "Serum Creatinine             0.9           mg/dL         0.7 - 1.3",
]
URINE_ROWS = [
    "Protiens                     Absent",
    "Glucose                      Absent",
    "Pus Cells                    1-2/HPF",
    "Red Blood Cells              Absent",
]


def make_pdf(rows: list[str], date: str = "01 Oct 2026") -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9)
    for line in [h.format(date=date) for h in HEADER] + rows:
        pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def form():
    return {
        "name": "Ravi Shah",
        "age": 42,
        "gender": "male",
        "alcohol": "true",
        "smoker": "false",
        "email": "ravi@example.com",
        "phone": "+91 98765 43210",
        "consent": "true",
        "height_cm": 172,
        "weight_kg": 84,
        "waist_cm": 98,
    }


@pytest.fixture
def files():
    return {
        "blood_report": ("blood.pdf", make_pdf(BLOOD_ROWS), "application/pdf"),
        "urine_report": ("urine.pdf", make_pdf(URINE_ROWS), "application/pdf"),
    }
