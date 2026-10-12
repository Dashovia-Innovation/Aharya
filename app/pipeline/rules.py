"""Deterministic interpretation of biomarkers.

Every threshold lives here, in code, so it can be reviewed by a clinician. The
LLM never decides whether a value is abnormal. Severities:
  info        worth knowing, no action
  attention   addressed through diet
  see_doctor  needs a clinician, a plan is still produced
  urgent      no plan is produced; the user is told to see a doctor first
"""

from datetime import date, datetime

from app.config import settings

PANELS = {
    "cbc": ("hb",),
    "lipid": ("tc", "ldl", "hdl", "tg"),
    "glucose": ("fbs", "hba1c"),
    "liver": ("alt", "ast"),
    "kidney": ("creatinine",),
    "thyroid": ("tsh",),
    "vitamin_d": ("vit_d",),
    "vitamin_b12": ("vit_b12",),
}
PANEL_ADVICE = {
    "cbc": ("Complete blood count", "screens for anaemia"),
    "lipid": ("Lipid profile", "decides how much and which fats the plan allows"),
    "glucose": ("Fasting sugar and HbA1c", "decides the carbohydrate load of the plan"),
    "liver": ("Liver function test (SGPT/SGOT)", "screens for fatty liver"),
    "kidney": ("Kidney function test (creatinine)", "confirms a higher-protein plan is safe"),
    "thyroid": ("TSH", "thyroid problems change weight and energy needs"),
    "vitamin_d": ("Vitamin D", "deficiency is very common in India"),
    "vitamin_b12": ("Vitamin B12", "deficiency is common, especially in vegetarians"),
}

_TITLES = {"mr", "mrs", "ms", "miss", "dr", "shri", "smt", "master", "kumari"}
_DATE_FORMATS = ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y")


