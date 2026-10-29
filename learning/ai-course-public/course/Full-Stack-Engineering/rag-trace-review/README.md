# RAG Trace Review Platform

Internal full-stack app for inspecting RAG traces, comparing prompt versions, and submitting feedback.

## Stack
- **Backend**: FastAPI, SQLite, Pydantic, pytest
- **Frontend**: React 18, TypeScript, Vite, Tailwind, TanStack Query/Table/Virtual

## Quick start (Apple Silicon macOS)

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py            # 10,000 synthetic traces
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs for OpenAPI.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

### Tests
```bash
cd backend && pytest -q          # backend
cd frontend && npm test          # frontend
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/traces?day=&prompt_version=&min_latency=&max_latency=&cursor=&limit=` | Cursor-paginated list |
| GET | `/traces/{id}` | Full trace detail |
| PUT | `/traces/{id}/feedback` | Idempotent feedback upsert |
| GET | `/health` | Liveness |

## Design notes
- **Cursor pagination** uses opaque base64(`created_at|trace_id`) with deterministic `ORDER BY created_at DESC, trace_id DESC` and a `LIMIT n+1` trick to compute `has_more`.
- **Indexes**: composite `(created_at DESC, trace_id DESC)`, plus `prompt_version` and `latency_ms`.
- **Optimistic UI** via TanStack Query `onMutate` cache patches; rollback in `onError` from captured snapshots.
- **Virtualization** keeps DOM cost constant for 10,000+ rows.

## Project layout
```
rag-trace-review/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── routes/{traces,feedback}.py
│   ├── tests/
│   ├── seed.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── types/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── docker-compose.yml
└── README.md
```
