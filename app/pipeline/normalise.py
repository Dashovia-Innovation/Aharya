"""Map lab-specific test names and values onto canonical biomarkers."""

import re
from dataclasses import dataclass

Range = tuple[float | None, float | None]


@dataclass(frozen=True)
class Marker:
    code: str
    label: str
    panel: str
    aliases: tuple[str, ...]
    # Used only when the report prints no reference range of its own.
    ref: Range | dict[str, Range] | None = None


def _m(code, label, panel, aliases, ref=None) -> Marker:
    return Marker(code, label, panel, tuple(aliases.split()), ref)


# Aliases are matched after lower-casing and stripping everything but a-z0-9.
BLOOD = [
    _m("hb", "Haemoglobin", "cbc", "haemoglobin hemoglobin hb hgb", {"male": (13.0, 17.0), "female": (12.0, 15.0)}),
    _m("rbc", "RBC count", "cbc", "rbccount rbc totalrbccount redbloodcellcount"),
    _m("hct", "Haematocrit (PCV)", "cbc", "hematocritpcv hematocrit haematocrit pcv packedcellvolume"),
    _m("mcv", "MCV", "cbc", "mcv", (80, 100)),
    _m("mch", "MCH", "cbc", "mch"),
    _m("mchc", "MCHC", "cbc", "mchc"),
    _m("rdw", "RDW", "cbc", "rdwcv rdw"),
    _m("mpv", "MPV", "cbc", "mpv"),
    _m("wbc", "WBC count", "cbc", "wbccount wbc totalwbccount tlc totalleucocytecount totalleukocytecount", (4000, 11000)),
    _m("platelets", "Platelet count", "cbc", "plateletcount platelets", (150000, 450000)),
    _m("neutrophils", "Neutrophils", "cbc", "neutrophils"),
    _m("lymphocytes", "Lymphocytes", "cbc", "lymphocytes"),
    _m("monocytes", "Monocytes", "cbc", "monocytes"),
    _m("eosinophils", "Eosinophils", "cbc", "eosinophils"),
    _m("basophils", "Basophils", "cbc", "basophils"),
    _m("fbs", "Fasting blood sugar", "glucose", "fastingbloodsugar fastingbloodglucose glucosefasting fbs fastingplasmaglucose bloodsugarfasting fastingglucose", (70, 100)),
    _m("ppbs", "Post-prandial blood sugar", "glucose", "postprandialbloodsugar ppbs glucosepostprandial bloodsugarpp glucosepp", (70, 140)),
    _m("hba1c", "HbA1c", "glucose", "hba1c glycosylatedhemoglobin glycatedhemoglobin glycosylatedhaemoglobin glycatedhaemoglobin hba1cglycosylatedhemoglobin", (4.0, 5.6)),
    _m("tc", "Total cholesterol", "lipid", "totalcholesterol cholesteroltotal cholesterol serumcholesterol", (None, 200)),
    _m("ldl", "LDL cholesterol", "lipid", "ldlcholesterol ldl ldlc ldlcholesteroldirect ldlcholesterolcalculated", (None, 100)),
    _m("hdl", "HDL cholesterol", "lipid", "hdlcholesterol hdl hdlc", {"male": (40, None), "female": (50, None)}),
    _m("tg", "Triglycerides", "lipid", "triglycerides triglyceride serumtriglycerides tg", (None, 150)),
    _m("vldl", "VLDL cholesterol", "lipid", "vldl vldlcholesterol"),
    _m("alt", "ALT (SGPT)", "liver", "sgpt alt sgptalt altsgpt alanineaminotransferase", (None, 45)),
    _m("ast", "AST (SGOT)", "liver", "sgot ast sgotast astsgot aspartateaminotransferase", (None, 40)),
    _m("ggt", "GGT", "liver", "ggt gammagt ggtp", (None, 55)),
    _m("alp", "Alkaline phosphatase", "liver", "alkalinephosphatase alp"),
    _m("bilirubin_total", "Total bilirubin", "liver", "totalbilirubin bilirubintotal", (None, 1.2)),
    _m("creatinine", "Creatinine", "kidney", "creatinine serumcreatinine", {"male": (0.7, 1.3), "female": (0.6, 1.1)}),
    _m("urea", "Urea", "kidney", "urea bloodurea serumurea"),
    _m("bun", "BUN", "kidney", "bun bloodureanitrogen"),
    _m("egfr", "eGFR", "kidney", "egfr estimatedgfr", (90, None)),
    _m("uric_acid", "Uric acid", "kidney", "uricacid serumuricacid", {"male": (3.5, 7.2), "female": (2.6, 6.0)}),
    _m("sodium", "Sodium", "electrolytes", "sodium serumsodium", (135, 145)),
    _m("potassium", "Potassium", "electrolytes", "potassium serumpotassium", (3.5, 5.1)),
    _m("calcium", "Calcium", "electrolytes", "calcium serumcalcium", (8.6, 10.2)),
    _m("tsh", "TSH", "thyroid", "tsh tshultrasensitive tshultra thyroidstimulatinghormone", (0.4, 4.5)),
    _m("vit_d", "Vitamin D (25-OH)", "vitamin_d", "vitamind vitamind25hydroxy vitamind25oh 25ohvitamind 25hydroxyvitamind vitamindtotal", (30, 100)),
    _m("vit_b12", "Vitamin B12", "vitamin_b12", "vitaminb12 b12 vitb12", (200, 900)),
    _m("ferritin", "Ferritin", "iron", "ferritin serumferritin"),
    _m("iron", "Serum iron", "iron", "serumiron iron"),
    _m("crp", "CRP", "inflammation", "crp hscrp creactiveprotein"),
]

