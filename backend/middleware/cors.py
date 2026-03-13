from __future__ import annotations
import os

from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app) -> None:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    origins = ["http://localhost:3000"]
    if frontend_url not in origins:
        origins.append(frontend_url)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
