# ai_service.py
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("AI_PROVIDER", "groq")

def generate_text(prompt: str, system_prompt: str = "") -> str:
    if PROVIDER == "groq":
        from adapters.groq_adapter import call_groq
        return call_groq(prompt, system_prompt)
    elif PROVIDER == "gemini":
        from adapters.gemini_adapter import call_gemini
        return call_gemini(prompt, system_prompt)
    else:
        raise ValueError(f"Unknown provider: {PROVIDER}")

def generate_json(prompt: str, system_prompt: str = "") -> dict:
    full_system = (system_prompt or "") + "\nReturn ONLY valid JSON. No explanation. No markdown."
    raw = generate_text(prompt, full_system)
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        fix_prompt = f"Fix this JSON and return ONLY valid JSON:\n{cleaned}"
        fixed = generate_text(fix_prompt, "Return ONLY valid JSON.")
        fixed_cleaned = re.sub(r"```(?:json)?|```", "", fixed).strip()
        return json.loads(fixed_cleaned)

def generate_tactical_summary(report: dict) -> str:
    system_prompt = """You are a disaster response tactical analyst for an NGO command center.
Be precise, urgent, and operational. No fluff. No storytelling."""

    prompt = f"""Write a 2-sentence tactical assessment.
Sentence 1: State the immediate threat and severity.
Sentence 2: State the most critical response action.

Report:
Location: {report.get('location', 'Unknown')}
Summary: {report.get('summary', '')}
Affected: {report.get('affected_people', 0)}
Urgency: {report.get('urgency', 5)}/10
Needs: {', '.join(report.get('needs', []))}
Categories: {', '.join(report.get('categories', []))}

Return ONLY 2 sentences."""

    try:
        return generate_text(prompt, system_prompt).strip()
    except Exception as e:
        print("Summary error:", e)
        return "AI assessment unavailable"