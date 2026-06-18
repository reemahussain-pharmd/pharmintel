# File: backend/services/formulation.py
# Purpose: Orchestrates formulation feasibility pipeline
# Flow: rule_engine (Python scores) → RAG retrieval (relevant literature) → Gemini (one sentence per form)
# Connects to: routes/formulation.py, rule_engine.py, rag_engine.py, ai_engine.py

from backend.models.schemas import FormulationRequest, FormulationResponse, FormulationScore, ReportRequest, ConfidenceScore
from backend.services.rule_engine import score_dosage_forms
from backend.services.rag_engine import embed_papers, retrieve_context
from backend.services.ai_engine import generate_text_sync
from backend.services.confidence_scorer import calculate_formulation_confidence
from ai.prompts import SYSTEM_PHARMA_EXPERT, FORMULATION_REASONING_PROMPT


async def assess_formulation(request: FormulationRequest) -> FormulationResponse:
    """
    Full formulation feasibility pipeline:
    1. Embed papers into ChromaDB (RAG setup)
    2. Rule engine scores all dosage forms (pure Python — deterministic)
    3. For each form, retrieve relevant literature context from ChromaDB
    4. Gemini writes one sentence using the score + retrieved context
    """
    # Step 1: Embed papers into ChromaDB so RAG can retrieve them
    await embed_papers(request.drug_name, request.papers)

    # Step 2: Score with rule engine — deterministic Python logic
    scores = score_dosage_forms(
        drug_name=request.drug_name,
        papers=request.papers,
        analyses=request.paper_analyses,
    )

    # Collect found excipients for the prompt
    found_excipients: list[str] = []
    for analysis in request.paper_analyses:
        for ex in analysis.excipients:
            if ex not in found_excipients:
                found_excipients.append(ex)

    # Track which papers were retrieved as RAG sources
    all_rag_sources: list[str] = []

    # Step 3 & 4: For each scored form, retrieve context → Gemini reasoning
    for score in scores:
        try:
            # Retrieve most relevant paper chunks for this dosage form query
            rag_chunks = await retrieve_context(
                drug_name=request.drug_name,
                query=f"{request.drug_name} {score.dosage_form} formulation",
                n_results=2,
            )

            # Format context for the prompt
            if rag_chunks:
                rag_context = "\n".join([
                    f"- [{c.get('year', '')}] {c.get('title', '')[:80]}: {c.get('text', '')[:200]}"
                    for c in rag_chunks
                ])
                # Track source titles
                for c in rag_chunks:
                    title = c.get("title", "")
                    if title and title not in all_rag_sources:
                        all_rag_sources.append(title[:80])
            else:
                rag_context = "No specific literature retrieved for this dosage form."

            prompt = FORMULATION_REASONING_PROMPT.format(
                drug_name=request.drug_name,
                dosage_form=score.dosage_form,
                score=score.score,
                frequency=score.frequency,
                excipients=", ".join(found_excipients[:5]) if found_excipients else "none identified",
                rag_context=rag_context,
            )

            reasoning = generate_text_sync(SYSTEM_PHARMA_EXPERT, prompt, max_tokens=120)
            score.reasoning = reasoning.strip()

        except Exception:
            score.reasoning = _fallback_reasoning(score)

        # Attach confidence score
        conf = calculate_formulation_confidence(
            frequency=score.frequency,
            total_papers=len(request.papers),
            rule_score=score.score,
            paper_titles=[p.title for p in request.papers],
            paper_abstracts=[p.abstract for p in request.papers],
        )
        score.confidence = ConfidenceScore(
            score=conf["score"],
            level=conf["level"],
            color=conf["color"],
        )

    top = scores[0].dosage_form.title() if scores else "Insufficient data"

    return FormulationResponse(
        drug_name=request.drug_name,
        scores=scores,
        top_recommendation=top,
        rag_sources=all_rag_sources[:5],
    )


def _fallback_reasoning(score: FormulationScore) -> str:
    """Rule-based fallback when Gemini is unavailable."""
    form = score.dosage_form.title()
    s = score.score
    freq = score.frequency
    if s >= 70:
        return (
            f"{form} is strongly supported by {freq} literature source(s) "
            f"and scores highly on manufacturing feasibility and patient compliance."
        )
    elif s >= 40:
        return (
            f"{form} shows moderate feasibility with limited literature support "
            f"and formulation rule compatibility for this drug class."
        )
    else:
        return (
            f"{form} scores low due to limited literature support "
            f"or formulation complexity concerns for this drug class."
        )


async def generate_pdf_report(request: ReportRequest) -> dict:
    """
    Generate a 10-section PDF and upload to Supabase Storage.
    Returns base64-encoded PDF bytes so the Streamlit frontend can serve a download
    button directly — works whether frontend and backend are on the same machine or
    on different servers (Render.com + Streamlit Cloud).
    """
    import base64
    from backend.services.pdf_generator import generate_pdf, save_and_upload_pdf

    pdf_bytes = generate_pdf(request)
    result = await save_and_upload_pdf(pdf_bytes, request.drug_name)

    return {
        "status": "success",
        "drug_name": request.drug_name,
        "filename": result["filename"],
        "pdf_bytes_b64": base64.b64encode(pdf_bytes).decode("utf-8"),
        "public_url": result["public_url"],
        "pdf_size_kb": round(len(pdf_bytes) / 1024, 1),
    }
