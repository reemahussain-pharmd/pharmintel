import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import plotly.graph_objects as go
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Regulatory Intelligence — PharmIntel", page_icon="🏛️", layout="wide")
render_sidebar()

st.title("🏛️ Regulatory Intelligence")
st.markdown(
    "Multi-authority regulatory status: India CDSCO/DCGI, USFDA, EMA, MHRA. "
    "Assess regulatory readiness for new formulation development."
)
st.divider()

drug_name = st.session_state.get("last_search_drug", "")

rc1, rc2 = st.columns([4, 1])
with rc1:
    entered_drug = st.text_input(
        "Drug name",
        value=drug_name,
        placeholder="e.g. metformin, omeprazole, cetirizine",
        label_visibility="collapsed",
    )
with rc2:
    reg_btn = st.button("Get Regulatory Data", type="primary", use_container_width=True)

if reg_btn and entered_drug.strip():
    with st.spinner("Fetching regulatory intelligence..."):
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/v1/regulatory/{entered_drug.strip().lower()}",
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["regulatory_data"] = data
                st.session_state["last_search_drug"] = entered_drug.strip().lower()
            elif response.status_code == 404:
                st.warning(
                    f"No regulatory data for '{entered_drug}'. "
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
data = st.session_state.get("regulatory_data")

if not data:
    st.info("Enter a drug name and click 'Get Regulatory Data' to begin.")
    st.stop()

drug_display = data.get("drug_name", entered_drug)
readiness_score = data.get("regulatory_readiness_score", 0)
readiness_color = data.get("readiness_color", "#95A5A6")
readiness_label = data.get("readiness_label", "Unknown")

# ── Header with Readiness Score ───────────────────────────────────────────────
st.markdown(
    f"""<div style='background:linear-gradient(135deg,#1B4F72,#154360);
    color:white;padding:20px 24px;border-radius:12px;margin-bottom:16px;'>
    <h3 style='margin:0;color:white;'>Regulatory Intelligence — {drug_display}</h3>
    <p style='margin:4px 0 0;opacity:0.9;'>Regulatory Readiness Score:
    <span style='color:{readiness_color};font-weight:bold;font-size:1.2em;'>
    {readiness_score}/100 — {readiness_label}</span></p></div>""",
    unsafe_allow_html=True,
)

# ── Readiness Gauge ───────────────────────────────────────────────────────────
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=readiness_score,
    title={"text": "Regulatory Readiness for New Formulation"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": readiness_color},
        "steps": [
            {"range": [0, 60], "color": "#FADBD8"},
            {"range": [60, 80], "color": "#FDEBD0"},
            {"range": [80, 100], "color": "#D5F5E3"},
        ],
        "threshold": {
            "line": {"color": "black", "width": 3},
            "thickness": 0.75,
            "value": readiness_score,
        },
    },
))
fig_gauge.update_layout(height=280, margin=dict(t=40, b=10))
st.plotly_chart(fig_gauge, use_container_width=True)

# ── Multi-Authority Cards ─────────────────────────────────────────────────────
st.markdown("### Regulatory Status by Authority")

authorities = data.get("authorities", [])
if authorities:
    flag_map = {"IN": "🇮🇳", "US": "🇺🇸", "EU": "🇪🇺", "UK": "🇬🇧"}

    for i in range(0, len(authorities), 2):
        cols = st.columns(2)
        for j, auth in enumerate(authorities[i:i+2]):
            flag = flag_map.get(auth.get("flag", ""), "🌍")
            status = auth.get("status", "Unknown")
            status_color = "#27AE60" if "Approved" in status else "#E74C3C" if "Not" in status else "#F39C12"

            with cols[j]:
                st.markdown(
                    f"<div style='border:1px solid #D5D8DC;border-radius:10px;padding:16px;"
                    f"background:#FDFEFE;'>"
                    f"<h4 style='margin:0;'>{flag} {auth.get('name')}</h4>"
                    f"<p style='margin:4px 0;'><span style='background:{status_color};"
                    f"color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;'>"
                    f"{status}</span></p>",
                    unsafe_allow_html=True,
                )

                if auth.get("schedule"):
                    st.markdown(f"**Schedule:** {auth['schedule']}")
                if auth.get("application"):
                    st.markdown(f"**Application:** {auth['application']}")

                approved_forms = auth.get("approved_forms", [])
                if approved_forms:
                    st.markdown(f"**Approved Forms:** {', '.join(approved_forms)}")

                if auth.get("black_box_warning"):
                    st.markdown(
                        f"<span style='background:#E74C3C;color:white;padding:2px 8px;"
                        f"border-radius:4px;font-size:0.8em;'>⚠ Black Box Warning</span>",
                        unsafe_allow_html=True,
                    )
                    if auth.get("bbw_detail"):
                        st.caption(auth["bbw_detail"])

                if auth.get("otc_available"):
                    st.markdown("**OTC Available:** Yes")

                if auth.get("restrictions"):
                    st.caption(f"Restrictions: {auth['restrictions']}")
                if auth.get("special_requirements"):
                    st.caption(f"Special Requirements: {auth['special_requirements']}")
                if auth.get("notes"):
                    st.caption(auth["notes"])

                st.markdown("</div>", unsafe_allow_html=True)

# ── New Formulation Notes ─────────────────────────────────────────────────────
formulation_notes = data.get("new_formulation_notes", "")
if formulation_notes:
    st.markdown("### New Formulation Development Notes")
    st.markdown(
        f"<div style='background:#EBF5FB;padding:16px;border-radius:10px;"
        f"border-left:4px solid #2E86AB;'>{formulation_notes}</div>",
        unsafe_allow_html=True,
    )

# ── AI Regulatory Strategy ────────────────────────────────────────────────────
ai_strategy = data.get("ai_regulatory_strategy", "")
if ai_strategy:
    st.markdown("### AI Regulatory Strategy")
    st.info(ai_strategy)

st.divider()
st.info("Go to **Drug Repurposing** to explore new therapeutic opportunities for this drug.")
