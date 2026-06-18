# File: backend/services/nlp_extractor.py
# Purpose: spaCy NLP pipeline to extract pharmaceutical entities from paper abstracts
# Connects to: routes/analysis.py, data/dosage_form_database.json, data/excipient_database.json
# How it works: PhraseMatcher scans abstracts for known pharmaceutical terms from our
# knowledge base — deterministic, explainable, no AI involved.

import json
import re
import os
import spacy
from spacy.matcher import PhraseMatcher
from functools import lru_cache
from backend.models.schemas import Paper, PaperAnalysis, ExtractedEntity

# ── Load knowledge base files once at startup ─────────────────────────────────
_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load_json(filename: str) -> dict:
    path = os.path.join(_BASE, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Build the spaCy NLP pipeline with PhraseMatcher ──────────────────────────
@lru_cache(maxsize=1)
def _build_nlp():
    """
    Load spaCy model and attach a PhraseMatcher for pharma entities.
    lru_cache means this runs only once — not on every paper.
    """
    nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

    dosage_db = _load_json("dosage_form_database.json")
    excipient_db = _load_json("excipient_database.json")

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    # Add dosage form synonyms from dosage_form_database.json
    for form, info in dosage_db.items():
        synonyms = info.get("synonyms", [form])
        patterns = [nlp.make_doc(s.lower()) for s in synonyms]
        label = f"DOSAGE_FORM::{form}"
        matcher.add(label, patterns)

    # Add excipient names from excipient_database.json
    for excipient_name in excipient_db.keys():
        patterns = [nlp.make_doc(excipient_name.lower())]
        matcher.add(f"EXCIPIENT::{excipient_name}", patterns)

    return nlp, matcher


# Stability condition keywords — rule-based, no ML needed
_STABILITY_PATTERNS = [
    r"\b(\d+\s*°?\s*[Cc])\b",                         # temperatures: 25°C, 40 C
    r"\b(\d+\s*%\s*(?:RH|relative humidity))\b",       # humidity: 75% RH
    r"\blight[\s-]sensitive\b",
    r"\bphotostable\b",
    r"\bmoisture[\s-]sensitive\b",
    r"\brefrigerat\w*\b",
    r"\bfreezing?\b",
    r"\broom temperature\b",
    r"\bstabilit\w+\b",
    r"\bdegradation\b",
    r"\bshelf[\s-]life\b",
    r"\bexpiry\b",
    r"\bstable\s+(?:at|for|under|in)\b",
    r"\bpH\s*[\d.]+",                                   # pH values
    r"\bhydrolysis\b",
    r"\boxidation\b",
    r"\bphotodegradation\b",
]
_STABILITY_RE = re.compile("|".join(_STABILITY_PATTERNS), re.IGNORECASE)

# Development stage keywords
_DEV_STAGE_PATTERNS = [
    r"\bphase [I|II|III|IV]\b",
    r"\bclinical trial\b",
    r"\bin vitro\b",
    r"\bin vivo\b",
    r"\bpreclinical\b",
    r"\bpilot study\b",
    r"\bformulation development\b",
    r"\boptimization\b",
    r"\bscale[\s-]up\b",
    r"\bbioavailability\b",
    r"\bbioequivalence\b",
    r"\bdissolution\b",
    r"\bpermeability\b",
    r"\bpharmacokinetics?\b",
    r"\bpharmacokinetic\b",
]
_DEV_STAGE_RE = re.compile("|".join(_DEV_STAGE_PATTERNS), re.IGNORECASE)


def extract_entities(paper: Paper) -> PaperAnalysis:
    """
    Run the full NLP extraction pipeline on a single paper abstract.
    Returns structured entity lists ready for the rule engine and frontend display.
    """
    nlp, matcher = _build_nlp()

    abstract = paper.abstract or ""
    title = paper.title or ""
    full_text = f"{title}. {abstract}"

    doc = nlp(full_text)
    matches = matcher(doc)

    entities: list[ExtractedEntity] = []
    dosage_forms: list[str] = []
    excipients: list[str] = []

    seen_labels = set()

    for match_id, start, end in matches:
        label_str = nlp.vocab.strings[match_id]   # e.g. "DOSAGE_FORM::tablet"
        span_text = doc[start:end].text

        if label_str in seen_labels:
            continue
        seen_labels.add(label_str)

        if label_str.startswith("DOSAGE_FORM::"):
            canonical = label_str.split("::")[1]
            entities.append(ExtractedEntity(text=canonical, label="DOSAGE_FORM"))
            if canonical not in dosage_forms:
                dosage_forms.append(canonical)

        elif label_str.startswith("EXCIPIENT::"):
            canonical = label_str.split("::")[1]
            entities.append(ExtractedEntity(text=canonical, label="EXCIPIENT"))
            if canonical not in excipients:
                excipients.append(canonical)

    # Extract stability conditions with regex
    stability_conditions: list[str] = []
    for match in _STABILITY_RE.finditer(full_text):
        term = match.group(0).strip()
        if term not in stability_conditions:
            stability_conditions.append(term)

    # Cap to avoid noise
    stability_conditions = stability_conditions[:8]

    # Extract development stage keywords
    dev_stages: list[str] = []
    for match in _DEV_STAGE_RE.finditer(full_text):
        term = match.group(0).strip()
        if term.lower() not in [d.lower() for d in dev_stages]:
            dev_stages.append(term)
    dev_stages = dev_stages[:6]

    # Add dev stage entities
    for stage in dev_stages:
        entities.append(ExtractedEntity(text=stage, label="DEV_STAGE"))

    return PaperAnalysis(
        pubmed_id=paper.pubmed_id,
        title=paper.title,
        entities=entities,
        dosage_forms=dosage_forms,
        excipients=excipients,
        stability_conditions=stability_conditions,
    )


def extract_entities_batch(papers: list[Paper]) -> list[PaperAnalysis]:
    """Extract entities from multiple papers."""
    return [extract_entities(paper) for paper in papers]
