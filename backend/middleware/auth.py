from __future__ import annotations
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


_PROTECTED_PREFIXES = ("/ingest", "/query")


class AuthMiddleware(BaseHTTPMiddleware):
    """Check Bearer token for all /ingest and /query routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES):
            api_key = os.environ.get("API_KEY", "")
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Missing Authorization header"},
                )
            token = auth_header[len("Bearer "):]
            if token != api_key:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Invalid API key"},
                )
        return await call_next(request)
