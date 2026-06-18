# File: backend/routes/report.py
# Purpose: API route for PDF report generation and upload to Supabase Storage
# Returns base64-encoded PDF bytes so the Streamlit frontend can offer a download
# button regardless of where backend is hosted (local or Render.com)

import base64
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ReportRequest
from backend.services.formulation import generate_pdf_report

router = APIRouter()


@router.post("/report")
async def generate_report(request: ReportRequest):
    """
    Generate a 10-section consulting PDF.
    Returns JSON with base64 PDF bytes + Supabase public URL.
    The frontend decodes the bytes and serves a download button — no shared filesystem needed.
    """
    try:
        result = await generate_pdf_report(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
