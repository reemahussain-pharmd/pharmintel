import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import base64
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Generate Report — PharmIntel", page_icon="📄", layout="wide")
render_sidebar()

st.title("📄 Generate Intelligence Report")
st.markdown(
    "Compile all analyses into a consulting-grade PDF — "
    "literature findings, evidence scoring, formulation intelligence, market SWOT, "
    "regulatory pathway, and repurposing opportunities."
)
st.divider()

# ── Session State ─────────────────────────────────────────────────────────────
search_data      = st.session_state.get("search_response")
analysis_data    = st.session_state.get("paper_analyses")
formulation_data = st.session_state.get("formulation_response") or st.session_state.get("last_formulation")
market_data      = st.session_state.get("market_data") or st.session_state.get("last_market")
competitor_data  = st.session_state.get("competitor_data") or st.session_state.get("last_competitor")
regulatory_data  = st.session_state.get("regulatory_data")
repurposing_data = st.session_state.get("repurposing_data")
search_drug      = st.session_state.get("last_search_drug", "")
drug_display     = search_drug.title() if search_drug else "Unknown Drug"

# ── Completion Status ─────────────────────────────────────────────────────────
st.markdown("### Analysis Completion Status")

s1, s2 = st.columns(2)
with s1:
    if search_data:
        st.success(f"Search — {len(search_data.get('papers', []))} papers retrieved")
    else:
        st.error("Search — not completed (go to Search page first)")
    if analysis_data:
        st.success(f"NLP Analysis — {len(analysis_data)} papers analysed")
    else:
        st.warning("NLP Analysis — not completed")
    if formulation_data:
        st.success(f"Formulation — top form: {formulation_data.get('top_recommendation', 'N/A')}")
    else:
        st.warning("Formulation Assessment — not completed")
    if regulatory_data:
        score = regulatory_data.get("regulatory_readiness_score", "N/A")
        st.success(f"Regulatory Intelligence — readiness score: {score}/100")
    else:
        st.info("Regulatory Intelligence — optional")

with s2:
    if market_data:
        st.success(f"Market Intelligence — {market_data.get('drug_name', 'loaded')}")
    else:
        st.info("Market Intelligence — optional")
    if competitor_data:
        st.success(f"Competitor Intelligence — {competitor_data.get('drug_name', 'loaded')}")
    else:
        st.info("Competitor Intelligence — optional")
    if repurposing_data:
        n_opp = len(repurposing_data.get("opportunities", []))
        st.success(f"Drug Repurposing — {n_opp} opportunities identified")
    else:
        st.info("Drug Repurposing — optional")

st.divider()

# ── Evidence Dashboard Preview ────────────────────────────────────────────────
if analysis_data:
    st.markdown("### Evidence Intelligence Summary")
    ev_counts = {"High": 0, "Medium": 0, "Low": 0}
    for a in analysis_data:
        level = (a.get("evidence_level") or "low").capitalize()
        if level in ev_counts:
            ev_counts[level] += 1

    total = len(analysis_data)
    quality = round((ev_counts["High"] * 3 + ev_counts["Medium"] * 2 + ev_counts["Low"]) / (total * 3) * 100) if total else 0

    ec1, ec2, ec3, ec4 = st.columns(4)
    ec1.metric("High Evidence", ev_counts["High"])
    ec2.metric("Medium Evidence", ev_counts["Medium"])
    ec3.metric("Low Evidence", ev_counts["Low"])
    ec4.metric("Quality Score", f"{quality}/100")

    ev_col, form_col = st.columns(2)
    with ev_col:
        fig_ev = px.pie(
            names=list(ev_counts.keys()),
            values=list(ev_counts.values()),
            color=list(ev_counts.keys()),
            color_discrete_map={"High": "#27AE60", "Medium": "#F39C12", "Low": "#E74C3C"},
            title="Evidence Distribution",
            hole=0.4,
        )
        fig_ev.update_layout(height=260, margin=dict(t=40, b=10))
        st.plotly_chart(fig_ev, use_container_width=True)

    with form_col:
        if formulation_data and formulation_data.get("scores"):
            scores = formulation_data["scores"][:8]
            fig_form = px.bar(
                x=[s["score"] for s in scores],
                y=[s["dosage_form"] for s in scores],
                orientation="h",
                title="Formulation Scores",
                color=[s["score"] for s in scores],
                color_continuous_scale="RdYlGn",
            )
            fig_form.update_layout(showlegend=False, coloraxis_showscale=False,
                                   height=260, margin=dict(t=40, b=10))
            st.plotly_chart(fig_form, use_container_width=True)

