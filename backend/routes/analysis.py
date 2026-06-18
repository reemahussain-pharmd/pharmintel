# File: backend/routes/analysis.py
# Purpose: API route for spaCy NLP entity extraction + ChromaDB embedding
# Connects to: services/nlp_extractor.py, services/rag_engine.py

from fastapi import APIRouter, HTTPException
from backend.models.schemas import AnalysisRequest, PaperAnalysis
from backend.services.nlp_extractor import extract_entities_batch
from backend.services.rag_engine import embed_papers, get_collection_stats

router = APIRouter()


@router.post("/analysis", response_model=list[PaperAnalysis])
async def analyze_papers(request: AnalysisRequest):
    """
    Run spaCy NLP extraction on all papers and embed into ChromaDB for RAG.
    Extracts: dosage forms, excipients, stability conditions, development stage keywords.
    """
    try:
        analyses = extract_entities_batch(request.papers)

        # Embed papers into ChromaDB for RAG retrieval in Phase 4 and beyond
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
    """Check how many papers are embedded in ChromaDB for a drug."""
    stats = get_collection_stats(drug_name)
    return {"drug_name": drug_name, **stats}
