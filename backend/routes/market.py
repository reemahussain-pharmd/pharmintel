# File: backend/routes/market.py
# Purpose: API route for Indian pharmaceutical market intelligence
# Connects to: services/market_data.py

from fastapi import APIRouter, HTTPException
from backend.models.schemas import MarketRequest
from backend.services.market_data import get_market_intelligence

router = APIRouter()


@router.post("/market")
async def get_market_data(request: MarketRequest):
    """
    Return Indian market data and Gemini-generated market intelligence for a drug.
    Data source: data/india_market_data.json + RAG literature context.
    """
    try:
        result = await get_market_intelligence(request.drug_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
