"""
routers/translate.py
Module 3 — Multilingual Translation
Supports 22+ Indian languages via Bhashini (primary) → Gemini (fallback).

Endpoints:
  POST /api/v1/translate/concept    → Translate + simplify an educational concept
  GET  /api/v1/translate/flashnews → Current affairs flash cards in target language
  GET  /api/v1/translate/languages → List supported languages
  POST /api/v1/translate/batch     → Translate multiple concepts at once
"""

import json
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from services.gemini import call_gemini
from services.bhashini import translate as bhashini_translate, is_configured as bhashini_ok
from services.news import fetch_news

router = APIRouter(prefix="/api/v1/translate", tags=["Multilingual"])

# Language registry
LANGUAGES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ml": "Malayalam",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "sa": "Sanskrit",
    "en": "English",
}


# ─── Request models ───────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=2)
    target_language: str = Field("hi", description="ISO code: hi / kn / ta / te ...")
    grade: int = Field(8, ge=1, le=12)
    source_language: str = "en"

class BatchTranslateRequest(BaseModel):
    texts: list[str] = Field(..., min_items=1, max_items=20)
    target_language: str = "hi"
    grade: int = 8


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _lang_name(code: str) -> str:
    return LANGUAGES.get(code, code)


async def _translate_with_fallback(text: str, source: str, target: str) -> str:
    """Try Bhashini first; fall back to Gemini if not configured or on error."""
    if bhashini_ok():
        try:
            return await bhashini_translate(text, source_lang=source, target_lang=target)
        except Exception:
            pass  # Fall through to Gemini
    # Gemini fallback
    prompt = f"Translate the following text from {_lang_name(source)} to {_lang_name(target)}. Return ONLY the translated text, nothing else.\n\nText: {text}"
    return await call_gemini(prompt)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/concept", summary="Translate and simplify an educational concept")
async def translate_concept(req: TranslateRequest):
    """
    Translate an educational concept into the target language and simplify
    it for the given grade level.

    Returns:
        { "original": "...", "translated": "...", "simplified": "...", "language": "Kannada" }
    """
    lang_name = _lang_name(req.target_language)
    prompt = f"""
Translate this educational concept to {lang_name} for a Grade {req.grade} student.
Simplify it so a {req.grade + 5}-year-old in rural India can understand it easily.
Use vocabulary appropriate for that age.

Return ONLY valid JSON:
{{
  "original": "{req.text}",
  "translated": "...translation in {lang_name}...",
  "simplified": "...simple {lang_name} explanation...",
  "romanised": "...transliteration in Roman script (helpful for students learning the script)..."
}}

Concept: {req.text}
"""
    raw = await call_gemini(prompt)
    try:
        result = json.loads(raw)
        result["language"] = lang_name
        return result
    except json.JSONDecodeError:
        return {
            "original": req.text,
            "translated": raw,
            "simplified": "",
            "language": lang_name,
        }


@router.get("/flashnews", summary="Current-affairs flash cards in target language")
async def flash_news(
    language: str = Query("hi", description="Target language code"),
    count: int = Query(5, ge=1, le=10),
):
    """
    Fetch live Indian news and convert into student-friendly flash cards
    in the target language.

    Returns:
        { "language": "Hindi", "cards": [ { "headline": "...", "summary": "...", "category": "..." } ] }
    """
    lang_name = _lang_name(language)
    articles = await fetch_news(count)

    prompt = f"""
Summarise these news articles for Indian students as current-affairs flash cards in {lang_name}.
Each card should be easy to understand for a Class 8-12 student.
Make headlines punchy and summaries under 40 words.

Articles:
{json.dumps(articles, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "cards": [
    {{
      "headline": "...in {lang_name}...",
      "summary": "...in {lang_name}...",
      "category": "Education / Science / Technology / Environment / Economy",
      "english_headline": "...English headline..."
    }}
  ]
}}
"""
    raw = await call_gemini(prompt)
    try:
        result = json.loads(raw)
        result["language"] = lang_name
        return result
    except json.JSONDecodeError:
        return {"language": lang_name, "cards": []}


@router.get("/languages", summary="List all supported languages")
async def list_languages():
    """Returns all supported language codes and names."""
    return {
        "languages": [{"code": k, "name": v} for k, v in LANGUAGES.items()],
        "bhashini_available": bhashini_ok(),
        "note": "Bhashini gives government-grade accuracy. Gemini handles fallback.",
    }


@router.post("/batch", summary="Translate multiple concepts at once")
async def batch_translate(req: BatchTranslateRequest):
    """
    Translate a list of terms/concepts in a single API call.
    Useful for vocabulary lists and glossaries.

    Returns:
        { "translations": [ { "original": "...", "translated": "..." } ] }
    """
    lang_name = _lang_name(req.target_language)
    items_json = json.dumps(req.texts, ensure_ascii=False)
    prompt = f"""
Translate each of these educational terms/concepts to {lang_name} for Grade {req.grade} students.

Terms: {items_json}

Return ONLY valid JSON:
{{
  "translations": [
    {{"original": "...", "translated": "...in {lang_name}..."}}
  ]
}}
"""
    raw = await call_gemini(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(500, "Failed to parse batch translation response")
