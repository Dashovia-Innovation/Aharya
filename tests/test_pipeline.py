from datetime import date

import pytest

from app.pipeline import rules
from app.pipeline.catalogue import DIET_KINDS, MEALS
from app.pipeline.extract import ExtractedReport, parse_report_text
from app.pipeline.normalise import normalise, parse_number, parse_range
from app.pipeline.planner import generate_plan
from app.pipeline.targets import compute_targets

PROFILE = {
    "name": "Ravi Shah", "age": 42, "gender": "male", "alcohol": False, "smoker": False,
    "diet_type": "veg", "cuisine": "north", "activity_level": "sedentary",
    "allergies": [], "conditions": [], "medications": [],
}


def test_parse_number_and_range():
    assert parse_number("1,69,000") == 169000
    assert parse_number("< 5") == 5
    assert parse_number("10-15/HPF") is None
    assert parse_range("12.0 - 18.0") == (12.0, 18.0)
    assert parse_range("0 TO 450") == (0, 450)
    assert parse_range("38.8~47.4") == (38.8, 47.4)
    assert parse_range("< 100") == (None, 100)
    assert parse_range("> 40") == (40, None)
    assert parse_range(None) == (None, None)


def test_normalise_uses_lab_range_then_fallback():
    row = normalise("blood", "HAEMOGLOBIN", "11.0", "g/dL", "12.0 - 18.0", "male")
    assert (row["code"], row["flag"]) == ("hb", "low")
    # No printed range: the sex-specific default applies.
    assert normalise("blood", "Hb", "12.5", "g/dL", None, "male")["flag"] == "low"
    assert normalise("blood", "Hb", "12.5", "g/dL", None, "female")["flag"] == "normal"


def test_normalise_scales_counts_printed_in_lakhs():
    row = normalise("blood", "Platelet Count", "2.4", "lakhs/cumm", "1.5 - 4.5", "male")
    assert (row["value_num"], row["ref_low"], row["flag"]) == (240000, 150000, "normal")


def test_same_name_maps_by_report_kind():
    assert normalise("blood", "Glucose Fasting", "90", None, None, "male")["code"] == "fbs"
    assert normalise("urine", "Glucose", "Absent", None, None, "male")["code"] == "urine_glucose"
    assert normalise("inbody", "Protein", "12.1", "kg", "10.4~12.6", "male")["code"] == "body_protein_kg"
    assert normalise("blood", "Some New Test", "5", None, None, "male")["code"] is None


def test_urine_qualitative_values():
    assert normalise("urine", "Protiens", "PRESENT+", None, None, "male")["flag"] == "abnormal"
    assert normalise("urine", "Glucose", "Absent", None, None, "male")["flag"] == "normal"
    pus = normalise("urine", "Pus Cells", "10-15/HPF", None, None, "male")
    assert (pus["value_num"], pus["flag"]) == (15, "abnormal")
    assert normalise("urine", "Pus Cells", "1-2/HPF", None, None, "male")["flag"] == "normal"


def test_text_parser_reads_lab_layout():
    text = """
      Name : MR. RAVI SHAH                     Collected On : 25 Sep 2026 02:53 PM
      Lab No : 1        Age : 42   Sex: MALE   Reported On : 25 Sep 2026
      Ref By : Dr. X                           Sample Collected At: (Om Pathology)
    HAEMOGLOBIN                 16.6          g/dL          12.0 - 18.0
    Absolute Neutrophils Count  3640          -
    W.B.C Morphology            Normal
    Platelet Count              169000        /cumm         150000-450000
    MANOJ PANDEY (M.Sc.)                      Dr. S.N. Tripathi (MD(Path))
    """
    report = parse_report_text("blood", text)
    assert report.patient_name == "MR. RAVI SHAH"
    assert (report.patient_age, report.patient_sex, report.lab_name) == (42, "MALE", "Om Pathology")
    assert rules.parse_date(report.report_date) == date(2026, 9, 25)
    assert [(r.name, r.value, r.unit, r.reference_range) for r in report.results] == [
        ("HAEMOGLOBIN", "16.6", "g/dL", "12.0 - 18.0"),
        ("Platelet Count", "169000", "/cumm", "150000-450000"),
    ]


def test_verify_report_flags_mismatch_and_stale_date():
    report = ExtractedReport(
        patient_name="MR. AMIT PATEL", patient_age=50, patient_sex="FEMALE",
        report_date="15.06.2026", results=[],
    )
    warnings = rules.verify_report("blood", PROFILE, report, today=date(2026, 10, 12))
    assert len(warnings) == 4
    matching = ExtractedReport(patient_name="Mr. Ravi K Shah", patient_age=41, patient_sex="M",
                               report_date="2026-10-01", results=[])
    assert rules.verify_report("blood", PROFILE, matching, today=date(2026, 10, 12)) == []


