# Wikipedia RAG ReAct Chat Assistant

This project implements the Educative workflow using LlamaIndex, a local BGE embedding model, OpenAI, Wikipedia, and Chainlit.

## 1. Set up

```bash
#python -m venv .venv
#source .venv/bin/activate
pip install -r requirements.txt
cp apikeys.example.yml apikeys.yml
```

Edit `apikeys.yml` and add your key. Never commit this file. Alternatively, put `OPENAI_API_KEY=...` in `.env` (both files are gitignored).

The chat model must be one that `llama-index-llms-openai` 0.1.x recognises — `gpt-4o-mini` (default) or `gpt-4o`. Passing `gpt-5-nano` raises `ValueError: Unknown model`.

## 2. Verify the key

```bash
python utils.py
```

## 3. Test indexing from the terminal

```bash
python index_wikipages.py
```

Example input:

```text
Please index: 2023 United States banking crisis
```

Titles are taken from the text after `:`, split on commas — no LLM call, so indexing
works without an API key. The first run downloads `BAAI/bge-small-en-v1.5`.

## 4. Launch the app

```bash
chainlit run chat_agent.py -h
```

Open the Chainlit URL, use Settings to select the model and enter Wikipedia titles, then ask questions.

## Security and RAG notes

- The API key is never printed or committed.
- Answers are grounded only in the pages indexed for the current session.
- The index is in memory and disappears when the process restarts.
- Wikipedia content is not the same as truly live transactional data. Re-index to pick up page changes.
- `similarity_top_k=10` follows the assignment, but evaluate retrieval quality before using it in production.

## Suggested evaluation

Create a small question set and track retrieval hit rate, answer correctness, faithfulness to retrieved text, latency, and API cost. Include unanswerable questions to verify that the assistant does not invent facts.

---

# How it works

## The pieces

| File | Role |
| --- | --- |
| `utils.py` | Loads `OPENAI_API_KEY` from `.env` or `apikeys.yml`. |
| `index_wikipages.py` | **Retrieval layer.** Titles → Wikipedia text → chunks → local embeddings → in-memory vector index. No OpenAI call. |
| `rag_agent.py` | **The core.** Wraps the index as a tool and hands it to a ReAct agent. No UI, no server. |
| `chat_agent.py` | **Host 1:** Chainlit web app. |
| `server.py` | **Host 2:** FastAPI HTTP API. |
| `client.py` | **Client A:** in-process, imports the core directly. |
| `client_http.py` | **Client B:** calls the FastAPI host over HTTP. |

The core knows nothing about its hosts. That is the whole point — you write one
`rag_agent.py` and put any front end in front of it.

## Request flow

```
                        ┌──────────────────── the core (rag_agent.py) ────────────────────┐
CLIENT                  │                                                                 │
  browser ──websocket──►│  build_agent(pages, model)                                      │
  (Chainlit host)       │      ├─ create_index(pages)          ← index_wikipages.py        │
                        │      │     1. wikipage_list()  "Please index: A, B" → ["A","B"] │
  curl / requests ─http─►│      │     2. WikipediaReader   → article text                  │
  (FastAPI host)        │      │     3. SentenceSplitter  → 150-token chunks               │
                        │      │     4. HuggingFaceEmbedding (BAAI/bge-small-en-v1.5)      │
  python import ───────►│      │        → VectorStoreIndex     [local, no API call]        │
  (no host at all)      │      └─ create_react_agent(index, model)                         │
                        │            QueryEngineTool("Wikipedia") + OpenAI(gpt-4o-mini)    │
                        │                                                                  │
                        │  agent.chat(question)                                            │
                        │      Thought → Action: Wikipedia → Observation → Answer          │
                        └──────────────────────────────────────────────────────────────────┘
```

Two phases, and they cost very different amounts:

1. **Index** — slow (Wikipedia fetch + embedding), done once per set of pages, free.
2. **Ask** — one `agent.chat()` per question, 2+ OpenAI calls (ReAct reasons, calls the tool, then answers).

Cache the agent after phase 1. Chainlit keeps it in `cl.user_session`; `server.py` keeps it in `STATE`.

## How to call it

**A. From your own Python — no server:**

```python
from rag_agent import build_agent

agent = build_agent("Please index: London, Birmingham")   # slow, once
print(agent.chat("Compare the two cities' populations"))  # fast, per question
```

```bash
python client.py "Please index: London, Birmingham"
```

**B. Over HTTP — `server.py` is the host:**

```bash
uvicorn server:app --port 8000        # host; interactive docs at /docs
```

```bash
curl -s -X POST http://localhost:8000/index \
  -H 'Content-Type: application/json' \
  -d '{"pages": "Please index: 2023 United States banking crisis", "model": "gpt-4o-mini"}'
# {"status":"indexed","pages":["2023 United States banking crisis"],"model":"gpt-4o-mini"}

curl -s -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Which banks failed?"}'
# {"question":"Which banks failed?","answer":"Silicon Valley Bank ..."}
```

```bash
python client_http.py "Which banks failed?"    # same thing from Python
```

| Endpoint | Purpose | Notes |
| --- | --- | --- |
| `GET /health` | Is an agent built yet? | Returns `ready`, `pages`, `model`. |
| `POST /index` | Build the index + agent | Blocking, seconds. `409` from `/ask` until this runs. |
| `POST /ask` | One question | `502` if the agent errors, `409` if not indexed. |

**C. In the browser — Chainlit is the host:**

```bash
chainlit run chat_agent.py -h
```

The browser is the client and talks to the Chainlit process over a websocket. `-h` means
headless (don't auto-open a tab). Each browser session gets its own agent, because
Chainlit stores it per session.

## Building your own

Start from `rag_agent.py` and swap one layer at a time:

- **Different knowledge source** — replace `create_wikidocs()` in `index_wikipages.py` with any
  LlamaIndex reader (`SimpleDirectoryReader` for local files, a database reader, a web scraper).
  Everything downstream is unchanged.
- **Persist the index** — right now it dies with the process. Use
  `index.storage_context.persist("./storage")` and `load_index_from_storage()` on startup, or a real
  vector store, so restarts don't re-embed.
- **More tools** — pass a longer list to `ReActAgent.from_tools([...])`. The agent picks among them
  by reading each `ToolMetadata.description`, so write those descriptions carefully — that text *is*
  the routing logic.
- **Multi-user HTTP** — `STATE` in `server.py` is one global agent. Key it by session id
  (`STATE[session_id]`) and have the client send that id, or the second user overwrites the first.
- **Streaming** — swap `agent.chat()` for `agent.stream_chat()` and forward tokens as they arrive
  (`cl.Message.stream_token()` in Chainlit, SSE in FastAPI).
- **Watch it reason** — `verbose=True` prints the ReAct Thought/Action/Observation trace to the
  console. Read it when an answer looks wrong; it usually shows the retrieval missed, not the model.
