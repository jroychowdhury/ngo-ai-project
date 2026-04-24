# ai_service.py

import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================= PROVIDER =================
PROVIDER = "groq"


# ================= TEXT GENERATION =================

def generate_text(prompt: str, system_prompt: str = "") -> str:
    """
    Calls Groq API to generate text response
    """
    from adapters.groq_adapter import call_groq
    return call_groq(prompt, system_prompt)


# ================= JSON GENERATION =================

def generate_json(prompt: str, system_prompt: str = "") -> dict:
    """
    Generates structured JSON safely using AI
    """
    full_system = (system_prompt or "") + "\nReturn ONLY valid JSON. No explanation."

    raw = generate_text(prompt, full_system)

    # Clean markdown wrappers
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        # Retry once with fix prompt
        fix_prompt = f"Fix this JSON and return ONLY valid JSON:\n{cleaned}"

        fixed = generate_text(fix_prompt, "Return ONLY valid JSON.")
        fixed_cleaned = re.sub(r"```(?:json)?|```", "", fixed).strip()

        return json.loads(fixed_cleaned)


# ================= AI SUMMARY (GROQ ONLY) =================

def gemini_summary_safe(data: dict) -> str:
    """
    Replaced Gemini with Groq summary for stability
    """
    from adapters.groq_adapter import call_groq

    try:
        prompt = f"Summarize this disaster report in one sentence:\n{data}"
        return call_groq(prompt)

    except Exception as e:
        print("Summary failed:", e)
        return "AI summary unavailable"