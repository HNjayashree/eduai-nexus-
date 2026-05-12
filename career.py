"""
routers/career.py
Module 4 — Career Readiness / ATS Resume Analyzer
Uses Groq/Llama for fast ATS analysis; Gemini for skill gap + chat.

Endpoints:
  POST /api/v1/career/ats-analyze    → ATS score, missing keywords, rewrites
  POST /api/v1/career/skill-gap      → Skills needed for a career goal
  POST /api/v1/career/chat           → AI career counsellor chat
  GET  /api/v1/career/careers        → List popular career paths for Indian students
  POST /api/v1/career/roadmap        → Generate a 6-month learning roadmap
"""

import json
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.groq_ai import call_groq
from services.gemini import call_gemini

router = APIRouter(prefix="/api/v1/career", tags=["Career Readiness"])


# ─── Request models ───────────────────────────────────────────────────────────

class ATSRequest(BaseModel):
    job_description: str = Field(..., min_length=50)
    resume_summary: str = Field(..., min_length=30)

class SkillGapRequest(BaseModel):
    career_goal: str = Field(..., min_length=3)
    current_skills: List[str] = []
    experience_years: int = Field(0, ge=0, le=30)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[dict] = []

class RoadmapRequest(BaseModel):
    career_goal: str
    current_skills: List[str] = []
    hours_per_week: int = Field(10, ge=1, le=80)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/ats-analyze", summary="ATS resume analysis (Groq/Llama for speed)")
