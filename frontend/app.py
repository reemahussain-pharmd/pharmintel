# File: frontend/app.py
# Purpose: PharmIntel home page — hero, pipeline visual, feature cards, API status
# Connects to: backend main.py (health check), all frontend pages via sidebar

import sys
import os
# Ensure repo root is in path so 'frontend.components' can be found on Streamlit Cloud
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="PharmIntel — Pharmaceutical R&D Intelligence",
    page_icon="⚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='background:linear-gradient(135deg, #1B3A6B 0%, #2E5FA3 60%, #1B3A6B 100%);
                border-radius:14px; padding:3rem 2rem 2.5rem 2rem;
                text-align:center; margin-bottom:1.5rem;'>
        <div style='font-size:3.5rem; margin-bottom:0.3rem;'>⚗</div>
        <h1 style='color:white; font-size:2.8rem; font-weight:900;
                   letter-spacing:-1px; margin:0 0 0.5rem 0;'>PharmIntel</h1>
        <p style='color:#C8D8F0; font-size:1.15rem; max-width:600px;
                  margin:0 auto 1.5rem auto; line-height:1.6;'>
            AI-Assisted Pharmaceutical R&amp;D Intelligence System
        </p>
        <div style='display:flex; justify-content:center; gap:1rem; flex-wrap:wrap;'>
            <span style='background:rgba(255,255,255,0.15); color:white; padding:5px 14px;
                         border-radius:20px; font-size:0.82rem;'>spaCy NLP</span>
            <span style='background:rgba(255,255,255,0.15); color:white; padding:5px 14px;
                         border-radius:20px; font-size:0.82rem;'>Rule Engine</span>
            <span style='background:rgba(255,255,255,0.15); color:white; padding:5px 14px;
                         border-radius:20px; font-size:0.82rem;'>TF-IDF RAG</span>
            <span style='background:rgba(255,255,255,0.15); color:white; padding:5px 14px;
                         border-radius:20px; font-size:0.82rem;'>Gemini AI</span>
            <span style='background:rgba(255,255,255,0.15); color:white; padding:5px 14px;
                         border-radius:20px; font-size:0.82rem;'>India Market</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── API Status (with cold-start wakeup) ──────────────────────────────────────
def _check_backend(timeout: int) -> tuple[bool, str]:
    try:
        resp = requests.get(f"{BACKEND_URL}/", timeout=timeout)
        if resp.status_code == 200:
            return True, resp.json().get("message", "PharmIntel API running")
        return False, f"Status {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except requests.exceptions.ConnectionError:
        return False, "offline"
    except Exception as e:
        return False, str(e)

# Fast check first (2s) — if already warm this completes immediately
ok, msg = _check_backend(timeout=2)

if ok:
    st.success(f"Backend connected — {msg}")
else:
    # Render free tier cold start: show wakeup banner and retry with long timeout
    wakeup_placeholder = st.empty()
    wakeup_placeholder.markdown(
        "<div style='background:#FFF3CD;border:1px solid #FFEAA7;border-radius:8px;"
        "padding:12px 16px;color:#856404;'>"
        "⏳ <b>Backend is waking up</b> — Render free tier sleeps after 15 min of inactivity. "
        "This takes <b>20–40 seconds</b> on first visit. Please wait…</div>",
        unsafe_allow_html=True,
    )
    with st.spinner("Waking up backend server…"):
        ok2, msg2 = _check_backend(timeout=55)

    wakeup_placeholder.empty()
    if ok2:
        st.success(f"Backend connected — {msg2}")
    else:
        st.warning(
            "Backend is still starting up. "
            "**Refresh this page in 30 seconds** — it will be ready. "
            "This only happens on the very first visit after inactivity."
        )

st.divider()

# ── Pipeline Flow ─────────────────────────────────────────────────────────────
st.markdown("### How PharmIntel Works")

steps = [
    ("🔍", "Search",      "PubMed API fetches peer-reviewed papers for any drug"),
    ("🧬", "Extract",     "spaCy NLP identifies dosage forms, excipients, stability data"),
    ("💊", "Score",       "Rule engine rates each dosage form 0–100 (no AI guessing)"),
    ("🤖", "Interpret",   "Gemini AI writes professional reasoning using RAG context"),
    ("📊", "Market",      "Indian market gaps, brands & CDSCO regulatory data"),
    ("📄", "Report",      "12-section consulting-grade PDF — instant download"),
]

