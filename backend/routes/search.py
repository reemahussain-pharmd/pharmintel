# File: backend/routes/search.py
# Purpose: API route for PubMed literature search
# Connects to: services/pubmed.py (does the actual search), database/db.py (saves results)

from fastapi import APIRouter, HTTPException
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.pubmed import search_pubmed
from backend.database.db import get_db

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_literature(request: SearchRequest):
    """Search PubMed for papers about a drug and save results to Supabase."""
    try:
        results = await search_pubmed(request.drug_name, request.max_results)

        # Save search record to Supabase
        try:
            db = get_db()
            db.table("searches").insert({
                "drug_name": request.drug_name,
                "results_count": results.total_found,
            }).execute()

            # Save each paper (upsert = insert or update if already exists)
            for paper in results.papers:
                db.table("papers").upsert({
                    "pubmed_id": paper.pubmed_id,
                    "drug_name": request.drug_name,
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "journal": paper.journal,
                    "abstract": paper.abstract,
                    "url": paper.url,
                }).execute()
        except Exception:
            # Don't fail the search if saving to DB fails
            pass

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/searches/recent")
async def get_recent_searches(limit: int = 10):
    """Return the most recent drug searches from Supabase."""
    try:
        db = get_db()
        result = (
            db.table("searches")
            .select("drug_name, results_count, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"searches": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{drug_name}")
async def get_papers_for_drug(drug_name: str):
    """Return all saved papers for a drug from Supabase."""
    try:
        db = get_db()
        result = (
            db.table("papers")
            .select("*")
            .eq("drug_name", drug_name.lower())
            .order("year", desc=True)
            .execute()
        )
        return {"papers": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