st.divider()

# ── Report Structure Preview ──────────────────────────────────────────────────
st.markdown("### Report Structure (12 Sections)")
papers_count = len(search_data.get("papers", [])) if search_data else 0
mkt_status = "included" if market_data else "skipped"
comp_status = "included" if competitor_data else "skipped"
reg_status = "included" if regulatory_data else "skipped"
rep_status = "included" if repurposing_data else "skipped"

preview_html = f"""
<div style='background:#F8F9FF; border:1px solid #DDE3F0; border-radius:10px; padding:1.5rem; max-width:700px;'>
    <div style='background:linear-gradient(135deg,#1B3A6B,#2E86AB); color:white; padding:1rem 1.5rem;
                border-radius:8px; margin-bottom:1rem; text-align:center;'>
        <h2 style='margin:0; font-size:1.3rem;'>PharmIntel V2 Intelligence Report</h2>
        <p style='margin:4px 0 0 0; font-size:0.9rem; opacity:0.8;'>{drug_display}</p>
    </div>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 1</b> — Executive Summary + KPI Dashboard</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 2</b> — Drug Overview &amp; Classification</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 3</b> — Literature Findings ({papers_count} papers)</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 4</b> — Evidence Strength Analysis</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 5</b> — NLP Entity Extraction</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 6</b> — Formulation Feasibility + Confidence Scores</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 7</b> — Excipient Compatibility Analysis</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 8</b> — Indian Market Intelligence ({mkt_status}) | SWOT</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 9</b> — Competitor Intelligence ({comp_status})</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 10</b> — Regulatory Intelligence ({reg_status}) | CDSCO/USFDA/EMA/MHRA</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 11</b> — Drug Repurposing Opportunities ({rep_status})</p>
    <p style='color:#555; font-size:0.88rem; margin:0.35rem 0;'>&#x2022; <b>Section 12</b> — R&D Recommendations &amp; Methodology</p>
</div>
"""
st.markdown(preview_html, unsafe_allow_html=True)
st.divider()

# ── Require minimum data ──────────────────────────────────────────────────────
can_generate = bool(search_data and analysis_data and formulation_data)
if not can_generate:
    st.warning("Complete **Search**, **Analysis**, and **Formulation** before generating the report.")

generate_btn = st.button("Generate PDF Report", type="primary", disabled=not can_generate)

if generate_btn and can_generate:
    with st.spinner("Building consulting-grade PDF... (10-25 seconds)"):
        try:
            payload = {
                "drug_name": search_drug or "Unknown",
                "search_response": search_data,
                "paper_analyses": analysis_data,
                "formulation_response": formulation_data,
                "market_data": market_data,
                "competitor_data": competitor_data,
            }

            resp = requests.post(f"{BACKEND_URL}/api/v1/report", json=payload, timeout=120)

            if resp.status_code == 200:
                result = resp.json()
                st.session_state["report_result"] = result
                st.success("PDF report generated successfully!")
            else:
                st.error(f"Report generation failed: {resp.status_code} — {resp.text[:200]}")

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ── Download ──────────────────────────────────────────────────────────────────
report_result = st.session_state.get("report_result")

