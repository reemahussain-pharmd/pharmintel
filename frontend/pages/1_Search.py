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

st.set_page_config(page_title="Literature Search — PharmIntel", page_icon="🔍", layout="wide")
render_sidebar()

st.title("🔍 PubMed Literature Search")
st.markdown("Search peer-reviewed pharmaceutical literature from PubMed's 36 million article database.")
st.divider()

# ── Search Form ───────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    drug_name = st.text_input("Drug name", placeholder="e.g. metformin, amlodipine, omeprazole",
                               label_visibility="collapsed")
with col2:
    max_results = st.selectbox("Results", [5, 10, 15, 20], index=1, label_visibility="collapsed")
with col3:
    search_btn = st.button("Search PubMed", type="primary", use_container_width=True)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("Advanced Filters", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_year_min = st.number_input("From year", min_value=1990, max_value=2026, value=2015)
    with fc2:
        filter_year_max = st.number_input("To year", min_value=1990, max_value=2026, value=2026)
    with fc3:
        filter_study_type = st.multiselect(
            "Study type filter",
            ["RCT / Meta-Analysis", "Cohort / Observational", "In vitro / Animal"],
            default=[],
        )

# ── Search Logic ──────────────────────────────────────────────────────────────
if search_btn and drug_name.strip():
    with st.spinner("Searching PubMed literature..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/search",
                json={"drug_name": drug_name.strip().lower(), "max_results": max_results},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                papers = data.get("papers", [])
                total = data.get("total_found", 0)

                # Apply year filter
                if papers and (filter_year_min > 1990 or filter_year_max < 2026):
                    papers = [p for p in papers
                              if filter_year_min <= (p.get("year") or 0) <= filter_year_max]

                st.session_state["last_search_drug"] = drug_name.strip().lower()
                st.session_state["last_search_papers"] = papers
                st.session_state["search_response"] = data

                if papers:
                    st.success(f"Found {total:,} papers on PubMed — showing top {len(papers)}")

                    # ── Executive KPI Cards ────────────────────────────────────
                    st.markdown("### Drug Intelligence Summary")
                    k1, k2, k3, k4 = st.columns(4)

                    years = [p.get("year") for p in papers if p.get("year")]
                    journals = [p.get("journal", "") for p in papers]
                    year_range = f"{min(years)}–{max(years)}" if years else "N/A"
                    unique_journals = len(set(journals))
                    avg_year = int(sum(years) / len(years)) if years else 0
                    recent_5yr = sum(1 for y in years if y and y >= 2020)

                    k1.metric("Total Papers Retrieved", len(papers))
                    k2.metric("Publication Span", year_range)
                    k3.metric("Unique Journals", unique_journals)
                    k4.metric("Recent (2020+)", f"{recent_5yr} papers")

                    # ── Literature Trend Chart ─────────────────────────────────
                    if years:
                        st.markdown("### Publication Trend")
                        year_counts = pd.Series(years).value_counts().sort_index()
                        fig_trend = px.bar(
                            x=year_counts.index,
                            y=year_counts.values,
                            labels={"x": "Year", "y": "Number of Papers"},
                            color=year_counts.values,
                            color_continuous_scale="Blues",
                            title=f"Research Output Over Time — {drug_name.title()}",
                        )
                        fig_trend.update_layout(
                            showlegend=False,
                            coloraxis_showscale=False,
                            height=300,
                            margin=dict(t=40, b=20),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)

                    # ── Search Analytics ───────────────────────────────────────
                    with st.expander("Search Analytics", expanded=False):
                        ac1, ac2 = st.columns(2)
                        with ac1:
                            # Top journals
                            journal_counts = pd.Series(journals).value_counts().head(6)
                            fig_j = px.bar(
                                x=journal_counts.values,
                                y=[j[:35] for j in journal_counts.index],
                                orientation="h",
                                title="Top Journals",
                                color=journal_counts.values,
                                color_continuous_scale="Greens",
                            )
                            fig_j.update_layout(showlegend=False, coloraxis_showscale=False,
                                                height=280, margin=dict(t=40, b=10))
                            st.plotly_chart(fig_j, use_container_width=True)
                        with ac2:
                            # Decade distribution
                            def decade(y):
                                if not y:
                                    return "Unknown"
                                return f"{(y // 10) * 10}s"
                            decade_data = pd.Series([decade(p.get("year")) for p in papers]).value_counts()
                            fig_d = px.pie(
                                names=decade_data.index,
                                values=decade_data.values,
                                title="Papers by Decade",
                                color_discrete_sequence=px.colors.sequential.Blues_r,
                            )
                            fig_d.update_layout(height=280, margin=dict(t=40, b=10))
                            st.plotly_chart(fig_d, use_container_width=True)

                    st.divider()
                    st.markdown(f"### Literature Results — `{drug_name.title()}`")

                    for i, paper in enumerate(papers, 1):
                        year_str = str(paper.get("year", "")) if paper.get("year") else "Year N/A"
                        with st.expander(
                            f"**{i}. {paper['title'][:100]}{'...' if len(paper['title']) > 100 else ''}**",
                            expanded=(i == 1),
                        ):
                            col_a, col_b, col_c = st.columns([2, 1, 1])
                            with col_a:
                                st.markdown(f"**Authors:** {paper['authors']}")
                            with col_b:
                                st.markdown(f"**Journal:** {paper['journal'][:40]}")
                            with col_c:
                                st.markdown(f"**Year:** {year_str}")

                            abstract = paper.get("abstract", "No abstract available.")
                            if len(abstract) > 500:
                                st.markdown(abstract[:500] + "...")
                                with st.expander("Read full abstract"):
                                    st.markdown(abstract)
                            else:
                                st.markdown(abstract)

                            st.markdown(f"[Open on PubMed →]({paper['url']})")

                    st.divider()
                    st.info("Papers saved. Go to **NLP Analysis** to extract pharmaceutical entities.")
                else:
                    st.warning(
                        f"No papers found for '{drug_name}' in the selected year range. "
                        "Try broadening the year filter or use a generic drug name."
                    )
            else:
                st.error(f"Search failed. Backend returned: {response.status_code}")

        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend. Make sure the FastAPI server is running.")
        except requests.exceptions.Timeout:
            st.error("Search timed out. PubMed may be slow — please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")

elif search_btn and not drug_name.strip():
    st.warning("Please enter a drug name before searching.")

# ── Recent Search History ─────────────────────────────────────────────────────
st.divider()
st.markdown("### Recent Searches")
try:
    hist_response = requests.get(f"{BACKEND_URL}/api/v1/searches/recent", timeout=5)
    if hist_response.status_code == 200:
        searches = hist_response.json().get("searches", [])
        if searches:
            df = pd.DataFrame(searches)
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            df.columns = ["Drug Name", "Papers Found", "Searched At"]
            df["Drug Name"] = df["Drug Name"].str.title()
            st.dataframe(df, use_container_width=True, hide_index=True)

            unique_drugs = list(dict.fromkeys([s["drug_name"] for s in searches]))
            st.markdown("**Quick re-search:**")
            cols = st.columns(min(len(unique_drugs), 5))
            for i, drug in enumerate(unique_drugs[:5]):
                with cols[i]:
                    if st.button(drug.title(), key=f"quick_{drug}"):
                        st.session_state["quick_search"] = drug
                        st.rerun()
        else:
            st.caption("No searches yet.")
    else:
        st.caption("Could not load search history.")
except Exception:
    st.caption("Search history unavailable — backend may be offline.")

if "quick_search" in st.session_state:
    drug = st.session_state.pop("quick_search")
    with st.spinner(f"Re-searching {drug}..."):
        try:
            r = requests.post(f"{BACKEND_URL}/api/v1/search",
                              json={"drug_name": drug, "max_results": 10}, timeout=30)
            if r.status_code == 200:
                d = r.json()
                st.session_state["last_search_drug"] = drug
                st.session_state["last_search_papers"] = d.get("papers", [])
                st.session_state["search_response"] = d
                st.success(f"Re-searched {drug.title()} — scroll up to see results.")
        except Exception:
            st.error("Re-search failed.")