async def ats_analyze(req: ATSRequest):
    """
    Analyse a resume summary against a job description.
    Uses Groq's Llama 3.1 for fast, structured JSON output.

    Returns:
        {
          "ats_score": 72,
          "missing_keywords": ["Python", "SQL"],
          "matched_keywords": ["communication", "teamwork"],
          "rewrites": ["Improved bullet 1", ...],
          "strengths": ["Good point"],
          "overall_feedback": "..."
        }
    """
    prompt = f"""
You are an expert ATS resume consultant for the Indian job market (IT, PSU, startup, UPSC).

Job Description:
{req.job_description[:2000]}

Resume Summary:
{req.resume_summary[:1000]}

Analyse the resume against the JD. Be specific to Indian job market norms.

Return ONLY valid JSON (no markdown):
{{
  "ats_score": 72,
  "missing_keywords": ["keyword1", "keyword2"],
  "matched_keywords": ["keyword3"],
  "rewrites": [
    "Original bullet → Improved version with keywords",
    "Original bullet → Improved version 2",
    "Original bullet → Improved version 3"
  ],
  "strengths": ["Strength 1", "Strength 2"],
  "overall_feedback": "2-3 sentences of honest, actionable feedback"
}}
"""
    try:
        result = await call_groq(prompt)
        return json.loads(result)
    except json.JSONDecodeError:
        # Fallback to Gemini if Groq returns bad JSON
        result = await call_gemini(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            raise HTTPException(500, "ATS analysis failed to return structured data")


@router.post("/skill-gap", summary="Identify skill gaps for a career goal")
async def skill_gap(req: SkillGapRequest):
    """
    Compare current skills against what is required for the career goal.
    Returns top 5-7 gaps with resources.

    Returns:
        { "career_goal": "...", "gaps": [ { "skill": "Python", "current": 30, "required": 85, "resource": "..." } ] }
    """
    prompt = f"""
Career goal: {req.career_goal}
Current skills: {req.current_skills}
Years of experience: {req.experience_years}

Identify the top 6 skill gaps for this career goal in the Indian job market.
Rate current and required proficiency on a 0-100 scale.
Recommend a free or affordable Indian-accessible resource for each gap.

Return ONLY valid JSON:
{{
  "career_goal": "{req.career_goal}",
  "market_context": "One sentence about this role's demand in India",
  "gaps": [
    {{
      "skill": "Python",
      "current": 30,
      "required": 85,
      "priority": "High / Medium / Low",
      "resource": "Name and URL of best free resource",
      "time_to_learn": "e.g. 3 months at 10 hrs/week"
    }}
  ]
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Skill gap analysis failed to return structured data")


@router.post("/chat", summary="AI career counsellor chat")
async def career_chat(req: ChatRequest):
    """
    Conversational career coaching. Maintains history for context.
    Focused on Indian job market: UPSC, SSC, IT, startups, emerging tech.

    Returns:
        { "reply": "..." }
    """
    system = (
        "You are an expert Indian career counsellor helping students aged 16-25. "
        "Be warm, encouraging, specific, and practical. "
        "Focus on the Indian job market: UPSC, SSC, IIT/NIT admissions, IT sector, "
        "startups, MSMEs, emerging tech (AI, EV, green energy). "
        "Reference free resources like NPTEL, Swayam, YouTube tutorials in Hindi/English. "
        "Keep responses under 150 words. End every reply with one concrete actionable step."
    )

    # Build conversation history string for Gemini (which doesn't support multi-turn natively here)
    history_text = ""
    for msg in req.history[-6:]:  # Last 6 turns for context
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"\n{role.capitalize()}: {content}"

    full_prompt = f"{history_text}\nUser: {req.message}" if history_text else req.message
    result = await call_gemini(full_prompt, system=system)
    return {"reply": result}


@router.get("/careers", summary="Popular career paths for Indian students")
async def list_careers():
    """Returns a curated list of high-demand careers in India with median salaries."""
    return {
        "careers": [
            {"title": "Software Engineer", "sector": "IT", "avg_salary_lpa": "6-20", "growth": "High", "entry_path": "B.Tech / BCA / self-taught"},
            {"title": "Data Scientist / ML Engineer", "sector": "Tech", "avg_salary_lpa": "8-25", "growth": "Very High", "entry_path": "B.Tech + Python + ML courses"},
            {"title": "Civil Services (IAS/IPS)", "sector": "Government", "avg_salary_lpa": "10-16", "growth": "Stable", "entry_path": "Any UG degree + UPSC prep"},
            {"title": "CA (Chartered Accountant)", "sector": "Finance", "avg_salary_lpa": "7-30", "growth": "High", "entry_path": "ICAI CPT → IPCC → Final"},
            {"title": "Doctor (MBBS)", "sector": "Healthcare", "avg_salary_lpa": "8-40", "growth": "High", "entry_path": "NEET → MBBS → PG"},
            {"title": "EV / Renewable Energy Engineer", "sector": "Green Tech", "avg_salary_lpa": "5-18", "growth": "Very High", "entry_path": "B.Tech EE/ME + specialisation"},
            {"title": "Cybersecurity Analyst", "sector": "Tech", "avg_salary_lpa": "6-22", "growth": "Very High", "entry_path": "B.Tech CS + CEH / OSCP cert"},
            {"title": "UX/UI Designer", "sector": "Design", "avg_salary_lpa": "4-18", "growth": "High", "entry_path": "Any degree + Figma + portfolio"},
            {"title": "Defence (NDA/CDS)", "sector": "Defence", "avg_salary_lpa": "6-14", "growth": "Stable", "entry_path": "12th + UPSC NDA/CDS exam"},
            {"title": "Content Creator / Digital Marketing", "sector": "Media", "avg_salary_lpa": "3-15", "growth": "High", "entry_path": "Any degree + portfolio"},
        ]
    }


@router.post("/roadmap", summary="Generate a personalised 6-month learning roadmap")
async def generate_roadmap(req: RoadmapRequest):
    """
    Create a week-by-week learning roadmap to achieve a career goal.

    Returns:
        { "roadmap": [ { "month": 1, "focus": "...", "tasks": [...], "milestone": "..." } ] }
    """
    prompt = f"""
Create a realistic 6-month learning roadmap for someone who wants to become a {req.career_goal}.
Current skills: {req.current_skills}
Available time: {req.hours_per_week} hours per week.
Context: Indian student, preferring free/affordable resources.

Return ONLY valid JSON:
{{
  "career_goal": "{req.career_goal}",
  "total_hours": {req.hours_per_week * 24},
  "roadmap": [
    {{
      "month": 1,
      "focus": "Foundation building",
      "weekly_tasks": ["Task 1", "Task 2"],
      "resources": ["Resource name + URL"],
      "milestone": "What they should be able to do by end of month"
    }}
  ],
  "final_outcome": "What they can achieve after 6 months"
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Roadmap generation failed")
