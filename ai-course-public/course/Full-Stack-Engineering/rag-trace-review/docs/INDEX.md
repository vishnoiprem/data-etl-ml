# RAG Trace Review Platform — Course Index

## Master Prompt Success Criteria
- [ ] Build a React + TypeScript frontend without copying blindly.
- [ ] Implement FastAPI endpoints and explain request validation.
- [ ] Implement cursor pagination correctly.
- [ ] Build a virtualized React table.
- [ ] Handle optimistic feedback and rollback.
- [ ] Debug frontend/backend issues independently.
- [ ] Write meaningful automated tests.
- [ ] Explain each design choice in a Meta L6 interview.
- [ ] Build and run the entire project locally.

## 21-Day Plan (90 min/day: 10 + 20 + 30 + 20 + 20)

| Day | Module | Topic |
|---|---|---|
| 1 | M1 | How full-stack applications work |
| 2 | M2 | JavaScript and TypeScript |
| 3 | M3 | React Foundations |
| 4 | M4 | FastAPI |
| 5 | M5 | SQL and Persistence |
| 6 | M6 | Frontend/Backend Integration |
| 7 | M7 | API Design |
| 8 | M8 | Cursor Pagination (Deep Dive) |
| 9 | M9 | React Data Tables (TanStack Table) |
| 10 | M10 | Virtualized Lists |
| 11 | M11 | Optimistic UI |
| 12 | M12 | RAG Trace Inspection |
| 13 | M13 | AI UI Features (Streaming) |
| 14 | M14 | Authentication and Security |
| 15 | M15 | Testing |
| 16 | M16 | Debugging and Performance |
| 17 | M17 | Packaging and Deployment |
| 18 | M18 | Mock Interview Day 1 |
| 19 | M18 | Mock Interview Day 2 |
| 20 | M18 | Mock Interview Day 3 |
| 21 | M18 | Capstone Polish + Final Review |

## Project structure
```
rag-trace-review/
├── README.md
├── docker-compose.yml
├── docs/
│   ├── INDEX.md
│   ├── STEP_BY_STEP.md
│   └── DAY_01.md → DAY_21.md
├── backend/    (FastAPI + SQLite + pytest, 14 tests)
└── frontend/   (React 18 + TS + Vite + TanStack)
```

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
Script: `/tmp/fix_review_100.sh`
Stable result: **100 / 100** (or 102/102 with the v2/v3 polish)

## Grading Rubric (used by every day)
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

**Pass mark:** ≥ 56/80 (≥ 70%).
**Distinction:** ≥ 64/80 (≥ 80%).