URINE = [
    _m("urine_protein", "Urine protein", "urine", "protein proteins protiens albumin"),
    _m("urine_glucose", "Urine glucose", "urine", "glucose sugar"),
    _m("urine_ketone", "Urine ketone", "urine", "ketone ketones ketonebodies"),
    _m("urine_bilirubin", "Urine bilirubin", "urine", "bilirubin"),
    _m("urine_blood", "Urine occult blood", "urine", "occultblood blood"),
    _m("urine_nitrite", "Urine nitrite", "urine", "nitrite nitrites"),
    _m("urine_pus_cells", "Urine pus cells", "urine", "puscells puscellswbc leucocytes"),
    _m("urine_rbc", "Urine red blood cells", "urine", "redbloodcells rbc rbcs"),
    _m("urine_epithelial", "Urine epithelial cells", "urine", "epithelialcells"),
    _m("urine_bacteria", "Urine bacteria", "urine", "bacteria"),
    _m("urine_casts", "Urine casts", "urine", "casts"),
    _m("urine_crystals", "Urine crystals", "urine", "crystals"),
    _m("urine_ph", "Urine pH", "urine", "ph reactionph reaction"),
    _m("urine_sg", "Urine specific gravity", "urine", "specificgravity"),
]

INBODY = [
    _m("height_cm", "Height", "inbody", "height"),
    _m("weight_kg", "Weight", "inbody", "weight"),
    _m("tbw_l", "Total body water", "inbody", "totalbodywater"),
    _m("body_protein_kg", "Body protein", "inbody", "protein"),
    _m("body_mineral_kg", "Body mineral", "inbody", "mineral minerals"),
    _m("fat_mass_kg", "Body fat mass", "inbody", "bodyfatmass"),
    _m("smm_kg", "Skeletal muscle mass", "inbody", "smm skeletalmusclemass smmskeletalmusclemass"),
    _m("bmi", "BMI", "inbody", "bmi bodymassindex bmibodymassindex"),
    _m("pbf", "Percent body fat", "inbody", "pbf percentbodyfat pbfpercentbodyfat"),
    _m("whr", "Waist-hip ratio", "inbody", "waisthipratio whr"),
    _m("visceral_fat", "Visceral fat level", "inbody", "visceralfatlevel visceralfat"),
    _m("bmr_kcal", "Basal metabolic rate", "inbody", "basalmetabolicrate bmr"),
    _m("ffm_kg", "Fat free mass", "inbody", "fatfreemass"),
    _m("target_weight_kg", "Target weight", "inbody", "targetweight"),
    _m("weight_control_kg", "Weight control", "inbody", "weightcontrol"),
    _m("fat_control_kg", "Fat control", "inbody", "fatcontrol"),
    _m("muscle_control_kg", "Muscle control", "inbody", "musclecontrol"),
    _m("inbody_score", "InBody score", "inbody", "inbodyscore"),
]

