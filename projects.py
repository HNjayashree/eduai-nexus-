"""
routers/projects.py
Module 6 — Micro-Project Generator
Generates 2-4 week India-relevant student projects by interest and level.
Also surfaces real hackathons, internships, and competitions.

Endpoints:
  POST /api/v1/projects/generate      → 3 personalised micro-project ideas
  GET  /api/v1/projects/opportunities → Hackathons, internships, competitions
  GET  /api/v1/projects/interests     → List supported interest areas
  POST /api/v1/projects/breakdown     → Detailed task breakdown for a project
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.gemini import call_gemini

router = APIRouter(prefix="/api/v1/projects", tags=["Micro-Projects"])

# Interest → tech context mapping
INTEREST_CONTEXT = {
    "AI/ML":           "machine learning, Python, TensorFlow/PyTorch, scikit-learn, data science, Kaggle",
    "Web Dev":         "HTML, CSS, JavaScript, React, Node.js, FastAPI, REST APIs, PostgreSQL",
    "Mobile Dev":      "Flutter, React Native, Android Studio, Kotlin, Firebase",
    "Sustainability":  "environment, climate change, IoT sensors, data visualisation, Arduino, solar energy",
    "Healthcare":      "medical data analysis, mobile health apps, accessibility, AI diagnostics, telemedicine",
    "Cybersecurity":   "network security, Python scripting, ethical hacking basics, OWASP, Kali Linux",
    "AgriTech":        "precision farming, IoT, weather data, crop disease detection, drone tech, rural India",
    "EdTech":          "learning apps, gamification, NLP, vernacular content, offline-first apps",
    "FinTech":         "UPI, digital payments, personal finance, fraud detection, stock analysis, Python",
    "Robotics/IoT":    "Arduino, Raspberry Pi, sensors, automation, smart home, industrial IoT",
    "Game Dev":        "Unity, Pygame, game design, 2D/3D graphics, game mechanics, storytelling",
    "Data Analytics":  "Python, Pandas, Matplotlib, Power BI, SQL, public datasets, open government data",
}


class ProjectRequest(BaseModel):
    interest: str = Field(..., description="Interest area — see GET /interests for options")
    level: str = Field("Beginner", pattern="^(Beginner|Intermediate|Advanced)$")
    age: int = Field(18, ge=12, le=30)
    team_size: int = Field(1, ge=1, le=6)

class BreakdownRequest(BaseModel):
    title: str
    description: str
    level: str = "Beginner"
    weeks: int = Field(4, ge=1, le=12)


@router.post("/generate", summary="Generate 3 personalised micro-project ideas")
async def generate_projects(req: ProjectRequest):
    """
    Suggest 3 micro-projects completable in 2-4 weeks, with India context,
    matching the student's interest area and skill level.

    Returns:
        { "projects": [ { "title", "description", "skills", "difficulty", "outcome", "indian_context" } ] }
    """
    context = INTEREST_CONTEXT.get(req.interest, req.interest)
    team_note = f"Team of {req.team_size} students." if req.team_size > 1 else "Solo project."
    prompt = f"""
You are a project mentor for Indian students aged {req.age} interested in {req.interest} ({context}).
Suggest 3 micro-projects completable in 2-4 weeks at {req.level} level. {team_note}

Each project should:
- Be locally relevant to India (rural / urban / governance context where possible)
- Use free/open-source tools only
- Result in something the student can show in a portfolio
- Be achievable with limited internet bandwidth if possible

