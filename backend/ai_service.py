# ai_service.py

import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROVIDER = "groq"


# ─────────────────────────────────────────
# TEXT GENERATION (GROQ ONLY)
# ─────────────────────────────────────────

def generate_text(prompt: str, system_prompt: str = "") -> str:
    from adapters.groq_adapter import call_groq
    return call_groq(prompt, system_prompt)


# ─────────────────────────────────────────
# JSON GENERATION (ROBUST)
# ─────────────────────────────────────────

def generate_json(prompt: str, system_prompt: str = "") -> dict:
    full_system = (system_prompt or "") + "\nReturn ONLY valid JSON. No explanation."

    raw = generate_text(prompt, full_system)

    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        fix_prompt = f"Fix this JSON and return ONLY valid JSON:\n{cleaned}"

        fixed = generate_text(fix_prompt, "Return ONLY valid JSON.")
        fixed_cleaned = re.sub(r"```(?:json)?|```", "", fixed).strip()

        return json.loads(fixed_cleaned)


# ─────────────────────────────────────────
# GEMINI SAFE SUMMARY (FIXED)
# ─────────────────────────────────────────

def gemini_summary_safe(data: dict) -> str:
    try:
        from google import genai

        # ✅ CORRECT WAY
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            return "Gemini API key not set"

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize this disaster report in one sentence:\n{data}"
        )

        return response.text if response and response.text else "No summary generated"

    except Exception as e:
        print("Gemini failed:", e)
        return "AI summary unavailable (fallback active)"