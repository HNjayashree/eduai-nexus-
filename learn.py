"""
routers/learn.py
Module 1 — Personalised Learning
Endpoints:
  POST /api/v1/learn/generate-mcqs   → 5 MCQs from any pasted text
  POST /api/v1/learn/flashcards      → 6 flashcards on a topic
  POST /api/v1/learn/summarise       → Concise summary of content
  POST /api/v1/learn/explain         → ELI5 / grade-appropriate explanation
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.gemini import call_gemini

router = APIRouter(prefix="/api/v1/learn", tags=["Personalised Learning"])


# ─── Request models ───────────────────────────────────────────────────────────

class MCQRequest(BaseModel):
    text: str = Field(..., min_length=20, description="Paste any educational content here")
    grade_level: str = Field("Class 10", description="e.g. Class 6, Class 10, Undergraduate")
    num_questions: int = Field(5, ge=1, le=15)

class FlashcardRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    language: str = Field("en", description="ISO language code: en / hi / kn / ta ...")
    num_cards: int = Field(6, ge=2, le=20)

class SummariseRequest(BaseModel):
    text: str = Field(..., min_length=50)
    grade_level: str = "Class 10"
    max_words: int = Field(150, ge=50, le=500)

class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=3)
    grade_level: str = "Class 8"
    language: str = "en"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json(raw: str, endpoint: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI returned non-JSON for {endpoint}. Raw: {raw[:300]}",
        ) from exc


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate-mcqs", summary="Generate MCQs from pasted content")
async def generate_mcqs(req: MCQRequest):
    """
    Given any educational text, generate multiple-choice questions
    suitable for the specified grade level.

    Returns:
        { "questions": [ { "question": "...", "options": ["A)...", ...], "answer": "A" } ] }
    """
    prompt = f"""
You are an expert Indian school teacher for {req.grade_level}.
Generate exactly {req.num_questions} high-quality MCQs from the content below.

Rules:
- Each question must have exactly 4 options labelled A, B, C, D.
- Vary question types: factual, conceptual, application.
- One clearly correct answer per question.
- Return ONLY valid JSON, no markdown, no explanation.

Format:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "A",
      "explanation": "Brief explanation of why A is correct"
    }}
  ]
}}

Content:
{req.text[:4000]}
"""
    result = await call_gemini(prompt)
    return _parse_json(result, "generate-mcqs")


@router.post("/flashcards", summary="Generate flashcards on a topic")
async def generate_flashcards(req: FlashcardRequest):
    """
    Generate study flashcards for any topic in the specified language.

    Returns:
        { "cards": [ { "front": "Q", "back": "A" } ] }
    """
    lang_note = f"Write the cards in language code '{req.language}'." if req.language != "en" else ""
    prompt = f"""
Create exactly {req.num_cards} flashcards on the topic: {req.topic}
{lang_note}
Make them suitable for a Class 8-10 Indian student.
Cover key terms, definitions, formulas, and concepts.

Return ONLY valid JSON:
{{
  "topic": "{req.topic}",
  "cards": [
    {{"front": "question or term", "back": "answer or definition"}}
  ]
}}
"""
    result = await call_gemini(prompt)
    return _parse_json(result, "flashcards")


@router.post("/summarise", summary="Summarise educational content")
async def summarise(req: SummariseRequest):
    """
    Summarise a passage in simple language for the given grade level.

    Returns:
        { "summary": "...", "key_points": ["..."], "word_count": 120 }
    """
    prompt = f"""
Summarise the following content for a {req.grade_level} Indian student.
Keep the summary under {req.max_words} words.
Use simple English. Highlight the most important ideas.

Return ONLY valid JSON:
{{
  "summary": "...",
  "key_points": ["point 1", "point 2", "point 3"],
  "word_count": 120
}}

Content:
{req.text[:5000]}
"""
    result = await call_gemini(prompt)
    return _parse_json(result, "summarise")


@router.post("/explain", summary="Explain a concept at grade level")
async def explain_concept(req: ExplainRequest):
    """
    Explain a concept in simple terms, with an analogy and a real-world
    India-relevant example.

    Returns:
        { "explanation": "...", "analogy": "...", "example": "...", "fun_fact": "..." }
    """
    lang_note = f"Respond in language '{req.language}'." if req.language != "en" else ""
    prompt = f"""
Explain "{req.concept}" to a {req.grade_level} student in India. {lang_note}
- Use very simple words.
- Give a relatable analogy from everyday Indian life.
- Give one real-world India-specific example.
- Add one fun / surprising fact.

Return ONLY valid JSON:
{{
  "concept": "{req.concept}",
  "explanation": "...",
  "analogy": "...",
  "example": "...",
  "fun_fact": "..."
}}
"""
    result = await call_gemini(prompt)
    return _parse_json(result, "explain")
