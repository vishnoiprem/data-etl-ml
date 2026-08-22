from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.enterprise_search.data import DOCUMENTS
from src.enterprise_search.index import LocalIndex, FederatedConnector
from src.enterprise_search.tools import ToolRegistry, Tool, get_order
from src.enterprise_search.agent import SearchAgent, evaluate_search

index = LocalIndex(DOCUMENTS)
tools = ToolRegistry()
tools.register(Tool("get_order", "Get an order by exact identifier", ["order_id"], get_order, True))
agent = SearchAgent(index, FederatedConnector(), tools)
app = FastAPI(title="Enterprise Search Agent", version="1.0.0")

class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    user_groups: list[str] = Field(default_factory=lambda: ["analytics"])
    run_id: str | None = None
    resume: bool = False

class EvalRequest(BaseModel):
    retrieved_ids: list[str]
    relevant_ids: list[str]
    k: int = 5

@app.get("/health")
def health(): return {"status": "healthy", "indexed_documents": len(DOCUMENTS), "tools": len(tools.tools)}
@app.get("/tools")
def list_tools(): return {"tools": tools.describe()}
@app.post("/search")
def search(req: SearchRequest):
    try: return agent.run(req.query, req.user_groups, req.run_id, req.resume)
    except Exception as exc: raise HTTPException(500, str(exc)) from exc
@app.post("/evaluate/search")
def evaluate(req: EvalRequest): return evaluate_search(req.retrieved_ids, req.relevant_ids, req.k)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
