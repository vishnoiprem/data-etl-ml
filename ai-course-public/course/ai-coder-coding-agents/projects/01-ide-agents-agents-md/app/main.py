"""
FastAPI app factory for the Kanban board.

This file is intentionally minimal — route definitions live in `routers/`.
The point of the split is that LLMs editing routes should never need to touch
the app factory, and the app factory should never need to know which routers
exist.

Run:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import cards

app = FastAPI(
    title="Kanban Board API",
    version="0.1.0",
    description="Single-board Kanban for the AI Coder course capstone.",
)

# Static frontend served at /. The SPA is two files: app.js and styles.css.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# API routes. All under /api so the static mount does not collide.
app.include_router(cards.router, prefix="/api", tags=["cards"])


@app.get("/api/healthz")
def healthz() -> dict[str, str]:
    """Cheap liveness probe. Returns the same shape on every call."""
    return {"status": "ok"}
