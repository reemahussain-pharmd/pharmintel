# File: backend/routes/competitor.py
# Purpose: API route for competitor intelligence — brands, manufacturers, gaps
# Connects to: services/market_data.py (get_competitor_intelligence)

from fastapi import APIRouter, HTTPException
from backend.models.schemas import CompetitorRequest
from backend.services.market_data import get_competitor_intelligence

router = APIRouter()


@router.post("/competitor")
async def get_competitor_data(request: CompetitorRequest):
    """
    Return competitor brand data and Gemini competitive landscape summary.
    Data source: data/india_market_data.json + RAG literature context.
    """
    try:
        result = await get_competitor_intelligence(request.drug_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
