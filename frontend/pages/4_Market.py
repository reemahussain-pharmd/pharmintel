# File: frontend/pages/4_Market.py
# Purpose: Indian Market Intelligence dashboard — brands, gaps, regulatory context, Gemini insight
# Connects to: backend POST /api/v1/market

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Indian Market Intelligence — PharmIntel",
    page_icon="📊",
    layout="wide",
)

render_sidebar()

st.title("📊 Indian Market Intelligence")
st.markdown(
    "Structured market analysis for the Indian pharmaceutical market — "
    "approved forms, major brands, CDSCO regulatory context, and R&D opportunity gaps."
)

st.divider()

# ── Drug Input ────────────────────────────────────────────────────────────────
drug_name = st.session_state.get("last_search_drug", "")

col1, col2 = st.columns([4, 1])
with col1:
    drug_input = st.text_input(
        "Drug name",
        value=drug_name,
        placeholder="e.g. metformin, amlodipine, omeprazole",
        label_visibility="collapsed",
    )
with col2:
    analyse_btn = st.button("Analyse Market", type="primary", use_container_width=True)

# ── Quick drug buttons ────────────────────────────────────────────────────────
st.markdown("**Quick select:**")
quick_drugs = ["metformin", "amlodipine", "atorvastatin", "omeprazole",
               "paracetamol", "azithromycin", "pantoprazole", "rosuvastatin"]
cols = st.columns(len(quick_drugs))
for i, d in enumerate(quick_drugs):
    with cols[i]:
        if st.button(d.title(), key=f"quick_market_{d}", use_container_width=True):
            drug_input = d
            analyse_btn = True

st.divider()

# ── Fetch Market Data ─────────────────────────────────────────────────────────
if analyse_btn and drug_input.strip():
    with st.spinner(f"Analysing Indian market for {drug_input.title()}..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/market",
                json={"drug_name": drug_input.strip().lower()},
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["market_data"] = data
                st.session_state["market_drug"] = drug_input.strip().lower()
            else:
                st.error(f"Market analysis failed: {response.status_code}")
                st.stop()
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend. Make sure `uvicorn backend.main:app --reload` is running.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Display Results ───────────────────────────────────────────────────────────
data = st.session_state.get("market_data")
current_drug = st.session_state.get("market_drug", "")

if data:
    drug_title = current_drug.title()
    found = data.get("found_in_database", False)

    # ── Header metrics ────────────────────────────────────────────────────────
    st.markdown(f"## {drug_title} — Indian Market Overview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Market Size", f"${data.get('market_size_usd_billion', 50)}B", "Indian Pharma")
    m2.metric("Approved Forms", len(data.get("approved_forms", [])))
    m3.metric("Major Brands", len(data.get("major_brands", [])))
    m4.metric("Market Gaps", len(data.get("market_gaps", [])))

    st.divider()

    # ── Regulatory Authority ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style='background:#1B3A6B; color:white; padding:0.8rem 1.2rem;
                    border-radius:8px; margin-bottom:1rem;'>
            <strong>Regulatory Authority:</strong> {data.get('regulatory_authority', 'CDSCO')}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <strong>Registration Body:</strong> {data.get('registration_body', 'DCGI')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Two-column layout: Market Data + Gaps ─────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Approved Dosage Forms in India")
        approved = data.get("approved_forms", [])
        if approved:
            for form in approved:
                st.markdown(
                    f"<span style='background:#27AE60; color:white; padding:4px 12px; "
                    f"border-radius:12px; font-size:0.85rem; margin:3px; display:inline-block;'>"
                    f"✓ {form.title()}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No approved forms data available for this drug.")

        st.markdown("### Major Brands")
        brands = data.get("major_brands", [])
        dominant = data.get("dominant_manufacturer", "")
        if brands:
            for brand in brands:
                is_dominant = dominant and brand.lower() in dominant.lower()
                badge = "👑 " if is_dominant else ""
                st.markdown(
                    f"<span style='background:#1B3A6B; color:white; padding:4px 12px; "
                    f"border-radius:12px; font-size:0.85rem; margin:3px; display:inline-block;'>"
                    f"{badge}{brand}</span>",
                    unsafe_allow_html=True,
                )
            if dominant:
                st.caption(f"👑 Market leader: {dominant}")
        else:
            st.caption("No brand data available.")

        if data.get("approximate_price_inr"):
            st.markdown(f"**Price Range (India):** {data['approximate_price_inr']}")

        if data.get("therapeutic_class"):
            st.markdown(f"**Therapeutic Class:** {data['therapeutic_class']}")

    with col_right:
        st.markdown("### R&D Opportunity Gaps")
        gaps = data.get("market_gaps", [])
        if gaps:
            for gap in gaps:
                st.markdown(
                    f"""
                    <div style='background:#FFF3CD; border-left:4px solid #F39C12;
                                padding:8px 12px; margin:6px 0; border-radius:4px;
                                font-size:0.88rem;'>
                        🔬 {gap}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No gap data available.")

        st.markdown("### Indian Manufacturers")
        manufacturers = data.get("local_manufacturers", [])
        if manufacturers:
            for mfr in manufacturers:
                st.markdown(
                    f"<span style='background:#8E44AD; color:white; padding:4px 10px; "
                    f"border-radius:12px; font-size:0.82rem; margin:3px; display:inline-block;'>"
                    f"🏭 {mfr}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No local manufacturer data available.")

    st.divider()

    # ── Market Notes ──────────────────────────────────────────────────────────
    notes = data.get("market_notes", "")
    if notes:
        st.markdown("### Market Context")
        st.info(notes)

    # ── Gemini AI Market Intelligence ─────────────────────────────────────────
    st.markdown("### 🤖 AI Market Intelligence")
    ai_insight = data.get("ai_market_insight", "")
    if ai_insight:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #F8F9FF, #EEF2FF);
                        border-left: 4px solid #1B3A6B; padding: 1.2rem 1.5rem;
                        border-radius: 8px; margin: 0.5rem 0;'>
                <p style='color: #1A1A2E; font-size: 0.95rem; line-height: 1.7;
                           margin: 0;'>{ai_insight}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("AI insight not available.")

    # ── RAG Sources ───────────────────────────────────────────────────────────
    rag_sources = data.get("rag_sources_used", [])
    if rag_sources:
        st.markdown("#### 📚 Literature Sources Used")
        for src in rag_sources:
            if src:
                st.markdown(
                    f"<div style='background:#F0F4FF; border-left:3px solid #1B3A6B; "
                    f"padding:5px 10px; margin:3px 0; border-radius:3px; font-size:0.82rem;'>"
                    f"📄 {src}</div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Market Characteristics ────────────────────────────────────────────────
    chars = data.get("market_characteristics", [])
    if chars:
        with st.expander("📌 Indian Pharma Market Characteristics"):
            for c in chars:
                st.markdown(f"- {c}")

    st.info(
        "Market analysis complete. Go to **Competitor Intelligence** for brand-level "
        "competitive analysis, or **Generate Report** to create a PDF of all findings."
    )

elif not data and not analyse_btn:
    st.markdown(
        """
        <div style='text-align:center; padding: 3rem; color:#888;'>
            <h3>Enter a drug name above and click Analyse Market</h3>
            <p>Or use the quick-select buttons for common drugs</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
