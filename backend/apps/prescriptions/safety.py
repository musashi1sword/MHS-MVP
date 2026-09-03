"""Allergy + drug-interaction checking — the demo's clinical safety layer.

`check_prescription_safety` returns a structured report:

    {
      "blocking": bool,          # True => prescription must not be sent without override
      "alerts": [
        {"type": "allergy"|"interaction", "severity": "...", "medication": "...",
         "detail": "...", "against": "..."}
      ],
      "checked_medications": [...],
      "patient_allergies": [...],
    }
"""
from __future__ import annotations

from .models import DrugInteraction, Medication

BLOCKING_INTERACTION_SEVERITIES = {"major", "contraindicated"}


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _allergy_hits(med: Medication, allergies: list[str]) -> list[str]:
    allergy_terms = {_norm(a) for a in allergies}
    med_terms = {_norm(med.name), _norm(med.drug_class)} | {_norm(g) for g in med.allergen_groups}
    med_terms.discard("")
    hits = []
    for term in allergy_terms:
        if not term:
            continue
        if term in med_terms or any(term in mt or mt in term for mt in med_terms):
            hits.append(term)
    return hits


def check_prescription_safety(
    medications: list[Medication],
    patient_allergies: list[str],
    concurrent_medication_names: list[str] | None = None,
) -> dict:
    concurrent = [_norm(m) for m in (concurrent_medication_names or [])]
    alerts: list[dict] = []

    # 1. Allergy checks.
    for med in medications:
        for hit in _allergy_hits(med, patient_allergies):
            alerts.append(
                {
                    "type": "allergy",
                    "severity": "contraindicated",
                    "medication": med.label,
                    "against": hit,
                    "detail": f"Patient has a documented {hit} allergy; {med.name} is cross-reactive.",
                }
            )

    # 2. Interaction checks: new meds vs each other and vs concurrent meds.
    new_names = [(_norm(m.name), _norm(m.drug_class), m) for m in medications]
    interaction_rules = list(DrugInteraction.objects.all())

    def matches(rule_side: str, name: str, drug_class: str) -> bool:
        r = _norm(rule_side)
        return r and (r == name or r == drug_class)

    universe = [(n, c, m.label) for (n, c, m) in new_names] + [(cn, cn, cn) for cn in concurrent]
    for i, (n1, c1, label1) in enumerate(universe):
        for (n2, c2, label2) in universe[i + 1 :]:
            for rule in interaction_rules:
                pair_ok = (
                    matches(rule.left, n1, c1) and matches(rule.right, n2, c2)
                ) or (matches(rule.left, n2, c2) and matches(rule.right, n1, c1))
                if pair_ok:
                    alerts.append(
                        {
                            "type": "interaction",
                            "severity": rule.severity,
                            "medication": label1,
                            "against": label2,
                            "detail": rule.description,
                        }
                    )

    blocking = any(
        a["type"] == "allergy"
        or (a["type"] == "interaction" and a["severity"] in BLOCKING_INTERACTION_SEVERITIES)
        for a in alerts
    )

    return {
        "blocking": blocking,
        "alerts": alerts,
        "checked_medications": [m.label for m in medications],
        "patient_allergies": list(patient_allergies or []),
    }