def parse_date(text: str | None) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime((text or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def _name_tokens(name: str) -> set[str]:
    return {t for t in name.lower().replace(".", " ").split() if t not in _TITLES}


def verify_report(kind: str, profile: dict, report, today: date | None = None) -> list[str]:
    """Warn when a report does not look like it belongs to this user, or is old."""
    warnings = []
    if report.patient_name and not _name_tokens(report.patient_name) & _name_tokens(profile["name"]):
        warnings.append(
            f"The name on the {kind} report ({report.patient_name}) does not match {profile['name']}."
        )
    if report.patient_age is not None and abs(report.patient_age - profile["age"]) > 1:
        warnings.append(
            f"The age on the {kind} report ({report.patient_age}) does not match the age given ({profile['age']})."
        )
    sex = (report.patient_sex or "").lower()[:1]
    if sex in ("m", "f") and profile["gender"] in ("male", "female") and sex != profile["gender"][0]:
        warnings.append(f"The sex on the {kind} report does not match the gender given.")
    taken = parse_date(report.report_date)
    if taken and ((today or date.today()) - taken).days > settings.stale_report_days:
        warnings.append(
            f"The {kind} report is dated {taken.isoformat()}, more than "
            f"{settings.stale_report_days} days old. A recent report gives a better plan."
        )
    return warnings


def missing_panels(values: dict) -> list[dict]:
    return [
        {"panel": panel, "test": PANEL_ADVICE[panel][0], "why": PANEL_ADVICE[panel][1]}
        for panel, codes in PANELS.items()
        if not any(code in values for code in codes)
    ]


def evaluate(profile: dict, values: dict, flags: dict, body: dict) -> list[dict]:
    """values: code -> number, flags: code -> flag, body: body-composition numbers."""
    male = profile["gender"] == "male"
    findings: list[dict] = []

    def add(code, severity, title, message, *diet_actions):
        findings.append(
            {
                "code": code,
                "severity": severity,
                "title": title,
                "message": message,
                "diet_actions": list(diet_actions),
            }
        )

    def v(code):
        return values.get(code)

    # --- Urgent values: stop and send the user to a doctor ---------------------
    urgent = [
        ("hb", lambda x: x < 7, "Haemoglobin is very low"),
        ("platelets", lambda x: x < 50000, "Platelet count is very low"),
        ("wbc", lambda x: x > 30000 or x < 2000, "White cell count is far outside the normal range"),
        ("fbs", lambda x: x >= 300, "Fasting blood sugar is very high"),
        ("hba1c", lambda x: x >= 10, "HbA1c is very high"),
        ("tg", lambda x: x >= 500, "Triglycerides are very high (pancreatitis risk)"),
        ("potassium", lambda x: x >= 6 or x < 3, "Potassium is at a dangerous level"),
        ("sodium", lambda x: x < 125 or x > 155, "Sodium is at a dangerous level"),
        ("creatinine", lambda x: x >= 2, "Creatinine is high (kidney function)"),
        ("egfr", lambda x: x < 30, "Kidney filtration (eGFR) is very low"),
        ("alt", lambda x: x >= 200, "Liver enzyme SGPT is very high"),
        ("ast", lambda x: x >= 200, "Liver enzyme SGOT is very high"),
    ]
    for code, is_urgent, title in urgent:
        if v(code) is not None and is_urgent(v(code)):
            add(f"urgent_{code}", "urgent", title, f"{title}. Please see a doctor before changing your diet.")

    # --- Blood ------------------------------------------------------------------
    hb_floor = 13 if male else 12
    if v("hb") is not None and 7 <= v("hb") < hb_floor:
        add("anaemia", "attention", "Low haemoglobin",
            f"Haemoglobin is {v('hb')} g/dL, below {hb_floor}.",
            "Include iron-rich foods daily: leafy greens, rajma, chana, jaggery, dates",
            "Pair iron-rich meals with vitamin C (lemon, amla, guava)",
            "Avoid tea and coffee within an hour of meals")

    fbs, a1c = v("fbs"), v("hba1c")
    if (fbs is not None and 126 <= fbs < 300) or (a1c is not None and 6.5 <= a1c < 10):
        add("diabetes_range", "see_doctor", "Blood sugar in the diabetic range",
            "Fasting sugar or HbA1c is in the diabetic range. Confirm with a doctor.",
            "No sugar, sweets, fruit juices or sweetened drinks",
            "Choose low-GI grains: millets, brown rice, whole wheat",
            "Start lunch and dinner with salad, then protein, then grains")
    elif (fbs is not None and 100 <= fbs < 126) or (a1c is not None and 5.7 <= a1c < 6.5):
        add("prediabetes", "attention", "Blood sugar in the pre-diabetic range",
            "Fasting sugar or HbA1c is above normal but below the diabetic range.",
            "Cut sugar, sweets and sweetened drinks",
            "Replace white rice and maida with millets and whole grains",
            "Add protein and fibre to every meal")

    lipid_issues = []
    if v("ldl") is not None and v("ldl") >= 130:
        lipid_issues.append(f"LDL {v('ldl')}")
    if v("tc") is not None and v("tc") >= 200:
        lipid_issues.append(f"total cholesterol {v('tc')}")
    if v("tg") is not None and 150 <= v("tg") < 500:
        lipid_issues.append(f"triglycerides {v('tg')}")
    if v("hdl") is not None and v("hdl") < (40 if male else 50):
        lipid_issues.append(f"low HDL {v('hdl')}")
    if lipid_issues:
        severity = "see_doctor" if (v("ldl") or 0) >= 190 else "attention"
        add("dyslipidaemia", severity, "Cholesterol needs attention",
            "Lipid profile shows " + ", ".join(lipid_issues) + ".",
            "Limit fried food, ghee, butter, cream, bakery items and red meat",
            "Use mustard, groundnut or rice bran oil, at most 3 teaspoons a day",
            "Add soluble fibre daily: oats, isabgol, methi seeds, beans",
            "Add a small handful of nuts or flaxseed daily")

    if (v("alt") is not None and 45 < v("alt") < 200) or (v("ast") is not None and 40 < v("ast") < 200):
        add("liver_enzymes", "see_doctor", "Raised liver enzymes",
            "SGPT or SGOT is above normal, which is often fatty liver. Confirm with a doctor.",
            "Stop alcohol completely",
            "Avoid sugar, fried food and refined flour",
            "Aim for gradual weight loss")

    if v("uric_acid") is not None and v("uric_acid") > (7.2 if male else 6.0):
        add("high_uric_acid", "attention", "High uric acid",
            f"Uric acid is {v('uric_acid')} mg/dL.",
            "Limit organ meat, red meat, shellfish and beer",
            "Drink at least 3 litres of water a day",
            "Avoid sweetened drinks and fruit juices")

    creatinine_high = v("creatinine") is not None and (1.3 if male else 1.1) < v("creatinine") < 2
    egfr_low = v("egfr") is not None and 30 <= v("egfr") < 60
    if creatinine_high or egfr_low:
        add("kidney_function", "see_doctor", "Kidney function needs a check",
            "Creatinine is raised or eGFR is reduced. See a doctor before raising protein intake.",
            "Keep protein moderate until a doctor clears a higher intake",
            "Limit salt, pickles, papad and packaged food")

    if v("tsh") is not None and not 0.4 <= v("tsh") <= 4.5:
        add("thyroid", "see_doctor", "TSH outside the normal range",
            f"TSH is {v('tsh')}. Thyroid problems need medical treatment, not only diet.")

    if v("vit_d") is not None and v("vit_d") < 20:
        add("vitamin_d_low", "see_doctor", "Vitamin D deficiency",
            f"Vitamin D is {v('vit_d')} ng/mL. Food alone rarely corrects this; ask a doctor about supplements.",
            "Get 15-20 minutes of midday sun on arms and legs",
            "Include eggs, fortified milk and mushrooms where the diet allows")

    if v("vit_b12") is not None and v("vit_b12") < 200:
        add("vitamin_b12_low", "see_doctor", "Vitamin B12 deficiency",
            f"Vitamin B12 is {v('vit_b12')} pg/mL. Ask a doctor about supplements.",
            "Include curd, milk, paneer, eggs or fish where the diet allows")

    # --- Urine ------------------------------------------------------------------
    if flags.get("urine_protein") == "abnormal":
        add("urine_protein", "see_doctor", "Protein in urine",
            "Protein was found in the urine. This needs a doctor's review and a repeat test.",
            "Keep protein moderate until a doctor reviews this",
            "Limit salt")
    if flags.get("urine_pus_cells") == "abnormal":
        add("urine_pus_cells", "see_doctor", "Pus cells in urine",
            "Pus cells are raised, which can mean a urinary infection. See a doctor.",
            "Drink 3 litres of water a day")
    if flags.get("urine_glucose") == "abnormal":
        add("urine_glucose", "see_doctor", "Sugar in urine",
            "Glucose was found in the urine. Get a fasting sugar and HbA1c test.",
            "Cut sugar, sweets and sweetened drinks")
    if flags.get("urine_ketone") == "abnormal":
        add("urine_ketone", "see_doctor", "Ketones in urine",
            "Ketones were found in the urine. See a doctor, especially if you are diabetic.")
    if flags.get("urine_blood") == "abnormal" or flags.get("urine_rbc") == "abnormal":
        add("urine_blood", "see_doctor", "Blood in urine",
            "Blood or red cells were found in the urine. See a doctor.")

    # --- Body composition (Asian Indian cut-offs) --------------------------------
    bmi = body.get("bmi")
    if bmi is not None and bmi >= 25:
        add("obesity", "attention", "BMI in the obese range for Indians",
            f"BMI is {bmi:.1f}. For Indians, 25 and above is classed as obese.",
            "Calorie deficit of about 500 kcal a day",
            "Fill half the plate with vegetables")
    elif bmi is not None and bmi >= 23:
        add("overweight", "attention", "BMI in the overweight range for Indians",
            f"BMI is {bmi:.1f}. For Indians, 23 and above is classed as overweight.",
            "Calorie deficit of about 500 kcal a day")

    central = []
    if body.get("whr") is not None and body["whr"] > (0.90 if male else 0.85):
        central.append(f"waist-hip ratio {body['whr']}")
    if body.get("waist_cm") is not None and body["waist_cm"] >= (90 if male else 80):
        central.append(f"waist {body['waist_cm']} cm")
    if body.get("visceral_fat") is not None and body["visceral_fat"] >= 10:
        central.append(f"visceral fat level {body['visceral_fat']:.0f}")
    if central:
        add("central_obesity", "attention", "Fat around the belly",
            "Belly fat is high (" + ", ".join(central) + "), which raises diabetes and heart risk.",
            "Cut sugar, refined flour, fried snacks and alcohol",
            "Have an early, light dinner",
            "Walk 10 minutes after each main meal")
    if body.get("pbf") is not None and body["pbf"] > (25 if male else 32):
        add("high_body_fat", "attention", "High body fat percentage",
            f"Body fat is {body['pbf']}%.",
            "Keep protein high to protect muscle while losing fat",
            "Add strength training 3 times a week")

    # --- Lifestyle ---------------------------------------------------------------
    if profile.get("alcohol"):
        add("alcohol", "info", "Alcohol",
            "Alcohol adds calories that go straight to the belly and strains the liver.",
            "Limit alcohol; avoid beer and sugary mixers")
    if profile.get("smoker"):
        add("smoking", "info", "Smoking",
            "Smoking raises heart risk and lowers vitamin C levels.",
            "Include a vitamin C source daily: amla, guava, lemon, orange")

    return findings
