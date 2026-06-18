import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="NLP Analysis — PharmIntel", page_icon="🧬", layout="wide")
render_sidebar()

st.title("🧬 NLP Entity Analysis")
st.markdown("spaCy pharmaceutical NLP + Evidence Strength Classification across your literature set.")
st.divider()

# ── Check session state ───────────────────────────────────────────────────────
papers = st.session_state.get("last_search_papers", [])
drug_name = st.session_state.get("last_search_drug", "")

if not papers:
    st.warning("No papers in session. Go to **Search** first and search for a drug.")
    st.stop()

st.markdown(f"**Analysing:** `{drug_name.title()}` — {len(papers)} papers")

if st.button("Run NLP Analysis", type="primary"):
    with st.spinner("Running spaCy NLP extraction + evidence classification..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/analysis",
                json={"drug_name": drug_name, "papers": papers},
                timeout=60,
            )

            if response.status_code == 200:
                analyses = response.json()
                st.session_state["paper_analyses"] = analyses
                st.session_state["last_analyses"] = analyses
                st.success(f"NLP analysis complete — {len(analyses)} papers processed.")
            else:
                st.error(f"Analysis failed: {response.status_code} — {response.text}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Load results ──────────────────────────────────────────────────────────────
analyses = st.session_state.get("paper_analyses") or st.session_state.get("last_analyses")

if not analyses:
    st.info("Click 'Run NLP Analysis' above to begin.")
    st.stop()

# ── Evidence Strength Dashboard ───────────────────────────────────────────────
st.markdown("### Evidence Strength Dashboard")

evidence_counts = {"High": 0, "Medium": 0, "Low": 0}
all_dosage_forms = []
all_excipients = []
all_study_types = []

for a in analyses:
    level = (a.get("evidence_level") or "low").capitalize()
    if level in evidence_counts:
        evidence_counts[level] += 1
    all_dosage_forms.extend(a.get("dosage_forms", []))
    all_excipients.extend(a.get("excipients", []))
    all_study_types.append(a.get("study_type", "Original Research"))

total = len(analyses)
quality_score = round(
    (evidence_counts["High"] * 3 + evidence_counts["Medium"] * 2 + evidence_counts["Low"] * 1) /
    (total * 3) * 100
) if total > 0 else 0

# KPI cards
e1, e2, e3, e4 = st.columns(4)
e1.metric("High Evidence Papers", evidence_counts["High"],
          delta=f"{round(evidence_counts['High']/total*100)}% of set" if total else None)
e2.metric("Medium Evidence Papers", evidence_counts["Medium"])
e3.metric("Low Evidence Papers", evidence_counts["Low"])
e4.metric("Literature Quality Score", f"{quality_score}/100")

# Charts row
ch1, ch2 = st.columns(2)

with ch1:
    ev_colors = {"High": "#27AE60", "Medium": "#F39C12", "Low": "#E74C3C"}
    fig_ev = px.pie(
        names=list(evidence_counts.keys()),
        values=list(evidence_counts.values()),
        title="Evidence Strength Distribution",
        color=list(evidence_counts.keys()),
        color_discrete_map=ev_colors,
        hole=0.45,
    )
    fig_ev.update_layout(height=300, margin=dict(t=40, b=10))
    st.plotly_chart(fig_ev, use_container_width=True)

with ch2:
    if all_dosage_forms:
        df_counts = pd.Series(all_dosage_forms).value_counts().head(8)
        fig_df = px.bar(
            x=df_counts.values,
            y=df_counts.index,
            orientation="h",
            title="Top Dosage Forms in Literature",
            color=df_counts.values,
            color_continuous_scale="Blues",
        )
        fig_df.update_layout(showlegend=False, coloraxis_showscale=False,
                             height=300, margin=dict(t=40, b=10))
        st.plotly_chart(fig_df, use_container_width=True)
    else:
        st.info("No dosage forms extracted from this literature set.")

# Study type breakdown
if all_study_types:
    st.markdown("### Study Type Breakdown")
    st_counts = pd.Series(all_study_types).value_counts()
    fig_st = px.bar(
        x=st_counts.index,
        y=st_counts.values,
        title="Study Types Identified",
        color=st_counts.values,
        color_continuous_scale="Viridis",
        labels={"x": "Study Type", "y": "Count"},
    )
    fig_st.update_layout(showlegend=False, coloraxis_showscale=False,
                         height=280, margin=dict(t=40, b=10))
    st.plotly_chart(fig_st, use_container_width=True)

# Drug Intelligence Summary
st.markdown("### Drug Intelligence Summary")
top_excipients = pd.Series(all_excipients).value_counts().head(5).index.tolist() if all_excipients else []
top_dosage_forms = pd.Series(all_dosage_forms).value_counts().head(3).index.tolist() if all_dosage_forms else []

cols_s = st.columns(3)
with cols_s[0]:
    st.markdown("**Top Dosage Forms**")
    for df_name in (top_dosage_forms or ["None identified"]):
        st.markdown(f"- {df_name.title()}")
with cols_s[1]:
    st.markdown("**Key Excipients Found**")
    for ex in (top_excipients or ["None identified"]):
        st.markdown(f"- {ex.title()}")
with cols_s[2]:
    st.markdown("**Evidence Profile**")
    pct_high = round(evidence_counts["High"] / total * 100) if total else 0
    pct_med = round(evidence_counts["Medium"] / total * 100) if total else 0
    pct_low = round(evidence_counts["Low"] / total * 100) if total else 0
    st.markdown(f"- High: {pct_high}% of papers")
    st.markdown(f"- Medium: {pct_med}% of papers")
    st.markdown(f"- Low: {pct_low}% of papers")

# ── Per-Paper Insight Panels ──────────────────────────────────────────────────
st.divider()
st.markdown("### Per-Paper Insight Panels")

paper_map = {p["pubmed_id"]: p for p in papers}

for i, analysis in enumerate(analyses, 1):
    paper = paper_map.get(analysis.get("pubmed_id"), {})
    ev_level = (analysis.get("evidence_level") or "low").capitalize()
    study_type = analysis.get("study_type", "Original Research")
    ev_color = {"High": "#27AE60", "Medium": "#F39C12", "Low": "#E74C3C"}.get(ev_level, "#95A5A6")

    title = paper.get("title", analysis.get("title", "Untitled"))
    year = paper.get("year", "")

    with st.expander(f"**{i}. {title[:90]}{'...' if len(title) > 90 else ''}** ({year})", expanded=False):
        badge_col, info_col = st.columns([1, 4])
        with badge_col:
            st.markdown(
                f"<div style='background:{ev_color};color:white;padding:8px 12px;"
                f"border-radius:8px;text-align:center;font-weight:bold;'>"
                f"{ev_level}<br><small>Evidence</small></div>",
                unsafe_allow_html=True,
            )
            st.caption(study_type)
        with info_col:
            pc1, pc2 = st.columns(2)
            with pc1:
                dosage_forms = analysis.get("dosage_forms", [])
                st.markdown(f"**Dosage Forms:** {', '.join(dosage_forms) if dosage_forms else 'None identified'}")
                excipients = analysis.get("excipients", [])
                st.markdown(f"**Excipients:** {', '.join(excipients[:4]) if excipients else 'None identified'}")
            with pc2:
                stability = analysis.get("stability_conditions", [])
                st.markdown(f"**Stability:** {', '.join(stability[:3]) if stability else 'None identified'}")
                entities = analysis.get("entities", [])
                drug_entities = [e["text"] for e in entities if e.get("label") in ("DRUG", "CHEMICAL")][:4]
                st.markdown(f"**Key Drug Entities:** {', '.join(drug_entities) if drug_entities else 'None'}")

        abstract = paper.get("abstract", "")
        if abstract:
            st.caption(abstract[:300] + ("..." if len(abstract) > 300 else ""))
        if paper.get("url"):
            st.markdown(f"[Open on PubMed →]({paper['url']})")

st.divider()
st.info("Analysis complete. Go to **Formulation Intelligence** to score dosage form feasibility.")
