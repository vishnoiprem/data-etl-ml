"""HTTP API for the enterprise search agent.

The API layer stays thin on purpose: validate input, call the agent, translate
exceptions into status codes. All the logic worth talking about lives in
``src/enterprise_search`` where it can be unit tested without HTTP.
"""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.enterprise_search.agent import SearchAgent
from src.enterprise_search.data import DOCUMENTS
from src.enterprise_search.evaluation import evaluate_search
from src.enterprise_search.index import FederatedConnector, LocalIndex
from src.enterprise_search.tools import ToolError, default_registry

logger = logging.getLogger(__name__)

# Built once at import time: the TF-IDF fit is the expensive part and the corpus
# is read-only. In production this becomes a client to a managed search service.
index = LocalIndex(DOCUMENTS)
tools = default_registry()
agent = SearchAgent(index, FederatedConnector(), tools)

app = FastAPI(
    title="Enterprise Search Agent",
    version="2.0.0",
    description="Query rewrite, fan-out, rank fusion, reranking, context budgeting, "
    "grounded answers with citations, MCP-style tool contracts, and offline evaluation.",
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000, examples=["How do we reduce context bloat?"])
    # The caller's group membership drives ACL filtering. In production this comes
    # from the validated auth token, never from the request body - a client that
    # can name its own groups can read anything.
    user_groups: list[str] = Field(default_factory=lambda: ["analytics"])
    run_id: str | None = Field(default=None, description="Reuse to resume a previous run.")
    resume: bool = Field(default=False, description="Replay completed steps from checkpoints.")


class EvalRequest(BaseModel):
    retrieved_ids: list[str]
    relevant_ids: list[str]
    k: int = Field(default=5, ge=1, le=100)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "indexed_documents": len(DOCUMENTS),
        "tools": len(tools.tools),
    }


@app.get("/tools")
def list_tools():
    """The tool catalogue, in MCP's ``name`` / ``description`` / ``inputSchema`` shape."""
    return {"tools": tools.describe()}


@app.post("/search")
def search(request: SearchRequest):
    try:
        return agent.run(request.query, request.user_groups, request.run_id, request.resume)
    except ToolError as exc:
        # The caller's fault: unknown tool or arguments that fail the schema.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Log the detail, return a generic message. Internal exception strings can
        # carry file paths, queries, and connection details - not for clients.
        logger.exception("search failed for query=%r", request.query)
        raise HTTPException(status_code=500, detail="Search failed. See server logs.") from exc


@app.post("/evaluate/search")
def evaluate(request: EvalRequest):
    return evaluate_search(request.retrieved_ids, request.relevant_ids, request.k)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
