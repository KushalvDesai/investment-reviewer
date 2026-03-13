from __future__ import annotations
import time
from collections import deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_MAX_REQUESTS = 30
_WINDOW_SECONDS = 60

# Maps IP -> deque of request timestamps (floats)
_request_log: dict[str, deque] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter: max 30 requests per minute per IP.
    Returns 429 with Retry-After header when exceeded.
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        if client_ip not in _request_log:
            _request_log[client_ip] = deque()

        window = _request_log[client_ip]

        # Evict timestamps older than the window
        cutoff = now - _WINDOW_SECONDS
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= _MAX_REQUESTS:
            oldest = window[0]
            retry_after = int(_WINDOW_SECONDS - (now - oldest)) + 1
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Retry after {retry_after} seconds.",
                },
            )

        window.append(now)
        return await call_next(request)
