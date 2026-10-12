"""Weekly meal plan and grocery list.

Claude writes the plan when an API key is configured; otherwise a rule-based
planner picks from the built-in catalogue. Either way the totals are recomputed
and checked here against the targets.
"""

import json
import math
from typing import Literal

import anthropic
from pydantic import BaseModel

from app.config import settings
from app.pipeline.catalogue import DIET_KINDS, MEALS, SLOTS, Meal

DISCLAIMER = (
    "Aharya gives general nutrition guidance based on your reports. It is not a medical "
    "diagnosis or treatment. Speak to a doctor before changing your diet if you have a "
    "medical condition or take medication."
)
KCAL_TOLERANCE = 0.15

# Finding code -> meal tags to leave out of the plan.
_AVOID_TAGS = {
    "prediabetes": {"high_gi"},
    "diabetes_range": {"high_gi"},
    "urine_glucose": {"high_gi"},
    "dyslipidaemia": {"high_sat_fat"},
    "liver_enzymes": {"high_sat_fat"},
    "high_uric_acid": {"high_purine"},
}


class PlanError(Exception):
    pass


class PlannedMeal(BaseModel):
    slot: Literal["breakfast", "mid_morning", "lunch", "evening_snack", "dinner"]
    name: str
    portion: str
    kcal: int
    protein_g: int


class PlannedDay(BaseModel):
    day: int
    meals: list[PlannedMeal]


