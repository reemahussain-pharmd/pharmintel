# File: frontend/pages/5_Competitor.py
# Purpose: Competitor Intelligence dashboard — brands table, gap analysis, Gemini summary
# Connects to: backend POST /api/v1/competitor

import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Competitor Intelligence — PharmIntel",
    page_icon="🏢",
    layout="wide",
)

render_sidebar()

st.title("🏢 Competitor Intelligence")
st.markdown(
    "Analyse the competitive landscape for any drug in the Indian market — "
    "brands, manufacturers, dosage forms, pricing tiers, and differentiation opportunities."
)

st.divider()

# ── Drug Input ────────────────────────────────────────────────────────────────
drug_name = st.session_state.get("last_search_drug", "")

col1, col2 = st.columns([4, 1])
with col1:
    drug_input = st.text_input(
        "Drug name",
        value=drug_name,
        placeholder="e.g. metformin, atorvastatin, omeprazole",
        label_visibility="collapsed",
    )
with col2:
    analyse_btn = st.button("Analyse Competitors", type="primary", use_container_width=True)

# Quick select buttons
st.markdown("**Quick select:**")
quick_drugs = ["metformin", "atorvastatin", "amlodipine", "omeprazole",
               "pantoprazole", "rosuvastatin", "azithromycin", "paracetamol"]
cols = st.columns(len(quick_drugs))
for i, d in enumerate(quick_drugs):
    with cols[i]:
        if st.button(d.title(), key=f"qc_{d}", use_container_width=True):
            drug_input = d
            analyse_btn = True

st.divider()

