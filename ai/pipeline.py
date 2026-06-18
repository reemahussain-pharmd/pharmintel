# File: ai/pipeline.py
# Purpose: Orchestrates the full AI pipeline in sequence
# Connects to: All services — this is the master coordinator
# Flow: PubMed → spaCy NLP → Rule Engine → ChromaDB RAG → Claude API

from backend.services.pubmed import search_pubmed
from backend.services.nlp_extractor import extract_entities
from backend.services.rule_engine import score_dosage_forms
from backend.services.rag_engine import embed_papers, retrieve_context
from backend.services.ai_engine import generate_text
from ai.prompts import SYSTEM_PHARMA_EXPERT, FORMULATION_REASONING_PROMPT


async def run_full_pipeline(drug_name: str, max_papers: int = 10) -> dict:
    """
    Runs the complete PharmIntel analysis pipeline.
    Each step passes structured data to the next — Claude only speaks at the end.
    """
    # Step 1: Fetch papers from PubMed
    search_result = await search_pubmed(drug_name, max_papers)

    # Step 2: Extract entities with spaCy (deterministic NLP)
    analyses = [extract_entities(paper) for paper in search_result.papers]

    # Step 3: Score dosage forms with Rule Engine (pure Python logic)
    scores = score_dosage_forms(drug_name, analyses)

    # Step 4: Embed papers into ChromaDB for RAG
    await embed_papers(drug_name, search_result.papers)

    # Step 5: Claude generates reasoning for each score (interpretation only)
    for score in scores:
        context_chunks = await retrieve_context(drug_name, score.dosage_form)
        prompt = FORMULATION_REASONING_PROMPT.format(
            drug_name=drug_name,
            dosage_form=score.dosage_form,
            score=score.score,
            frequency=score.frequency,
            excipients=", ".join([]),
        )
        score.reasoning = await generate_text(SYSTEM_PHARMA_EXPERT, prompt, max_tokens=150)

    return {
        "drug_name": drug_name,
        "papers": search_result.papers,
        "analyses": analyses,
        "scores": scores,
    }
