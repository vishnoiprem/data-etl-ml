"""Host 2: FastAPI. Any HTTP caller is the client.

Run with:  uvicorn server:app --port 8000
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from index_wikipages import wikipage_list
from rag_agent import MODELS, build_agent

app = FastAPI(title="Wikipedia RAG ReAct API")

# One in-memory agent for the whole process. Restarting the server clears it.
# For multiple users, key this by session id instead.
STATE: dict = {"agent": None, "pages": [], "model": None}


class IndexRequest(BaseModel):
    pages: str = "Please index: 2023 United States banking crisis"
    model: str = MODELS[0]


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"ready": STATE["agent"] is not None, "pages": STATE["pages"], "model": STATE["model"]}


@app.post("/index")
def index_pages(req: IndexRequest):
    """Fetch the pages, embed them locally, and build the agent. Slow (seconds)."""
    if req.model not in MODELS:
        raise HTTPException(status_code=400, detail=f"model must be one of {MODELS}")
    try:
        # Defined with `def`, so FastAPI runs this blocking work in a threadpool.
        STATE["agent"] = build_agent(req.pages, req.model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Indexing failed: {exc}") from exc

    STATE["pages"] = wikipage_list(req.pages)
    STATE["model"] = req.model
    return {"status": "indexed", "pages": STATE["pages"], "model": req.model}


@app.post("/ask")
def ask(req: AskRequest):
    """Ask a question against the pages indexed by the last /index call."""
    agent = STATE["agent"]
    if agent is None:
        raise HTTPException(status_code=409, detail="Call POST /index first")
    try:
        answer = agent.chat(req.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The agent could not answer: {exc}") from exc
    return {"question": req.question, "answer": str(answer)}
