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

st.set_page_config(page_title="Competitor Intelligence — PharmIntel", page_icon="⚔️", layout="wide")
render_sidebar()

st.title("⚔️ Competitor Intelligence")
st.markdown("Competitive landscape mapping, opportunity scoring, and differentiation strategy.")
st.divider()

drug_name = st.session_state.get("last_search_drug", "")

cc1, cc2 = st.columns([4, 1])
with cc1:
    entered_drug = st.text_input("Drug name", value=drug_name,
                                  placeholder="e.g. metformin", label_visibility="collapsed")
with cc2:
    comp_btn = st.button("Analyse Competitors", type="primary", use_container_width=True)

if comp_btn and entered_drug.strip():
    with st.spinner("Mapping competitive landscape..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/competitor",
                json={"drug_name": entered_drug.strip().lower()},
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["competitor_data"] = data
                st.session_state["last_competitor"] = data
                st.session_state["last_search_drug"] = entered_drug.strip().lower()
            else:
                st.error(f"Competitor analysis failed: {response.status_code}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Load results ──────────────────────────────────────────────────────────────
data = st.session_state.get("competitor_data") or st.session_state.get("last_competitor")

if not data:
    st.info("Enter a drug name and click 'Analyse Competitors' to begin.")
    st.stop()

drug_display = data.get("drug_name", entered_drug).title()

# ── KPI Cards ────────────────────────────────────────────────────────────────
st.markdown(f"### Competitive Intelligence — {drug_display}")

competitors = data.get("competitors", [])
total_comp = len(competitors)
market_leader = data.get("market_leader", "N/A")
generic_count = sum(1 for c in competitors if "generic" in str(c.get("type", "")).lower())
innovator_count = total_comp - generic_count
opp_score = data.get("competitive_opportunity_score", 0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Competitors", total_comp)
k2.metric("Market Leader", market_leader)
k3.metric("Generic Players", generic_count)
k4.metric("Opportunity Score", f"{opp_score}/100" if opp_score else "N/A")

# ── Opportunity Score Gauge ───────────────────────────────────────────────────
if opp_score:
    st.markdown("### Competitive Opportunity Score")
    opp_col, diff_col = st.columns(2)
    with opp_col:
        opp_color = "#27AE60" if opp_score >= 65 else "#F39C12" if opp_score >= 40 else "#E74C3C"
        fig_opp = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=opp_score,
            title={"text": "Competitive Opportunity Score"},
            delta={"reference": 50, "relative": False},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": opp_color},
                "steps": [
                    {"range": [0, 40], "color": "#FADBD8"},
                    {"range": [40, 65], "color": "#FDEBD0"},
                    {"range": [65, 100], "color": "#D5F5E3"},
                ],
            },
        ))
        fig_opp.update_layout(height=300, margin=dict(t=40, b=10))
        st.plotly_chart(fig_opp, use_container_width=True)

    with diff_col:
        # Differentiation quadrant placeholder
        st.markdown("**Differentiation Quadrant**")
        st.caption("Competitive positioning: Market Share vs Innovation Score")
        if competitors:
            quad_data = []
            for c in competitors[:8]:
                market_share = float(str(c.get("market_share_pct", 0)).replace("%", "") or 0)
                innovation = float(c.get("innovation_score", 50) or 50)
                quad_data.append({
                    "Company": c.get("company", "Unknown"),
                    "Market Share (%)": market_share,
                    "Innovation Score": innovation,
                    "Type": c.get("type", "Generic"),
                })
            df_quad = pd.DataFrame(quad_data)
            fig_quad = px.scatter(
                df_quad,
                x="Market Share (%)",
                y="Innovation Score",
                text="Company",
                color="Type",
                title="Differentiation Quadrant",
                size_max=40,
            )
            fig_quad.update_traces(textposition="top center")
            fig_quad.update_layout(height=300, margin=dict(t=40, b=10))
            st.plotly_chart(fig_quad, use_container_width=True)

# ── Competitor Matrix ─────────────────────────────────────────────────────────
if competitors:
    st.markdown("### Competitor Matrix")
    df_comp = pd.DataFrame(competitors)
    display_cols = [c for c in ["brand_name", "company", "type", "market_share_pct",
                                 "price_inr", "formulation", "strength"] if c in df_comp.columns]
    rename_map = {
        "brand_name": "Brand", "company": "Company", "type": "Type",
        "market_share_pct": "Market Share", "price_inr": "Price (INR)",
        "formulation": "Formulation", "strength": "Strength",
    }
    df_display = df_comp[display_cols].rename(columns=rename_map)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Market share chart
    if "market_share_pct" in df_comp.columns:
        try:
            share_data = df_comp[["brand_name", "market_share_pct"]].copy()
            share_data["market_share_pct"] = pd.to_numeric(
                share_data["market_share_pct"].astype(str).str.replace("%", ""), errors="coerce"
            )
            share_data = share_data.dropna(subset=["market_share_pct"])
            if not share_data.empty:
                fig_share = px.pie(
                    share_data,
                    names="brand_name",
                    values="market_share_pct",
                    title="Market Share Distribution",
                    hole=0.4,
                )
                fig_share.update_layout(height=350, margin=dict(t=40, b=10))
                st.plotly_chart(fig_share, use_container_width=True)
        except Exception:
            pass

# ── Differentiation Strategy ──────────────────────────────────────────────────
diff_strategy = data.get("differentiation_strategy", [])
if diff_strategy:
    st.markdown("### Differentiation Strategy")
    for i, strategy in enumerate(diff_strategy, 1):
        st.markdown(
            f"<div style='background:#EBF5FB;padding:12px 16px;border-radius:8px;"
            f"border-left:4px solid #2E86AB;margin-bottom:8px;'>"
            f"<b>{i}.</b> {strategy}</div>",
            unsafe_allow_html=True,
        )

# ── AI Insight ────────────────────────────────────────────────────────────────
ai_insight = data.get("ai_insight", "")
if ai_insight:
    st.markdown("### AI Strategic Insight")
    st.info(ai_insight)

st.divider()
st.info("Go to **Regulatory Intelligence** to assess the regulatory pathway for new formulations.")
