"""
routers/dashboard.py
Module 5 — Resource Allocation Dashboard (Teacher & Infrastructure)
Provides district-level KPIs, shortage forecasts, and AI policy simulation.

Endpoints:
  GET  /api/v1/dashboard/district-data      → KPIs + forecast for a district
  GET  /api/v1/dashboard/all-districts      → List all districts
  POST /api/v1/dashboard/simulate-policy    → AI impact prediction for a policy
  GET  /api/v1/dashboard/state-summary      → Aggregated Karnataka-level stats
  POST /api/v1/dashboard/recommend-action   → AI-recommended intervention
"""

import json
import random
from fastapi import APIRouter, Query, HTTPException
from services.gemini import call_gemini

router = APIRouter(prefix="/api/v1/dashboard", tags=["Resource Allocation"])

# ─── Mock district dataset ────────────────────────────────────────────────────
# Replace with Supabase query in production:
#   from db.supabase_client import get_client
#   sb = get_client()
#   result = sb.table("districts").select("*").eq("name", district).execute()

DISTRICT_DATA = {
    "Mysuru":     {"teachers": 450,  "schools": 38, "students": 14400, "infrastructure": 72, "digital_labs": 12, "region": "South"},
    "Bellary":    {"teachers": 210,  "schools": 41, "students": 18200, "infrastructure": 45, "digital_labs": 4,  "region": "North"},
    "Kalaburagi": {"teachers": 180,  "schools": 55, "students": 22000, "infrastructure": 38, "digital_labs": 3,  "region": "North"},
    "Dharwad":    {"teachers": 390,  "schools": 33, "students": 12500, "infrastructure": 68, "digital_labs": 9,  "region": "North-West"},
    "Hassan":     {"teachers": 310,  "schools": 29, "students": 10800, "infrastructure": 61, "digital_labs": 7,  "region": "South"},
    "Tumakuru":   {"teachers": 340,  "schools": 36, "students": 13200, "infrastructure": 59, "digital_labs": 6,  "region": "South-East"},
    "Belagavi":   {"teachers": 520,  "schools": 62, "students": 24600, "infrastructure": 55, "digital_labs": 8,  "region": "North-West"},
    "Shivamogga": {"teachers": 280,  "schools": 31, "students": 11500, "infrastructure": 64, "digital_labs": 5,  "region": "Central"},
    "Mangaluru":  {"teachers": 480,  "schools": 27, "students": 9800,  "infrastructure": 81, "digital_labs": 15, "region": "Coastal"},
    "Bengaluru":  {"teachers": 1200, "schools": 95, "students": 48000, "infrastructure": 88, "digital_labs": 42, "region": "South-East"},
}

MONTHS = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]


def _generate_forecast(infrastructure_score: int, teacher_count: int, student_count: int) -> list:
    """Simulate a 10-month shortage forecast based on district data."""
    base_shortage = max(0, 40 - infrastructure_score)
    ratio = student_count / max(teacher_count, 1)
    extra = max(0, int((ratio - 30) * 0.5))  # Extra stress from high ratio
    return [
        {
            "month": m,
            "shortage": max(0, base_shortage + extra + random.randint(-5, 8)),
            "utilisation_pct": min(100, round(60 + random.uniform(-10, 20), 1)),
        }
        for m in MONTHS
    ]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/district-data", summary="Get KPIs and forecast for a Karnataka district")
async def get_district_data(district: str = Query("Mysuru")):
    """
    Returns teacher count, school count, student-teacher ratio,
    infrastructure score, shortage forecast, and alert flags.
    """
    d = DISTRICT_DATA.get(district)
    if not d:
        available = list(DISTRICT_DATA.keys())
        raise HTTPException(404, detail=f"District '{district}' not found. Available: {available}")

    ratio = round(d["students"] / max(d["teachers"], 1), 1)
    alert = ratio > 40 or d["infrastructure"] < 50
    forecast = _generate_forecast(d["infrastructure"], d["teachers"], d["students"])

    return {
        "district": district,
        "region": d["region"],
        "teachers": d["teachers"],
        "schools": d["schools"],
        "students": d["students"],
        "digital_labs": d["digital_labs"],
        "student_teacher_ratio": ratio,
        "infrastructure_score": d["infrastructure"],
        "alert": alert,
        "alert_level": "critical" if ratio > 50 or d["infrastructure"] < 40 else "warning" if alert else "ok",
        "alert_message": (
            f"⚠ High ratio {ratio}:1 and low infra score {d['infrastructure']}/100. "
            "Recommend deploying 30+ teachers and upgrading 10+ classrooms."
            if alert else None
        ),
        "forecast": forecast,
    }


