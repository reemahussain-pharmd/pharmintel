# File: frontend/components/charts.py
# Purpose: Reusable chart functions for all dashboard pages
# Connects to: pages/3_Formulation.py, pages/4_Market.py

import pandas as pd
import streamlit as st


def render_formulation_bar_chart(scores: list[dict]):
    """
    Renders a horizontal bar chart of dosage form scores.
    Green > 70, Orange 40-70, Red < 40.
    """
    if not scores:
        st.info("No scores to display yet. Run an analysis first.")
        return

    df = pd.DataFrame(scores)
    df = df.sort_values("score", ascending=True)

    # Assign colors based on score threshold
    def color_score(score):
        if score >= 70:
            return "#27AE60"
        elif score >= 40:
            return "#F39C12"
        else:
            return "#E74C3C"

    df["color"] = df["score"].apply(color_score)

    st.markdown("#### Dosage Form Feasibility Scores")
    for _, row in df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            progress = int(row["score"])
            color = row["color"]
            st.markdown(
                f"""
                <div style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                        <span style="font-weight: 600;">{row['dosage_form'].title()}</span>
                        <span style="color: {color}; font-weight: bold;">{progress}/100</span>
                    </div>
                    <div style="background: #e0e0e0; border-radius: 4px; height: 12px;">
                        <div style="background: {color}; width: {progress}%; height: 12px; border-radius: 4px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