Return ONLY valid JSON:
{{
  "interest": "{req.interest}",
  "level": "{req.level}",
  "projects": [
    {{
      "title": "...",
      "description": "2-3 sentence project description",
      "difficulty": "{req.level}",
      "duration_weeks": 3,
      "skills": ["Python", "APIs", "Pandas"],
      "tools": ["VS Code", "Python 3", "public dataset link"],
      "outcome": "What the student will build and be able to demo",
      "indian_context": "Why this matters in India — specific problem it addresses",
      "starter_tip": "First step to get started today"
    }}
  ]
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Project generation failed to return structured data")


@router.get("/opportunities", summary="Hackathons, internships, and competitions for Indian students")
async def get_opportunities():
    """
    Returns a curated list of real hackathons, internships, and competitions
    available to Indian students. Updated for 2025-26.
    """
    return {
        "opportunities": [
            {
                "title": "Smart India Hackathon 2026",
                "type": "Hackathon",
                "organiser": "Government of India",
                "deadline": "Aug 2026",
                "prize": "₹1 Lakh per team",
                "link": "https://sih.gov.in",
                "eligibility": "UG/PG students",
                "description": "India's largest hackathon solving government problem statements.",
            },
            {
                "title": "Google Summer of Code 2026",
                "type": "Internship",
                "organiser": "Google",
                "deadline": "Apr 2026",
                "prize": "$3,000 stipend",
                "link": "https://summerofcode.withgoogle.com",
                "eligibility": "18+ students",
                "description": "Contribute to open-source organisations over 3 months.",
            },
            {
                "title": "Flipkart GRiD 6.0",
                "type": "Competition",
                "organiser": "Flipkart",
                "deadline": "Sep 2026",
                "prize": "₹5 Lakh",
                "link": "https://unstop.com",
                "eligibility": "Engineering students",
                "description": "E-commerce technology challenge by India's leading marketplace.",
            },
            {
                "title": "ISRO Yuvika Program",
                "type": "Workshop",
                "organiser": "ISRO",
                "deadline": "Rolling",
                "prize": "Free residential programme",
                "link": "https://isro.gov.in/yuvika",
                "eligibility": "Class 9 students",
                "description": "Young Scientist Programme — space technology exposure.",
            },
            {
                "title": "NASSCOM FutureSkills Internship",
                "type": "Internship",
                "organiser": "NASSCOM",
                "deadline": "Jun 2026",
                "prize": "Stipend + certificate",
                "link": "https://nasscom.in/futureskills",
                "eligibility": "IT students",
                "description": "Industry internship in AI, cloud, cybersecurity tracks.",
            },
            {
                "title": "IIT Bombay Techfest",
                "type": "Competition",
                "organiser": "IIT Bombay",
                "deadline": "Dec 2025",
                "prize": "Cash + internship offers",
                "link": "https://techfest.org",
                "eligibility": "All students",
                "description": "Asia's largest science and technology festival with 50+ competitions.",
            },
            {
                "title": "Kaggle India Competitions",
                "type": "Competition",
                "organiser": "Kaggle / Google",
                "deadline": "Ongoing",
                "prize": "$10,000+ (varies)",
                "link": "https://kaggle.com/competitions",
                "eligibility": "All ages",
                "description": "Data science and ML competitions with public leaderboards.",
            },
            {
                "title": "AWS Educate + Hackathon",
                "type": "Hackathon",
                "organiser": "Amazon Web Services",
                "deadline": "Rolling",
                "prize": "AWS credits + certificates",
                "link": "https://aws.amazon.com/education/awseducate",
                "eligibility": "Students 18+",
                "description": "Cloud computing learning and build challenges on AWS.",
            },
        ]
    }


@router.get("/interests", summary="List supported interest areas")
async def list_interests():
    """Returns all interest areas supported by the project generator."""
    return {
        "interests": [
            {"id": key, "context": val}
            for key, val in INTEREST_CONTEXT.items()
        ]
    }


@router.post("/breakdown", summary="Detailed week-by-week task breakdown for a project")
async def breakdown_project(req: BreakdownRequest):
    """
    Given a project title and description, generate a detailed
    week-by-week task breakdown with daily micro-tasks.

    Returns:
        { "weeks": [ { "week": 1, "focus": "...", "tasks": [...] } ] }
    """
    prompt = f"""
Create a detailed {req.weeks}-week task breakdown for this student project:
Title: {req.title}
Description: {req.description}
Level: {req.level}

Break it into weekly sprints with 3-5 daily tasks each.
Include setup, development, testing, and demo/presentation phases.

Return ONLY valid JSON:
{{
  "title": "{req.title}",
  "total_weeks": {req.weeks},
  "weeks": [
    {{
      "week": 1,
      "focus": "Setup & Research",
      "tasks": [
        {{"day": "Mon-Tue", "task": "...", "time_hours": 2}},
        {{"day": "Wed-Thu", "task": "...", "time_hours": 3}},
        {{"day": "Fri-Sun", "task": "...", "time_hours": 4}}
      ],
      "deliverable": "What should be done by end of week"
    }}
  ],
  "total_hours_estimate": 40
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Project breakdown generation failed")
