from fastapi import APIRouter, HTTPException
from backend.services.regulatory_intel import get_regulatory_intelligence

router = APIRouter()


@router.get("/regulatory/{drug_name}")
async def get_regulatory(drug_name: str):
    """
    Returns multi-authority regulatory intelligence for a drug:
    India (CDSCO/DCGI), USFDA, EMA, MHRA.
    Includes readiness score and AI-generated regulatory strategy.
    """
    try:
        result = get_regulatory_intelligence(drug_name)
        if not result.get("found"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