@router.get("/all-districts", summary="List all districts in the dataset")
async def all_districts():
    """Returns all district names and a brief summary of each."""
    summary = []
    for name, d in DISTRICT_DATA.items():
        ratio = round(d["students"] / max(d["teachers"], 1), 1)
        alert = ratio > 40 or d["infrastructure"] < 50
        summary.append({
            "district": name,
            "region": d["region"],
            "student_teacher_ratio": ratio,
            "infrastructure_score": d["infrastructure"],
            "alert": alert,
        })
    return {"districts": summary, "total": len(summary)}


@router.post("/simulate-policy", summary="AI prediction for a policy intervention")
async def simulate_policy(body: dict):
    """
    Describe a policy (e.g. 'Deploy 50 contract teachers to Kalaburagi')
    and get an AI-predicted 3-month impact on shortage, outcomes, and cost.

    Body:
        { "policy": "...", "district": "Kalaburagi", "district_data": {...} }

    Returns:
        { "teacher_shortage_change": -15, "outcome_improvement": 8, "cost_efficiency": "High", "risks": [...] }
    """
    policy = body.get("policy", "")
    district = body.get("district", "Unknown")
    district_data = body.get("district_data") or DISTRICT_DATA.get(district, {})

    if not policy:
        raise HTTPException(400, "Field 'policy' is required.")

    prompt = f"""
A Karnataka government education officer wants to evaluate this policy intervention:
Policy: {policy}
District: {district}
Current district data: {district_data}

Predict the impact over 3 months on:
1. Teacher shortage (positive = improvement)
2. Student learning outcomes
3. Cost efficiency
4. Risks and unintended consequences

Be specific, realistic, and grounded in Indian public education context.

Return ONLY valid JSON:
{{
  "policy_summary": "...",
  "teacher_shortage_change": -15,
  "outcome_improvement_pct": 8,
  "cost_efficiency": "High / Medium / Low",
  "estimated_cost_lakhs": 25,
  "risks": ["Risk 1", "Risk 2"],
  "implementation_steps": ["Step 1", "Step 2", "Step 3"],
  "confidence": "High / Medium / Low"
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"error": "Simulation failed to return structured data", "raw": result}


@router.get("/state-summary", summary="Aggregated Karnataka state stats")
async def state_summary():
    """Returns rolled-up statistics across all districts."""
    total_teachers = sum(d["teachers"] for d in DISTRICT_DATA.values())
    total_schools = sum(d["schools"] for d in DISTRICT_DATA.values())
    total_students = sum(d["students"] for d in DISTRICT_DATA.values())
    avg_infra = round(sum(d["infrastructure"] for d in DISTRICT_DATA.values()) / len(DISTRICT_DATA), 1)
    critical_districts = [
        name for name, d in DISTRICT_DATA.items()
        if (d["students"] / max(d["teachers"], 1)) > 40 or d["infrastructure"] < 50
    ]
    return {
        "state": "Karnataka",
        "total_teachers": total_teachers,
        "total_schools": total_schools,
        "total_students": total_students,
        "avg_student_teacher_ratio": round(total_students / max(total_teachers, 1), 1),
        "avg_infrastructure_score": avg_infra,
        "districts_tracked": len(DISTRICT_DATA),
        "critical_districts": critical_districts,
        "critical_count": len(critical_districts),
    }


@router.post("/recommend-action", summary="AI-recommended intervention for a district")
async def recommend_action(body: dict):
    """
    Given a district name, return AI-recommended priority actions.

    Body: { "district": "Kalaburagi" }
    """
    district = body.get("district", "Kalaburagi")
    d = DISTRICT_DATA.get(district, DISTRICT_DATA["Kalaburagi"])
    ratio = round(d["students"] / max(d["teachers"], 1), 1)

    prompt = f"""
You are a Karnataka education department advisor.
District: {district}
Data: teachers={d['teachers']}, schools={d['schools']}, students={d['students']},
      infrastructure_score={d['infrastructure']}/100, digital_labs={d['digital_labs']},
      student_teacher_ratio={ratio}

Recommend the top 3 most impactful interventions for this district.
Prioritise based on severity and cost-effectiveness.

Return ONLY valid JSON:
{{
  "district": "{district}",
  "priority_score": 85,
  "recommendations": [
    {{
      "action": "...",
      "rationale": "...",
      "estimated_impact": "...",
      "timeline": "Short-term (1-3 months) / Medium-term (3-6 months) / Long-term (6+ months)",
      "estimated_cost_lakhs": 10
    }}
  ]
}}
"""
    result = await call_gemini(prompt)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(500, "Recommendation generation failed")
