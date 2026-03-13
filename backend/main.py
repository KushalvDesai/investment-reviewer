from __future__ import annotations
import os

from dotenv import load_dotenv

load_dotenv()  # Must be called before any service imports that read env vars

from fastapi import FastAPI

from middleware.auth import AuthMiddleware
from middleware.cors import add_cors_middleware
from middleware.logging import LoggingMiddleware
from middleware.rate_limit import RateLimitMiddleware
from models.schemas import HealthResponse
from routers import ingest as ingest_router
from routers import query as query_router
from services import pinecone_client as pc

app = FastAPI(
    title="Investment Reviewer — Financial RAG API",
    version="1.0.0",
    description="RAG pipeline for monthly financial statement analysis.",
)

# ── Middleware (applied in reverse order; first registered = outermost) ───────
# Desired order: logging → cors → rate_limit → auth
# Starlette applies middleware in LIFO order during registration,
# so we register them outermost-last.
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
add_cors_middleware(app)
app.add_middleware(LoggingMiddleware)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(ingest_router.router, prefix="/ingest", tags=["ingest"])
app.include_router(query_router.router, prefix="/query", tags=["query"])


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    try:
        namespaces = pc.list_namespaces()
    except Exception:
        namespaces = []
    return HealthResponse(status="ok", pinecone_namespaces=namespaces)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
