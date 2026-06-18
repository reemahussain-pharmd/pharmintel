# File: backend/models/schemas.py
# Purpose: Pydantic data models — defines the shape of all data going in/out of the API
# Connects to: All routes and services (they import these models for validation)
# Simple explanation: Pydantic models are like forms — they enforce that data has the right fields and types

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SearchRequest(BaseModel):
    drug_name: str
    max_results: int = 10


class Paper(BaseModel):
    pubmed_id: str
    title: str
    authors: str
    year: Optional[int] = None
    journal: str
    abstract: str
    url: str


class SearchResponse(BaseModel):
    drug_name: str
    papers: list[Paper]
    total_found: int


class AnalysisRequest(BaseModel):
    drug_name: str
    papers: list[Paper]


class ExtractedEntity(BaseModel):
    text: str
    label: str


class PaperAnalysis(BaseModel):
    pubmed_id: str
    title: str
    entities: list[ExtractedEntity]
    dosage_forms: list[str]
    excipients: list[str]
    stability_conditions: list[str]
    evidence_level: Optional[str] = "low"      # "high" | "medium" | "low"
    study_type: Optional[str] = "Original Research"


class ScoreComponents(BaseModel):
    base: float = 0.0
    literature_frequency: float = 0.0
    score_boosters: float = 0.0
    excipient_compatibility: float = 0.0
    penalty: float = 0.0


class ConfidenceScore(BaseModel):
    score: float = 0.0
    level: str = "Low"
    color: str = "#E74C3C"


class FormulationScore(BaseModel):
    dosage_form: str
    score: float
    reasoning: str
    frequency: int
    color: str
    components: Optional[ScoreComponents] = None
    confidence: Optional[ConfidenceScore] = None


class FormulationRequest(BaseModel):
    drug_name: str
    papers: list[Paper]
    paper_analyses: list[PaperAnalysis]


class FormulationResponse(BaseModel):
    drug_name: str
    scores: list[FormulationScore]
    top_recommendation: str
    rag_sources: list[str]


class MarketRequest(BaseModel):
    drug_name: str


class CompetitorRequest(BaseModel):
    drug_name: str


class ReportRequest(BaseModel):
    drug_name: str
    search_response: SearchResponse
    paper_analyses: list[PaperAnalysis]
    formulation_response: FormulationResponse
    market_data: Optional[dict] = None
    competitor_data: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    message: str
