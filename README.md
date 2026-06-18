# PharmIntel v2.0 — AI-Assisted Pharmaceutical R&D Intelligence System

A professional pharmaceutical intelligence platform that transforms PubMed literature into structured, evidence-graded R&D decision support — covering formulation feasibility, market intelligence, regulatory status, and drug repurposing.

**Live Demo:** [pharmintel-ai.streamlit.app](https://pharmintel-ai.streamlit.app)  
**API:** [pharmintel.onrender.com](https://pharmintel.onrender.com)

---

## What It Does

PharmIntel takes a drug name and produces a full pharmaceutical intelligence report in under 2 minutes:

1. **Searches PubMed** — retrieves peer-reviewed literature (up to 20 papers per query)
2. **Runs NLP extraction** — spaCy identifies dosage forms, excipients, stability conditions
3. **Grades evidence** — classifies each paper as High / Medium / Low evidence
4. **Scores formulations** — deterministic rule engine (no AI guessing) scores every dosage form 0–100
5. **Calculates confidence** — 4-component confidence score per recommendation
6. **Analyses the market** — Indian pharma market context, SWOT, opportunity gaps
7. **Maps competitors** — brand landscape, market share, differentiation opportunities
8. **Assesses regulations** — CDSCO/DCGI, USFDA, EMA, MHRA status for each drug
9. **Identifies repurposing** — evidence-ranked new therapeutic applications
10. **Generates a PDF** — 12-section consulting-grade intelligence report

---

## Architecture

```
PubMed API
    ↓
spaCy NLP (en_core_web_sm + PhraseMatcher)
    ↓
Evidence Classifier (HIGH / MEDIUM / LOW)
    ↓
Rule Engine (deterministic 4-component scoring)
    ↓
Confidence Scorer (literature + evidence + score + volume)
    ↓
TF-IDF RAG (custom in-memory, no external vector DB)
    ↓
Gemini AI (gemini-2.0-flash via REST — interpretation only, not scoring)
    ↓
ReportLab PDF (12-section consulting report)
    ↓
Supabase (PostgreSQL + Storage)
```

**Key principle:** All scores are deterministic and explainable. Gemini is used only to write professional language interpretation — it never generates numbers.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (multipage) |
| Backend | FastAPI + Uvicorn |
| NLP | spaCy `en_core_web_sm` + PhraseMatcher |
| Rule Engine | Custom Python (4-component formulation scoring) |
| Evidence Grading | Keyword-based classifier (deterministic) |
| RAG | Custom TF-IDF (in-memory, cosine similarity) |
| AI Interpretation | Google Gemini 2.0 Flash (REST API) |
| Literature Search | PubMed / NCBI Entrez (Biopython) |
| PDF Generation | ReportLab |
| Database | Supabase (PostgreSQL + Storage) |
| Visualisations | Plotly |
| Backend Hosting | Render.com |
| Frontend Hosting | Streamlit Community Cloud |

---

## Project Structure

```
pharmintel/
├── backend/
│   ├── main.py                    # FastAPI app, route registration
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   ├── routes/
│   │   ├── search.py              # PubMed search endpoint
│   │   ├── analysis.py            # NLP analysis endpoint
│   │   ├── formulation.py         # Formulation scoring endpoint
│   │   ├── market.py              # Market intelligence endpoint
│   │   ├── competitor.py          # Competitor analysis endpoint
│   │   ├── regulatory.py          # Regulatory intelligence endpoint
│   │   ├── repurposing.py         # Drug repurposing endpoint
│   │   └── report.py              # PDF report generation endpoint
│   ├── services/
│   │   ├── nlp_extractor.py       # spaCy entity extraction
│   │   ├── evidence_classifier.py # HIGH/MEDIUM/LOW evidence grading
│   │   ├── rule_engine.py         # Deterministic formulation scoring
│   │   ├── confidence_scorer.py   # 4-component confidence calculation
│   │   ├── rag_engine.py          # TF-IDF RAG retrieval
│   │   ├── ai_engine.py           # Gemini REST calls
│   │   ├── formulation.py         # Formulation pipeline orchestrator
│   │   ├── market_data.py         # Market + competitor intelligence
│   │   ├── regulatory_intel.py    # Regulatory status service
│   │   ├── repurposing_intel.py   # Repurposing opportunities service
│   │   └── pdf_generator.py       # 12-section ReportLab PDF
│   └── database/
│       └── db.py                  # Supabase client
├── frontend/
│   ├── app.py                     # Streamlit entry point (hero page)
│   ├── components/
│   │   └── sidebar.py             # Shared sidebar + workflow tracker
│   └── pages/
│       ├── 1_Search.py            # Literature search + analytics
│       ├── 2_Analysis.py          # NLP analysis + evidence dashboard
│       ├── 3_Formulation.py       # Formulation scoring + radar chart
│       ├── 4_Market.py            # Market intelligence + SWOT
│       ├── 5_Competitor.py        # Competitor matrix + quadrant
│       ├── 6_Report.py            # PDF report generation
│       ├── 7_Regulatory.py        # Regulatory intelligence
│       └── 8_Repurposing.py       # Drug repurposing opportunities
├── data/
│   ├── india_market_data.json     # 10 drugs × Indian market data
│   ├── formulation_rules.json     # Rule engine knowledge base
│   ├── excipient_database.json    # Excipient compatibility database
│   ├── dosage_form_database.json  # Dosage form synonyms
│   ├── regulatory_data.json       # 10 drugs × CDSCO/USFDA/EMA/MHRA
│   └── repurposing_data.json      # 10 drugs × repurposing opportunities
├── ai/
│   └── prompts.py                 # Gemini prompt templates
├── requirements.txt
├── render.yaml                    # Render.com deployment config
└── .streamlit/
    └── config.toml                # Streamlit theme config
```

---

## Supported Drugs (v2.0)

| Drug | Class | Primary Indication |
|---|---|---|
| Metformin | Biguanide | Type 2 Diabetes |
| Amlodipine | Calcium Channel Blocker | Hypertension |
| Atorvastatin | Statin | Hypercholesterolaemia |
| Omeprazole | Proton Pump Inhibitor | GERD / Peptic Ulcer |
| Lisinopril | ACE Inhibitor | Hypertension / Heart Failure |
| Paracetamol | Analgesic / Antipyretic | Pain / Fever |
| Azithromycin | Macrolide Antibiotic | Respiratory Infections |
| Pantoprazole | Proton Pump Inhibitor | GERD / Stress Ulcer |
| Cetirizine | Antihistamine | Allergic Rhinitis |
| Rosuvastatin | Statin | Cardiovascular Risk |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/api/v1/search` | PubMed literature search |
| `POST` | `/api/v1/analysis` | NLP entity extraction + evidence grading |
| `POST` | `/api/v1/formulation` | Formulation feasibility scoring |
| `POST` | `/api/v1/market` | Indian market intelligence |
| `POST` | `/api/v1/competitor` | Competitor landscape analysis |
| `GET` | `/api/v1/regulatory/{drug}` | Regulatory intelligence (4 authorities) |
| `GET` | `/api/v1/repurposing/{drug}` | Drug repurposing opportunities |
| `POST` | `/api/v1/report` | Generate 12-section PDF report |

---

## PDF Report Structure (12 Sections)

1. Executive Intelligence Dashboard — KPI cards (top form, confidence, evidence quality, competition level, regulatory readiness, repurposing score)
2. Drug Overview — regulatory classification, approved forms, scheduling
3. Literature Findings & Evidence Grading — per-paper evidence table (HIGH/MEDIUM/LOW)
4. Pharmaceutical Entity Intelligence — delivery technologies, excipient landscape, stability data
5. Dosage Form Feasibility & Confidence Scoring — rule engine scores + confidence + component breakdown
6. Excipient Compatibility Analysis — excipient roles and compatible dosage forms
7. Indian Market Intelligence — market context, SWOT, attractiveness score, formulation gaps
8. Competitor Intelligence — brand matrix, market share, differentiation strategy
9. Regulatory Intelligence — CDSCO/USFDA/EMA/MHRA status table
10. Drug Repurposing Opportunities — scored pipeline with evidence levels
11. R&D Recommendations — consolidated strategic recommendations
12. Methodology & Disclaimer — full pipeline description, data sources

---

## Scoring Methodology

### Formulation Feasibility Score (0–100)
```
Score = (base_score
       + literature_frequency_score   [0–25]
       + booster_keyword_score        [0–15]
       + excipient_compatibility_score [0–10]
       − penalty_score)               [0–20]
       × weight
```
Clamped to 0–100. No AI involved in scoring.

### Confidence Score (0–100)
```
Confidence = literature_frequency_component  [0–30]
           + evidence_strength_component     [0–35]
           + score_alignment_component       [0–20]
           + data_volume_component           [0–15]
```

### Evidence Grading
- **High:** RCT, meta-analysis, systematic review, Phase III trial
- **Medium:** Cohort study, observational study, prospective study
- **Low:** In vitro, animal study, case report

---

## Local Setup

```bash
# Clone
git clone https://github.com/reemahussain-pharmd/pharmintel.git
cd pharmintel

# Install dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# Set environment variables
cp .env.example .env
# Fill in: GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, PUBMED_EMAIL

# Start backend
uvicorn backend.main:app --reload

# Start frontend (new terminal)
streamlit run frontend/app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `PUBMED_EMAIL` | Email for NCBI Entrez API (required by NCBI) |
| `BACKEND_URL` | FastAPI backend URL (for frontend) |

---

## About

Built by **Reema Hussain** — PharmD + AI Expert  
Targeting pharmaceutical R&D analytics, clinical data analytics, and healthcare AI roles.

This project demonstrates end-to-end pharmaceutical intelligence engineering:
- Domain knowledge (pharmaceutical formulation, regulatory affairs, market analysis)
- AI/ML pipeline design (NLP, RAG, rule engines, LLM integration)
- Full-stack development (FastAPI backend, Streamlit frontend, cloud deployment)
- Consulting-grade output (evidence-graded, confidence-scored, explainable recommendations)

---

*PharmIntel is a portfolio and research project. All recommendations are for R&D intelligence purposes only and do not constitute regulatory advice.*