# ── Fetch Competitor Data ─────────────────────────────────────────────────────
if analyse_btn and drug_input.strip():
    with st.spinner(f"Analysing competitive landscape for {drug_input.title()}..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/competitor",
                json={"drug_name": drug_input.strip().lower()},
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["competitor_data"] = data
                st.session_state["competitor_drug"] = drug_input.strip().lower()
            else:
                st.error(f"Analysis failed: {response.status_code}")
                st.stop()
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend. Make sure `uvicorn backend.main:app --reload` is running.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Display Results ───────────────────────────────────────────────────────────
data = st.session_state.get("competitor_data")
current_drug = st.session_state.get("competitor_drug", "")

if data:
    drug_title = current_drug.title()
    found = data.get("found_in_database", False)

    if not found:
        st.warning(
            f"No competitor data found for **{drug_title}** in our database. "
            "Try: metformin, amlodipine, atorvastatin, omeprazole, paracetamol, "
            "azithromycin, pantoprazole, cetirizine, rosuvastatin, lisinopril."
        )
        st.stop()

    st.markdown(f"## {drug_title} — Competitive Landscape (India)")

    # ── Headline metrics ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Competing Brands", len(data.get("brands", [])))
    c2.metric("Local Manufacturers", len(data.get("manufacturers", [])))
    c3.metric("Approved Dosage Forms", len(data.get("approved_forms", [])))
    c4.metric("Market Gaps Identified", len(data.get("market_gaps", [])))

    st.divider()

    # ── Brand Table ───────────────────────────────────────────────────────────
    st.markdown("### 🏷️ Brand Landscape")

    brand_details = data.get("brand_details", [])
    dominant = data.get("dominant_manufacturer", "")

    if brand_details:
        rows = []
        for b in brand_details:
            brand = b.get("brand", "")
            forms = ", ".join([f.title() for f in b.get("dosage_forms", [])])
            is_leader = dominant and brand.lower() in dominant.lower()
            rows.append({
                "Brand": f"👑 {brand}" if is_leader else brand,
                "Available in India": "✅ Yes",
                "Dosage Forms": forms,
                "Market Position": "Market Leader" if is_leader else "Competitor",
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Brand": st.column_config.TextColumn("Brand", width="medium"),
                "Available in India": st.column_config.TextColumn("India", width="small"),
                "Dosage Forms": st.column_config.TextColumn("Dosage Forms", width="large"),
                "Market Position": st.column_config.TextColumn("Position", width="medium"),
            }
        )

        if dominant:
            st.markdown(
                f"""
                <div style='background:#1B3A6B; color:white; padding:0.6rem 1rem;
                            border-radius:6px; font-size:0.88rem; margin-top:0.5rem;'>
                    👑 <strong>Market Leader:</strong> {dominant}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Two columns: manufacturers + gaps ────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🏭 Indian Manufacturers")
        manufacturers = data.get("manufacturers", [])
        if manufacturers:
            for mfr in manufacturers:
                st.markdown(
                    f"<div style='background:#F8F9FF; border:1px solid #DDE3F0; "
                    f"padding:6px 12px; margin:4px 0; border-radius:6px; font-size:0.88rem;'>"
                    f"🏭 {mfr}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No local manufacturer data.")

        if data.get("price_range_inr"):
            st.markdown("### 💰 Price Range")
            st.markdown(
                f"""
                <div style='background:#F0F4FF; border-left:3px solid #1B3A6B;
                            padding:8px 14px; border-radius:4px; font-size:0.9rem;'>
                    ₹ {data['price_range_inr']}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if data.get("therapeutic_class"):
            st.markdown(f"**Therapeutic Class:** {data['therapeutic_class']}")

    with col_right:
        st.markdown("### 🔬 Competitive Gaps & Opportunities")
        gaps = data.get("market_gaps", [])
        if gaps:
            for i, gap in enumerate(gaps, 1):
                st.markdown(
                    f"""
                    <div style='background:linear-gradient(135deg, #FFF8E7, #FFF3CD);
                                border-left:4px solid #F39C12; padding:8px 14px;
                                margin:6px 0; border-radius:6px; font-size:0.88rem;'>
                        <strong>Gap {i}:</strong> {gap}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No gap data available.")

    st.divider()

    # ── Approved Dosage Forms visual ──────────────────────────────────────────
    st.markdown("### 💊 Currently Approved Dosage Forms")
    approved = data.get("approved_forms", [])
    if approved:
        tags = " ".join([
            f"<span style='background:#27AE60; color:white; padding:5px 14px; "
            f"border-radius:14px; font-size:0.88rem; margin:3px; display:inline-block;'>"
            f"✓ {f.title()}</span>"
            for f in approved
        ])
        st.markdown(tags, unsafe_allow_html=True)
        st.caption("These forms are already marketed in India — differentiation opportunity lies in forms NOT listed above.")
    else:
        st.caption("No approved form data.")

    st.divider()

    # ── Gemini AI Competitive Summary ─────────────────────────────────────────
    st.markdown("### 🤖 AI Competitive Landscape Summary")
    ai_summary = data.get("ai_competitive_summary", "")
    if ai_summary:
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg, #F8F9FF, #EEF2FF);
                        border-left:4px solid #1B3A6B; padding:1.2rem 1.5rem;
                        border-radius:8px; line-height:1.8;'>
                <p style='color:#1A1A2E; font-size:0.95rem; margin:0;'>{ai_summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("AI summary not available.")

    st.divider()

    # ── Differentiation matrix ────────────────────────────────────────────────
    with st.expander("📐 Differentiation Opportunity Matrix"):
        all_possible_forms = [
            "tablet", "extended release tablet", "oral solution", "capsule",
            "injection", "transdermal patch", "nanoparticle", "inhaler",
            "topical cream", "dispersible tablet", "orally disintegrating tablet",
        ]
        approved_lower = [f.lower() for f in approved]
        rows = []
        for form in all_possible_forms:
            in_market = form.lower() in approved_lower or any(
                form.lower() in a.lower() for a in approved_lower
            )
            rows.append({
                "Dosage Form": form.title(),
                "In Indian Market": "✅ Yes" if in_market else "❌ No",
                "Opportunity": "Low — already competitive" if in_market else "🔬 R&D Opportunity",
            })
        df2 = pd.DataFrame(rows)
        st.dataframe(df2, use_container_width=True, hide_index=True)

    st.info(
        "Competitor analysis complete. Go to **Generate Report** to create a "
        "full PDF covering all findings from Phases 2–7."
    )

elif not data and not analyse_btn:
    st.markdown(
        """
        <div style='text-align:center; padding:3rem; color:#888;'>
            <h3>Enter a drug name above and click Analyse Competitors</h3>
            <p>Or use the quick-select buttons</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
