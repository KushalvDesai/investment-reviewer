from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import DeleteMonthResponse, MonthsResponse, UploadResponse
from services import embeddings as emb_service
from services import pinecone_client as pc
from services.pdf_parser import parse_pdf
from utils.chunker import chunk_document

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF upload, parse it, chunk it, embed chunks, and upsert to Pinecone.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Parse PDF
    parsed = parse_pdf(file_bytes, file.filename)

    if parsed.month_key == "unknown":
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not detect a statement date in the PDF. "
                "Ensure it contains a pattern like 'Statement Period: MM/YYYY' or 'Month: January 2025'."
            ),
        )

    # Chunk document
    chunks = chunk_document(parsed, source_filename=file.filename)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text content could be extracted from the PDF.")

    chunk_texts = [c.text for c in chunks]
    chunk_dicts = [c.metadata for c in chunks]

    # Embed all chunks
    embeddings = await emb_service.get_embeddings(chunk_texts)

    # Upsert to Pinecone
    namespace = parsed.month_key
    upserted = pc.upsert_chunks(chunk_dicts, embeddings, namespace=namespace)

    return UploadResponse(
        month_key=parsed.month_key,
        chunks_indexed=upserted,
        namespace=namespace,
    )


@router.get("/months", response_model=MonthsResponse)
async def list_months():
    """Return all stored month_keys from Pinecone namespaces."""
    months = pc.list_namespaces()
    return MonthsResponse(months=months)


@router.delete("/month/{month_key}", response_model=DeleteMonthResponse)
async def delete_month(month_key: str):
    """Delete a namespace (and all its vectors) from Pinecone."""
    pc.delete_namespace(month_key)
    return DeleteMonthResponse(deleted=True, month_key=month_key)
