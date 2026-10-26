# 01 — IDE agents & `AGENTS.md`

> **Week 1 capstone.** The Kanban board you build with Cursor, Copilot, Codex, or
> Antigravity. The deliverable that actually matters is `AGENTS.md`.

---

## What this is

A FastAPI + Postgres Kanban board with a vanilla-JS drag-and-drop front end.
Small enough to hold in your head, real enough to have the bugs worth debugging.

The course builds it **five different ways** — once per agent — so you can
compare them on an identical task. That's the point. A Kanban board is a
control group.

| Agent | Host | Lecture that uses it |
|---|---|---|
| Cursor | Cursor IDE | Building a Kanban App with the Cursor AI Agent in YOLO Mode |
| Copilot | VS Code | Building a Kanban Board with GitHub Copilot in VS Code |
| Codex | VS Code | OpenAI Codex VS Code Extension: Zero-Shot Kanban App Build |
| Antigravity | Antigravity IDE | Building a Kanban App with Antigravity IDE and Gemini 3 Pro |
| (Claude Code) | CLI / VS Code | Week 2 builds a larger version of this |

---

## Files

```
01-ide-agents-agents-md/
├── AGENTS.md                       ← THE deliverable. Canonical project rules.
├── CLAUDE.md                       ← one-paragraph pointer to AGENTS.md
├── .github/copilot-instructions.md ← same shape, for Copilot
├── app/
│   ├── main.py                     ← app factory. Route-order note inline.
│   ├── db.py                       ← engine + session dependency
│   ├── models.py                   ← SQLAlchemy 2.x models
│   ├── schemas.py                  ← Pydantic v2 request/response models
│   └── routers/
│       └── cards.py                ← all card CRUD
├── static/
│   ├── index.html
│   ├── app.js                      ← native HTML5 drag-and-drop
│   └── styles.css
├── tests/
│   ├── conftest.py                 ← SQLite override; env-var-before-import note
│   └── test_cards.py               ← 9 tests
├── Makefile
├── pyproject.toml
└── notes/
    └── context-strategy.md         ← the real lecture content
```

---

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# tests need no database
pytest

# running it needs Postgres 16
docker run -d --name kanban-pg \
  -e POSTGRES_USER=kanban -e POSTGRES_PASSWORD=kanban \
  -e POSTGRES_DB=kanban -p 5432:5432 postgres:16

alembic revision --autogenerate -m "initial"
alembic upgrade head
make dev
```

Then open http://localhost:8000.

---

## The two bugs this codebase contains on purpose

Both were found by running the code, not by reading it. Both are documented
inline because the *debugging* is the lesson.

1. **Route-ordering 404s.** `app.mount("/", StaticFiles(...))` registered before
   `include_router` swallows every API route. Symptom: every endpoint 404s or
   405s while the app looks correct. → `app/main.py`, and
   `notes/context-strategy.md` §5.
2. **204 with `-> None`.** FastAPI asserts a 204 route has no response model, so
   the return annotation fails at *import* time, before any request. →
   `app/routers/cards.py`.

---

## Test status

```
$ pytest
9 passed
```

No Postgres required — `tests/conftest.py` overrides the session dependency
with in-memory SQLite and a `StaticPool` (without `StaticPool`, each checkout
gets a fresh `:memory:` database and the tables vanish between tests).

---

## What this is NOT

- **Not a portfolio piece as-is.** It's course scaffolding. Strip it, keep the
  `AGENTS.md` patterns.
- **Not authenticated, not multi-board, not collaborative.** Deliberately. Every
  feature an agent "helpfully" adds here is a feature you're now debugging.
- **Not the drag-and-drop lecture.** `static/app.js` uses native HTML5 DnD
  because it's dependency-free, not because it's pleasant. If you want a real
  drag-and-drop library, that's an exercise.

---

**Last updated:** 2026-10-21