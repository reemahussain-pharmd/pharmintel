# File: frontend/pages/1_Search.py
# Purpose: PubMed literature search page — input, results table, search history
# Connects to: backend POST /api/v1/search, GET /api/v1/searches/recent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from frontend.components.sidebar import render_sidebar

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Literature Search — PharmIntel",
    page_icon="🔍",
    layout="wide",
)

render_sidebar()

st.title("🔍 PubMed Literature Search")
st.markdown("Search peer-reviewed pharmaceutical literature from PubMed's 36 million article database.")

st.divider()

# ── Search Form ──────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([4, 1, 1])

with col1:
    drug_name = st.text_input(
        "Drug name",
        placeholder="e.g. metformin, amlodipine, omeprazole",
        label_visibility="collapsed",
    )
with col2:
    max_results = st.selectbox("Results", [5, 10, 15, 20], index=1, label_visibility="collapsed")
with col3:
    search_btn = st.button("Search PubMed", type="primary", use_container_width=True)

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

                # Save to session state — both keys needed (pages + report)
                st.session_state["last_search_drug"] = drug_name.strip().lower()
                st.session_state["last_search_papers"] = papers
                st.session_state["search_response"] = data  # used by Report page

                if papers:
                    st.success(f"Found {total:,} papers on PubMed — showing top {len(papers)}")
                    st.markdown(f"**Results for:** `{drug_name}`")
                    st.divider()

                    # Display each paper as an expander card
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

                            st.markdown("**Abstract:**")
                            abstract = paper.get("abstract", "No abstract available.")
                            if len(abstract) > 500:
                                st.markdown(abstract[:500] + "...")
                                with st.expander("Read full abstract"):
                                    st.markdown(abstract)
                            else:
                                st.markdown(abstract)

                            st.markdown(f"[Open on PubMed →]({paper['url']})")

                    st.divider()
                    st.info(
                        "Papers saved to database. Go to **NLP Analysis** page to extract "
                        "pharmaceutical entities from these papers."
                    )
                else:
                    st.warning(
                        f"No papers found for '{drug_name}'. "
                        "Try a generic drug name (e.g. metformin instead of Glucophage)."
                    )
            else:
                st.error(f"Search failed. Backend returned: {response.status_code}")

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot reach the backend. Make sure you ran: "
                "`uvicorn backend.main:app --reload` in your terminal."
            )
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

            # Quick re-search button
            st.markdown("**Quick re-search:**")
            unique_drugs = list(dict.fromkeys([s["drug_name"] for s in searches]))
            cols = st.columns(min(len(unique_drugs), 5))
            for i, drug in enumerate(unique_drugs[:5]):
                with cols[i]:
                    if st.button(drug.title(), key=f"quick_{drug}"):
                        st.session_state["quick_search"] = drug
                        st.rerun()
        else:
            st.caption("No searches yet. Search for a drug above to get started.")
    else:
        st.caption("Could not load search history.")
except Exception:
    st.caption("Search history unavailable — backend may be offline.")

# Handle quick re-search
if "quick_search" in st.session_state:
    drug = st.session_state.pop("quick_search")
    with st.spinner(f"Searching for {drug}..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/search",
                json={"drug_name": drug, "max_results": 10},
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["last_search_drug"] = drug
                st.session_state["last_search_papers"] = data.get("papers", [])
                st.success(f"Re-searched {drug.title()} — {len(data.get('papers', []))} papers loaded. Scroll up to see results.")
        except Exception:
            st.error("Re-search failed.")
