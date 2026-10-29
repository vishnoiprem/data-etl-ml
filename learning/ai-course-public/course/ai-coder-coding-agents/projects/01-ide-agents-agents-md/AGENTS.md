# AGENTS.md — Kanban board (FastAPI + Postgres + vanilla JS)

> This is a **teaching template**, not the course's exact file. Every section below is
> a lesson from Day 2–3: "Context Engineering" and "Mastering agents.md".
>
> The rules here are ordered by how often an agent violates them. Most agents get
> breadth right and specificity wrong.

---

## What this project is

A single-page Kanban board. Columns: Backlog / In Progress / Done. Cards have a
title, an optional description, and an optimistic position for drag-and-drop.

## Stack — and the versions that matter

- **Python 3.11+**, FastAPI, Uvicorn
- **Postgres 16** via SQLAlchemy 2.x (use the 2.x `DeclarativeBase` style, not legacy)
- **Vanilla JS** ES modules. No build step. No framework. Do not add one.

## Hard rules

1. **Never add a dependency without asking.** Adding `pandas` to compute a mean
   of three numbers is a failure, not a feature.
2. **Never write a migration by hand.** Alembic autogenerate only. If you hand-edit
   a migration, migrations will diverge between machines.
3. **Every API route returns a typed `response_model`.** Pydantic, not dicts.
4. **Tests run with `pytest`.** Before you claim a feature works, run
   `pytest -q` and paste the real output. Do not claim success without it.
5. **No `print()` in application code.** Use the `logging` module.

## Commands

```bash
make dev      # start the API on :8000 with reload
make test     # pytest -q
make lint     # ruff check . && ruff format --check .
make migrate # alembic upgrade head
```

## Project layout

```
app/
  main.py         # FastAPI app factory. No route definitions here.
  models.py       # SQLAlchemy models. One class per table.
  schemas.py      # Pydantic models for request/response. Distinct from models.py.
  routers/
    cards.py      # All /cards routes live here.
  db.py           # Engine + session. One session per request.
alembic/          # Migrations. Never edit by hand.
tests/
static/           # index.html, app.js, styles.css
```

## Style

- Type hints on every function signature.
- Imports: stdlib, then third-party, then local — separated by blank lines.
- Line length 100.
- Prefer `pathlib.Path` over `os.path` string joins.

## Definition of done

A feature is done when: the route has a `response_model`, a test exists that fails
without the change, `make test` passes, and `make lint` passes. If you cannot run
`make test`, say so explicitly rather than guessing at the result.

## What this project is not

- Not a place to demonstrate agent capabilities. The point is a working Kanban board.
- Not multi-tenant. No auth. Do not add it "for completeness."