from fastapi import APIRouter, HTTPException
from backend.services.repurposing_intel import get_repurposing_intelligence

router = APIRouter()


@router.get("/repurposing/{drug_name}")
async def get_repurposing(drug_name: str):
    """
    Returns drug repurposing intelligence:
    - Scored opportunities ranked by evidence and commercial potential
    - Mechanism of action for each opportunity
    - Clinical stage and evidence level
    - AI-generated repurposing strategy summary
    """
    try:
        result = get_repurposing_intelligence(drug_name)
        if not result.get("found"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
