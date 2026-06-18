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

st.set_page_config(page_title="Formulation Intelligence — PharmIntel", page_icon="💊", layout="wide")
render_sidebar()

st.title("💊 Formulation Intelligence")
st.markdown("Rule Engine scoring + Confidence Assessment + Gemini-powered reasoning for every dosage form.")
st.divider()

# ── Session state check ───────────────────────────────────────────────────────
papers = st.session_state.get("last_search_papers", [])
analyses = st.session_state.get("paper_analyses") or st.session_state.get("last_analyses", [])
drug_name = st.session_state.get("last_search_drug", "")

if not papers:
    st.warning("No papers found. Run **Search** first.")
    st.stop()
if not analyses:
    st.warning("No analysis data. Run **NLP Analysis** first.")
    st.stop()

st.markdown(f"**Drug:** `{drug_name.title()}` | {len(papers)} papers | {len(analyses)} analysed")

if st.button("Run Formulation Assessment", type="primary"):
    with st.spinner("Scoring dosage forms with Rule Engine + Confidence Scoring + Gemini..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/formulation",
                json={"drug_name": drug_name, "papers": papers, "paper_analyses": analyses},
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["formulation_response"] = data
                st.session_state["last_formulation"] = data
                st.success(f"Assessment complete — {len(data.get('scores', []))} dosage forms scored.")
            else:
                st.error(f"Formulation assessment failed: {response.status_code}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Load results ──────────────────────────────────────────────────────────────
data = st.session_state.get("formulation_response") or st.session_state.get("last_formulation")

if not data:
    st.info("Click 'Run Formulation Assessment' above to begin.")
    st.stop()

scores = data.get("scores", [])
top_rec = data.get("top_recommendation", "N/A")
rag_sources = data.get("rag_sources", [])

if not scores:
    st.warning("No dosage forms scored. Ensure NLP analysis found relevant entities.")
    st.stop()

# ── Top Recommendation Banner ─────────────────────────────────────────────────
top_score_obj = scores[0] if scores else {}
top_conf = (top_score_obj.get("confidence") or {})
top_conf_score = top_conf.get("score", 0)
top_conf_level = top_conf.get("level", "Low")
top_conf_color = top_conf.get("color", "#E74C3C")

st.markdown(
    f"""<div style='background:linear-gradient(135deg,#1B4F72,#2E86AB);
    color:white;padding:20px 24px;border-radius:12px;margin-bottom:16px;'>
    <h3 style='margin:0;color:white;'>Top Recommendation: {top_rec}</h3>
    <p style='margin:4px 0 0;opacity:0.9;'>Score: {top_score_obj.get('score',0)}/100 &nbsp;|&nbsp;
    Confidence: <span style='color:{top_conf_color};font-weight:bold;'>{top_conf_level}
    ({top_conf_score:.0f}/100)</span> &nbsp;|&nbsp;
    Literature mentions: {top_score_obj.get('frequency',0)}</p></div>""",
    unsafe_allow_html=True,
)

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
high_scores = sum(1 for s in scores if s.get("score", 0) >= 70)
avg_score = round(sum(s.get("score", 0) for s in scores) / len(scores), 1)
avg_conf = round(sum((s.get("confidence") or {}).get("score", 0) for s in scores) / len(scores), 1)
k1.metric("Dosage Forms Scored", len(scores))
k2.metric("High-Scoring Forms (≥70)", high_scores)
k3.metric("Average Score", f"{avg_score}/100")
k4.metric("Average Confidence", f"{avg_conf}/100")

# ── Bar Chart ─────────────────────────────────────────────────────────────────
st.markdown("### Dosage Form Feasibility Scores")
top_n = scores[:10]
df_chart = pd.DataFrame([
    {"Dosage Form": s["dosage_form"], "Score": s["score"],
     "Confidence": (s.get("confidence") or {}).get("score", 0),
     "Color": s.get("color", "#95A5A6")}
    for s in top_n
])

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    y=df_chart["Dosage Form"],
    x=df_chart["Score"],
    orientation="h",
    marker_color=df_chart["Color"],
    name="Feasibility Score",
))
fig_bar.update_layout(
    title="Rule Engine Feasibility Score (0–100)",
    xaxis_title="Score",
    height=max(300, len(top_n) * 42),
    margin=dict(t=40, b=20, l=150, r=20),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Radar Chart ───────────────────────────────────────────────────────────────
top5 = scores[:5]
if top5 and top5[0].get("components"):
    st.markdown("### Score Component Radar — Top 5 Forms")
    categories = ["Base Score", "Literature Freq.", "Boosters", "Excipient Compat.", "Penalty"]
    fig_radar = go.Figure()
    for s in top5:
        comp = s.get("components") or {}
        values = [
            comp.get("base", 0),
            comp.get("literature_frequency", 0),
            comp.get("score_boosters", 0),
            comp.get("excipient_compatibility", 0),
            comp.get("penalty", 0),
        ]
        values.append(values[0])
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            name=s["dosage_form"],
            opacity=0.7,
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 35])),
        showlegend=True,
        height=450,
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Score Breakdown Table ─────────────────────────────────────────────────────
st.markdown("### Score Breakdown by Component")
breakdown_rows = []
for s in scores:
    comp = s.get("components") or {}
    conf = s.get("confidence") or {}
    breakdown_rows.append({
        "Dosage Form": s["dosage_form"],
        "Base": comp.get("base", 0),
        "Lit. Freq.": comp.get("literature_frequency", 0),
        "Boosters": comp.get("score_boosters", 0),
        "Excipient": comp.get("excipient_compatibility", 0),
        "Penalty": f"-{comp.get('penalty', 0)}",
        "Final Score": s["score"],
        "Confidence": f"{conf.get('score', 0):.0f} ({conf.get('level', 'Low')})",
    })
