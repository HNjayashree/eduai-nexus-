"""
routers/labs.py
Module 2 — Virtual Labs
Simulates Physics, Chemistry, and Biology experiments server-side.
Physics formulas computed without AI quota; Gemini adds explanation.

Endpoints:
  POST /api/v1/labs/explain        → Simulate a lab + explain result
  GET  /api/v1/labs/list           → All available labs
  POST /api/v1/labs/quiz           → Generate post-lab quiz questions
"""

import json
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.gemini import call_gemini

router = APIRouter(prefix="/api/v1/labs", tags=["Virtual Labs"])


# ─── Lab registry ─────────────────────────────────────────────────────────────

LABS = [
    {
        "id": "pendulum",
        "name": "Simple Pendulum",
        "subject": "Physics",
        "description": "Explore how period changes with length and gravity",
        "parameters": {"length": "Length in metres (e.g. 1.5)", "gravity": "Gravitational acceleration (e.g. 9.8)"},
    },
    {
        "id": "projectile",
        "name": "Projectile Motion",
        "subject": "Physics",
        "description": "Simulate horizontal and vertical motion under gravity",
        "parameters": {"velocity": "Initial velocity m/s", "angle": "Launch angle degrees", "gravity": "g (default 9.8)"},
    },
    {
        "id": "ohms_law",
        "name": "Ohm's Law Circuit",
        "subject": "Physics",
        "description": "Verify V = IR with adjustable voltage and resistance",
        "parameters": {"voltage": "Voltage in Volts", "resistance": "Resistance in Ohms"},
    },
    {
        "id": "titration",
        "name": "Acid-Base Titration",
        "subject": "Chemistry",
        "description": "Neutralisation reactions with pH tracking",
        "parameters": {"acid_conc": "Acid concentration mol/L", "base_conc": "Base concentration mol/L", "acid_vol": "Acid volume mL"},
    },
    {
        "id": "boyles_law",
        "name": "Boyle's Law",
        "subject": "Chemistry",
        "description": "Pressure-volume relationship at constant temperature",
        "parameters": {"pressure1": "Initial pressure atm", "volume1": "Initial volume L", "pressure2": "New pressure atm"},
    },
    {
        "id": "cell",
        "name": "Cell Division (Mitosis)",
        "subject": "Biology",
        "description": "Mitosis stages with 3D model guidance",
        "parameters": {"stage": "prophase / metaphase / anaphase / telophase"},
    },
    {
        "id": "photosynthesis",
        "name": "Photosynthesis Rate",
        "subject": "Biology",
        "description": "Effect of light intensity and CO₂ on photosynthesis",
        "parameters": {"light_intensity": "lux (0-10000)", "co2_ppm": "CO2 in ppm (e.g. 400)"},
    },
    {
        "id": "weather",
        "name": "Agriculture Weather Lab",
        "subject": "Environmental Science",
        "description": "Real weather data for farm simulation (uses Open-Meteo, no key needed)",
        "parameters": {"latitude": "Latitude", "longitude": "Longitude"},
    },
]

LAB_INDEX = {lab["id"]: lab for lab in LABS}


# ─── Server-side physics / chemistry calculators ──────────────────────────────