_CATALOGUES = {"blood": BLOOD, "urine": URINE, "inbody": INBODY}
_LOOKUP = {
    kind: {alias: marker for marker in markers for alias in marker.aliases}
    for kind, markers in _CATALOGUES.items()
}

# Cell counts some labs print in thousands or lakhs; store per cumm.
_COUNT_SCALES = {"platelets": ((10, 100000), (1000, 1000)), "wbc": ((100, 1000),)}
# Urine microscopy: abnormal above this many cells per high-power field.
_HPF_LIMITS = {"urine_pus_cells": 5, "urine_rbc": 2}
_NEGATIVE = ("absent", "nil", "negative", "normal", "not seen", "none", "not detected")
_POSITIVE = ("present", "positive", "trace", "+", "detected", "seen")

_NUMBER = r"\d[\d,]*\.?\d*"
_VALUE = re.compile(rf"^[<>]?\s*(-?{_NUMBER})$")
_RANGE = re.compile(rf"({_NUMBER})\s*(?:-|–|~|to)\s*({_NUMBER})", re.I)
_UPPER = re.compile(rf"(?:<|upto|up to|less than|below)\s*=?\s*({_NUMBER})", re.I)
_LOWER = re.compile(rf"(?:>|more than|above)\s*=?\s*({_NUMBER})", re.I)


def name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def lookup(kind: str, name: str) -> Marker | None:
    return _LOOKUP[kind].get(name_key(name))


def _float(text: str) -> float:
    return float(text.replace(",", ""))


def parse_number(text: str) -> float | None:
    match = _VALUE.match(text.strip())
    return _float(match.group(1)) if match else None


def parse_range(text: str | None) -> Range:
    if not text:
        return None, None
    if match := _RANGE.search(text):
        return _float(match.group(1)), _float(match.group(2))
    if match := _UPPER.search(text):
        return None, _float(match.group(1))
    if match := _LOWER.search(text):
        return _float(match.group(1)), None
    return None, None


def _scale(code: str, value: float | None) -> float | None:
    if value is None:
        return None
    for below, factor in _COUNT_SCALES.get(code, ()):
        if value < below:
            return value * factor
    return value


def _qualitative_flag(text: str) -> str | None:
    lowered = text.lower()
    if any(token in lowered for token in _NEGATIVE):
        return "normal"
    if any(token in lowered for token in _POSITIVE):
        return "abnormal"
    return None


def normalise(kind: str, name: str, value: str, unit: str | None, reference: str | None, sex: str) -> dict:
    """Return the fields of a Biomarker row for one extracted result."""
    marker = lookup(kind, name)
    code = marker.code if marker else None
    value = value.strip()
    number = parse_number(value)
    low, high = parse_range(reference)

    if marker and low is None and high is None and marker.ref:
        ref = marker.ref
        low, high = ref.get(sex, (None, None)) if isinstance(ref, dict) else ref

    flag = None
    if code in _HPF_LIMITS:
        # "10-15/HPF" -> judge on the upper bound.
        counts = [int(n) for n in re.findall(r"\d+", value)]
        if counts:
            number = float(max(counts))
            flag = "abnormal" if number > _HPF_LIMITS[code] else "normal"
        else:
            flag = _qualitative_flag(value)
    elif number is not None:
        if code in _COUNT_SCALES:
            number, low, high = _scale(code, number), _scale(code, low), _scale(code, high)
        if low is not None and number < low:
            flag = "low"
        elif high is not None and number > high:
            flag = "high"
        elif low is not None or high is not None:
            flag = "normal"
    elif kind == "urine" and code:
        flag = _qualitative_flag(value)

    return {
        "source": kind,
        "code": code,
        "label": marker.label if marker else name.strip(),
        "raw_name": name.strip(),
        "value_num": number,
        "value_text": value,
        "unit": unit or None,
        "ref_low": low,
        "ref_high": high,
        "flag": flag,
    }
