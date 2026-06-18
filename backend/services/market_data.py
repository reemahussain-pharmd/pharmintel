# File: backend/services/market_data.py
# Purpose: Indian pharmaceutical market intelligence and competitor analysis
# Connects to: routes/market.py, routes/competitor.py, data/india_market_data.json
# Flow: Load JSON → match drug → structure data → RAG context → Gemini insight

import json
import os
from backend.services.rag_engine import retrieve_context
from backend.services.ai_engine import generate_text_sync
from ai.prompts import SYSTEM_PHARMA_EXPERT, MARKET_INTELLIGENCE_PROMPT, COMPETITOR_LANDSCAPE_PROMPT

_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load_india_data() -> dict:
    path = os.path.join(_BASE, "india_market_data.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_drug(drug_name: str, market_data: dict) -> dict | None:
    """Case-insensitive drug lookup. Returns drug entry or None."""
    drugs = market_data.get("drugs", {})
    name_lower = drug_name.lower().strip()
    # Exact match first
    if name_lower in drugs:
        return drugs[name_lower]
    # Partial match
    for key in drugs:
        if name_lower in key or key in name_lower:
            return drugs[key]
    return None


async def get_market_intelligence(drug_name: str) -> dict:
    """
    Returns structured Indian market data for a drug + Gemini-generated market insight.
    Gemini receives the structured data + RAG context — it does NOT guess from training data.
    """
    market_data = _load_india_data()
    drug_entry = _find_drug(drug_name, market_data)

    # Build structured market summary
    market_summary = {
        "drug_name": drug_name,
        "found_in_database": drug_entry is not None,
        "regulatory_authority": market_data.get("regulatory_authority", "CDSCO"),
        "registration_body": market_data.get("registration_body", "DCGI"),
        "market_size_usd_billion": market_data.get("market_size_usd_billion", 50.0),
        "market_characteristics": market_data.get("market_characteristics", []),
    }

    if drug_entry:
        market_summary.update({
            "approved_forms": drug_entry.get("approved_forms", []),
            "major_brands": drug_entry.get("major_brands", []),
            "local_manufacturers": drug_entry.get("local_manufacturers", []),
            "dominant_manufacturer": drug_entry.get("dominant_manufacturer", ""),
            "market_gaps": drug_entry.get("market_gap", []),
            "market_notes": drug_entry.get("market_notes", ""),
            "approximate_price_inr": drug_entry.get("approximate_price_inr", ""),
            "therapeutic_class": drug_entry.get("therapeutic_class", ""),
        })
    else:
        market_summary.update({
            "approved_forms": [],
            "major_brands": [],
            "local_manufacturers": [],
            "dominant_manufacturer": "",
            "market_gaps": ["No specific data available — manual research recommended"],
            "market_notes": f"No pre-loaded market data found for {drug_name}.",
            "approximate_price_inr": "",
            "therapeutic_class": "",
        })

    # Retrieve RAG context for richer Gemini analysis
    rag_chunks = await retrieve_context(drug_name, f"{drug_name} Indian market formulation", n_results=2)
    rag_text = ""
    if rag_chunks:
        rag_text = "\n".join([
            f"- [{c.get('year','')}] {c.get('title','')[:70]}: {c.get('text','')[:150]}"
            for c in rag_chunks
        ])
    else:
        rag_text = "No literature context retrieved. Base analysis on market database only."

    # Generate Gemini market insight
    market_data_str = json.dumps({
        "approved_forms": market_summary.get("approved_forms"),
        "major_brands": market_summary.get("major_brands"),
        "local_manufacturers": market_summary.get("local_manufacturers"),
        "market_gaps": market_summary.get("market_gaps"),
        "dominant_manufacturer": market_summary.get("dominant_manufacturer"),
        "therapeutic_class": market_summary.get("therapeutic_class"),
        "market_notes": market_summary.get("market_notes"),
    }, indent=2)

    try:
        ai_insight = generate_text_sync(
            SYSTEM_PHARMA_EXPERT,
            MARKET_INTELLIGENCE_PROMPT.format(
                drug_name=drug_name,
                market_data_json=market_data_str,
                rag_context=rag_text,
            ),
            max_tokens=300,
        )
    except Exception:
        ai_insight = _fallback_market_insight(drug_name, market_summary)

    market_summary["ai_market_insight"] = ai_insight
    market_summary["rag_sources_used"] = [c.get("title", "") for c in rag_chunks]

    return market_summary


async def get_competitor_intelligence(drug_name: str) -> dict:
    """
    Returns competitor brand analysis for a drug in India + Gemini competitive summary.
    """
    market_data = _load_india_data()
    drug_entry = _find_drug(drug_name, market_data)

    if not drug_entry:
        competitor_data = {
            "drug_name": drug_name,
            "found_in_database": False,
            "brands": [],
            "manufacturers": [],
            "message": f"No competitor data found for {drug_name} in our database.",
        }
    else:
        brands = drug_entry.get("major_brands", [])
        manufacturers = drug_entry.get("local_manufacturers", [])
        dominant = drug_entry.get("dominant_manufacturer", "")
        approved_forms = drug_entry.get("approved_forms", [])
        gaps = drug_entry.get("market_gap", [])

        # Build brand-level detail table
        brand_details = []
        for brand in brands:
            brand_details.append({
                "brand": brand,
                "available_in_india": True,
                "dosage_forms": approved_forms,
            })

        competitor_data = {
            "drug_name": drug_name,
            "found_in_database": True,
            "brands": brands,
            "brand_details": brand_details,
            "manufacturers": manufacturers,
            "dominant_manufacturer": dominant,
            "approved_forms": approved_forms,
            "market_gaps": gaps,
            "therapeutic_class": drug_entry.get("therapeutic_class", ""),
            "price_range_inr": drug_entry.get("approximate_price_inr", ""),
        }

    # Gemini competitive summary
    rag_chunks = await retrieve_context(drug_name, f"{drug_name} competitor brand market", n_results=2)
    rag_text = "\n".join([
        f"- {c.get('title','')[:60]}: {c.get('text','')[:120]}"
        for c in rag_chunks
    ]) if rag_chunks else "No literature context available."

    try:
        ai_summary = generate_text_sync(
            SYSTEM_PHARMA_EXPERT,
            COMPETITOR_LANDSCAPE_PROMPT.format(
                drug_name=drug_name,
                competitor_data_json=json.dumps(competitor_data, indent=2),
            ),
            max_tokens=250,
        )
    except Exception:
        ai_summary = (
            f"The Indian {drug_name} market is competitive with "
            f"{len(competitor_data.get('brands', []))} major brands identified. "
            f"Market gaps include: {', '.join(competitor_data.get('market_gaps', [])[:2])}."
        )

    competitor_data["ai_competitive_summary"] = ai_summary
    return competitor_data


def _fallback_market_insight(drug_name: str, summary: dict) -> str:
    gaps = summary.get("market_gaps", [])
    brands = summary.get("major_brands", [])
    gap_str = gaps[0] if gaps else "novel delivery systems"
    brand_str = ", ".join(brands[:3]) if brands else "multiple generic brands"
    return (
        f"The Indian {drug_name} market is regulated by CDSCO/DCGI and currently "
        f"served by brands including {brand_str}. "
        f"A key R&D opportunity exists in developing {gap_str}, "
        f"which is currently underrepresented in the Indian market."
    )
