import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")


def parse_trip_prompt(prompt: str):
    response = model.generate_content(f"""
    Extract travel preferences from this prompt.

    Return ONLY valid JSON:

    {{
        "days": number,
        "budget": number,
        "members": number,
        "vibe": "string"
    }}

    Prompt:
    {prompt}
    """)

    return json.loads(response.text)