# Aharya

Lab reports in, a personalised Indian meal plan and weekly grocery list out.

A user submits their profile with a blood report, a urine report and an optional
body-composition (InBody) report. Aharya reads the reports, flags what matters,
computes daily targets and returns a 1 to 4 week meal plan with a grocery list.

## Run locally

```bash
uv sync
uv run fastapi dev app/main.py
```

Open http://127.0.0.1:8000/docs to try the API. Data goes to `./data` (SQLite and uploads).

```bash
uv run pytest
```

## Configuration

Copy `.env.example` to `.env`.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/aharya.db` | Any SQLAlchemy URL |
| `UPLOAD_DIR` | `./data/uploads` | Where report files are stored |
| `LLM_MODE` | `auto` | `auto`, `claude` or `offline` |
| `ANTHROPIC_API_KEY` | unset | Enables the Claude path in `auto` mode |
| `EXTRACTION_MODEL`, `PLANNER_MODEL` | `claude-opus-5-5` | Models used for each step |

Two modes:

- **Claude** (API key set): Claude reads any PDF or photo, including scanned reports,
  and writes the meal plan.
- **Offline** (no key): a text parser reads digitally generated lab PDFs, and a
  rule-based planner picks meals from a built-in catalogue. Scanned reports and
  photos cannot be read in this mode.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/assessments` | Submit profile and reports (multipart). Returns `202` and an id |
| `GET` | `/v1/assessments/{id}` | Status, findings, warnings, targets, recommended tests |
| `GET` | `/v1/assessments/{id}/biomarkers` | Every extracted value with range and flag |
| `GET` | `/v1/assessments/{id}/plan` | Meal plan and grocery list |
| `DELETE` | `/v1/assessments/{id}` | Delete the assessment and its files |

Required form fields: `name`, `age`, `gender`, `alcohol`, `smoker`, `email`, `phone`,
`consent`, `blood_report`, `urine_report`.
Optional: `inbody_report`, `diet_type` (veg, eggetarian, non_veg, jain, vegan),
`cuisine` (north, south, west, east), `activity_level`, `allergies`, `conditions`,
`medications`, `height_cm`, `weight_kg`, `waist_cm`, `weeks` (1 to 4).

```bash
curl -X POST http://127.0.0.1:8000/v1/assessments \
  -F name="Ravi Shah" -F age=42 -F gender=male -F alcohol=true -F smoker=false \
  -F email=ravi@example.com -F phone=9876543210 -F consent=true \
  -F diet_type=veg -F cuisine=west -F height_cm=172 -F weight_kg=84 \
  -F blood_report=@blood.pdf -F urine_report=@urine.pdf
```

Assessment status is one of `queued`, `processing`, `completed`, `needs_doctor`
(an urgent value was found, so no plan is produced) or `failed`.

## How it works

1. **Extract** (`app/pipeline/extract.py`): each report becomes a list of name, value, unit, range.
2. **Normalise** (`normalise.py`): lab-specific names map to canonical biomarkers and get a flag.
3. **Verify** (`rules.py`): name, age and sex on the report are checked against the form; old reports are flagged.
4. **Flag** (`rules.py`): fixed thresholds produce findings, using Indian cut-offs for BMI and waist.
5. **Safety gate**: an urgent finding stops the pipeline with `needs_doctor`.
6. **Targets** (`targets.py`): calories, protein, carbs, fat and fibre are computed in code.
7. **Plan** (`planner.py`): Claude or the catalogue planner writes the week; totals are re-checked against the targets.

The LLM only reads documents and writes meals. Every medical threshold and every
calorie calculation is plain code that a clinician can review.

## Not built yet

- Authentication. Anyone with an assessment id can read or delete it.
- Supabase Storage and Postgres migrations (Alembic). Tables are created on startup.
- Emailing the plan and a PDF export.
- A durable job queue. Processing runs as an in-process background task.
- Clinical review of the thresholds in `rules.py` and the nutrition values in `catalogue.py`.
