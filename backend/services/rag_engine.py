# File: backend/services/rag_engine.py
# Purpose: ChromaDB RAG layer using TF-IDF embeddings (no model download required)
# Connects to: routes/analysis.py (embed), services/formulation.py (retrieve)
# How RAG works: paper abstracts → TF-IDF vectors → ChromaDB → query finds similar papers
# TF-IDF = Term Frequency-Inverse Document Frequency — counts important words per document

import os
import json
import math
import re
from collections import Counter
from functools import lru_cache
from backend.models.schemas import Paper
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# In-memory store: drug_name -> list of {id, text, metadata, vector}
_paper_store: dict[str, list[dict]] = {}
_idf_cache: dict[str, dict[str, float]] = {}


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer: lowercase, remove punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if len(w) > 2]


def _compute_tfidf(text: str, idf: dict[str, float]) -> dict[str, float]:
    """Convert text to a TF-IDF weighted word-frequency vector."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    tf = Counter(tokens)
    total = len(tokens)
    return {word: (count / total) * idf.get(word, 1.0) for word, count in tf.items()}


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two sparse TF-IDF vectors (0.0 to 1.0)."""
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[w] * vec_b[w] for w in common)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_idf(documents: list[str]) -> dict[str, float]:
    """Build IDF (Inverse Document Frequency) weights from a corpus of documents."""
    N = len(documents)
    df: dict[str, int] = {}
    for doc in documents:
        tokens = set(_tokenize(doc))
        for token in tokens:
            df[token] = df.get(token, 0) + 1
    return {word: math.log(N / count) for word, count in df.items()}


def _collection_key(drug_name: str) -> str:
    return drug_name.lower().strip().replace(" ", "_")


async def embed_papers(drug_name: str, papers: list[Paper]) -> int:
    """
    Embed all paper abstracts into the in-memory RAG store using TF-IDF.
    Returns the number of new papers embedded.
    """
    if not papers:
        return 0

    key = _collection_key(drug_name)
    if key not in _paper_store:
        _paper_store[key] = []

    existing_ids = {p["id"] for p in _paper_store[key]}
    new_docs = []

    for paper in papers:
        doc_id = f"{drug_name}_{paper.pubmed_id}"
        if doc_id in existing_ids:
            continue
        text = f"{paper.title}. {paper.abstract}"
        new_docs.append({
            "id": doc_id,
            "text": text,
            "metadata": {
                "pubmed_id": paper.pubmed_id,
                "title": paper.title[:200],
                "authors": paper.authors[:100],
                "year": str(paper.year or ""),
                "journal": paper.journal[:100],
                "url": paper.url,
                "drug_name": drug_name,
            },
            "vector": None,    # computed after IDF is built
        })

    if not new_docs:
        return 0

    # Rebuild IDF over all documents (existing + new)
    all_docs = _paper_store[key] + new_docs
    all_texts = [d["text"] for d in all_docs]
    idf = _build_idf(all_texts)
    _idf_cache[key] = idf

    # Compute TF-IDF vectors for all documents
    for doc in all_docs:
        doc["vector"] = _compute_tfidf(doc["text"], idf)

    _paper_store[key] = all_docs
    return len(new_docs)


async def retrieve_context(drug_name: str, query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieve the most relevant paper chunks for a given query using cosine similarity.
    Returns ranked list of paper dicts with relevance scores.
    """
    key = _collection_key(drug_name)
    store = _paper_store.get(key, [])

    if not store:
        return []

    idf = _idf_cache.get(key, {})
    query_vec = _compute_tfidf(query, idf)

    # Score every document against the query
    scored = []
    for doc in store:
        sim = _cosine_similarity(query_vec, doc.get("vector", {}))
        scored.append((sim, doc))

    # Sort by similarity descending
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for sim, doc in scored[:n_results]:
        if sim > 0:
            meta = doc["metadata"]
            results.append({
                "text": doc["text"][:600],
                "title": meta.get("title", "Unknown"),
                "authors": meta.get("authors", ""),
                "year": meta.get("year", ""),
                "url": meta.get("url", ""),
                "pubmed_id": meta.get("pubmed_id", ""),
                "relevance_score": round(sim, 3),
            })

    return results


def get_collection_stats(drug_name: str) -> dict:
    """Return how many papers are embedded for a drug."""
    key = _collection_key(drug_name)
    store = _paper_store.get(key, [])
    return {"embedded": len(store) > 0, "count": len(store)}
