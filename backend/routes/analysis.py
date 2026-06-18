# File: backend/routes/analysis.py
# Purpose: NLP entity extraction + evidence classification + RAG embedding
# Connects to: services/nlp_extractor.py, services/rag_engine.py, services/evidence_classifier.py

from fastapi import APIRouter, HTTPException
from backend.models.schemas import AnalysisRequest, PaperAnalysis
from backend.services.nlp_extractor import extract_entities_batch
from backend.services.rag_engine import embed_papers, get_collection_stats
from backend.services.evidence_classifier import classify_evidence, detect_study_type

router = APIRouter()


@router.post("/analysis", response_model=list[PaperAnalysis])
async def analyze_papers(request: AnalysisRequest):
    """
    Run spaCy NLP extraction + evidence classification on all papers.
    Also embeds papers into TF-IDF RAG store for formulation reasoning.
    """
    try:
        analyses = extract_entities_batch(request.papers)

        # Enrich each analysis with evidence level and study type
        paper_map = {p.pubmed_id: p for p in request.papers}
        for analysis in analyses:
            paper = paper_map.get(analysis.pubmed_id)
            if paper:
                analysis.evidence_level = classify_evidence(paper.title, paper.abstract)
                analysis.study_type     = detect_study_type(paper.title, paper.abstract)

        # Embed papers into TF-IDF RAG store
        try:
            count = await embed_papers(request.drug_name, request.papers)
            print(f"RAG: embedded {count} new papers for {request.drug_name}")
        except Exception as e:
            print(f"RAG embedding skipped: {e}")

        return analyses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/status/{drug_name}")
async def rag_status(drug_name: str):
    """Check how many papers are embedded in the TF-IDF RAG store for a drug."""
    stats = get_collection_stats(drug_name)
    return {"drug_name": drug_name, **stats}
