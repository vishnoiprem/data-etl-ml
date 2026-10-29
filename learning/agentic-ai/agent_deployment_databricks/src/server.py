import os
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .agent import Agent
from .config import Settings

app = FastAPI(title="Databricks Agent App", version="0.1.0")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation: list[dict] = Field(default_factory=list)

class ChatResponse(BaseModel):
    answer: str
    environment: str

@lru_cache
def get_agent() -> Agent:
    return Agent(Settings.from_env())

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        agent = get_agent()
        answer = agent.respond(request.message, request.conversation)
        return ChatResponse(answer=answer, environment=agent.settings.environment)
    except Exception as exc:
        # In production, send the complete exception to structured logs and return a correlation ID.
        raise HTTPException(status_code=500, detail="Agent request failed") from exc

def main() -> None:
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", "8000")))

if __name__ == "__main__":
    main()
