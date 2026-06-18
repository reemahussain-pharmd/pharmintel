# File: backend/services/pubmed.py
# Purpose: Search PubMed for pharmaceutical literature using Biopython Entrez API
# Connects to: routes/search.py (called by POST /api/v1/search)
# Simple explanation: Biopython's Entrez module is an official NCBI tool that
# lets us search PubMed exactly like a scientist would, but automatically.

import os
from Bio import Entrez
from dotenv import load_dotenv
from backend.models.schemas import Paper, SearchResponse

load_dotenv()

# NCBI requires an email so they can contact you if your script causes issues
Entrez.email = os.getenv("PUBMED_EMAIL", "reemahussain2097@gmail.com")


async def search_pubmed(drug_name: str, max_results: int = 10) -> SearchResponse:
    """
    Search PubMed for papers about a drug.
    Returns structured paper data including title, authors, abstract, and link.
    """
    papers = []

    try:
        # Step 1: Search PubMed for paper IDs matching the drug name
        # We add [tiab] to search in titles and abstracts only — more relevant results
        search_term = f"{drug_name}[tiab] AND (formulation OR pharmacokinetics OR drug delivery)"
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results, sort="relevance")
        search_results = Entrez.read(handle)
        handle.close()

        id_list = search_results.get("IdList", [])
        total_found = int(search_results.get("Count", 0))

        if not id_list:
            # Fallback: broader search with just the drug name
            handle = Entrez.esearch(db="pubmed", term=drug_name, retmax=max_results, sort="relevance")
            search_results = Entrez.read(handle)
            handle.close()
            id_list = search_results.get("IdList", [])
            total_found = int(search_results.get("Count", 0))

        if not id_list:
            return SearchResponse(drug_name=drug_name, papers=[], total_found=0)

        # Step 2: Fetch full details for each paper ID
        ids_joined = ",".join(id_list)
        handle = Entrez.efetch(db="pubmed", id=ids_joined, rettype="xml", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        # Step 3: Parse each record into our Paper model
        for record in records.get("PubmedArticle", []):
            try:
                paper = _parse_pubmed_record(record)
                if paper:
                    papers.append(paper)
            except Exception:
                continue  # Skip malformed records silently

    except Exception as e:
        # Return empty results rather than crashing — user sees a friendly message
        return SearchResponse(drug_name=drug_name, papers=[], total_found=0)

    return SearchResponse(
        drug_name=drug_name,
        papers=papers,
        total_found=total_found if papers else 0,
    )


def _parse_pubmed_record(record: dict) -> Paper | None:
    """Extract clean fields from a raw PubMed XML record."""
    try:
        article = record["MedlineCitation"]["Article"]

        # Title
        title = str(article.get("ArticleTitle", "No title available"))

        # Authors — join up to 5 authors, then add "et al."
        author_list = article.get("AuthorList", [])
        authors = _parse_authors(author_list)

        # Journal and year
        journal_info = article.get("Journal", {})
        journal = str(journal_info.get("Title", "Unknown Journal"))
        pub_date = journal_info.get("JournalIssue", {}).get("PubDate", {})
        year = _parse_year(pub_date)

        # Abstract
        abstract_obj = article.get("Abstract", {})
        abstract_texts = abstract_obj.get("AbstractText", [])
        if isinstance(abstract_texts, list):
            abstract = " ".join(str(t) for t in abstract_texts)
        else:
            abstract = str(abstract_texts)

        if not abstract:
            abstract = "No abstract available."

        # PubMed ID and URL
        pubmed_id = str(record["MedlineCitation"]["PMID"])
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"

        return Paper(
            pubmed_id=pubmed_id,
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            abstract=abstract,
            url=url,
        )

    except Exception:
        return None


def _parse_authors(author_list: list) -> str:
    """Format author list as 'Smith J, Jones A, et al.'"""
    names = []
    for author in author_list[:5]:
        last = author.get("LastName", "")
        initials = author.get("Initials", "")
        if last:
            names.append(f"{last} {initials}".strip())
    if not names:
        return "Unknown Authors"
    result = ", ".join(names)
    if len(author_list) > 5:
        result += " et al."
    return result


def _parse_year(pub_date: dict) -> int | None:
    """Extract publication year from PubMed date object."""
    try:
        return int(str(pub_date.get("Year", "")))
    except (ValueError, TypeError):
        medline_date = str(pub_date.get("MedlineDate", ""))
        if medline_date:
            try:
                return int(medline_date[:4])
            except ValueError:
                pass
    return None
