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

# API routes. All under /api so the static mount does not collide.
#
# ORDER IS LOAD-BEARING. Starlette matches routes in registration order, and a
# `Mount("/")` matches every path. Registering the static mount first makes it
# swallow all API routes below, which surfaces as a baffling 404/405 on every
# endpoint. Always mount last, or mount at a real prefix like /static.
app.include_router(cards.router, prefix="/api", tags=["cards"])


@app.get("/api/healthz")
def healthz() -> dict[str, str]:
    """Cheap liveness probe. Returns the same shape on every call."""
    return {"status": "ok"}


# Static frontend served at /. Registered LAST — see the ordering note above.
# The SPA is three files: index.html, app.js, styles.css.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
