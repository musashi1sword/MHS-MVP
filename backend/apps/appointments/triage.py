"""Mock AI-assisted triage. Deterministic keyword rules — clearly not a real model.

Swappable for a real inference call behind the same `run_triage` signature.
"""
from __future__ import annotations

RED_FLAGS = ["chest pain", "shortness of breath", "bleeding", "unconscious", "stroke", "seizure"]
URGENT = ["fever", "vomiting", "dehydration", "severe", "injury"]


def run_triage(symptom_note: str, intake: dict | None = None) -> dict:
    text = (symptom_note or "").lower()
    intake = intake or {}

    if any(flag in text for flag in RED_FLAGS):
        acuity, level = "emergency", 1
        recommendation = "Escalate to in-person emergency care immediately."
    elif any(word in text for word in URGENT):
        acuity, level = "urgent", 2
        recommendation = "Same-day video consult; prepare for possible referral."
    else:
        acuity, level = "routine", 3
        recommendation = "Standard video consult within same-day slot."

    duration = intake.get("duration_days")
    if isinstance(duration, (int, float)) and duration >= 14 and level == 3:
        level = 2
        acuity = "urgent"
        recommendation = "Chronic/persistent symptom — prioritise review and labs."

    return {
        "acuity": acuity,
        "priority_level": level,
        "recommendation": recommendation,
        "matched_terms": [t for t in RED_FLAGS + URGENT if t in text],
        "model": "mock-rules-v1",
    }
