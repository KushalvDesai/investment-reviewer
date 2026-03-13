from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.schemas import (
    AnalyzeRequest,
    AskRequest,
    AskResponse,
    CompareRequest,
    MonthComparisonResult,
    SingleMonthAnalysis,
    SourceChunk,
)
from services import embeddings as emb_service
from services import groq_client as groq
from services import pinecone_client as pc

router = APIRouter()

_COMPARISON_QUERY = "income expenses profit loss summary transactions"


@router.post("/analyze", response_model=SingleMonthAnalysis)
async def analyze_month(body: AnalyzeRequest):
    """
    Embed the user question, retrieve context from the specified month's namespace,
    and return a structured LLM analysis.
    """
    months = pc.list_namespaces()
    if body.month_key not in months:
        raise HTTPException(
            status_code=404,
            detail=f"No statement found for month {body.month_key}.",
        )

    vectors = await emb_service.get_embeddings([body.question])
    matches = pc.query_namespace(vectors[0], namespace=body.month_key, top_k=8)

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No relevant chunks found for month {body.month_key}.",
        )

    context_chunks = [m["metadata"].get("text", "") for m in matches]
    result = groq.analyze_single_month(context_chunks, body.month_key, body.question)

    # Handle groq returning an error dict (shouldn't happen here, but guard anyway)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result.get("message", "LLM error"))

    return SingleMonthAnalysis(**result)


@router.post("/compare")
async def compare_months(body: CompareRequest):
    """
    Retrieve context from both months and return a structured month-over-month comparison.
    Returns MonthComparisonResult or an error object if previous month has no data.
    """
    vectors = await emb_service.get_embeddings([_COMPARISON_QUERY])
    query_vec = vectors[0]

    current_matches = pc.query_namespace(query_vec, namespace=body.current_month, top_k=8)
    previous_matches = pc.query_namespace(query_vec, namespace=body.previous_month, top_k=8)

    if not current_matches:
        raise HTTPException(
            status_code=404,
            detail=f"No statement found for current month {body.current_month}.",
        )

    current_context = [m["metadata"].get("text", "") for m in current_matches]
    previous_context = [m["metadata"].get("text", "") for m in previous_matches]

    result = groq.compare_months(
        current_context,
        previous_context,
        body.current_month,
        body.previous_month,
    )

    if "error" in result:
        # Return the error object as-is with a 404 status
        raise HTTPException(
            status_code=404,
            detail=result.get("message", f"No data for {body.previous_month}"),
        )

    return MonthComparisonResult(**result)


@router.post("/ask", response_model=AskResponse)
async def ask_question(body: AskRequest):
    """
    Free-form question over one or more selected months using cross-namespace search.
    """
    if not body.months:
        raise HTTPException(status_code=400, detail="At least one month must be specified.")

    vectors = await emb_service.get_embeddings([body.question])
    matches = pc.query_cross_namespace(vectors[0], namespaces=body.months, top_k=5)

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No relevant context found for the selected months.",
        )

    context_chunks = [m["metadata"].get("text", "") for m in matches]
    answer = groq.answer_question(context_chunks, body.question)

    sources = [
        SourceChunk(
            month_key=m["metadata"].get("month_key", ""),
            chunk_preview=m["metadata"].get("text", "")[:200],
        )
        for m in matches
    ]

    return AskResponse(answer=answer, sources=sources)
