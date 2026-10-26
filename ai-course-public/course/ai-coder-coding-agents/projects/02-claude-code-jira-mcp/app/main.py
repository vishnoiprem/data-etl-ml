"""
FastAPI app factory for the AI Legal Doc Generator — Week 2 SaaS build.

Week 2 is built with Claude Code against Jira + GitHub MCP servers. This file
itself is small — it exists so Claude Code has the same starting point Week 1
did, and so the test suite has something to import.

Week 2 routes ('/api/jobs/*', '/api/documents/*') are added by the
`feature-builder` subagent from Jira tickets. This file is the seed, not the
finished product.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Legal Doc Generator",
    version="0.1.0",
    description="SaaS for generating legal documents with an LLM. JWT auth, queued jobs, Postgres.",
)

# CORS is configured narrowly here; wildcards here would defeat JWT auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.ai-legal-doc-generator.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/api/healthz")
def healthz() -> dict[str, str]:
    """Cheap liveness probe. No auth required."""
    return {"status": "ok"}


# Optional: include routers here as they land from Jira tickets.
#
# from app.routers import jobs, documents
# app.include_router(jobs.router, prefix="/api/jobs")
# app.include_router(documents.router, prefix="/api/documents")
