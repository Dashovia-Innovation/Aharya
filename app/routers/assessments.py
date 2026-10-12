import re
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.config import settings
from app.db import get_db
from app.models import Assessment, Report, User
from app.pipeline.runner import run_assessment

router = APIRouter(prefix="/v1/assessments", tags=["assessments"])

Gender = Literal["male", "female", "other"]
DietType = Literal["veg", "eggetarian", "non_veg", "jain", "vegan"]
Cuisine = Literal["north", "south", "west", "east"]
Activity = Literal["sedentary", "light", "moderate", "active"]

_EMAIL = TypeAdapter(EmailStr)
_PHONE = re.compile(r"^(?:\+?91)?[6-9]\d{9}$")


class AssessmentCreated(BaseModel):
    assessment_id: str
    status: str


def _unprocessable(field: str, message: str) -> HTTPException:
    return HTTPException(422, detail=[{"loc": ["body", field], "msg": message}])


def _split(text: str) -> list[str]:
    return [item.strip().lower() for item in text.split(",") if item.strip()]


async def _read_report(field: str, upload: UploadFile) -> tuple[str, bytes]:
    limit = settings.max_upload_mb * 1024 * 1024
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"{field} is larger than {settings.max_upload_mb} MB.")
    media_type = storage.sniff_media_type(data)
    if media_type is None:
        raise _unprocessable(field, "Upload a PDF, JPEG or PNG file.")
    return media_type, data


def _get(db: Session, assessment_id: str) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found.")
    return assessment


@router.post("", status_code=202, response_model=AssessmentCreated)
async def create_assessment(
    background: BackgroundTasks,
    name: Annotated[str, Form(min_length=2, max_length=200)],
    age: Annotated[int, Form(ge=18, le=80)],
    gender: Annotated[Gender, Form()],
    alcohol: Annotated[bool, Form()],
    smoker: Annotated[bool, Form()],
    email: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    consent: Annotated[bool, Form(description="User agrees to their health reports being processed.")],
    blood_report: Annotated[UploadFile, File()],
    urine_report: Annotated[UploadFile, File()],
    inbody_report: Annotated[UploadFile | None, File()] = None,
    diet_type: Annotated[DietType, Form()] = "veg",
    cuisine: Annotated[Cuisine, Form()] = "north",
    activity_level: Annotated[Activity, Form()] = "sedentary",
    allergies: Annotated[str, Form(description="Comma-separated, e.g. peanuts, milk")] = "",
    conditions: Annotated[str, Form(description="Comma-separated known medical conditions")] = "",
    medications: Annotated[str, Form(description="Comma-separated current medications")] = "",
    height_cm: Annotated[float | None, Form(ge=120, le=220)] = None,
    weight_kg: Annotated[float | None, Form(ge=30, le=250)] = None,
    waist_cm: Annotated[float | None, Form(ge=40, le=200)] = None,
    weeks: Annotated[int, Form(ge=1, le=4)] = 1,
    db: Session = Depends(get_db),
):
    if not consent:
        raise _unprocessable("consent", "Consent is required to process health reports.")
    try:
        email = _EMAIL.validate_python(email.strip().lower())
    except ValidationError:
        raise _unprocessable("email", "Enter a valid email address.") from None
    phone = re.sub(r"[\s-]", "", phone)
    if not _PHONE.match(phone):
        raise _unprocessable("phone", "Enter a valid 10-digit Indian mobile number.")

    uploads = [("blood", "blood_report", blood_report), ("urine", "urine_report", urine_report)]
    if inbody_report is not None:
        uploads.append(("inbody", "inbody_report", inbody_report))
    files = [(kind, upload.filename or kind, *await _read_report(field, upload)) for kind, field, upload in uploads]

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.add(user)
    user.name, user.phone, user.age, user.gender = name.strip(), phone, age, gender
    user.alcohol, user.smoker = alcohol, smoker

    assessment = Assessment(
        user=user,
        weeks=weeks,
        profile={
            "name": name.strip(),
            "age": age,
            "gender": gender,
            "alcohol": alcohol,
            "smoker": smoker,
            "diet_type": diet_type,
            "cuisine": cuisine,
            "activity_level": activity_level,
            "allergies": _split(allergies),
            "conditions": _split(conditions),
            "medications": _split(medications),
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "waist_cm": waist_cm,
        },
    )
    db.add(assessment)
    db.flush()
    for kind, filename, media_type, data in files:
        path = storage.save(assessment.id, kind, media_type, data)
        db.add(Report(assessment_id=assessment.id, kind=kind, filename=filename, media_type=media_type, storage_path=path))
    db.commit()

    background.add_task(run_assessment, assessment.id)
    return AssessmentCreated(assessment_id=assessment.id, status=assessment.status)


@router.get("/{assessment_id}")
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = _get(db, assessment_id)
    return {
        "assessment_id": assessment.id,
        "status": assessment.status,
        "stage": assessment.stage,
        "error": assessment.error,
        "warnings": assessment.warnings,
        "findings": assessment.findings,
        "recommended_tests": assessment.recommended_tests,
        "body_composition": assessment.body_composition,
        "targets": assessment.targets,
        "reports": [
            {
                "kind": report.kind,
                "filename": report.filename,
                "lab_name": report.lab_name,
                "report_date": report.report_date,
            }
            for report in assessment.reports
        ],
        "created_at": assessment.created_at,
    }


@router.get("/{assessment_id}/biomarkers")
def get_biomarkers(assessment_id: str, db: Session = Depends(get_db)):
    assessment = _get(db, assessment_id)
    return {
        "assessment_id": assessment.id,
        "status": assessment.status,
        "biomarkers": [
            {
                "source": b.source,
                "code": b.code,
                "name": b.label,
                "value": b.value_num if b.value_num is not None else b.value_text,
                "value_text": b.value_text,
                "unit": b.unit,
                "ref_low": b.ref_low,
                "ref_high": b.ref_high,
                "flag": b.flag,
            }
            for b in assessment.biomarkers
        ],
    }


@router.get("/{assessment_id}/plan")
def get_plan(assessment_id: str, db: Session = Depends(get_db)):
    assessment = _get(db, assessment_id)
    if assessment.status == "needs_doctor":
        urgent = [f for f in assessment.findings if f["severity"] == "urgent"]
        raise HTTPException(409, detail={"message": "See a doctor before starting a diet plan.", "findings": urgent})
    if assessment.status == "failed":
        raise HTTPException(409, detail={"message": assessment.error})
    if assessment.status != "completed":
        raise HTTPException(409, detail={"message": f"The plan is not ready yet (status: {assessment.status})."})
    return {"assessment_id": assessment.id, "targets": assessment.targets, **assessment.plan}


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: str, db: Session = Depends(get_db)):
    assessment = _get(db, assessment_id)
    db.delete(assessment)
    db.commit()
    storage.delete_assessment(assessment_id)