if report_result and report_result.get("status") == "success":
    st.divider()
    st.markdown("### Download Report")

    filename = report_result.get("filename", "pharmintel_report.pdf")
    public_url = report_result.get("public_url")
    pdf_size = report_result.get("pdf_size_kb", 0)
    pdf_b64 = report_result.get("pdf_bytes_b64", "")

    dc1, dc2, dc3 = st.columns(3)
    dc1.metric("File", filename[:28] + "…" if len(filename) > 28 else filename)
    dc2.metric("Size", f"{pdf_size} KB")
    dc3.metric("Sections", "12")

    if pdf_b64:
        pdf_bytes = base64.b64decode(pdf_b64)
        st.download_button(
            label="⬇ Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
        )
    else:
        st.warning("PDF bytes not returned by backend. Please try again.")

    if public_url:
        st.markdown(
            f"<div style='background:#F0F4FF;border-left:4px solid #1B3A6B;"
            f"padding:10px 16px;border-radius:6px;margin-top:0.5rem;font-size:0.88rem;'>"
            f"Cloud URL: <a href='{public_url}' target='_blank'>{public_url[:90]}</a></div>",
            unsafe_allow_html=True,
        )

    # ── Report Section Previews ───────────────────────────────────────────────
    st.divider()
    st.markdown("### Report Content Preview")

    with st.expander("Executive Summary"):
        if formulation_data:
            top_form = formulation_data.get("top_recommendation", "N/A")
            n_scored = len(formulation_data.get("scores", []))
            st.markdown(
                f"Based on **{papers_count} PubMed papers**, the top recommended dosage form "
                f"for **{drug_display}** is **{top_form}** ({n_scored} forms scored). "
                f"Analysis used spaCy NLP, deterministic rule engine, TF-IDF RAG, and Gemini AI. "
                f"Indian pharmaceutical market context from CDSCO database."
            )

    with st.expander("Formulation Intelligence"):
        if formulation_data:
            for s in formulation_data.get("scores", [])[:6]:
                score_val = s.get("score", 0)
                conf = (s.get("confidence") or {})
                color = "#27AE60" if score_val >= 70 else "#F39C12" if score_val >= 40 else "#E74C3C"
                st.markdown(
                    f"<span style='color:{color};font-weight:bold;'>■</span> "
                    f"**{s.get('dosage_form','').title()}** — {score_val}/100 | "
                    f"Confidence: {conf.get('level', 'N/A')} ({conf.get('score', 0):.0f})",
                    unsafe_allow_html=True,
                )

    with st.expander("Market Intelligence"):
        if market_data:
            st.markdown(f"**Market Size:** {market_data.get('market_size_inr', 'N/A')}")
            st.markdown(f"**Growth Rate:** {market_data.get('market_growth_rate', 'N/A')}")
            gaps = market_data.get("formulation_gaps", [])
            if gaps:
                st.markdown(f"**Formulation Gaps:** {len(gaps)} identified")
                for g in gaps[:3]:
                    st.markdown(f"- {g}")
        else:
            st.caption("Market analysis not run.")

    with st.expander("Regulatory Intelligence"):
        if regulatory_data:
            st.markdown(f"**Readiness Score:** {regulatory_data.get('regulatory_readiness_score')}/100 — {regulatory_data.get('readiness_label')}")
            for auth in regulatory_data.get("authorities", [])[:2]:
                st.markdown(f"**{auth.get('name')}:** {auth.get('status')}")
            if regulatory_data.get("ai_regulatory_strategy"):
                st.caption(regulatory_data["ai_regulatory_strategy"][:200] + "...")
        else:
            st.caption("Regulatory intelligence not run.")

    with st.expander("Drug Repurposing"):
        if repurposing_data:
            st.markdown(f"**Overall Score:** {repurposing_data.get('overall_repurposing_score')}/100 — {repurposing_data.get('repurposing_label')}")
            for opp in repurposing_data.get("opportunities", [])[:3]:
                st.markdown(f"- **{opp.get('new_indication')}** — Score: {opp.get('opportunity_score')} | {opp.get('evidence_level')} evidence")
        else:
            st.caption("Repurposing analysis not run.")

    st.info(
        "Report generated by PharmIntel v2.0 — AI-Assisted Pharmaceutical R&D Intelligence System. "
        "For regulatory submissions, validate all data against current CDSCO/DCGI guidelines."
    )
else:
    if can_generate:
        st.markdown(
            "<div style='text-align:center;padding:2rem;color:#888;'>"
            "<h3>All required data loaded.</h3>"
            "<p>Click <b>Generate PDF Report</b> above.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='text-align:center;padding:2rem;color:#888;'>"
            "<h3>Complete the workflow first</h3>"
            "<p>Search → Analysis → Formulation → (Market → Competitor → Regulatory → Repurposing) → Report</p>"
            "</div>",
            unsafe_allow_html=True,
        )
