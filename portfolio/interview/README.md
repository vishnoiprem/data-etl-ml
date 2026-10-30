# Makro LLM Gateway

> **A self-hosted LangServe gateway over Azure OpenAI.** Drop-in
> replacement for "calling the OpenAI SDK from every notebook and
> dashboard." One FastAPI service, two clients (`server_api.py` +
> `client.py`), three endpoint shapes (single-call, streaming,
> multi-user chatbot with memory), one deployment target (Azure
> Container Apps).

This is the project that lives at the top of the `medium/` directory.
The two Python files you need to read are `server_api.py` (the
LangServe server) and `client.py` (the way other services call it).
The rest of the `medium/` directory is the writing and interview
prep that surrounds it.

---

## What it is, in one sentence

A small production-shaped LangServe gateway that fronts Azure OpenAI
so your Power BI reports, internal dashboards, Databricks notebooks,
and other Python services can call LLMs through a single typed
endpoint with auth, streaming, and conversation memory — instead of
re-implementing that stack in every consumer.

---

## Endpoints exposed

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/llm-chain/invoke` | Single LLM call, JSON in / JSON out |
| `POST` | `/llm-chain/stream` | Same chain, but streaming tokens (SSE) |
| `POST` | `/chatbot/invoke` | Multi-turn chatbot with file-backed session memory |
| `POST` | `/chatbot/stream` | Streaming chatbot with the same memory |
| `GET`  | `/docs` | Auto-generated Swagger UI |
| `GET`  | `/llm-chain/playground` | LangServe's built-in test UI |
| `GET`  | `/health` | Health check (200 if up) |

---

## How to run locally

```bash
# 1. Install
pip install -r requirements.txt    # see Appendix A below

# 2. Set env vars
cp .env.example .env               # see Appendix B below
# (fill in your Azure OpenAI keys)

# 3. Start the server
uvicorn server_api:app --host 0.0.0.0 --port 8000 --reload

# 4. Test in browser
open http://localhost:8000/docs                    # Swagger UI
open http://localhost:8000/llm-chain/playground     # LangServe playground
curl http://localhost:8000/health                  # health check

# 5. Test with the client
python client.py
```

---

## How a consumer calls it

```python
from langserve import RemoteRunnable

# Single call
chain = RemoteRunnable("http://localhost:8000/llm-chain/")
print(chain.invoke({"question": "What is the AML rule for structuring?"}))

# Streaming
for chunk in chain.stream({"question": "Summarize MAS 626 in 5 bullets"}):
    print(chunk, end="", flush=True)

# Multi-turn chatbot
chatbot = RemoteRunnable("http://localhost:8000/chatbot/")
print(chatbot.invoke(
    {"input": "Hi, my name is Prem."},
    config={"configurable": {"session_id": "prem-1"}},
))
print(chatbot.invoke(
    {"input": "What's my name?"},
    config={"configurable": {"session_id": "prem-1"}},
))
```

`session_id` is the only thing that matters for memory. Use the same
`session_id` for the same conversation; pick a new one per user / per
thread. The history is file-backed (`FileChatMessageHistory`), so it
survives server restarts.

---

## How to deploy (Azure Container Apps)

```bash
# Build + push
docker build -t makro-llm-gateway .
docker tag makro-llm-gateway <your-acr>.azurecr.io/makro-llm-gateway:v1
docker push <your-acr>.azurecr.io/makro-llm-gateway:v1

# Deploy
az containerapp create \
  --name makro-llm-gateway \
  --resource-group makro-rg \
  --image <your-acr>.azurecr.io/makro-llm-gateway:v1 \
  --target-port 8000 \
  --ingress external
```

A production Dockerfile is in Appendix C below. The image is
~200 MB on `python:3.11-slim`. Cold-start on Container Apps is
~3-5 seconds.

---

## When this is the right pattern

This gateway is the right call when:

- You have **3+ consumers** of the same LLM (BI tool + Databricks +
  internal service) and you want one place to enforce auth, retries,
  and model routing.
- You want **LangSmith tracing** to work end-to-end without
  instrumenting every consumer.
- You want **typed endpoints** instead of "we call OpenAI and hope
  for the best." `/llm-chain/invoke` returns a Pydantic-validated
  payload; the OpenAI SDK returns whatever OpenAI feels like.
- You're **migrating from OpenAI to Azure OpenAI** (or vice versa)
  and want a single swap point instead of touching every consumer.

It is **not** the right call when:

- You have one consumer and one notebook. Just call the SDK.
- You need token-by-token cost attribution per request. The gateway
  has it (LangSmith), but the project has to wire it up.
- You need multi-modal (vision, audio) routing. This is text-only.

---

## What this project is NOT

- **Not a production LLM platform.** No auth, no rate limit, no
  retry budget, no per-tenant routing. The reference is what
  [`../ai-engineering/01-enterprise-rag-platform/`](../../learning/ai-engineering/01-enterprise-rag-platform/)
  builds on top of.
- **Not a replacement for an LLM gateway like LiteLLM or Portkey.**
  Those are designed for multi-provider routing, fallback, and
  cost control. This is a single-provider gateway in 150 lines.
- **Not a chatbot framework.** The `/chatbot/` endpoints are
  minimal; they're enough to demo LangChain's `RunnableWithMessageHistory`,
  not enough to ship a customer-facing chat product.

---

## File layout

```
medium/
├── README.md                    ← this file
├── server_api.py                ← the LangServe server (153 lines)
├── client.py                    ← example consumers (111 lines)
├── requirements.txt             ← (Appendix A below)
├── .env.example                 ← (Appendix B below)
└── Dockerfile                   ← (Appendix C below)
```

---

## Appendix A — `requirements.txt`

```text
langchain==0.2.0
langchain-openai==0.1.7
langchain-community==0.2.0
langserve[all]==0.2.0
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.1
httpx==0.27.0
python-dotenv==1.0.1
```

## Appendix B — `.env.example`

```text
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
LANGCHAIN_API_KEY=your-langsmith-key        # optional — for tracing
LANGCHAIN_TRACING_V2=true                   # optional — enables LangSmith
```

## Appendix C — `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "server_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Related directories

- [`../ai-engineering/01-enterprise-rag-platform/`](../../learning/ai-engineering/01-enterprise-rag-platform/) —
  The RAG cousin: this gateway is the front door, the RAG platform
  is what you put behind it.
- [`../ai-engineering/07-prompt-engineering/`](../../learning/ai-engineering/07-prompt-engineering/) —
  The versioning + A/B-test layer that belongs on top of this
  gateway.
- [`../ai-engineering/08-llmops-platform/`](../../learning/ai-engineering/08-llmops-platform/) —
  The observability / cost / drift layer that the gateway's
  LangSmith trace feeds into.
- [`./`](../medium/) — the rest of the `medium/` directory: long-form
  articles, interview prep, and the supporting writing.

---

**Last updated:** 2026-10-13
**License:** MIT — use freely in your own courses, prototypes, and products.
