"""
services/groq_ai.py
Groq → Llama 3.1 8B Instant wrapper — fast inference fallback.
Free tier: 14,400 req/day, 30 req/min  →  console.groq.com

Used primarily for ATS resume analysis where structured JSON + speed matters.
"""

import os
import asyncio
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GROQ_API_KEY", "")
_client = Groq(api_key=_api_key) if _api_key else None


async def call_groq(
    prompt: str,
    system: str = "Return only valid JSON. No markdown, no explanation.",
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 1000,
    temperature: float = 0.3,
) -> str:
    """
    Async wrapper for the synchronous Groq SDK.
    Returns raw response text (strip JSON fences if needed).
    Raises RuntimeError if GROQ_API_KEY is not set.
    """
    if not _client:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to your .env file (get one free at console.groq.com)."
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: _client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        ),
    )

    text: str = response.choices[0].message.content.strip()

    # Strip markdown fences just in case
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]

    return text.strip()
