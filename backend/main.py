# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from ai_service import generate_json, generate_tactical_summary
from priority_engine import rank_reports
from database import init_db, save_report, get_all_reports
import json
import os

app = FastAPI(title="NGO Resource Allocator")

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.netlify.app",
    ],                          # FIX: removed "*" — wildcard + credentials=True blocks all browser requests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Init DB ───────────────────────────────────────────────────────────
init_db()

# ── Models ────────────────────────────────────────────────────────────
class RawReport(BaseModel):
    submitted_by: str
    raw_text: str

    @field_validator("submitted_by")
    @classmethod
    def validate_submitted_by(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("submitted_by must be at least 2 characters")
        return v.strip()

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v):
        if len(v.strip()) < 30:
            raise ValueError("raw_text must be at least 30 characters")
        if len(v.strip()) > 2000:
            raise ValueError("raw_text must not exceed 2000 characters")
        return v.strip()

# ── Prompts ───────────────────────────────────────────────────────────
PARSE_SYSTEM_PROMPT = """
You are an NGO field data analyst.
Extract structured information from field reports.
Always return valid JSON only.
"""

def build_parse_prompt(text: str) -> str:
    return f"""
Parse this field report and return JSON with exactly these fields:
- location (string)
- needs (list of strings)
- affected_people (integer — if count is vague like "hundreds", "many families",
  "several people", estimate a realistic integer. NEVER return 0 unless explicitly stated.)
- urgency (integer 1-10, 10 = life-threatening)
- categories (list, choose from: Food, Water, Medical, Shelter, Education, Infrastructure)
- summary (one sentence max)

Field Report:
\"\"\"{text}\"\"\"
"""

# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/parse-report")
async def parse_report(report: RawReport):
    try:
        # Step 1 — Parse raw text into structured JSON
        parsed = generate_json(
            prompt=build_parse_prompt(report.raw_text),
            system_prompt=PARSE_SYSTEM_PROMPT
        )
        parsed["submitted_by"] = report.submitted_by

        # Step 2 — Generate tactical AI summary
        parsed["ai_summary"] = generate_tactical_summary(parsed)

        # Step 3 — Save to database
        save_report(parsed)
        return parsed

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned malformed JSON after retry"
        )
    except Exception as e:
        print(f"[ERROR] /parse-report failed: {e}")   # FIX: log errors so you can debug in terminal
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
async def get_reports():
    return get_all_reports()


@app.get("/priority-tasks")
async def get_priority_tasks(top_n: int = 3):
    reports = get_all_reports()
    if not reports:
        return {
            "message": "No reports submitted yet.",
            "total_reports": 0,
            "priority_tasks": []
        }
    ranked = rank_reports(reports, top_n=top_n)
    return {
        "total_reports": len(reports),
        "showing_top": len(ranked),
        "priority_tasks": ranked
    }


@app.get("/health")
async def health():
    reports = get_all_reports()
    return {
        "status": "ok",
        "total_reports": len(reports),
        "provider": os.getenv("AI_PROVIDER", "groq"),
        "ai_provider_active": os.getenv("AI_PROVIDER", "groq").upper()
    }