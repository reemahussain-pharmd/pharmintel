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

st.set_page_config(page_title="Market Intelligence — PharmIntel", page_icon="📈", layout="wide")
render_sidebar()

st.title("📈 Market Intelligence")
st.markdown("Indian pharmaceutical market analysis — commercial landscape, SWOT, and strategic positioning.")
st.divider()

drug_name = st.session_state.get("last_search_drug", "")

mc1, mc2 = st.columns([4, 1])
with mc1:
    entered_drug = st.text_input("Drug name", value=drug_name,
                                  placeholder="e.g. metformin", label_visibility="collapsed")
with mc2:
    market_btn = st.button("Analyse Market", type="primary", use_container_width=True)

if market_btn and entered_drug.strip():
    with st.spinner("Analysing Indian pharmaceutical market..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/market",
                json={"drug_name": entered_drug.strip().lower()},
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state["market_data"] = data
                st.session_state["last_market"] = data
                st.session_state["last_search_drug"] = entered_drug.strip().lower()
            else:
                st.error(f"Market analysis failed: {response.status_code}")
                st.stop()

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.stop()

# ── Load results ──────────────────────────────────────────────────────────────
data = st.session_state.get("market_data") or st.session_state.get("last_market")

if not data:
    st.info("Enter a drug name and click 'Analyse Market' to begin.")
    st.stop()

drug_display = data.get("drug_name", entered_drug).title()

# ── Market KPI Cards ──────────────────────────────────────────────────────────
st.markdown(f"### Market Intelligence — {drug_display}")

market_size = data.get("market_size_inr", "N/A")
growth_rate = data.get("market_growth_rate", "N/A")
total_brands = data.get("total_brands", 0)
market_leader = data.get("market_leader", "N/A")
patient_population = data.get("patient_population", "N/A")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Market Size (INR)", market_size)
k2.metric("Annual Growth Rate", growth_rate)
k3.metric("Active Brands", total_brands)
k4.metric("Market Leader", market_leader)

# Market Attractiveness Score
attractiveness_score = data.get("market_attractiveness_score", 0)
saturation_index = data.get("market_saturation_index", 0)

if attractiveness_score or saturation_index:
    st.markdown("### Market Attractiveness & Saturation")
    ma1, ma2 = st.columns(2)
    with ma1:
        at_color = "#27AE60" if attractiveness_score >= 70 else "#F39C12" if attractiveness_score >= 50 else "#E74C3C"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=attractiveness_score,
            title={"text": "Market Attractiveness Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": at_color},
                "steps": [
                    {"range": [0, 50], "color": "#FADBD8"},
                    {"range": [50, 70], "color": "#FDEBD0"},
                    {"range": [70, 100], "color": "#D5F5E3"},
                ],
                "threshold": {"line": {"color": "black", "width": 3}, "thickness": 0.75, "value": attractiveness_score},
            },
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with ma2:
        sat_color = "#E74C3C" if saturation_index >= 70 else "#F39C12" if saturation_index >= 50 else "#27AE60"
        fig_sat = go.Figure(go.Indicator(
            mode="gauge+number",
            value=saturation_index,
            title={"text": "Market Saturation Index"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": sat_color},
                "steps": [
                    {"range": [0, 50], "color": "#D5F5E3"},
                    {"range": [50, 70], "color": "#FDEBD0"},
                    {"range": [70, 100], "color": "#FADBD8"},
                ],
            },
        ))
        fig_sat.update_layout(height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig_sat, use_container_width=True)

# ── SWOT Analysis ─────────────────────────────────────────────────────────────
swot = data.get("swot", {})
if swot:
    st.markdown("### SWOT Analysis")
    sw1, sw2 = st.columns(2)

    with sw1:
        st.markdown(
            "<div style='background:#D5F5E3;padding:16px;border-radius:10px;border-left:4px solid #27AE60;'>"
            "<b style='color:#1E8449;'>Strengths</b><br>" +
            "".join(f"<p style='margin:4px 0;'>✓ {s}</p>" for s in swot.get("strengths", [])) +
            "</div>", unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#FADBD8;padding:16px;border-radius:10px;border-left:4px solid #E74C3C;'>"
            "<b style='color:#C0392B;'>Weaknesses</b><br>" +
            "".join(f"<p style='margin:4px 0;'>⚠ {w}</p>" for w in swot.get("weaknesses", [])) +
            "</div>", unsafe_allow_html=True
        )

    with sw2:
        st.markdown(
            "<div style='background:#D6EAF8;padding:16px;border-radius:10px;border-left:4px solid #2E86AB;'>"
            "<b style='color:#1A5276;'>Opportunities</b><br>" +
            "".join(f"<p style='margin:4px 0;'>→ {o}</p>" for o in swot.get("opportunities", [])) +
            "</div>", unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#FEF9E7;padding:16px;border-radius:10px;border-left:4px solid #F39C12;'>"
            "<b style='color:#B7770D;'>Threats</b><br>" +
            "".join(f"<p style='margin:4px 0;'>⚡ {t}</p>" for t in swot.get("threats", [])) +
            "</div>", unsafe_allow_html=True
        )

# ── Market Brands Table ───────────────────────────────────────────────────────
brands = data.get("brands", [])
if brands:
    st.markdown("### Current Market Brands")
    df_brands = pd.DataFrame(brands)
    if "price_inr" in df_brands.columns:
        df_brands["price_inr"] = df_brands["price_inr"].apply(
            lambda x: f"₹{x}" if x and not str(x).startswith("₹") else x
        )
    st.dataframe(df_brands, use_container_width=True, hide_index=True)

    if "price_inr" in df_brands.columns:
        try:
            price_vals = [float(str(b.get("price_inr", 0)).replace("₹", "").replace(",", ""))
                          for b in brands if b.get("price_inr")]
            if price_vals:
                fig_price = px.histogram(
                    x=price_vals,
                    nbins=8,
                    title="Price Distribution (INR)",
                    labels={"x": "Price (INR)", "y": "Number of Brands"},
                    color_discrete_sequence=["#2E86AB"],
                )
                fig_price.update_layout(height=280, margin=dict(t=40, b=20))
                st.plotly_chart(fig_price, use_container_width=True)
        except Exception:
            pass

# ── Formulation Gaps ──────────────────────────────────────────────────────────
gaps = data.get("formulation_gaps", [])
if gaps:
    st.markdown("### Formulation Gaps (Unmet Needs)")
    for gap in gaps:
        st.markdown(f"- {gap}")

# ── AI Insight ────────────────────────────────────────────────────────────────
ai_insight = data.get("ai_insight", "")
if ai_insight:
    st.markdown("### AI Strategic Insight")
    st.info(ai_insight)

# ── Data Source Transparency ──────────────────────────────────────────────────
with st.expander("Data Sources & Methodology"):
    st.markdown("""
    **Market data sources:**
    - IQVIA India PharmaTrac (brand-level sales)
    - CDSCO/DCGI product registry
    - NPPA (National Pharmaceutical Pricing Authority) price data
    - India Brand Equity Foundation (IBEF) pharma reports
    - PharmIntel curated database (updated quarterly)

    **Scoring methodology:**
    - Market Attractiveness Score: weighted composite of market size, growth rate, unmet need, and regulatory accessibility
    - Market Saturation Index: brand density, price competition intensity, generic penetration rate
    """)

st.divider()
st.info("Go to **Competitor Intelligence** to analyse competitive landscape.")
