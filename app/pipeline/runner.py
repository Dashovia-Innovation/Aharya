"""Runs one assessment end to end: extract, normalise, verify, flag, target, plan."""

import logging

from sqlalchemy.orm import Session

from app import storage
from app.db import SessionLocal
from app.models import Assessment, Biomarker
from app.pipeline import rules
from app.pipeline.extract import ExtractionError, extract_report
from app.pipeline.normalise import INBODY, normalise
from app.pipeline.planner import PlanError, generate_plan
from app.pipeline.targets import compute_targets

logger = logging.getLogger(__name__)

_BODY_CODES = {marker.code for marker in INBODY}
_KIND_ORDER = {"blood": 0, "urine": 1, "inbody": 2}


def _set_stage(db: Session, assessment: Assessment, stage: str) -> None:
    assessment.stage = stage
    db.commit()


def _run(db: Session, assessment: Assessment) -> None:
    profile = assessment.profile
    assessment.status = "processing"
    _set_stage(db, assessment, "extracting")

    warnings: list[str] = []
    values: dict[str, float] = {}
    flags: dict[str, str] = {}
    for report in sorted(assessment.reports, key=lambda r: _KIND_ORDER[r.kind]):
        try:
            extracted = extract_report(report.kind, storage.read(report.storage_path), report.media_type)
        except ExtractionError as exc:
            if report.kind != "inbody":
                raise
            # The body-composition report is optional, so carry on without it.
            warnings.append(f"{exc} The plan was built without it.")
            continue
        taken = rules.parse_date(extracted.report_date)
        report.lab_name = extracted.lab_name
        report.report_date = taken.isoformat() if taken else None
        report.patient_name = extracted.patient_name
        report.patient_age = extracted.patient_age
        report.patient_sex = extracted.patient_sex
        warnings += rules.verify_report(report.kind, profile, extracted)
        for result in extracted.results:
            row = normalise(
                report.kind, result.name, result.value, result.unit, result.reference_range, profile["gender"]
            )
            db.add(Biomarker(assessment_id=assessment.id, **row))
            code = row["code"]
            if code and code not in flags and code not in values:
                if row["value_num"] is not None:
                    values[code] = row["value_num"]
                if row["flag"]:
                    flags[code] = row["flag"]

    _set_stage(db, assessment, "analysing")
    # Measured body composition wins over what the user typed into the form.
    body = {key: profile[key] for key in ("height_cm", "weight_kg", "waist_cm") if profile.get(key)}
    body.update({code: values[code] for code in _BODY_CODES if code in values})
    if "bmi" not in body and body.get("height_cm") and body.get("weight_kg"):
        body["bmi"] = round(body["weight_kg"] / (body["height_cm"] / 100) ** 2, 1)

    findings = rules.evaluate(profile, values, flags, body)
    assessment.body_composition = body
    assessment.findings = findings
    assessment.recommended_tests = rules.missing_panels(values)
    assessment.warnings = warnings

    if any(finding["severity"] == "urgent" for finding in findings):
        assessment.status = "needs_doctor"
        _set_stage(db, assessment, "done")
        return

    _set_stage(db, assessment, "planning")
    targets = compute_targets(profile, body, findings)
    assessment.targets = targets
    assessment.plan = generate_plan(profile, findings, targets, assessment.weeks)
    assessment.status = "completed"
    _set_stage(db, assessment, "done")


def run_assessment(assessment_id: str) -> None:
    with SessionLocal() as db:
        assessment = db.get(Assessment, assessment_id)
        if assessment is None:
            return
        try:
            _run(db, assessment)
        except (ExtractionError, PlanError) as exc:
            db.rollback()
            assessment.status, assessment.error = "failed", str(exc)
            db.commit()
        except Exception:
            logger.exception("Assessment %s failed", assessment_id)
            db.rollback()
            assessment.status, assessment.error = "failed", "Unexpected error while processing the reports."
            db.commit()
