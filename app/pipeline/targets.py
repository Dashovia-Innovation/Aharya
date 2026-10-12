"""Daily calorie and nutrient targets, computed in code rather than by the LLM."""

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
KCAL_FLOOR = {"male": 1500, "female": 1200, "other": 1350}
FALLBACK_BMR = {"male": 1650, "female": 1350, "other": 1500}
FALLBACK_WEIGHT = {"male": 70, "female": 58, "other": 64}
_SEX_TERM = {"male": 5, "female": -161, "other": -78}

_WEIGHT_LOSS = {"overweight", "obesity", "central_obesity", "high_body_fat"}
_PROTEIN_LIMITED = {"kidney_function", "urine_protein"}
_HIGH_FIBRE = {"dyslipidaemia", "prediabetes", "diabetes_range"}


def compute_targets(profile: dict, body: dict, findings: list[dict]) -> dict:
    gender = profile["gender"]
    codes = {finding["code"] for finding in findings}
    weight, height = body.get("weight_kg"), body.get("height_cm")
    notes = []

    if body.get("bmr_kcal"):
        bmr, bmr_source = body["bmr_kcal"], "body-composition report"
    elif weight and height:
        bmr = 10 * weight + 6.25 * height - 5 * profile["age"] + _SEX_TERM[gender]
        bmr_source = "Mifflin-St Jeor equation"
    else:
        bmr, bmr_source = FALLBACK_BMR[gender], "population average"
        notes.append(
            "Height and weight were not provided, so calories are based on an average adult. "
            "Add them or upload a body-composition report for an accurate target."
        )

    tdee = bmr * ACTIVITY[profile["activity_level"]]
    lose_weight = bool(codes & _WEIGHT_LOSS)
    kcal = max(tdee - 500 if lose_weight else tdee, KCAL_FLOOR[gender])
    kcal = int(round(kcal / 50) * 50)

    # Protein is set against a healthy reference weight, not the current one.
    if body.get("target_weight_kg"):
        reference_weight = body["target_weight_kg"]
    elif height and weight and weight / (height / 100) ** 2 >= 23:
        reference_weight = 23 * (height / 100) ** 2
    else:
        reference_weight = weight or FALLBACK_WEIGHT[gender]
    protein_per_kg = 0.8 if codes & _PROTEIN_LIMITED else 1.2
    if protein_per_kg == 0.8:
        notes.append("Protein is kept moderate until a doctor reviews the kidney or urine finding.")
    protein = int(round(reference_weight * protein_per_kg))

    fat = int(round(kcal * 0.27 / 9))
    carbs = int(round((kcal - protein * 4 - fat * 9) / 4))

    return {
        "goal": "fat_loss" if lose_weight else "maintenance",
        "bmr_kcal": int(round(bmr)),
        "bmr_source": bmr_source,
        "tdee_kcal": int(round(tdee)),
        "calories_kcal": kcal,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fibre_g": 35 if codes & _HIGH_FIBRE else 30,
        "sodium_mg_max": 2000,
        "water_l": 3.0,
        "notes": notes,
    }
