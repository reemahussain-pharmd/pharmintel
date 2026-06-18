# File: backend/services/evidence_classifier.py
# Purpose: Classify PubMed papers by evidence strength based on title/abstract keywords
# Used by: analysis route, confidence scorer

HIGH_KEYWORDS = [
    "randomized controlled trial", "randomised controlled trial", "rct",
    "meta-analysis", "meta analysis", "systematic review",
    "phase iii", "phase 3", "phase ii trial", "double-blind",
    "multicenter", "multicentre", "clinical trial", "phase 2 trial",
]

MEDIUM_KEYWORDS = [
    "observational study", "cohort study", "prospective study",
    "retrospective study", "comparative study", "cross-sectional",
    "epidemiological", "population-based", "real-world",
    "pharmacovigilance", "surveillance",
]

LOW_KEYWORDS = [
    "in vitro", "in vivo", "animal study", "mouse model", "rat model",
    "murine", "cell line", "case report", "case series",
    "mechanistic", "computational", "molecular docking", "simulation",
]

STUDY_TYPE_MAP = {
    "high": [
        "Randomized Controlled Trial", "Meta-Analysis", "Systematic Review",
        "Phase III Clinical Trial", "Phase II Clinical Trial",
    ],
    "medium": [
        "Observational Study", "Cohort Study", "Comparative Study",
        "Retrospective Study", "Prospective Study",
    ],
    "low": [
        "In Vitro Study", "Animal Study", "Case Report",
        "Mechanistic Study", "Computational Study",
    ],
}


def classify_evidence(title: str, abstract: str = "") -> str:
    """Return 'high', 'medium', or 'low' based on study design keywords."""
    text = (title + " " + abstract).lower()
    for kw in HIGH_KEYWORDS:
        if kw in text:
            return "high"
    for kw in MEDIUM_KEYWORDS:
        if kw in text:
            return "medium"
    return "low"


def detect_study_type(title: str, abstract: str = "") -> str:
    """Return a human-readable study type label."""
    text = (title + " " + abstract).lower()
    if any(k in text for k in ["randomized controlled", "randomised controlled", "rct"]):
        return "Randomized Controlled Trial"
    if any(k in text for k in ["meta-analysis", "meta analysis"]):
        return "Meta-Analysis"
    if any(k in text for k in ["systematic review"]):
        return "Systematic Review"
    if any(k in text for k in ["phase iii", "phase 3 trial"]):
        return "Phase III Clinical Trial"
    if any(k in text for k in ["phase ii", "phase 2 trial"]):
        return "Phase II Clinical Trial"
    if any(k in text for k in ["cohort study", "prospective", "retrospective"]):
        return "Observational / Cohort Study"
    if any(k in text for k in ["comparative", "cross-sectional"]):
        return "Comparative Study"
    if any(k in text for k in ["in vitro"]):
        return "In Vitro Study"
    if any(k in text for k in ["animal", "mouse", "rat", "murine"]):
        return "Animal Study"
    if any(k in text for k in ["case report", "case series"]):
        return "Case Report"
    if any(k in text for k in ["review"]):
        return "Literature Review"
    return "Original Research"


def get_evidence_summary(papers: list[dict]) -> dict:
    """Aggregate evidence level counts across a list of paper dicts."""
    counts = {"high": 0, "medium": 0, "low": 0}
    for p in papers:
        level = classify_evidence(p.get("title", ""), p.get("abstract", ""))
        counts[level] += 1

    total = len(papers)
    quality_score = round(
        (counts["high"] * 3 + counts["medium"] * 1.5) / max(total * 3, 1) * 100, 1
    )

    return {
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "total": total,
        "quality_score": quality_score,
    }
