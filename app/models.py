import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(10))
    alcohol: Mapped[bool] = mapped_column(Boolean)
    smoker: Mapped[bool] = mapped_column(Boolean)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # queued | processing | completed | needs_doctor | failed
    status: Mapped[str] = mapped_column(String(20), default="queued")
    stage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    weeks: Mapped[int] = mapped_column(Integer, default=1)
    # Snapshot of the form at submission (age, diet, cuisine, allergies, ...).
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    body_composition: Mapped[dict] = mapped_column(JSON, default=dict)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    recommended_tests: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    targets: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    user: Mapped[User] = relationship(back_populates="assessments")
    reports: Mapped[list["Report"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    biomarkers: Mapped[list["Biomarker"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # blood | urine | inbody
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(50))
    storage_path: Mapped[str] = mapped_column(String(500))
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date
    patient_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    patient_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patient_sex: Mapped[str | None] = mapped_column(String(10), nullable=True)

    assessment: Mapped[Assessment] = relationship(back_populates="reports")


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    source: Mapped[str] = mapped_column(String(10))  # blood | urine | inbody
    # Canonical code, or None when the lab's test name is not in our catalogue.
    code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    label: Mapped[str] = mapped_column(String(120))
    raw_name: Mapped[str] = mapped_column(String(200))
    value_num: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    flag: Mapped[str | None] = mapped_column(String(10), nullable=True)  # low|high|normal|abnormal

    assessment: Mapped[Assessment] = relationship(back_populates="biomarkers")
