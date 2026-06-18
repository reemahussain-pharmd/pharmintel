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

st.set_page_config(page_title="Drug Repurposing — PharmIntel", page_icon="🔄", layout="wide")
render_sidebar()

st.title("🔄 Drug Repurposing Intelligence")
st.markdown(
    "Identify evidence-backed new therapeutic applications for existing drugs. "
    "Ranked by opportunity score, clinical stage, and India market relevance."
)
st.divider()

drug_name = st.session_state.get("last_search_drug", "")

dc1, dc2 = st.columns([4, 1])
with dc1:
    entered_drug = st.text_input(
        "Drug name",
        value=drug_name,
        placeholder="e.g. metformin, atorvastatin, azithromycin",
        label_visibility="collapsed",
    )
with dc2:
    rep_btn = st.button("Get Repurposing Data", type="primary", use_container_width=True)

if rep_btn and entered_drug.strip():
    with st.spinner("Fetching drug repurposing intelligence..."):
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/v1/repurposing/{entered_drug.strip().lower()}",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["repurposing_data"] = data
                st.session_state["last_search_drug"] = entered_drug.strip().lower()
            elif response.status_code == 404:
                st.warning(
                    f"No repurposing data for '{entered_drug}'. "
                    "Supported drugs: metformin, amlodipine, atorvastatin, omeprazole, "
                    "lisinopril, paracetamol, azithromycin, pantoprazole, cetirizine, rosuvastatin."
                )
                st.stop()
            else:
                st.error(f"Request failed: {response.status_code}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Load results ──────────────────────────────────────────────────────────────
data = st.session_state.get("repurposing_data")

if not data:
    st.info("Enter a drug name and click 'Get Repurposing Data' to begin.")
    st.stop()

drug_display = data.get("drug_name", entered_drug)
overall_score = data.get("overall_repurposing_score", 0)
rep_color = data.get("repurposing_color", "#95A5A6")
rep_label = data.get("repurposing_label", "Unknown")
opportunities = data.get("opportunities", [])

# ── Header Banner ─────────────────────────────────────────────────────────────
st.markdown(
    f"""<div style='background:linear-gradient(135deg,#1A5276,#0E6655);
    color:white;padding:20px 24px;border-radius:12px;margin-bottom:16px;'>
    <h3 style='margin:0;color:white;'>Drug Repurposing Intelligence — {drug_display}</h3>
    <p style='margin:4px 0 0;opacity:0.9;'>
    Primary Indication: <b>{data.get('primary_indication', 'N/A')}</b> &nbsp;|&nbsp;
    Drug Class: <b>{data.get('drug_class', 'N/A')}</b><br>
    Overall Repurposing Score:
    <span style='color:{rep_color};font-weight:bold;font-size:1.2em;'>
    {overall_score}/100 — {rep_label}</span></p></div>""",
    unsafe_allow_html=True,
)

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
high_opp = sum(1 for o in opportunities if o.get("opportunity_score", 0) >= 75)
high_ev = sum(1 for o in opportunities if (o.get("evidence_level") or "").lower() == "high")
phase3_count = sum(1 for o in opportunities if "phase iii" in str(o.get("clinical_stage", "")).lower() or
                   "approved" in str(o.get("clinical_stage", "")).lower())

k1.metric("Total Opportunities Identified", len(opportunities))
k2.metric("High-Score Opportunities (≥75)", high_opp)
k3.metric("High Evidence Opportunities", high_ev)
k4.metric("Phase III / Approved", phase3_count)

# ── Opportunity Score Chart ───────────────────────────────────────────────────
if opportunities:
    st.markdown("### Opportunity Score Ranking")
    df_opp = pd.DataFrame([
        {
            "Indication": o.get("new_indication", "Unknown"),
            "Score": o.get("opportunity_score", 0),
            "Evidence": o.get("evidence_level", "Low"),
            "Stage": o.get("clinical_stage", "Unknown"),
            "Color": o.get("color", "#95A5A6"),
        }
        for o in opportunities
    ])

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_opp["Score"],
        y=df_opp["Indication"],
        orientation="h",
        marker_color=df_opp["Color"],
        text=df_opp["Score"],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Repurposing Opportunity Score (0–100)",
        xaxis_title="Score",
        height=max(300, len(opportunities) * 48),
        margin=dict(t=40, b=20, l=220, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── India Market Relevance ────────────────────────────────────────────────────
india_relevance = data.get("india_market_relevance", "")
if india_relevance:
    st.markdown(
        f"<div style='background:#FEF9E7;padding:12px 16px;border-radius:8px;"
        f"border-left:4px solid #F39C12;'>"
        f"<b>India Market Relevance:</b> {india_relevance}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")

# ── Per-Opportunity Cards ─────────────────────────────────────────────────────
st.markdown("### Detailed Opportunity Analysis")

ev_stage_order = {"High": 1, "Medium": 2, "Low": 3}
sorted_opps = sorted(opportunities, key=lambda x: ev_stage_order.get(x.get("evidence_level", "Low"), 4))

for i, opp in enumerate(sorted_opps, 1):
    score = opp.get("opportunity_score", 0)
    ev_level = opp.get("evidence_level", "Low")
    ev_color = opp.get("evidence_color", "#95A5A6")
    score_color = opp.get("color", "#95A5A6")
    score_label = opp.get("score_label", "Emerging")

    with st.expander(
        f"**{i}. {opp.get('new_indication', 'Unknown')}** — "
        f"Score: {score}/100 | Evidence: {ev_level} | {opp.get('clinical_stage', 'N/A')}",
        expanded=(i <= 2),
    ):
        oc1, oc2, oc3 = st.columns([1, 1, 3])

        with oc1:
            st.markdown(
                f"<div style='background:{score_color};color:white;padding:10px;"
                f"border-radius:8px;text-align:center;'>"
                f"<b>{score}/100</b><br><small>{score_label}</small></div>",
                unsafe_allow_html=True,
            )

        with oc2:
            st.markdown(
                f"<div style='background:{ev_color};color:white;padding:10px;"
                f"border-radius:8px;text-align:center;'>"
                f"<b>{ev_level}</b><br><small>Evidence</small></div>",
                unsafe_allow_html=True,
            )

        with oc3:
            st.markdown(f"**Clinical Stage:** {opp.get('clinical_stage', 'N/A')}")
            st.markdown(f"**Mechanism:** {opp.get('mechanism', 'See literature')}")
            if opp.get("target_cancers"):
                st.markdown(f"**Target Cancers:** {', '.join(opp['target_cancers'])}")
            key_finding = opp.get("key_finding", "")
            if key_finding:
                st.markdown(f"**Key Finding:** {key_finding}")

# ── AI Repurposing Summary ────────────────────────────────────────────────────
ai_summary = data.get("ai_repurposing_summary", "")
if ai_summary:
    st.markdown("### AI Repurposing Strategy Summary")
    st.info(ai_summary)

# ── Evidence Summary Table ────────────────────────────────────────────────────
if opportunities:
    with st.expander("Full Opportunity Data Table"):
        table_rows = [{
            "Indication": o.get("new_indication"),
            "Score": o.get("opportunity_score"),
            "Evidence": o.get("evidence_level"),
            "Clinical Stage": o.get("clinical_stage"),
            "Mechanism": (o.get("mechanism") or "")[:80],
        } for o in opportunities]
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

st.divider()
st.info("Go to **Generate Report** to compile a full consulting-grade intelligence report.")
