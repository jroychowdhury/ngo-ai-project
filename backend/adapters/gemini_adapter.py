# gemini_adapter.py
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

def call_gemini(prompt: str, system_prompt: str = "") -> str:
    try:
        # Combine system prompt and user prompt for Gemini
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        generation_config = genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=1024,
        )

        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )

        # Clean response text
        text = response.text.strip()

        # Remove any markdown fences Gemini adds
        text = re.sub(r"```(?:json)?|```", "", text).strip()

        return text

    except Exception as e:
        print("Gemini API error:", e)
        raise Exception(f"Gemini error: {str(e)}")