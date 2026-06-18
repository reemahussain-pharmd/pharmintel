# File: frontend/pages/3_Formulation.py
# Purpose: Formulation feasibility dashboard — bar chart, scores, Gemini reasoning
# Connects to: backend POST /api/v1/formulation, session_state from 1_Search and 2_Analysis

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Formulation Feasibility — PharmIntel",
    page_icon="💊",
    layout="wide",
)

render_sidebar()

st.title("💊 Formulation Feasibility Assessment")
st.markdown(
    "The rule engine scores each dosage form **0–100** using literature frequency, "
    "excipient compatibility, and pharmaceutical formulation rules. "
    "AI generates one sentence of interpretation per form after scoring is complete."
)

st.divider()

# ── Check session state ───────────────────────────────────────────────────────
papers = st.session_state.get("last_search_papers", [])
analyses = st.session_state.get("last_analyses", [])
drug_name = st.session_state.get("last_search_drug", "")

if not papers:
    st.warning("No papers loaded. Go to **Literature Search** first and search for a drug.")
    st.stop()

if not analyses:
    st.warning("No NLP analysis found. Go to **NLP Analysis** and run extraction first.")
    st.stop()

st.markdown(f"**Drug:** `{drug_name.title()}` | **Papers:** {len(papers)} | **Analyses:** {len(analyses)}")

# ── Run Scoring ───────────────────────────────────────────────────────────────
if st.button("Run Formulation Scoring", type="primary"):
    with st.spinner("Scoring dosage forms with rule engine... then generating AI reasoning..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/formulation",
                json={
                    "drug_name": drug_name,
                    "papers": papers,
                    "paper_analyses": analyses,
                },
                timeout=120,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["formulation_result"] = data
                st.session_state["formulation_response"] = data  # used by Report page
                st.success(
                    f"Scoring complete — {len(data['scores'])} dosage forms assessed. "
                    f"Top recommendation: **{data['top_recommendation']}**"
                )
            else:
                st.error(f"Scoring failed: {response.status_code} — {response.text[:300]}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach backend. Make sure `uvicorn backend.main:app --reload` is running.")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("Request timed out. Try again — AI reasoning can take up to 60 seconds.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Display Results ───────────────────────────────────────────────────────────
result = st.session_state.get("formulation_result")

if result:
    scores = result.get("scores", [])
    top_rec = result.get("top_recommendation", "")

    if not scores:
        st.info("No dosage form scores generated. This may happen if abstracts contain limited formulation data.")
        st.stop()

    # Top recommendation banner
    if top_rec:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #1B3A6B, #2E5FA3);
                        color: white; padding: 1.2rem 1.5rem; border-radius: 10px;
                        margin-bottom: 1.5rem;'>
                <h3 style='margin:0; color:white;'>🏆 Top Recommendation</h3>
                <p style='margin:0.3rem 0 0 0; font-size:1.3rem; font-weight:600;'>{top_rec}</p>
                <p style='margin:0.2rem 0 0 0; font-size:0.85rem; opacity:0.85;'>
                    Highest combined score from literature frequency + formulation rules + excipient compatibility
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Score legend
    st.markdown(
        """
        <div style='display:flex; gap:1.5rem; margin-bottom:1rem; flex-wrap:wrap;'>
            <span style='color:#27AE60; font-weight:600;'>■ ≥70 Highly Feasible</span>
            <span style='color:#F39C12; font-weight:600;'>■ 40–69 Moderately Feasible</span>
            <span style='color:#E74C3C; font-weight:600;'>■ &lt;40 Low Feasibility</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Dosage Form Scores")

    # Bar chart + reasoning
    for score_item in scores:
        form = score_item["dosage_form"]
        score_val = score_item["score"]
        color = score_item["color"]
        frequency = score_item["frequency"]
        reasoning = score_item.get("reasoning", "")

        # Bar row
        col1, col2 = st.columns([5, 1])
        with col1:
            is_top = form.lower() == top_rec.lower()
            label = f"{'🏆 ' if is_top else ''}{form.title()}"
            border = "2px solid #1B3A6B" if is_top else "none"

            st.markdown(
                f"""
                <div style='margin-bottom:4px; padding: 4px 8px;
                            border-left: {border}; border-radius:4px;'>
                    <div style='display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:3px;'>
                        <span style='font-weight:{"700" if is_top else "500"};
                                     font-size:0.95rem;'>{label}</span>
                        <span style='color:{color}; font-weight:700;
                                     font-size:0.95rem;'>{score_val}/100</span>
                    </div>
                    <div style='background:#e8e8e8; border-radius:6px; height:14px;'>
                        <div style='background:{color}; width:{score_val}%;
                                    height:14px; border-radius:6px;
                                    transition: width 0.3s;'></div>
                    </div>
                    <div style='color:#888; font-size:0.75rem; margin-top:2px;'>
                        Mentioned in {frequency} paper(s)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            # Expandable reasoning button
            with st.expander("Why?"):
                if reasoning:
                    st.markdown(f"*{reasoning}*")
                else:
                    st.caption("No reasoning generated.")

    st.divider()

    # Summary stats
    green = sum(1 for s in scores if s["score"] >= 70)
    orange = sum(1 for s in scores if 40 <= s["score"] < 70)
    red = sum(1 for s in scores if s["score"] < 40)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Forms Assessed", len(scores))
    c2.metric("Highly Feasible (≥70)", green, delta=None)
    c3.metric("Moderate (40–69)", orange, delta=None)
    c4.metric("Low (<40)", red, delta=None)

    st.divider()

    # Scoring methodology transparency
    with st.expander("📐 How scores are calculated (Rule Engine methodology)"):
        st.markdown(
            """
            **Score = Base Score + Frequency Score + Booster Score + Excipient Score − Penalty**

            | Component | Max Points | Source |
            |---|---|---|
            | Base Score | 20–60 | `formulation_rules.json` — each dosage form has a pre-set base |
            | Literature Frequency | 0–25 | Papers mentioning this form ÷ total papers × 25 |
            | Score Boosters | 0–15 | Manufacturing keywords in abstracts (granulation, coating, etc.) |
            | Excipient Compatibility | 0–10 | Compatible excipients found in literature |
            | Contraindication Penalty | −0 to −20 | Contraindication keywords found in abstracts |

            **This is fully deterministic Python logic.** No AI was used in the scoring.
            The AI (Gemini) only writes one explanatory sentence per form after the score is set.
            """
        )

    # RAG Sources section
    rag_sources = result.get("rag_sources", [])
    if rag_sources:
        st.markdown("### 📚 Literature Sources Used by AI")
        st.markdown(
            "_The following papers were retrieved from ChromaDB and provided "
            "as context to Gemini when generating reasoning:_"
        )
        for i, source in enumerate(rag_sources, 1):
            st.markdown(
                f"<div style='background:#F0F4FF; border-left:3px solid #1B3A6B; "
                f"padding:6px 12px; margin:4px 0; border-radius:4px; font-size:0.85rem;'>"
                f"📄 {i}. {source}</div>",
                unsafe_allow_html=True,
            )
        st.caption(
            "Gemini's reasoning is grounded in these retrieved papers — "
            "not general AI knowledge."
        )
    else:
        st.info(
            "Run NLP Analysis first to embed papers into ChromaDB, "
            "then re-run scoring to see literature sources used by AI."
        )

    st.divider()
    st.info(
        "Scores saved to session. Go to **Indian Market Intelligence** to see "
        "how these forms compare against what's already available in the Indian market."
    )