cols = st.columns(len(steps))
for i, (icon, title, desc) in enumerate(steps):
    with cols[i]:
        connector = "→" if i < len(steps) - 1 else ""
        st.markdown(
            f"""
            <div style='background:#F8F9FF; border:1px solid #DDE3F0; border-radius:10px;
                        padding:1.1rem 0.8rem; text-align:center; min-height:130px;
                        border-top:3px solid #1B3A6B;'>
                <div style='font-size:1.6rem;'>{icon}</div>
                <div style='font-weight:700; color:#1B3A6B; font-size:0.9rem;
                            margin:4px 0;'>{title}</div>
                <div style='color:#666; font-size:0.78rem; line-height:1.4;'>{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Feature Cards ─────────────────────────────────────────────────────────────
st.markdown("### What You Can Do")

c1, c2, c3 = st.columns(3)

cards = [
    (c1, "#1B3A6B", [
        ("🔍 Literature Search",
         "Search PubMed's 36 million papers. Get top peer-reviewed results with abstracts, authors, and direct links."),
        ("📊 Indian Market Intelligence",
         "CDSCO-approved forms, major brands, market gaps, and R&D opportunities for the Indian market."),
    ]),
    (c2, "#27AE60", [
        ("🧬 NLP Entity Extraction",
         "spaCy + PhraseMatcher identifies pharmaceutical entities in every abstract automatically."),
        ("🏢 Competitor Intelligence",
         "Map brands, Indian manufacturers, dosage forms, and find differentiation opportunities."),
    ]),
    (c3, "#F39C12", [
        ("💊 Formulation Feasibility",
         "Deterministic rule engine scores all dosage forms using literature + excipient compatibility."),
        ("📄 PDF Report Generation",
         "10-section consulting-grade report with market data, scores, and AI reasoning — downloadable PDF."),
    ]),
]

for col, border_color, items in cards:
    with col:
        for title, desc in items:
            st.markdown(
                f"""
                <div style='background:#F8F9FF; border-left:4px solid {border_color};
                            padding:1.1rem; border-radius:6px; min-height:110px;
                            margin-bottom:0.8rem;'>
                    <div style='font-weight:700; color:#1A1A2E; font-size:0.95rem;
                                margin-bottom:5px;'>{title}</div>
                    <div style='color:#555; font-size:0.87rem; line-height:1.5;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# ── Quick Start Guide ─────────────────────────────────────────────────────────
st.markdown("### Quick Start")

col_qs, col_drugs = st.columns([3, 2])

with col_qs:
    st.markdown(
        """
        1. Click **Literature Search** in the sidebar
        2. Enter a drug name and click Search PubMed
        3. Go to **NLP Analysis** → click Run NLP Extraction
        4. Go to **Formulation Feasibility** → click Run Formulation Scoring
        5. Optionally visit **Market** and **Competitor** pages
        6. Go to **Generate Report** → download your PDF
        """
    )

with col_drugs:
    st.markdown("**Try these drugs:**")
    demo_drugs = ["metformin", "atorvastatin", "amlodipine", "omeprazole",
                  "paracetamol", "azithromycin"]
    tag_html = " ".join([
        f"<span style='background:#1B3A6B; color:white; padding:4px 12px; "
        f"border-radius:14px; font-size:0.82rem; margin:3px; display:inline-block;'>"
        f"{d.title()}</span>"
        for d in demo_drugs
    ])
    st.markdown(tag_html, unsafe_allow_html=True)
    st.caption("All 10 drugs have full Indian market data in our database.")

st.divider()

# ── Architecture Note ─────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='background:#F0F4FF; border-radius:8px; padding:1.2rem 1.5rem;'>
        <div style='color:#1B3A6B; font-weight:700; margin-bottom:6px;'>
            Architecture Transparency
        </div>
        <div style='color:#444; font-size:0.88rem; line-height:1.6;'>
            PharmIntel uses a <strong>hybrid AI pipeline</strong>: NLP and scoring are
            100% deterministic Python — no AI guessing involved.
            Gemini AI is used only to write professional explanatory text after the
            rule engine has already computed the scores.
            This ensures reproducible, auditable pharmaceutical analysis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style='text-align:center; padding:1rem 0 0 0;'>
        <span style='color:#AAA; font-size:0.8rem;'>
            Built with FastAPI · spaCy · ReportLab · Supabase · Streamlit
            &nbsp;|&nbsp; India Market Focus | CDSCO/DCGI
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)