def _compute_physics(lab_id: str, params: dict) -> dict:
    """Pure-math computations — no AI quota used."""
    p = params

    if lab_id == "pendulum":
        L = float(p.get("length", 1.0))
        g = float(p.get("gravity", 9.8))
        T = round(2 * math.pi * math.sqrt(L / g), 4)
        return {"period_seconds": T, "formula": "T = 2π√(L/g)"}

    if lab_id == "projectile":
        v = float(p.get("velocity", 20))
        angle_deg = float(p.get("angle", 45))
        g = float(p.get("gravity", 9.8))
        angle_rad = math.radians(angle_deg)
        t_flight = round(2 * v * math.sin(angle_rad) / g, 3)
        range_m = round(v**2 * math.sin(2 * angle_rad) / g, 3)
        max_height = round((v * math.sin(angle_rad))**2 / (2 * g), 3)
        return {
            "time_of_flight_s": t_flight,
            "range_m": range_m,
            "max_height_m": max_height,
            "formula": "R = v²sin(2θ)/g",
        }

    if lab_id == "ohms_law":
        V = float(p.get("voltage", 12))
        R = float(p.get("resistance", 4))
        I = round(V / R, 4)
        return {"current_A": I, "formula": "I = V/R", "power_W": round(V * I, 4)}

    if lab_id == "titration":
        ca = float(p.get("acid_conc", 1.0))
        cb = float(p.get("base_conc", 1.0))
        va = float(p.get("acid_vol", 25.0))
        vb = round((ca * va) / cb, 2)
        return {"base_volume_needed_mL": vb, "formula": "Ca×Va = Cb×Vb", "equivalence_pH": 7.0}

    if lab_id == "boyles_law":
        p1 = float(p.get("pressure1", 1.0))
        v1 = float(p.get("volume1", 10.0))
        p2 = float(p.get("pressure2", 2.0))
        v2 = round((p1 * v1) / p2, 4)
        return {"new_volume_L": v2, "formula": "P1V1 = P2V2 (constant T)"}

    if lab_id == "photosynthesis":
        light = float(p.get("light_intensity", 5000))
        co2 = float(p.get("co2_ppm", 400))
        # Simplified Michaelis-Menten-like rate
        rate = round(min(light / 10000, 1) * min(co2 / 1000, 1) * 100, 2)
        return {"photosynthesis_rate_percent": rate, "limiting_factor": "light" if light < 5000 else "CO₂"}

    return {}


# ─── Request models ───────────────────────────────────────────────────────────

class LabRequest(BaseModel):
    lab: str
    parameters: dict = {}

class LabQuizRequest(BaseModel):
    lab: str
    grade_level: str = "Class 9"
    num_questions: int = 3


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/explain", summary="Run a virtual lab simulation with AI explanation")
async def explain_lab(req: LabRequest):
    """
    Compute physics/chemistry result server-side (no AI quota),
    then ask Gemini for a student-friendly explanation.

    Returns:
        { "explanation": "...", "formula": "...", "fun_fact": "...", ...computed fields }
    """
    if req.lab not in LAB_INDEX:
        raise HTTPException(400, detail=f"Unknown lab '{req.lab}'. Call GET /api/v1/labs/list for options.")

    physics = _compute_physics(req.lab, req.parameters)
    lab_meta = LAB_INDEX[req.lab]

    prompt = f"""
Explain what is happening in a "{lab_meta['name']}" simulation.
Subject: {lab_meta['subject']}
Parameters the student set: {req.parameters}
Computed result: {physics}

Write for a Class 9 Indian student. Keep under 120 words.
Mention real-world uses in India where relevant.

Return ONLY valid JSON:
{{
  "explanation": "...",
  "formula": "...",
  "fun_fact": "...",
  "safety_note": "Lab safety tip (if applicable)"
}}
"""
    raw = await call_gemini(prompt)
    try:
        data = json.loads(raw)
        data.update(physics)   # Merge computed numbers into response
        return data
    except json.JSONDecodeError:
        return {"explanation": raw, **physics}


@router.get("/list", summary="List all available virtual labs")
async def list_labs():
    """Returns the full catalogue of available virtual labs."""
    return {"labs": LABS, "total": len(LABS)}


@router.post("/quiz", summary="Generate a post-lab quiz")
async def lab_quiz(req: LabQuizRequest):
    """
    Generate short-answer / MCQ questions based on a completed lab.

    Returns:
        { "questions": [ { "question": "...", "answer": "..." } ] }
    """
    if req.lab not in LAB_INDEX:
        raise HTTPException(400, detail=f"Unknown lab '{req.lab}'.")

    lab_meta = LAB_INDEX[req.lab]
    prompt = f"""
Generate {req.num_questions} post-lab questions for the "{lab_meta['name']}" experiment
for a {req.grade_level} student.
Mix factual recall and conceptual understanding questions.

Return ONLY valid JSON:
{{
  "lab": "{lab_meta['name']}",
  "questions": [
    {{"question": "...", "type": "MCQ or short-answer", "answer": "..."}}
  ]
}}
"""
    raw = await call_gemini(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(500, "Failed to parse quiz response")
