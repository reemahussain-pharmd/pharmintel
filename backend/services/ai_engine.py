# File: backend/services/ai_engine.py
# Purpose: Gemini API integration — interpretation and language generation ONLY
# Connects to: services/formulation.py, services/market_data.py
# ARCHITECTURE NOTE: Gemini receives pre-computed scores and structured data.
# It generates professional language — it does NOT make decisions or extract data.

import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def generate_text(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Send a prompt to Gemini REST API and return the text response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be set in your .env file")

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def generate_text_sync(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Synchronous version for use outside async contexts."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be set in your .env file")

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
