"""Turn an uploaded report (PDF or photo) into structured results.

Claude reads the document directly when an API key is configured. Without one,
a layout-based text parser handles digitally generated PDFs only; scanned
reports and photos need the Claude path.
"""

import base64
import io
import re

import anthropic
from pydantic import BaseModel
from pypdf import PdfReader

from app.config import settings
from app.pipeline import normalise


class ExtractionError(Exception):
    pass


class ExtractedResult(BaseModel):
    name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None


class ExtractedReport(BaseModel):
    patient_name: str | None = None
    patient_age: int | None = None
    patient_sex: str | None = None
    lab_name: str | None = None
    report_date: str | None = None
    results: list[ExtractedResult]


_SYSTEM = """You transcribe Indian medical reports into structured data.

Copy every test result exactly as printed: the test name, the value, the unit and the
reference range. Do not interpret, correct, convert units or decide whether a value is
normal. Keep qualitative values verbatim (for example "PRESENT+", "Absent", "10-15/HPF").
If a field is not printed, leave it null. Never invent a value.

For body-composition printouts (InBody and similar), treat each measured quantity as a
result: Height, Weight, Total Body Water, Protein, Mineral, Body Fat Mass, SMM, BMI, PBF,
Waist-Hip Ratio, Visceral Fat Level, Basal Metabolic Rate, Fat Free Mass, Target Weight,
Weight Control, Fat Control, Muscle Control and InBody Score. Use the latest measurement,
ignore history charts, exercise tables and impedance values, and put the printed normal
range in reference_range.

report_date is the sample collection or test date in YYYY-MM-DD. patient_sex is "male" or
"female"."""

_KIND_HINT = {
    "blood": "This is a blood test report.",
    "urine": "This is a urine examination report.",
    "inbody": "This is a body-composition (InBody) report.",
}


def _extract_with_claude(kind: str, data: bytes, media_type: str) -> ExtractedReport:
    encoded = base64.standard_b64encode(data).decode("ascii")
    block_type = "document" if media_type == "application/pdf" else "image"
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.parse(
            model=settings.extraction_model,
            max_tokens=16000,
            system=_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": block_type,
                            "source": {"type": "base64", "media_type": media_type, "data": encoded},
                        },
                        {"type": "text", "text": f"{_KIND_HINT[kind]} Extract every result."},
                    ],
                }
            ],
            output_format=ExtractedReport,
        )
    except anthropic.APIError as exc:
        raise ExtractionError(f"Could not read the {kind} report: {exc}") from exc
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise ExtractionError(
            f"Could not read the {kind} report (stop_reason={response.stop_reason})."
        )
    return response.parsed_output


_HEADER = {
    "patient_name": re.compile(r"Name\s*:\s*(.+?)(?:\s{2,}|$)", re.I),
    "patient_age": re.compile(r"Age\s*:\s*(\d{1,3})", re.I),
    "patient_sex": re.compile(r"Sex\s*:\s*(male|female|m|f)\b", re.I),
    "report_date": re.compile(r"Collected On\s*:\s*(\d{1,2}[ /.-]\w{2,9}[ /.-]\d{4})", re.I),
    "lab_name": re.compile(r"Collected At\s*:\s*\(?([^)\n]+?)\)?\s*$", re.I),
}
_RANGE_LIKE = re.compile(r"\d\s*(?:-|–|~|to)\s*\d|^[<>]", re.I)


def _pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text(extraction_mode="layout") or "" for page in reader.pages)
    except Exception as exc:
        raise ExtractionError(f"Unreadable PDF: {exc}") from exc


def parse_report_text(kind: str, text: str) -> ExtractedReport:
    """Parse the column layout most Indian lab software prints: name, value, unit, range."""
    header: dict = {}
    results: list[ExtractedResult] = []
    for line in text.splitlines():
        for field, pattern in _HEADER.items():
            if field not in header and (match := pattern.search(line)):
                header[field] = match.group(1).strip()
        parts = re.split(r"\s{2,}", line.strip())
        # Only keep rows whose name is a test we know, which drops headers and signatures.
        if len(parts) < 2 or not normalise.lookup(kind, parts[0]):
            continue
        # Blood values are always numeric; this skips smear notes and chart labels.
        if kind != "urine" and normalise.parse_number(parts[1]) is None:
            continue
        rest = [part for part in parts[2:] if part != "-"]
        reference = next((part for part in rest if _RANGE_LIKE.search(part)), None)
        unit = next((part for part in rest if part != reference), None)
        results.append(
            ExtractedResult(name=parts[0], value=parts[1], unit=unit, reference_range=reference)
        )
    if "patient_age" in header:
        header["patient_age"] = int(header["patient_age"])
    return ExtractedReport(**header, results=results)


def _extract_offline(kind: str, data: bytes, media_type: str) -> ExtractedReport:
    needs_llm = "Set ANTHROPIC_API_KEY so the report can be read by Claude."
    if media_type != "application/pdf":
        raise ExtractionError(f"The {kind} report is an image. {needs_llm}")
    report = parse_report_text(kind, _pdf_text(data))
    if not report.results:
        raise ExtractionError(
            f"No results could be read from the {kind} report (scanned or unfamiliar layout). {needs_llm}"
        )
    return report


def extract_report(kind: str, data: bytes, media_type: str) -> ExtractedReport:
    if settings.use_llm:
        return _extract_with_claude(kind, data, media_type)
    return _extract_offline(kind, data, media_type)
