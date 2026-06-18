# File: frontend/pages/2_Analysis.py
# Purpose: NLP entity extraction page — color-coded pharmaceutical entity tags per paper
# Connects to: backend POST /api/v1/analysis, session_state from 1_Search.py

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="NLP Analysis — PharmIntel",
    page_icon="🧬",
    layout="wide",
)

render_sidebar()

st.title("🧬 NLP Entity Extraction")
st.markdown(
    "spaCy scans each paper abstract and extracts pharmaceutical entities — "
    "dosage forms, excipients, stability conditions, and development stage keywords."
)

# ── Legend ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='display:flex; gap:1.5rem; margin:0.5rem 0 1rem 0; flex-wrap:wrap;'>
        <span style='background:#1B3A6B; color:white; padding:3px 10px;
                     border-radius:12px; font-size:0.82rem;'>💊 Dosage Form</span>
        <span style='background:#27AE60; color:white; padding:3px 10px;
                     border-radius:12px; font-size:0.82rem;'>🧪 Excipient</span>
        <span style='background:#E67E22; color:white; padding:3px 10px;
                     border-radius:12px; font-size:0.82rem;'>🌡️ Stability</span>
        <span style='background:#8E44AD; color:white; padding:3px 10px;
                     border-radius:12px; font-size:0.82rem;'>🔬 Dev Stage</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Check session state for papers from Search page ──────────────────────────
papers = st.session_state.get("last_search_papers", [])
drug_name = st.session_state.get("last_search_drug", "")

if not papers:
    st.warning(
        "No papers loaded. Go to the **Literature Search** page first, "
        "search for a drug, then come back here."
    )
    st.stop()

st.markdown(f"**Drug:** `{drug_name.title()}` &nbsp;|&nbsp; **Papers to analyse:** {len(papers)}")

