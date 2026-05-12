"""
db/supabase_client.py
Supabase (PostgreSQL) connection for EduAI Nexus.
Free tier: 500 MB DB, 2 GB bandwidth  →  supabase.com

Usage:
    from db.supabase_client import get_client
    sb = get_client()
    data = sb.table("students").select("*").execute()
"""

import os
from dotenv import load_dotenv

load_dotenv()

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_client = None


def get_client():
    """
    Returns a lazily-initialised Supabase client.
    Returns None (with a warning) if env vars are not set, so the app still
    runs in dev mode without a database.
    """
    global _client
    if _client is not None:
        return _client

    if not _SUPABASE_URL or not _SUPABASE_KEY:
        print(
            "[WARNING] SUPABASE_URL / SUPABASE_ANON_KEY not set. "
            "Database features will be unavailable. "
            "Create a free project at supabase.com and add the keys to .env."
        )
        return None

    from supabase import create_client  # imported lazily to avoid crash if not installed

    _client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    return _client


# ─── Convenience helpers ──────────────────────────────────────────────────────

async def save_student_progress(student_id: str, module: str, score: int, details: dict):
    """Upsert a progress record for a student."""
    sb = get_client()
    if not sb:
        return None
    data = {
        "student_id": student_id,
        "module": module,
        "score": score,
        "details": details,
    }
    return sb.table("student_progress").upsert(data).execute()


async def get_student_progress(student_id: str) -> list:
    """Fetch all progress records for a student."""
    sb = get_client()
    if not sb:
        return []
    result = (
        sb.table("student_progress")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def save_career_plan(student_id: str, goal: str, plan: dict):
    """Save or update a student's career plan."""
    sb = get_client()
    if not sb:
        return None
    data = {"student_id": student_id, "goal": goal, "plan": plan}
    return sb.table("career_plans").upsert(data).execute()
