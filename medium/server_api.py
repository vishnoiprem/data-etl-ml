# =============================================================================
# Makro LLM Gateway — LangServe Server
# File: server_api.py
# Run: uvicorn server_api:app --host 0.0.0.0 --port 8000 --reload
#
# Endpoints exposed:
#   POST /llm-chain/invoke        ← simple single question
#   POST /llm-chain/stream        ← streaming tokens
#   POST /chatbot/invoke          ← multi-user chatbot with memory
#   POST /chatbot/stream          ← streaming chatbot
#   GET  /docs                    ← Swagger UI (auto-generated)
#   GET  /llm-chain/playground    ← LangServe built-in test UI
# =============================================================================

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import FileChatMessageHistory

from langserve import add_routes
from pydantic import BaseModel

# =============================================================================
# 1. Azure OpenAI setup (Makro uses Azure, not OpenAI directly)
# =============================================================================
llm = AzureChatOpenAI(
    azure_deployment   = os.environ["AZURE_OPENAI_DEPLOYMENT"],    # e.g. "gpt-4o"
    azure_endpoint     = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key            = os.environ["AZURE_OPENAI_API_KEY"],
    api_version        = "2024-02-01",
    temperature        = 0.7,
    max_tokens         = 1000,
    streaming          = True,    # enables /stream/ endpoint
)

# =============================================================================
# 2. Chain 1 — Simple LLM Chain (like slide L2)
# Prompt → LLM → parse to string
# Use case: one-off questions, no memory needed
# =============================================================================

# System prompt customised for Makro domain
makro_system_prompt = """You are a helpful AI assistant for CPAxtra (Makro/Lotus's).
You help with data analysis, business insights, supplier queries, and operational questions.
Always respond concisely and in the same language the user writes in (Thai or English).
If you don't know something, say so clearly."""

llm_chain_prompt = ChatPromptTemplate.from_messages([
    ("system", makro_system_prompt),
    ("human",  "{input}"),
])

# LCEL pipe: prompt | llm | parse output to plain string
llm_chain = llm_chain_prompt | llm | StrOutputParser()

# =============================================================================
# 3. Chain 2 — Multi-User Conversational Chatbot (like slide L3)
# Each user gets their own session_id → isolated memory in separate JSON files
# =============================================================================

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", makro_system_prompt),
    MessagesPlaceholder(variable_name="history"),   # ← injects past messages
    ("human", "{input}"),
])

# Base chain (no memory yet)
base_chat_chain = chat_prompt | llm | StrOutputParser()

# Memory directory — one JSON file per session_id
MEMORY_DIR = Path("./chat_histories")
MEMORY_DIR.mkdir(exist_ok=True)

def get_session_history(session_id: str) -> FileChatMessageHistory:
    """
    Returns FileChatMessageHistory for the given session_id.
    Creates a new JSON file if it doesn't exist.

    session_id examples:
      "user_prem_001"     → chat_histories/user_prem_001.json
      "store_bkk_02"      → chat_histories/store_bkk_02.json
      "supplier_nestle"   → chat_histories/supplier_nestle.json
    """
    history_file = MEMORY_DIR / f"{session_id}.json"
    return FileChatMessageHistory(str(history_file))

# Wrap chain with message history — this is the full conversational chain
conversational_chain = RunnableWithMessageHistory(
    base_chat_chain,
    get_session_history,
    input_messages_key   = "input",
    history_messages_key = "history",
)

# =============================================================================
# 4. FastAPI app + LangServe routes
# =============================================================================

app = FastAPI(
    title       = "Makro LLM Gateway API",
    description = "LangServe-powered LLM endpoints for CPAxtra data & AI team",
    version     = "1.0.0",
)

# Allow calls from internal dashboards / Power BI / frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],    # restrict to internal IPs in production
    allow_methods     = ["*"],
    allow_headers     = ["*"],
    allow_credentials = True,
)

# Route 1 — Simple chain
# Accessible at: POST /llm-chain/invoke
#                POST /llm-chain/stream
#                GET  /llm-chain/playground
add_routes(
    app,
    llm_chain,
    path              = "/llm-chain",
    enable_feedback_endpoint = True,   # thumbs up/down for LangSmith
    enable_public_trace_link = True,   # shareable trace links
)

# Route 2 — Conversational chatbot
# Accessible at: POST /chatbot/invoke
#                POST /chatbot/stream
add_routes(
    app,
    conversational_chain,
    path              = "/chatbot",
    enable_feedback_endpoint = True,
)

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok", "service": "Makro LLM Gateway"}

# =============================================================================
# 5. Run locally
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
