"""
services/gemini.py
Google Gemini 1.5 Flash wrapper — primary LLM for EduAI Nexus.
Free tier: 15 req/min, 1M tokens/day  →  aistudio.google.com
"""

import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY", "")
if _api_key:
    genai.configure(api_key=_api_key)

_model = genai.GenerativeModel("gemini-1.5-flash") if _api_key else None


async def call_gemini(prompt: str, system: str = None) -> str:
    """
    Async wrapper around the synchronous Gemini SDK.
    Strips markdown code fences so callers always get raw text / JSON.
    Raises RuntimeError if GEMINI_API_KEY is not set.
    """
    if not _model:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file (get one free at aistudio.google.com)."
        )

    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    # Run the blocking SDK call in a thread pool so FastAPI stays async
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: _model.generate_content(full_prompt)
    )

    text: str = response.text.strip()

    # Strip markdown code fences that Gemini sometimes wraps JSON in
    if text.startswith("```"):
        parts = text.split("```")
        # parts[1] is the content between first and second fence
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]

    return text.strip()