df_breakdown = pd.DataFrame(breakdown_rows)
st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

# ── Explainability Panels ─────────────────────────────────────────────────────
st.divider()
st.markdown("### Detailed Explainability Panel")

for i, score in enumerate(scores, 1):
    conf = score.get("confidence") or {}
    conf_color = conf.get("color", "#95A5A6")
    conf_level = conf.get("level", "Low")
    conf_score = conf.get("score", 0)

    with st.expander(
        f"**{i}. {score['dosage_form']}** — Score: {score['score']}/100 | "
        f"Confidence: {conf_level} ({conf_score:.0f}/100)",
        expanded=(i == 1),
    ):
        ec1, ec2, ec3 = st.columns([1, 1, 2])
        with ec1:
            st.metric("Feasibility Score", f"{score['score']}/100")
            st.metric("Literature Mentions", score.get("frequency", 0))
        with ec2:
            st.markdown(
                f"<div style='background:{conf_color};color:white;padding:12px;"
                f"border-radius:8px;text-align:center;'>"
                f"<b>Confidence</b><br>{conf_level}<br>{conf_score:.0f}/100</div>",
                unsafe_allow_html=True,
            )
        with ec3:
            comp = score.get("components") or {}
            st.markdown("**Score Breakdown:**")
            st.markdown(f"- Base score: **{comp.get('base', 0)}**")
            st.markdown(f"- Literature frequency bonus: **+{comp.get('literature_frequency', 0)}**")
            st.markdown(f"- Score boosters: **+{comp.get('score_boosters', 0)}**")
            st.markdown(f"- Excipient compatibility: **+{comp.get('excipient_compatibility', 0)}**")
            st.markdown(f"- Contraindication penalty: **-{comp.get('penalty', 0)}**")

        st.markdown("**AI Reasoning:**")
        st.info(score.get("reasoning", "No reasoning available."))

# ── RAG Sources ───────────────────────────────────────────────────────────────
if rag_sources:
    st.divider()
    st.markdown("### Literature Sources Used (RAG)")
    for src in rag_sources:
        st.markdown(f"- {src}")

st.divider()
st.info("Go to **Market Intelligence** to analyse commercial opportunity for this drug.")
