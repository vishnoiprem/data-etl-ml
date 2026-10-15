# RAG Trace Review Platform — Course Index

## Documents
- **[STEP_BY_STEP.md](./STEP_BY_STEP.md)** — Full theory + build walkthrough + 100-question review checklist
- **[DAY_01.md](./DAY_01.md)** — Day 1: How full-stack applications work (Module 1)

## Project root
`/Users/pvishnoi/PycharmProjects/data-etl-ml/ai-course-public/course/Full-Stack-Engineering/rag-trace-review/`

## Quick commands

```bash
# Backend
cd <project>/backend && source .venv/bin/activate
python seed.py
uvicorn app.main:app --reload --port 8000
pytest -q

# Frontend
cd <project>/frontend && npm install && npm run dev

# Health
curl http://localhost:8000/health
curl 'http://localhost:8000/traces?limit=2'
```

## 100× Review
- 100-point script: `/tmp/fix_review_100.sh`
- Stable result: **100 / 100**
- 14 backend tests passing × 10 runs