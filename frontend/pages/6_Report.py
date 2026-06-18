# File: frontend/pages/6_Report.py
# Purpose: PDF report generation UI — assembles all session data and requests PDF from backend
# Connects to: backend POST /api/v1/report

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import base64
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Generate Report — PharmIntel",
    page_icon="📄",
    layout="wide",
)

render_sidebar()

st.title("📄 Generate Intelligence Report")
st.markdown(
    "Compile all analysis into a professional PDF report — "
    "literature findings, NLP results, formulation scores, market intelligence, and R&D recommendations."
)

st.divider()

# ── Session State ─────────────────────────────────────────────────────────────
search_data      = st.session_state.get("search_response")
analysis_data    = st.session_state.get("paper_analyses")
formulation_data = st.session_state.get("formulation_response")
market_data      = st.session_state.get("market_data")
competitor_data  = st.session_state.get("competitor_data")
search_drug      = st.session_state.get("last_search_drug", "")

# ── Completion Status ─────────────────────────────────────────────────────────
st.markdown("### Analysis Completion Status")

col1, col2 = st.columns(2)

with col1:
    if search_data:
        paper_count = len(search_data.get("papers", []))
        st.success(f"Search — {paper_count} papers retrieved")
    else:
        st.error("Search — not completed (go to Search page first)")

    if analysis_data:
        st.success(f"NLP Analysis — {len(analysis_data)} papers analysed")
    else:
        st.warning("NLP Analysis — not completed (go to Analysis page)")

    if formulation_data:
        top = formulation_data.get("top_recommendation", "N/A")
        st.success(f"Formulation Assessment — top form: {top}")
    else:
        st.warning("Formulation Assessment — not completed (go to Formulation page)")

with col2:
    if market_data:
        drug_mkt = st.session_state.get("market_drug", "")
        st.success(f"Market Intelligence — {drug_mkt.title() if drug_mkt else 'loaded'}")
    else:
        st.info("Market Intelligence — optional (go to Market page)")

    if competitor_data:
        drug_comp = st.session_state.get("competitor_drug", "")
        st.success(f"Competitor Intelligence — {drug_comp.title() if drug_comp else 'loaded'}")
    else:
        st.info("Competitor Intelligence — optional (go to Competitor page)")

st.divider()

# ── Require minimum data ──────────────────────────────────────────────────────
can_generate = bool(search_data and analysis_data and formulation_data)
drug_display = search_drug.title() if search_drug else "Unknown Drug"

# ── Report Preview Card ───────────────────────────────────────────────────────
st.markdown("### Report Preview")

papers_count_preview = len(search_data.get("papers", [])) if search_data else 0
mkt_status  = "included" if market_data   else "skipped"
comp_status = "included" if competitor_data else "skipped"

preview_html = f"""
<div style='background:#F8F9FF; border:1px solid #DDE3F0; border-radius:10px;
            padding:1.5rem; max-width:700px;'>
    <div style='background:#1B3A6B; color:white; padding:1rem 1.5rem;
                border-radius:8px; margin-bottom:1rem; text-align:center;'>
        <h2 style='margin:0; font-size:1.3rem;'>PharmIntel Intelligence Report</h2>
        <p style='margin:4px 0 0 0; font-size:0.9rem; opacity:0.8;'>{drug_display}</p>
    </div>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 1</strong> &mdash; Executive Summary</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 2</strong> &mdash; Drug Overview</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 3</strong> &mdash; Literature Findings ({papers_count_preview} papers)</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 4</strong> &mdash; NLP Extraction Summary</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 5</strong> &mdash; Dosage Form Feasibility Assessment</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 6</strong> &mdash; Excipient Analysis</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 7</strong> &mdash; Indian Market Opportunity ({mkt_status})</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 8</strong> &mdash; Competitor Intelligence ({comp_status})</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 9</strong> &mdash; R&D Recommendations</p>
    <p style='color:#555; font-size:0.9rem; margin:0.4rem 0;'>&#x2022; <strong>Section 10</strong> &mdash; Methodology &amp; Disclaimer</p>
</div>
"""
st.markdown(preview_html, unsafe_allow_html=True)

st.divider()

if not can_generate:
    st.warning(
        "Complete **Search**, **Analysis**, and **Formulation** before generating. "
        "Market and Competitor data are optional."
    )

# ── Generate Button ───────────────────────────────────────────────────────────
generate_btn = st.button(
    "Generate PDF Report",
    type="primary",
    disabled=not can_generate,
)

