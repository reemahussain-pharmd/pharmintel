# File: backend/services/rule_engine.py
# Purpose: Deterministic scoring of dosage forms — pure Python logic, NO AI involved
# Connects to: services/formulation.py, data/formulation_rules.json, data/excipient_database.json
# ARCHITECTURE PRINCIPLE: Every score can be fully explained by the logic below.
# Claude is called AFTER scoring only to write one human-readable sentence.

import json
import os
import re
from backend.models.schemas import PaperAnalysis, FormulationScore, Paper, ScoreComponents

_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load_json(filename: str) -> dict:
    with open(os.path.join(_BASE, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def score_dosage_forms(
    drug_name: str,
    papers: list[Paper],
    analyses: list[PaperAnalysis],
) -> list[FormulationScore]:
    """
    Scores every known dosage form 0–100 using a 4-component formula:

    Score = base_score
          + frequency_score   (how often this form appears in literature)
          + booster_score     (how many supporting process/excipient keywords found)
          + excipient_score   (how many compatible excipients were identified)
          - penalty_score     (contraindication keywords in abstracts)

    Final score is clamped to 0–100.
    """
    rules_db = _load_json("formulation_rules.json")
    excipient_db = _load_json("excipient_database.json")

    total_papers = max(len(papers), 1)

    # Combine all abstract + title text for keyword scanning
    all_text = " ".join(
        (p.title or "") + " " + (p.abstract or "")
        for p in papers
    ).lower()

    # Aggregate found excipients and dosage forms across all analyses
    found_excipients: set[str] = set()
    form_paper_count: dict[str, int] = {}

    for analysis in analyses:
        for ex in analysis.excipients:
            found_excipients.add(ex.lower())
        for df in analysis.dosage_forms:
            key = df.lower()
            form_paper_count[key] = form_paper_count.get(key, 0) + 1

    scores: list[FormulationScore] = []

    for form_name, rules in rules_db.items():

        # ── Component 1: Base score (from knowledge base) ────────────────────
        base = rules.get("base_score", 30)
        weight = rules.get("weight", 1.0)

        # ── Component 2: Literature frequency score (0–25 points) ───────────
        mentions = form_paper_count.get(form_name.lower(), 0)
        # Also check synonyms from dosage_form_database
        try:
            dosage_db = _load_json("dosage_form_database.json")
            synonyms = dosage_db.get(form_name, {}).get("synonyms", [])
            for syn in synonyms:
                mentions += form_paper_count.get(syn.lower(), 0)
        except Exception:
            pass

        frequency_score = min((mentions / total_papers) * 25, 25)

        # ── Component 3: Score booster keywords (0–15 points) ────────────────
        boosters = rules.get("score_boosters", [])
        booster_hits = sum(1 for b in boosters if b.lower() in all_text)
        booster_score = min(booster_hits * 2.5, 15)

        # ── Component 4: Compatible excipient bonus (0–10 points) ────────────
        excipient_score = 0
        for ex_name, ex_info in excipient_db.items():
            compatible_forms = [f.lower() for f in ex_info.get("compatible_forms", [])]
            if ex_name.lower() in found_excipients and form_name.lower() in compatible_forms:
                contribution = ex_info.get("score_contribution", 3)
                excipient_score += contribution * 0.5

        excipient_score = min(excipient_score, 10)

        # ── Penalty: Contraindication keywords in abstracts (−10 per hit) ────
        contraindications = rules.get("contraindications", [])
        penalty = sum(5 for c in contraindications if c.lower() in all_text)
        penalty = min(penalty, 20)

        # ── Final Score ───────────────────────────────────────────────────────
        raw_score = (base + frequency_score + booster_score + excipient_score - penalty) * weight
        final_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Only include forms with a meaningful score or literature mention
        if final_score > 0 or mentions > 0:
            color = _score_to_color(final_score)
            components = ScoreComponents(
                base=round(base, 1),
                literature_frequency=round(frequency_score, 1),
                score_boosters=round(booster_score, 1),
                excipient_compatibility=round(excipient_score, 1),
                penalty=round(penalty, 1),
            )
            scores.append(
                FormulationScore(
                    dosage_form=form_name,
                    score=final_score,
                    reasoning="",
                    frequency=mentions,
                    color=color,
                    components=components,
                )
            )

    # Sort by score descending
    scores.sort(key=lambda x: x.score, reverse=True)
    return scores


def _score_to_color(score: float) -> str:
    if score >= 70:
        return "#27AE60"   # green
    elif score >= 40:
        return "#F39C12"   # orange
    else:
        return "#E74C3C"   # red


def get_score_breakdown(form_name: str, score: FormulationScore, papers: list[Paper]) -> dict:
    """Returns human-readable explanation of why a form received its score."""
    rules_db = _load_json("formulation_rules.json")
    rules = rules_db.get(form_name, {})
    return {
        "dosage_form": form_name,
        "final_score": score.score,
        "literature_mentions": score.frequency,
        "advantages": rules.get("advantages", []),
        "score_boosters": rules.get("score_boosters", []),
        "contraindications": rules.get("contraindications", []),
    }