# ── Run Analysis ──────────────────────────────────────────────────────────────
if st.button("Run NLP Extraction", type="primary"):
    with st.spinner("Extracting pharmaceutical entities from abstracts..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/analysis",
                json={"drug_name": drug_name, "papers": papers},
                timeout=60,
            )

            if response.status_code == 200:
                analyses = response.json()
                st.session_state["last_analyses"] = analyses
                st.session_state["paper_analyses"] = analyses   # used by Report page
                st.session_state["last_analyses_drug"] = drug_name
                st.success(f"Extraction complete — analysed {len(analyses)} papers")
            else:
                st.error(f"Analysis failed: {response.status_code} — {response.text[:200]}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend. Make sure `uvicorn backend.main:app --reload` is running.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Display Results ───────────────────────────────────────────────────────────
analyses = st.session_state.get("last_analyses", [])

if analyses:
    # Aggregate counts across all papers
    all_dosage_forms: dict[str, int] = {}
    all_excipients: dict[str, int] = {}
    all_stability: list[str] = []

    for a in analyses:
        for df in a.get("dosage_forms", []):
            all_dosage_forms[df] = all_dosage_forms.get(df, 0) + 1
        for ex in a.get("excipients", []):
            all_excipients[ex] = all_excipients.get(ex, 0) + 1
        for sc in a.get("stability_conditions", []):
            if sc not in all_stability:
                all_stability.append(sc)

    # Summary cards
    st.markdown("### Aggregate Summary Across All Papers")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers Analysed", len(analyses))
    c2.metric("Dosage Forms Found", len(all_dosage_forms))
    c3.metric("Excipients Found", len(all_excipients))
    c4.metric("Stability Factors", len(all_stability))

    st.divider()

    # Top findings
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Most Mentioned Dosage Forms")
        if all_dosage_forms:
            sorted_df = sorted(all_dosage_forms.items(), key=lambda x: x[1], reverse=True)
            for form, count in sorted_df[:8]:
                st.markdown(
                    f"<span style='background:#1B3A6B; color:white; padding:3px 10px; "
                    f"border-radius:12px; font-size:0.82rem; margin:2px; display:inline-block;'>"
                    f"💊 {form.title()}</span> "
                    f"<span style='color:#666; font-size:0.8rem;'>mentioned in {count} paper(s)</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No dosage forms detected.")

    with col_right:
        st.markdown("#### Excipients Identified")
        if all_excipients:
            sorted_ex = sorted(all_excipients.items(), key=lambda x: x[1], reverse=True)
            for excipient, count in sorted_ex[:8]:
                st.markdown(
                    f"<span style='background:#27AE60; color:white; padding:3px 10px; "
                    f"border-radius:12px; font-size:0.82rem; margin:2px; display:inline-block;'>"
                    f"🧪 {excipient.title()}</span> "
                    f"<span style='color:#666; font-size:0.8rem;'>in {count} paper(s)</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No excipients detected.")

    if all_stability:
        st.markdown("#### Stability Conditions Mentioned")
        tags_html = " ".join([
            f"<span style='background:#E67E22; color:white; padding:3px 10px; "
            f"border-radius:12px; font-size:0.82rem; margin:2px; display:inline-block;'>"
            f"🌡️ {s}</span>"
            for s in all_stability[:12]
        ])
        st.markdown(tags_html, unsafe_allow_html=True)

    st.divider()

    # Per-paper breakdown
    st.markdown("### Per-Paper Entity Breakdown")
    for i, analysis in enumerate(analyses, 1):
        title_short = analysis["title"][:90] + ("..." if len(analysis["title"]) > 90 else "")
        has_entities = (
            analysis.get("dosage_forms") or
            analysis.get("excipients") or
            analysis.get("stability_conditions")
        )

        with st.expander(f"**{i}. {title_short}**", expanded=False):
            if not has_entities:
                st.caption("No pharmaceutical entities detected in this abstract.")
                continue

            # Dosage forms
            if analysis.get("dosage_forms"):
                tags = " ".join([
                    f"<span style='background:#1B3A6B; color:white; padding:2px 8px; "
                    f"border-radius:10px; font-size:0.78rem; margin:1px; display:inline-block;'>"
                    f"💊 {df.title()}</span>"
                    for df in analysis["dosage_forms"]
                ])
                st.markdown(f"**Dosage Forms:** {tags}", unsafe_allow_html=True)

            # Excipients
            if analysis.get("excipients"):
                tags = " ".join([
                    f"<span style='background:#27AE60; color:white; padding:2px 8px; "
                    f"border-radius:10px; font-size:0.78rem; margin:1px; display:inline-block;'>"
                    f"🧪 {ex.title()}</span>"
                    for ex in analysis["excipients"]
                ])
                st.markdown(f"**Excipients:** {tags}", unsafe_allow_html=True)

            # Stability
            if analysis.get("stability_conditions"):
                tags = " ".join([
                    f"<span style='background:#E67E22; color:white; padding:2px 8px; "
                    f"border-radius:10px; font-size:0.78rem; margin:1px; display:inline-block;'>"
                    f"🌡️ {s}</span>"
                    for s in analysis["stability_conditions"]
                ])
                st.markdown(f"**Stability:** {tags}", unsafe_allow_html=True)

            # Dev stage
            dev_entities = [e for e in analysis.get("entities", []) if e.get("label") == "DEV_STAGE"]
            if dev_entities:
                tags = " ".join([
                    f"<span style='background:#8E44AD; color:white; padding:2px 8px; "
                    f"border-radius:10px; font-size:0.78rem; margin:1px; display:inline-block;'>"
                    f"🔬 {e['text']}</span>"
                    for e in dev_entities[:5]
                ])
                st.markdown(f"**Research Stage:** {tags}", unsafe_allow_html=True)

    st.divider()
    st.info(
        "Extraction complete. Go to **Formulation Feasibility** page to see "
        "dosage form scores calculated from these results."
    )
