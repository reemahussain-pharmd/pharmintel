# File: frontend/components/sidebar.py
# Purpose: Shared sidebar — branding, workflow progress, current drug status, API health
# Connects to: All frontend pages (call render_sidebar() at the top of each page)

import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def render_sidebar():
    """Render PharmIntel sidebar with branding, workflow progress, and API status."""
    with st.sidebar:
        # ── Branding ──────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style='text-align:center; padding:0.8rem 0 0.5rem 0;'>
                <div style='font-size:2rem;'>⚗</div>
                <div style='color:#1B3A6B; font-size:1.4rem; font-weight:800;
                            letter-spacing:-0.5px;'>PharmIntel</div>
                <div style='color:#888; font-size:0.78rem; margin-top:2px;'>
                    AI R&amp;D Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Workflow Progress ─────────────────────────────────────────────────
        drug = st.session_state.get("last_search_drug", "")
        has_search      = bool(st.session_state.get("last_search_papers"))
        has_analysis    = bool(st.session_state.get("last_analyses"))
        has_formulation = bool(st.session_state.get("formulation_result"))
        has_market      = bool(st.session_state.get("market_data"))
        has_competitor  = bool(st.session_state.get("competitor_data"))
        has_report      = bool(st.session_state.get("report_result"))

        if drug:
            st.markdown(
                f"<div style='background:#E8F0FE; border-radius:6px; padding:5px 10px; "
                f"font-size:0.82rem; color:#1B3A6B; font-weight:600; margin-bottom:6px;'>"
                f"Current drug: {drug.title()}</div>",
                unsafe_allow_html=True,
            )

        steps = [
            ("Search",      has_search,      "🔍"),
            ("Analysis",    has_analysis,    "🧬"),
            ("Formulation", has_formulation, "💊"),
            ("Market",      has_market,      "📊"),
            ("Competitor",  has_competitor,  "🏢"),
            ("Report",      has_report,      "📄"),
        ]

        progress_html = ""
        for name, done, icon in steps:
            if done:
                row_style = "color:#27AE60; font-weight:600;"
                check = "✓"
            else:
                row_style = "color:#AAA;"
                check = "○"
            progress_html += (
                f"<div style='font-size:0.83rem; padding:2px 0; {row_style}'>"
                f"{check} {icon} {name}</div>"
            )

        st.markdown(
            f"<div style='background:#F8F9FF; border-radius:6px; padding:8px 12px; "
            f"border:1px solid #DDE3F0;'>{progress_html}</div>",
            unsafe_allow_html=True,
        )

        # Count complete
        done_count = sum(1 for _, done, _ in steps if done)
        st.progress(done_count / len(steps), text=f"{done_count}/{len(steps)} steps complete")

        st.divider()

        # ── API Status ────────────────────────────────────────────────────────
        try:
            resp = requests.get(f"{BACKEND_URL}/", timeout=2)
            if resp.status_code == 200:
                st.markdown(
                    "<div style='background:#EAFAF1; border-radius:6px; padding:5px 10px; "
                    "font-size:0.8rem; color:#27AE60; font-weight:600;'>● API Connected</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='background:#FDEDEC; border-radius:6px; padding:5px 10px; "
                    "font-size:0.8rem; color:#E74C3C; font-weight:600;'>● API Error</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                "<div style='background:#FDEDEC; border-radius:6px; padding:5px 10px; "
                "font-size:0.8rem; color:#E74C3C; font-weight:600;'>● API Offline</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Start: uvicorn backend.main:app --reload")

        st.divider()

        st.markdown(
            "<div style='font-size:0.75rem; color:#AAA; text-align:center;'>"
            "spaCy · Rule Engine · RAG · Gemini AI<br>"
            "India Market | CDSCO/DCGI</div>",
            unsafe_allow_html=True,
        )
