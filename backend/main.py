# File: backend/main.py
# Purpose: FastAPI application entry point — registers all routes and starts the server
# Connects to: All route files in backend/routes/

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import search, analysis, market, report, competitor, formulation, regulatory, repurposing

app = FastAPI(
    title="PharmIntel API",
    description="AI-Assisted Pharmaceutical R&D Intelligence System",
    version="2.0.0",
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route modules
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(market.router, prefix="/api/v1", tags=["Market"])
app.include_router(report.router, prefix="/api/v1", tags=["Report"])
app.include_router(competitor.router, prefix="/api/v1", tags=["Competitor"])
app.include_router(formulation.router, prefix="/api/v1", tags=["Formulation"])
app.include_router(regulatory.router, prefix="/api/v1", tags=["Regulatory"])
app.include_router(repurposing.router, prefix="/api/v1", tags=["Repurposing"])


@app.get("/", tags=["Health"])
async def health_check():
    """Health check — confirms the API is running."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "PharmIntel API running v2.0",
    }
