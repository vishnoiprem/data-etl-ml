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

## 26-Day Plan (90 min/day: 10 + 20 + 30 + 20 + 20)

### Core full-stack (Days 1–21)
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

### System design + AI domain (Days 22–26)
| Day | Module | Topic |
|---|---|---|
| 22 | M19 | System Design: URL Shortener |
| 23 | M19 | System Design: RAG at Scale |
| 24 | M20 | AI Domain: Vector Databases + Embeddings |
| 25 | M20 | AI Domain: LLM Streaming, Function Calling, Evals |
| 26 | M19 | System Design Mock Interview (Chat) |

### Algorithms + coding interview (Days 27–32) 🆕
| Day | Module | Topic |
|---|---|---|
| 27 | M21 | Arrays, Strings, Hash Maps |
| 28 | M21 | Sliding Window + Two Pointers |
| 29 | M21 | Trees, BFS, DFS |
| 30 | M21 | Graphs, Topological Sort, Union-Find |
| 31 | M21 | Dynamic Programming |
| 32 | M21 | Mock Coding Interview (LRU + Word Ladder) |

### Supplementary reading
- `docs/SYSTEM_DESIGN_PRIMER.md` — 60-min framework + 5 designs
- `docs/ALGORITHMS_PRIMER.md` — 60-min coding interview framework + 50 most-asked problems
- `docs/META_GOOGLE_REALITY_CHECK.md` — what this course covers vs. what you still need

## Project structure
```
rag-trace-review/
├── README.md
├── docker-compose.yml
├── docs/
│   ├── INDEX.md
│   ├── STEP_BY_STEP.md
│   ├── SYSTEM_DESIGN_PRIMER.md
│   ├── ALGORITHMS_PRIMER.md
│   ├── META_GOOGLE_REALITY_CHECK.md
│   └── DAY_01.md → DAY_32.md
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
Stable result: **100 / 100**

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