if generate_btn and can_generate:
    with st.spinner("Building PDF... this takes 10-20 seconds"):
        try:
            payload = {
                "drug_name": search_drug or "Unknown",
                "search_response": search_data,
                "paper_analyses": analysis_data,
                "formulation_response": formulation_data,
                "market_data": market_data,
                "competitor_data": competitor_data,
            }

            resp = requests.post(
                f"{BACKEND_URL}/api/v1/report",
                json=payload,
                timeout=120,
            )

            if resp.status_code == 200:
                result = resp.json()
                st.session_state["report_result"] = result
                st.success("PDF report generated successfully!")
            else:
                st.error(f"Report generation failed: {resp.status_code} — {resp.text[:200]}")

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend. Make sure `uvicorn backend.main:app --reload` is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ── Download Section ──────────────────────────────────────────────────────────
report_result = st.session_state.get("report_result")

if report_result and report_result.get("status") == "success":
    st.divider()
    st.markdown("### Download Report")

    filename   = report_result.get("filename", "pharmintel_report.pdf")
    public_url = report_result.get("public_url")
    pdf_size   = report_result.get("pdf_size_kb", 0)
    pdf_b64    = report_result.get("pdf_bytes_b64", "")

    c1, c2, c3 = st.columns(3)
    c1.metric("File", filename[:28] + "…" if len(filename) > 28 else filename)
    c2.metric("Size", f"{pdf_size} KB")
    c3.metric("Sections", "10")

    if pdf_b64:
        pdf_bytes = base64.b64decode(pdf_b64)
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
        )
    else:
        st.warning("PDF bytes not returned by backend. Please try again.")

    if public_url:
        st.markdown(
            f"""
            <div style='background:#F0F4FF; border-left:4px solid #1B3A6B;
                        padding:10px 16px; border-radius:6px; margin-top:0.5rem; font-size:0.88rem;'>
                Cloud URL: <a href="{public_url}" target="_blank">{public_url[:90]}</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("Cloud upload skipped — report saved locally.")

    st.divider()

    # ── Section Previews ──────────────────────────────────────────────────────
    st.markdown("### Report Contents")

    with st.expander("Executive Summary"):
        if formulation_data:
            top_form = formulation_data.get("top_recommendation", "N/A")
            st.markdown(
                f"Based on **{papers_count_preview} PubMed papers**, the top recommended dosage form "
                f"is **{top_form}**. Analysis used spaCy NLP, rule-based scoring, RAG retrieval, "
                f"and Gemini AI interpretation. Indian market context from CDSCO database."
            )

    with st.expander("Formulation Scores"):
        if formulation_data:
            for s in formulation_data.get("scores", [])[:6]:
                score_val = s.get("score", 0)
                color = "#27AE60" if score_val >= 70 else ("#F39C12" if score_val >= 40 else "#E74C3C")
                st.markdown(
                    f"<span style='color:{color}; font-weight:bold;'>&#9632;</span> "
                    f"**{s.get('dosage_form','').title()}** — {score_val}/100",
                    unsafe_allow_html=True,
                )

    with st.expander("Indian Market Snapshot"):
        if market_data:
            brands = market_data.get("major_brands", [])
            gaps   = market_data.get("market_gaps", [])
            st.markdown(f"**Major brands:** {', '.join(brands[:5])}")
            st.markdown(f"**R&D gaps:** {len(gaps)} identified")
            for g in gaps[:3]:
                st.markdown(f"- {g}")
        else:
            st.caption("Market analysis not run.")

    with st.expander("Competitor Intelligence"):
        if competitor_data and competitor_data.get("found_in_database"):
            brands_comp = competitor_data.get("brands", [])
            dominant    = competitor_data.get("dominant_manufacturer", "")
            st.markdown(f"**Competing brands:** {len(brands_comp)}")
            if dominant:
                st.markdown(f"**Market leader:** {dominant}")
        else:
            st.caption("Competitor analysis not run.")

    st.info(
        "Report generated by PharmIntel — AI-Assisted Pharmaceutical R&D Intelligence System. "
        "For regulatory submissions, validate with CDSCO/DCGI guidelines."
    )

else:
    if can_generate:
        st.markdown(
            """
            <div style='text-align:center; padding:2rem; color:#888;'>
                <h3>All required data loaded. Click Generate PDF Report above.</h3>
                <p>Market and Competitor data are optional — they enrich the PDF but are not required.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style='text-align:center; padding:2rem; color:#888;'>
                <h3>Complete the workflow first</h3>
                <p>Search &rarr; Analysis &rarr; Formulation &rarr; Market (optional) &rarr; Competitor (optional) &rarr; Report</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
