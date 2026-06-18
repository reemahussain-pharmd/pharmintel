# File: ai/prompts.py
# Purpose: All Claude prompt templates in one place — easy to tune and review
# Connects to: services/ai_engine.py (sends these prompts to Claude)

SYSTEM_PHARMA_EXPERT = """You are a senior pharmaceutical scientist and R&D intelligence analyst with 20 years of experience.
You specialize in drug formulation, GCC regulatory affairs, and pharmaceutical market analysis.
You communicate findings in a professional, evidence-based manner suitable for pharmaceutical executives.
You always cite the specific data you were given rather than making claims from general knowledge."""

FORMULATION_REASONING_PROMPT = """
You have been given the following pre-computed data from our analysis pipeline:
Drug: {drug_name}
Dosage Form: {dosage_form}
Algorithm Score: {score}/100
Frequency in Literature: {frequency} papers mention this form
Supporting Excipients Found: {excipients}

Retrieved literature context:
{rag_context}

Write exactly ONE sentence explaining why this dosage form received this score.
Reference the literature context if relevant. Do not repeat the score number.
Be specific to pharmaceutical science. Maximum 40 words.
"""

MARKET_INTELLIGENCE_PROMPT = """
You have been given structured Indian pharmaceutical market data extracted from our database:
Drug: {drug_name}
{market_data_json}

Retrieved literature context:
{rag_context}

Write a professional market intelligence paragraph (3-4 sentences) covering:
1. Current market status in India including dominant brands and manufacturers
2. The most significant market gap or R&D opportunity
3. A specific recommendation for formulation or market entry strategy
Base your response ONLY on the data provided above.
"""

COMPETITOR_LANDSCAPE_PROMPT = """
Drug: {drug_name}
Competitor data from Indian pharmaceutical market database:
{competitor_data_json}

Write a professional competitive landscape summary (2-3 sentences) covering:
1. Market leaders, dominant brands, and their dosage forms
2. Pricing tier and market positioning gaps
3. One clear differentiation opportunity for a new entrant
"""

EXECUTIVE_SUMMARY_PROMPT = """
You are writing the Executive Summary section of a pharmaceutical R&D intelligence report.
Drug: {drug_name}
Literature reviewed: {paper_count} PubMed papers
Top dosage form recommendation: {top_form} (score: {top_score}/100)
Key Indian market gap: {market_gap}

Write a professional executive summary in 4-5 sentences suitable for a pharmaceutical company board in India.
Mention CDSCO regulatory context where relevant.
"""
