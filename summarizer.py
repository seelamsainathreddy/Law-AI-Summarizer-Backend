# backend/summarizer.py
from dotenv import load_dotenv
import os
from utils.pdf_parser import extract_text_from_pdf
import requests

# Load environment variables from .env
load_dotenv()
print("API key loaded : " + os.getenv("GROQ_API_KEY"))

PROMPT_TEMPLATE = """
You are a legal assistant. Analyze the following legal document and return a JSON object in the following format:

{{
  "summary": "Short summary here",
  "key_legal_clauses": [
    "Clause 1",
    "Clause 2"
  ],
  "flagged_clauses": [
    "Clause X may be risky because...",
    "Clause Y is unusual because..."
  ],
  "plain_english_explanation": "Layman's explanation of the legal content"
}}

Only return the JSON. Do not include any extra commentary.


Document:
{text}
"""



import json

def summarize_document(file_bytes):
    text = extract_text_from_pdf(file_bytes)
    short_text = text[:8000]  # Truncate if too long
    prompt = PROMPT_TEMPLATE.format(text=short_text)

    response = query_llm(prompt)
    print("LLM response received")
    print("Response: " + response)
    # Attempt to parse the response as JSON
    try:
        summary_json = json.loads(response.strip())
        return summary_json
    except json.JSONDecodeError:
        # fallback in case of invalid format
        return {
            "summary": "Failed to parse LLM response.",
            "key_legal_clauses": [],
            "flagged_clauses": [],
            "plain_english_explanation": ""
        }

def query_llm(prompt):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not found. Please set it in your .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    res.raise_for_status()  # Raise error if request failed
    return res.json()["choices"][0]["message"]["content"]
