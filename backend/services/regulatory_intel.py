import json
import os
from backend.services.ai_engine import generate_text_sync
from ai.prompts import SYSTEM_PHARMA_EXPERT

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "regulatory_data.json")

_REGULATORY_PROMPT = """You are a pharmaceutical regulatory intelligence expert specialising in India (CDSCO/DCGI), USFDA, EMA, and MHRA.

Drug: {drug_name}
Regulatory Readiness Score: {readiness_score}/100
India Status: {india_status} | Schedule: {india_schedule}
USFDA Status: {fda_status}
EMA Status: {ema_status}
MHRA Status: {mhra_status}
New Formulation Development Notes: {formulation_notes}

Write a 3-sentence regulatory strategy summary for pharmaceutical R&D teams considering new formulation development for this drug in India. Cover:
1. Regulatory pathway complexity in India
2. Cross-regulatory alignment opportunity (if any)
3. Key risk or special requirement to address
Be specific, professional, and actionable."""


def _load_regulatory_data() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_regulatory_intelligence(drug_name: str) -> dict:
    data = _load_regulatory_data()
    drug_key = drug_name.lower().strip()

    drug_data = data.get(drug_key)
    if not drug_data:
        return {
            "drug_name": drug_name,
            "found": False,
            "message": f"Regulatory data not available for {drug_name}",
        }

    india = drug_data.get("india", {})
    usfda = drug_data.get("usfda", {})
    ema = drug_data.get("ema", {})
    mhra = drug_data.get("mhra", {})

    readiness_score = drug_data.get("regulatory_readiness_score", 75)
    color = _score_to_color(readiness_score)

    prompt = _REGULATORY_PROMPT.format(
        drug_name=drug_name.title(),
        readiness_score=readiness_score,
        india_status=india.get("status", "Unknown"),
        india_schedule=india.get("schedule", "Unknown"),
        fda_status=usfda.get("status", "Unknown"),
        ema_status=ema.get("status", "Unknown"),
        mhra_status=mhra.get("status", "Unknown"),
        formulation_notes=drug_data.get("new_formulation_notes", "No specific notes."),
    )

    try:
        ai_strategy = generate_text_sync(SYSTEM_PHARMA_EXPERT, prompt, max_tokens=200)
    except Exception:
        ai_strategy = _fallback_strategy(drug_name, readiness_score, india)

    authorities = [
        {
            "name": "CDSCO / DCGI (India)",
            "status": india.get("status", "Unknown"),
            "schedule": india.get("schedule", ""),
            "approved_forms": india.get("approved_forms", []),
            "restrictions": india.get("restrictions", ""),
            "special_requirements": india.get("special_requirements", ""),
            "flag": "IN",
        },
        {
            "name": "USFDA",
            "status": usfda.get("status", "Unknown"),
            "application": usfda.get("application", ""),
            "approved_forms": usfda.get("approved_forms", []),
            "black_box_warning": usfda.get("black_box_warning", False),
            "bbw_detail": usfda.get("bbw_detail", ""),
            "otc_available": usfda.get("otc_availability", False),
            "flag": "US",
        },
        {
            "name": "EMA (European Union)",
            "status": ema.get("status", "Unknown"),
            "approved_forms": ema.get("approved_forms", []),
            "notes": ema.get("notes", ""),
            "flag": "EU",
        },
        {
            "name": "MHRA (United Kingdom)",
            "status": mhra.get("status", "Unknown"),
            "approved_forms": mhra.get("approved_forms", []),
            "notes": mhra.get("notes", ""),
            "flag": "UK",
        },
    ]

    return {
        "drug_name": drug_name.title(),
        "found": True,
        "regulatory_readiness_score": readiness_score,
        "readiness_color": color,
        "readiness_label": _score_to_label(readiness_score),
        "authorities": authorities,
        "new_formulation_notes": drug_data.get("new_formulation_notes", ""),
        "ai_regulatory_strategy": ai_strategy.strip(),
    }


def _score_to_color(score: int) -> str:
    if score >= 80:
        return "#27AE60"
    elif score >= 60:
        return "#F39C12"
    else:
        return "#E74C3C"


def _score_to_label(score: int) -> str:
    if score >= 80:
        return "High Readiness"
    elif score >= 60:
        return "Moderate Readiness"
    else:
        return "Low Readiness"


def _fallback_strategy(drug_name: str, score: int, india: dict) -> str:
    schedule = india.get("schedule", "Schedule H")
    forms = ", ".join(india.get("approved_forms", ["Tablet"]))
    return (
        f"{drug_name.title()} holds a strong regulatory position in India under {schedule}, "
        f"with existing approvals for {forms}. New formulation development can leverage the "
        f"established safety profile (regulatory readiness score: {score}/100), though a full "
        f"CTD dossier will be required for novel delivery systems. "
        f"Attention to India-specific requirements including bioequivalence data and labelling "
        f"in local languages is strongly recommended."
    )
