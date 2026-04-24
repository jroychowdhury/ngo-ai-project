# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai_service import generate_json, gemini_summary_safe
from priority_engine import rank_reports
from dotenv import load_dotenv
import json
import os

# ================= INIT =================

load_dotenv()

app = FastAPI(title="NGO Resource Allocator")

# ✅ CORS (CRITICAL FOR FRONTEND)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= STORAGE =================

reports_db = []

# ================= VOLUNTEERS =================

volunteers = [
    {"name": "Rahul", "skills": ["medical"], "zone": "Odisha"},
    {"name": "Anita", "skills": ["food"], "zone": "Assam"},
]

def assign_volunteers(report: dict):
    assigned = []
    for v in volunteers:
        if report.get("location") and report["location"] in v["zone"]:
            assigned.append(v["name"])
    return assigned

# ================= MODELS =================

class RawReport(BaseModel):
    submitted_by: str
    raw_text: str

# ================= AI PROMPT =================

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
- affected_people (integer)
- urgency (integer 1-10)
- categories (list: Food, Water, Medical, Shelter, Education, Infrastructure)
- summary (one sentence max)

Field Report:
\"\"\"{text}\"\"\"
"""

# ================= ROUTES =================

@app.get("/")
def root():
    return {"message": "NGO Backend Running"}

# ---------- Parse Report ----------

@app.post("/parse-report")
async def parse_report(report: RawReport):
    try:
        parsed = generate_json(
            prompt=build_parse_prompt(report.raw_text),
            system_prompt=PARSE_SYSTEM_PROMPT
        )

        # AI summary
        parsed["ai_summary"] = gemini_summary_safe(parsed)

        # Volunteer assignment
        parsed["assigned_volunteers"] = assign_volunteers(parsed)

        parsed["submitted_by"] = report.submitted_by

        reports_db.append(parsed)

        return parsed

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Get All Reports ----------

@app.get("/reports")
async def get_reports():
    return sorted(reports_db, key=lambda r: r.get("urgency", 0), reverse=True)

# ---------- Priority Tasks ----------

@app.get("/priority-tasks")
async def get_priority_tasks(top_n: int = 3):
    if not reports_db:
        return {
            "message": "No reports submitted yet",
            "total_reports": 0,
            "priority_tasks": []
        }

    ranked = rank_reports(reports_db, top_n=top_n)

    return {
        "total_reports": len(reports_db),
        "showing_top": len(ranked),
        "priority_tasks": ranked
    }

# ---------- Health ----------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "reports": len(reports_db),
        "provider": os.getenv("AI_PROVIDER", "groq")
    }