class GroceryItem(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str


class PlannedWeek(BaseModel):
    days: list[PlannedDay]
    grocery: list[GroceryItem]


def _guidance(profile: dict, findings: list[dict], targets: dict) -> list[str]:
    lines = []
    for finding in findings:
        for action in finding["diet_actions"]:
            if action not in lines:
                lines.append(action)
    if not any("litres of water" in line for line in lines):
        lines.append(f"Drink about {targets['water_l']:g} litres of water a day")
    lines.append("Use at most 3 teaspoons of oil and 1 teaspoon of salt a day in total")
    if profile["diet_type"] == "jain":
        lines.append("Cook every dish without onion, garlic or root vegetables")
    return lines


def _finish(generator: str, weeks: list[dict], profile: dict, findings: list[dict], targets: dict) -> dict:
    """Recompute totals from the meals and check each day against the targets."""
    warnings = []
    kcal_target, protein_target = targets["calories_kcal"], targets["protein_g"]
    protein_days = []
    for week in weeks:
        for day in week["days"]:
            day["total_kcal"] = sum(meal["kcal"] for meal in day["meals"])
            day["total_protein_g"] = sum(meal["protein_g"] for meal in day["meals"])
            protein_days.append(day["total_protein_g"])
            if abs(day["total_kcal"] - kcal_target) > KCAL_TOLERANCE * kcal_target:
                warnings.append(
                    f"Week {week['week']} day {day['day']} is {day['total_kcal']} kcal "
                    f"against a target of {kcal_target}."
                )
    average_protein = sum(protein_days) / len(protein_days)
    if average_protein < 0.85 * protein_target:
        warnings.append(
            f"The plan averages {average_protein:.0f} g protein a day against a target of "
            f"{protein_target} g. Add a protein serving such as curd, paneer, dal, tofu or eggs."
        )
    return {
        "generator": generator,
        "weeks": weeks,
        "guidance": _guidance(profile, findings, targets),
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }


# --- Offline catalogue planner --------------------------------------------------


def _allowed(meal: Meal, profile: dict, avoid_tags: set[str]) -> bool:
    if meal.kind not in DIET_KINDS[profile["diet_type"]]:
        return False
    if profile["diet_type"] == "jain" and not meal.jain:
        return False
    if meal.tags & avoid_tags:
        return False
    text = (meal.name + " " + " ".join(item[0] for item in meal.ingredients)).lower()
    return not any(allergen in text for allergen in profile["allergies"])


def _round_quantity(quantity: float, unit: str) -> float:
    if unit == "g":
        return float(math.ceil(quantity / 50) * 50)
    return float(math.ceil(quantity))


def _plan_from_catalogue(profile: dict, findings: list[dict], targets: dict, weeks: int) -> list[dict]:
    codes = {finding["code"] for finding in findings}
    avoid_tags = set().union(*(_AVOID_TAGS.get(code, set()) for code in codes))
    cuisine = profile["cuisine"]
    pools = {}
    for slot in SLOTS:
        pool = [meal for meal in MEALS if meal.slot == slot and _allowed(meal, profile, avoid_tags)]
        if not pool:
            raise PlanError(
                f"No {slot.replace('_', ' ')} options fit this diet and allergy combination."
            )
        # Preferred cuisine first, iron-rich first for anaemia; the sort is stable.
        pool.sort(key=lambda meal: (
            meal.cuisine not in (cuisine, "any"),
            "anaemia" in codes and "high_iron" not in meal.tags,
        ))
        pools[slot] = pool

    result = []
    for week in range(weeks):
        days, grocery = [], {}
        for day in range(7):
            index = week * 7 + day
            chosen = [pools[slot][(index + offset) % len(pools[slot])] for offset, slot in enumerate(SLOTS)]
            # Scale portions so the day lands on the calorie target.
            factor = targets["calories_kcal"] / sum(meal.kcal for meal in chosen)
            factor = min(max(factor, 0.7), 1.5)
            meals = []
            for meal in chosen:
                portion = meal.portion if abs(factor - 1) < 0.08 else f"{meal.portion} (about {factor:.1f}x this serving)"
                meals.append({
                    "slot": meal.slot,
                    "name": meal.name,
                    "portion": portion,
                    "kcal": round(meal.kcal * factor),
                    "protein_g": round(meal.protein_g * factor),
                })
                for name, quantity, unit, category in meal.ingredients:
                    key = (name, unit, category)
                    grocery[key] = grocery.get(key, 0) + quantity * factor
            days.append({"day": day + 1, "meals": meals})
        items = [
            {"name": name, "quantity": _round_quantity(quantity, unit), "unit": unit, "category": category}
            for (name, unit, category), quantity in grocery.items()
        ]
        items.sort(key=lambda item: (item["category"], item["name"]))
        result.append({"week": week + 1, "days": days, "grocery": items})
    return result


# --- Claude planner ---------------------------------------------------------------

_SYSTEM = """You are a clinical nutritionist writing weekly meal plans for Indian adults.

You are given the person's profile, daily targets and a list of findings from their lab
reports. The targets and findings were computed by a rules engine and are final: do not
change them, diagnose anything, or recommend medicines or supplements.

Write a 7-day plan with exactly five meals a day: breakfast, mid_morning, lunch,
evening_snack and dinner.
- Each day must total within 5% of the calorie target and reach the protein target.
- Follow the diet type strictly. Jain means no onion, garlic, root vegetables, eggs or
  meat. Never include an ingredient the person is allergic to.
- Apply every diet action listed in the findings.
- Use everyday home-cooked food from the person's preferred cuisine, with ingredients
  available in an ordinary Indian kirana shop or sabzi mandi. No exotic or imported items.
- Give portions in household measures (katori, phulka, cup, glass, tablespoon).
- Vary the meals across the week and do not repeat a main dish more than twice.
- kcal and protein_g are your best estimate for the stated portion.

Then give one consolidated grocery list for the week covering every meal: raw
ingredients with total quantity for one person, in g, kg, ml, litres or pieces, and a
category from: grains, pulses, dairy, vegetables, fruits, nuts_seeds, protein, pantry."""


def _plan_with_claude(profile: dict, findings: list[dict], targets: dict, weeks: int) -> list[dict]:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    person = {
        "age": profile["age"],
        "gender": profile["gender"],
        "diet_type": profile["diet_type"],
        "preferred_cuisine": profile["cuisine"],
        "allergies": profile["allergies"],
        "medical_conditions": profile["conditions"],
        "medications": profile["medications"],
        "drinks_alcohol": profile["alcohol"],
        "smokes": profile["smoker"],
    }
    brief = {
        "person": person,
        "daily_targets": {key: value for key, value in targets.items() if key != "notes"},
        "findings": [
            {"title": f["title"], "detail": f["message"], "diet_actions": f["diet_actions"]}
            for f in findings
        ],
    }
    result, used = [], []
    for week in range(1, weeks + 1):
        request = f"Write the plan for week {week} of {weeks}.\n\n{json.dumps(brief, indent=2)}"
        if used:
            request += "\n\nMain dishes already used in earlier weeks, to vary from:\n" + "\n".join(used)
        try:
            response = client.messages.parse(
                model=settings.planner_model,
                max_tokens=16000,
                system=_SYSTEM,
                messages=[{"role": "user", "content": request}],
                output_format=PlannedWeek,
            )
        except anthropic.APIError as exc:
            raise PlanError(f"Could not generate the meal plan: {exc}") from exc
        planned = response.parsed_output
        if response.stop_reason != "end_turn" or planned is None:
            raise PlanError(f"Could not generate the meal plan (stop_reason={response.stop_reason}).")
        if len(planned.days) != 7:
            raise PlanError(f"The generated plan for week {week} has {len(planned.days)} days, not 7.")
        used += [m.name for d in planned.days for m in d.meals if m.slot in ("lunch", "dinner")]
        result.append({"week": week, **planned.model_dump()})
    return result


def generate_plan(profile: dict, findings: list[dict], targets: dict, weeks: int) -> dict:
    if settings.use_llm:
        plan_weeks = _plan_with_claude(profile, findings, targets, weeks)
        generator = settings.planner_model
    else:
        plan_weeks = _plan_from_catalogue(profile, findings, targets, weeks)
        generator = "catalogue"
    return _finish(generator, plan_weeks, profile, findings, targets)
