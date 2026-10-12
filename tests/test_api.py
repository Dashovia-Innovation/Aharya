from pathlib import Path

from app.config import settings
from tests.conftest import BLOOD_ROWS, URINE_ROWS, make_pdf


def _submit(client, form, files, **overrides):
    return client.post("/v1/assessments", data=form | overrides, files=files)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "llm": "offline"}


def test_full_assessment(client, form, files):
    created = _submit(client, form, files, diet_type="jain", cuisine="west", weeks=2)
    assert created.status_code == 202
    assessment_id = created.json()["assessment_id"]

    status = client.get(f"/v1/assessments/{assessment_id}").json()
    assert status["status"] == "completed" and status["error"] is None
    assert status["warnings"] == []
    assert status["reports"][0]["lab_name"] == "Test Pathology"
    assert status["reports"][0]["report_date"] == "2026-10-01"
    codes = {finding["code"] for finding in status["findings"]}
    assert {"prediabetes", "dyslipidaemia", "obesity", "central_obesity", "alcohol"} <= codes
    assert status["targets"]["goal"] == "fat_loss"
    assert "kidney" not in {test["panel"] for test in status["recommended_tests"]}

    biomarkers = client.get(f"/v1/assessments/{assessment_id}/biomarkers").json()["biomarkers"]
    by_code = {b["code"]: b for b in biomarkers}
    assert by_code["ldl"]["flag"] == "high" and by_code["hdl"]["flag"] == "low"
    assert by_code["platelets"]["value"] == 240000
    assert by_code["urine_pus_cells"]["flag"] == "normal"
    assert len(by_code) == len(biomarkers)  # the smear note row is not read as a second WBC

    plan = client.get(f"/v1/assessments/{assessment_id}/plan").json()
    assert len(plan["weeks"]) == 2 and len(plan["weeks"][0]["days"]) == 7
    assert plan["weeks"][0]["grocery"] and plan["disclaimer"]
    assert "Cook every dish without onion, garlic or root vegetables" in plan["guidance"]


def test_blood_report_alone_is_enough(client, form, files):
    assessment_id = _submit(client, form, {"blood_report": files["blood_report"]}).json()["assessment_id"]
    status = client.get(f"/v1/assessments/{assessment_id}").json()
    assert status["status"] == "completed"
    assert [report["kind"] for report in status["reports"]] == ["blood"]
    biomarkers = client.get(f"/v1/assessments/{assessment_id}/biomarkers").json()["biomarkers"]
    assert {b["source"] for b in biomarkers} == {"blood"}


def test_urgent_value_blocks_the_plan(client, form, files):
    rows = BLOOD_ROWS + ["HbA1c                        11.4          %             4.0 - 5.6"]
    files["blood_report"] = ("blood.pdf", make_pdf(rows), "application/pdf")
    assessment_id = _submit(client, form, files).json()["assessment_id"]

    assert client.get(f"/v1/assessments/{assessment_id}").json()["status"] == "needs_doctor"
    plan = client.get(f"/v1/assessments/{assessment_id}/plan")
    assert plan.status_code == 409
    assert plan.json()["detail"]["findings"][0]["code"] == "urgent_hba1c"


def test_mismatched_and_old_report_warns(client, form, files):
    files["urine_report"] = ("urine.pdf", make_pdf(URINE_ROWS, date="01 Jan 2026"), "application/pdf")
    assessment_id = _submit(client, form, files, name="Suresh Mehta", age=30).json()["assessment_id"]
    warnings = client.get(f"/v1/assessments/{assessment_id}").json()["warnings"]
    assert sum("does not match" in w for w in warnings) == 4  # name and age on both reports
    assert sum("days old" in w for w in warnings) == 1


def test_unreadable_required_report_fails(client, form, files):
    files["blood_report"] = ("blood.pdf", make_pdf(["Nothing useful here"]), "application/pdf")
    assessment_id = _submit(client, form, files).json()["assessment_id"]
    status = client.get(f"/v1/assessments/{assessment_id}").json()
    assert status["status"] == "failed" and "blood report" in status["error"]
    assert client.get(f"/v1/assessments/{assessment_id}/plan").status_code == 409


def test_unreadable_inbody_is_skipped(client, form, files):
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    files["inbody_report"] = ("inbody.png", png, "image/png")
    assessment_id = _submit(client, form, files).json()["assessment_id"]
    status = client.get(f"/v1/assessments/{assessment_id}").json()
    assert status["status"] == "completed"
    assert any("inbody report" in w for w in status["warnings"])


def test_validation(client, form, files):
    assert _submit(client, form, files, consent="false").status_code == 422
    assert _submit(client, form, files, email="not-an-email").status_code == 422
    assert _submit(client, form, files, phone="12345").status_code == 422
    assert _submit(client, form, files, age=12).status_code == 422
    assert _submit(client, form, files, diet_type="keto").status_code == 422
    assert _submit(client, form, {"urine_report": files["urine_report"]}).status_code == 422
    files["urine_report"] = ("urine.pdf", b"this is not a pdf", "application/pdf")
    assert _submit(client, form, files).status_code == 422


def test_delete_removes_data_and_files(client, form, files):
    assessment_id = _submit(client, form, files).json()["assessment_id"]
    folder = Path(settings.upload_dir) / assessment_id
    assert folder.exists()
    assert client.delete(f"/v1/assessments/{assessment_id}").status_code == 204
    assert not folder.exists()
    assert client.get(f"/v1/assessments/{assessment_id}").status_code == 404
    assert client.get("/v1/assessments/unknown").status_code == 404