def _codes(findings):
    return {f["code"] for f in findings}


def test_rules_metabolic_profile():
    values = {"hb": 14, "fbs": 112, "ldl": 148, "hdl": 38, "tg": 210, "creatinine": 0.9}
    body = {"bmi": 28.4, "waist_cm": 98}
    findings = rules.evaluate(PROFILE | {"alcohol": True}, values, {}, body)
    assert _codes(findings) == {"prediabetes", "dyslipidaemia", "obesity", "central_obesity", "alcohol"}
    assert not any(f["severity"] == "urgent" for f in findings)
    assert {p["panel"] for p in rules.missing_panels(values)} == {"liver", "thyroid", "vitamin_d", "vitamin_b12"}


def test_rules_urine_findings_need_a_doctor():
    findings = rules.evaluate(PROFILE, {}, {"urine_protein": "abnormal", "urine_pus_cells": "abnormal"}, {})
    assert {f["code"]: f["severity"] for f in findings} == {
        "urine_protein": "see_doctor", "urine_pus_cells": "see_doctor",
    }


@pytest.mark.parametrize("values", [{"hba1c": 11.2}, {"hb": 6.1}, {"creatinine": 2.4}, {"potassium": 6.3}])
def test_rules_urgent_values(values):
    assert any(f["severity"] == "urgent" for f in rules.evaluate(PROFILE, values, {}, {}))


def test_indian_bmi_cutoffs():
    assert "overweight" in _codes(rules.evaluate(PROFILE, {}, {}, {"bmi": 23.5}))
    assert "obesity" in _codes(rules.evaluate(PROFILE, {}, {}, {"bmi": 25.0}))
    assert not _codes(rules.evaluate(PROFILE, {}, {}, {"bmi": 22.9}))


def test_targets_prefer_measured_bmr_and_target_weight():
    body = {"weight_kg": 81.8, "height_cm": 177, "bmr_kcal": 1684, "target_weight_kg": 71.6, "bmi": 26.1}
    targets = compute_targets(PROFILE, body, [{"code": "obesity"}])
    assert targets["bmr_source"] == "body-composition report"
    assert targets["goal"] == "fat_loss"
    assert targets["calories_kcal"] == 1500  # 1684 x 1.2 - 500, rounded to 50
    assert targets["protein_g"] == 86  # 1.2 g per kg of target weight


def test_targets_floor_protein_limit_and_fallback():
    small = {"weight_kg": 45, "height_cm": 150}
    targets = compute_targets(PROFILE | {"gender": "female"}, small, [{"code": "overweight"}])
    assert targets["calories_kcal"] == 1200
    limited = compute_targets(PROFILE, {"weight_kg": 70, "height_cm": 175}, [{"code": "urine_protein"}])
    assert limited["protein_g"] == 56 and limited["notes"]
    unknown = compute_targets(PROFILE, {}, [])
    assert unknown["bmr_source"] == "population average" and unknown["notes"]


@pytest.mark.parametrize("diet_type", list(DIET_KINDS))
def test_catalogue_plan_respects_diet_and_calories(diet_type):
    profile = PROFILE | {"diet_type": diet_type, "allergies": ["peanut"]}
    findings = [{"code": "prediabetes", "title": "", "message": "", "diet_actions": ["Cut sugar"]}]
    targets = compute_targets(profile, {"weight_kg": 84, "height_cm": 172}, [{"code": "obesity"}])
    plan = generate_plan(profile, findings, targets, weeks=2)

    by_name = {meal.name: meal for meal in MEALS}
    assert plan["generator"] == "catalogue" and len(plan["weeks"]) == 2
    for week in plan["weeks"]:
        assert len(week["days"]) == 7 and week["grocery"]
        for day in week["days"]:
            assert len(day["meals"]) == 5
            assert abs(day["total_kcal"] - targets["calories_kcal"]) <= 0.15 * targets["calories_kcal"]
            for planned in day["meals"]:
                meal = by_name[planned["name"]]
                assert meal.kind in DIET_KINDS[diet_type]
                assert diet_type != "jain" or meal.jain
                assert "high_gi" not in meal.tags
                assert "peanut" not in meal.name.lower()
                assert not any("peanut" in item[0] for item in meal.ingredients)
    assert "Cut sugar" in plan["guidance"]
    assert not [w for w in plan["warnings"] if "kcal" in w]
