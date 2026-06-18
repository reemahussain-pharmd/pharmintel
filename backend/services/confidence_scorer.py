# File: backend/services/confidence_scorer.py
# Purpose: Calculate confidence scores (0-100) for formulation recommendations
# Formula: frequency + evidence strength + score alignment + data volume
# Used by: formulation service, analysis route

from backend.services.evidence_classifier import classify_evidence


def calculate_formulation_confidence(
    frequency: int,
    total_papers: int,
    rule_score: float,
    paper_titles: list[str] | None = None,
    paper_abstracts: list[str] | None = None,
) -> dict:
    """
    Returns confidence dict with overall score, label, and component breakdown.

    Components:
    - Literature Frequency  (0-30): how often this form appears in literature
    - Evidence Strength     (0-35): quality of supporting studies
    - Score Alignment       (0-20): how high the rule engine scored it
    - Data Volume           (0-15): how many total papers were analysed
    """
    paper_titles    = paper_titles or []
    paper_abstracts = paper_abstracts or []

    # ── Frequency component ───────────────────────────────────────────────────
    if total_papers > 0:
        freq_pct = frequency / total_papers
        frequency_component = min(30, freq_pct * 30 + (5 if frequency >= 2 else 0))
    else:
        frequency_component = 0.0

    # ── Evidence strength component ───────────────────────────────────────────
    high_count = 0
    med_count  = 0
    for title, abstract in zip(paper_titles, paper_abstracts):
        level = classify_evidence(title, abstract)
        if level == "high":
            high_count += 1
        elif level == "medium":
            med_count += 1

    evidence_component = min(35, high_count * 10 + med_count * 4)

    # ── Score alignment component ─────────────────────────────────────────────
    score_component = min(20, rule_score * 0.2)

    # ── Data volume component ─────────────────────────────────────────────────
    volume_component = min(15, total_papers * 1.5)

    total = frequency_component + evidence_component + score_component + volume_component
    confidence = round(min(100.0, total), 1)

    if confidence >= 75:
        level_label = "High"
        color       = "#27AE60"
    elif confidence >= 50:
        level_label = "Moderate"
        color       = "#F39C12"
    else:
        level_label = "Low"
        color       = "#E74C3C"

    return {
        "score":  confidence,
        "level":  level_label,
        "color":  color,
        "components": {
            "literature_frequency": round(frequency_component, 1),
            "evidence_strength":    round(evidence_component, 1),
            "score_alignment":      round(score_component, 1),
            "data_volume":          round(volume_component, 1),
        },
    }


def calculate_overall_platform_confidence(
    total_papers: int,
    evidence_summary: dict,
    top_score: float,
) -> dict:
    """
    Platform-level confidence score shown in the Executive Summary.
    Combines evidence quality, paper volume, and recommendation strength.
    """
    quality_score = evidence_summary.get("quality_score", 50)
    volume_score  = min(30, total_papers * 3)
    rec_score     = min(25, top_score * 0.25)

    total = round(min(100, quality_score * 0.45 + volume_score + rec_score), 1)

    if total >= 75:
        label = "High Confidence"
    elif total >= 50:
        label = "Moderate Confidence"
    else:
        label = "Low Confidence — Gather More Evidence"

    return {"score": total, "label": label}
