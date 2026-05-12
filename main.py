"""
main.py
EduAI Nexus — FastAPI Entry Point
Team MAHADEV · WitchHunt Hackathon 2026

Run locally:
    uvicorn main:app --reload --port 8000

Swagger docs auto-available at:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from routers import learn, labs, translate, career, dashboard, projects

# ─── App instance ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="EduAI Nexus API",
    version="1.0.0",
    description=(
        "AI-Powered Smart Education Ecosystem — Team MAHADEV · WitchHunt 2026\n\n"
        "**Free API Stack**: Google Gemini 1.5 Flash · Groq/Llama 3.1 · Bhashini · NewsData.io\n\n"
        "**Modules**:\n"
        "- 📚 Personalised Learning (MCQs, flashcards, summaries)\n"
        "- 🔬 Virtual Labs (Physics, Chemistry, Biology simulations)\n"
        "- 🌐 Multilingual Translation (22+ Indian languages)\n"
        "- 💼 Career Readiness (ATS analysis, skill gap, coaching)\n"
        "- 📊 Resource Allocation (teacher shortage dashboard)\n"
        "- 🚀 Micro-Projects (personalised project ideas + opportunities)\n"
    ),
    contact={
        "name": "Team MAHADEV",
        "email": "team@eduainexus.in",
    },
    license_info={
        "name": "MIT",
    },
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins for hackathon POC.
# In production: restrict to ["https://your-lovable-app.lovable.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request timing middleware ────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(process_time)
    return response

# ─── Global exception handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(learn.router)
app.include_router(labs.router)
app.include_router(translate.router)
app.include_router(career.router)
app.include_router(dashboard.router)
app.include_router(projects.router)

# ─── Health & Info ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
async def health():
    """Returns server status. Used by POC acceptance checklist."""
    return {"status": "ok", "app": "EduAI Nexus", "version": "1.0.0"}


@app.get("/", tags=["System"], summary="API root")
async def root():
    return {
        "message": "Welcome to EduAI Nexus API 🎓",
        "docs": "/docs",
        "health": "/health",
        "modules": {
            "learning":    "/api/v1/learn",
            "labs":        "/api/v1/labs",
            "translate":   "/api/v1/translate",
            "career":      "/api/v1/career",
            "dashboard":   "/api/v1/dashboard",
            "projects":    "/api/v1/projects",
        },
        "team": "MAHADEV — Jayashree H N, Roshini D",
        "hackathon": "WitchHunt 2026 · Education Theme",
    }
