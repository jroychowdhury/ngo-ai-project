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
    elif PROVIDER == "openrouter":
        from adapters.openrouter_adapter import call_openrouter
        return call_openrouter(prompt, system_prompt)
    else:
        raise ValueError(f"Unknown provider: {PROVIDER}")

def generate_json(prompt: str, system_prompt: str = "") -> dict:
    full_system = (system_prompt or "") + "\nReturn ONLY valid JSON. No explanation. No markdown. No code blocks."
    raw = generate_text(prompt, full_system)
    
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        fix_prompt = f"This is invalid JSON. Fix it and return ONLY valid JSON:\n{cleaned}"
        fixed = generate_text(fix_prompt, "Return ONLY valid JSON. Nothing else.")
        fixed_cleaned = re.sub(r"```(?:json)?|```", "", fixed).strip()
        return json.loads(fixed_cleaned)

def gemini_summary_safe(data):
    try:
        from google import genai

        client = genai.Client(api_key="AIzaSyBiHoiVAMVvlR2dNvRU79pHS0EWarhakGE")

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize this disaster report:\n{data}"
        )

        return response.text

    except Exception as e:
        print("Gemini failed:", e)
        return "AI-generated summary (Gemini fallback active)"