# File: backend/routes/formulation.py
# Purpose: API route for formulation feasibility scoring
# Connects to: services/formulation.py (orchestrates rule engine + Gemini)

from fastapi import APIRouter, HTTPException
from backend.models.schemas import FormulationRequest, FormulationResponse
from backend.services.formulation import assess_formulation

router = APIRouter()


@router.post("/formulation", response_model=FormulationResponse)
async def formulation_feasibility(request: FormulationRequest):
    """
    Score all dosage forms for a drug using the rule engine.
    Rule engine runs first (pure Python). Gemini adds one sentence per form after.
    """
    try:
        result = await assess_formulation(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
