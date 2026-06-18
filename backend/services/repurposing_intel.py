import json
import os
from backend.services.ai_engine import generate_text_sync
from ai.prompts import SYSTEM_PHARMA_EXPERT

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "repurposing_data.json")

_REPURPOSING_PROMPT = """You are a pharmaceutical drug repurposing expert.

Drug: {drug_name}
Primary Indication: {primary_indication}
Drug Class: {drug_class}
Overall Repurposing Score: {repurposing_score}/100

Top Repurposing Opportunities:
{opportunities_text}

India Market Relevance: {india_relevance}

Write a 3-sentence executive summary of this drug's repurposing potential for a pharmaceutical R&D intelligence platform. Cover:
1. The strongest repurposing opportunity and its evidence base
2. The mechanistic rationale that supports repurposing
3. Strategic recommendation for the Indian pharmaceutical R&D context
Be specific, professional, and commercially minded."""


def _load_repurposing_data() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_repurposing_intelligence(drug_name: str) -> dict:
    data = _load_repurposing_data()
    drug_key = drug_name.lower().strip()

    drug_data = data.get(drug_key)
    if not drug_data:
        return {
            "drug_name": drug_name,
            "found": False,
            "message": f"Repurposing data not available for {drug_name}",
        }

    opportunities = drug_data.get("repurposing_opportunities", [])
    overall_score = drug_data.get("overall_repurposing_score", 50)

    # Sort opportunities by score
    sorted_opps = sorted(opportunities, key=lambda x: x.get("opportunity_score", 0), reverse=True)

    # Build text for Gemini
    opp_lines = []
    for opp in sorted_opps[:3]:
        opp_lines.append(
            f"- {opp.get('new_indication')}: Score {opp.get('opportunity_score')}/100 | "
            f"Evidence: {opp.get('evidence_level')} | Stage: {opp.get('clinical_stage')} | "
            f"Mechanism: {opp.get('mechanism', '')}"
        )
    opportunities_text = "\n".join(opp_lines)

    prompt = _REPURPOSING_PROMPT.format(
        drug_name=drug_name.title(),
        primary_indication=drug_data.get("primary_indication", ""),
        drug_class=drug_data.get("drug_class", ""),
        repurposing_score=overall_score,
        opportunities_text=opportunities_text,
        india_relevance=drug_data.get("india_market_relevance", "Not assessed"),
    )

    try:
        ai_summary = generate_text_sync(SYSTEM_PHARMA_EXPERT, prompt, max_tokens=200)
    except Exception:
        ai_summary = _fallback_summary(drug_name, sorted_opps, overall_score)

    # Add color coding to each opportunity
    enriched_opps = []
    for opp in sorted_opps:
        score = opp.get("opportunity_score", 50)
        enriched_opps.append({
            **opp,
            "color": _score_to_color(score),
            "score_label": _score_to_label(score),
            "evidence_color": _evidence_to_color(opp.get("evidence_level", "Low")),
        })

    return {
        "drug_name": drug_name.title(),
        "found": True,
        "primary_indication": drug_data.get("primary_indication", ""),
        "drug_class": drug_data.get("drug_class", ""),
        "overall_repurposing_score": overall_score,
        "repurposing_color": _score_to_color(overall_score),
        "repurposing_label": _score_to_label(overall_score),
        "opportunities": enriched_opps,
        "india_market_relevance": drug_data.get("india_market_relevance", ""),
        "ai_repurposing_summary": ai_summary.strip(),
    }


def _score_to_color(score: int) -> str:
    if score >= 75:
        return "#27AE60"
    elif score >= 50:
        return "#F39C12"
    else:
        return "#E74C3C"


def _score_to_label(score: int) -> str:
    if score >= 75:
        return "High Potential"
    elif score >= 50:
        return "Moderate Potential"
    else:
        return "Emerging / Exploratory"


def _evidence_to_color(level: str) -> str:
    mapping = {"High": "#27AE60", "Medium": "#F39C12", "Low": "#E74C3C"}
    return mapping.get(level, "#95A5A6")


def _fallback_summary(drug_name: str, opportunities: list, score: int) -> str:
    if not opportunities:
        return f"{drug_name.title()} has limited repurposing data available. Further literature review is recommended."
    top = opportunities[0]
    return (
        f"{drug_name.title()} shows its strongest repurposing potential for {top.get('new_indication')} "
        f"(Score: {top.get('opportunity_score')}/100, Evidence: {top.get('evidence_level')}), "
        f"based on the mechanism: {top.get('mechanism', 'see clinical literature')}. "
        f"With an overall repurposing score of {score}/100, this drug warrants systematic R&D evaluation "
        f"for expanded therapeutic applications in the Indian pharmaceutical market."
    )
