# groq_adapter.py

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key safely

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize client
client = Groq(api_key=api_key)


def call_groq(prompt: str, system_prompt: str = "") -> str:
    try:
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq API error:", e)
        return "Error generating response"
