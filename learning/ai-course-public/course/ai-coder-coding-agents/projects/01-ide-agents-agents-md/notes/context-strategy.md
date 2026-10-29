# Context strategy — Week 1 capstone

The single biggest thing that separates "the agent keeps going off-topic" from
"the agent finished the feature" is **what the agent has loaded, in what order,
and how fresh**. This note captures the rules the course insists on, and the
ones that nearly every first-week student violates.

---

## 1. The hierarchy

Files the agent reads, in the order they matter:

1. **`AGENTS.md`** (or `CLAUDE.md` / `copilot-instructions.md` — see file 2). One
   project = one canonical file. The other filenames are **pointers**, not copies.
2. **The relevant subset of source.** The agent does not start by reading the whole
   repo. It reads the file it has been asked to edit, and the files that file
   imports. If you let it sweep the repo blind, you have already lost the
   budget to your own imports.
3. **Tool outputs.** Tests passing > tests predicting to pass. Reading a file
   > assuming what's in it.

> "Read the file before you edit it" is not a politeness. The cost of opening
> a 200-line file is ~3k tokens. The cost of an edit that misreads that file
> is the next 30 minutes of your session.

---

## 2. Never duplicate rules across `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md`

They will drift. Within a week of you copy-pasting them, one will be updated
and the others will not, and the agent will read whichever one its host loads
first and behave inconsistently depending on whether you opened Cursor or
Claude Code.

The pattern that works:

- `AGENTS.md` — canonical, authored, hand-maintained.
- `CLAUDE.md` — one paragraph: "Read AGENTS.md. Here's what's different about
  Claude Code specifically." See this project's `CLAUDE.md`.
- `.github/copilot-instructions.md` — same shape, same one-paragraph rule.

If you find yourself writing a long `CLAUDE.md`, you are duplicating.

---

## 3. The context budget, by tool

| Tool | Useful budget | Mechanism |
|---|---|---|
| **Cursor** | Whole repo, but search-first | Agent uses `@file`, ripgrep, and `codebase` retrieval. Loading everything is wasteful. |
| **Claude Code** | Project files + open tabs | `CLAUDE.md` is auto-loaded. The model's session includes shell access, so it should grep before reading. |
| **Copilot** | The current file + neighbours | Inline completions are tightly scoped. The new "agent mode" reads more, but with the same retrieval caveats. |
| **Codex** | The whole open codebase | More aggressive retrieval than Cursor. Common failure: retrieving the wrong file at 50k tokens before reading the right one. |

The budget column is what *most* projects should rely on. Real ceiling is
whatever the model supports — which is now large enough to be a trap.

---

## 4. The "never" list — failures from Day 3

> These are real, from running the course live. Every one was a single commit
> that the agent authored confidently.

- **Never say "I will do X" without running X.** If you cannot run it, say so.
- **Never edit generated code.** Alembic migrations, `package-lock.json`,
  OpenAPI-generated clients. These are scrap output; regenerate them, don't
  rewrite them.
- **Never invent a dependency.** If the rule is "stack is FastAPI + Postgres,"
  there is no `flask`, no `sqlmodel`, no `tinyorm`. If you think the project
  needs one, ask first.
- **Never hand-roll a migration.** Always `alembic revision --autogenerate`,
  always run the migration in dev, always inspect the generated file.
- **Never pin versions above what `requirements.txt` already has.** Older is
  fine because of the lockfile; newer is not, because the lockfile will
  silently upgrade on next install.
- **Never add a framework.** The course's mantra: vanilla JS, vanilla HTML,
  vanilla CSS. Adding a bundler is the single most common "I thought this
  would help" failure.

---

## 5. Why ordering matters in `app/main.py`

Starlette matches routes in registration order. A `Mount("/")` matches every
path that hasn't been matched already. So:

```python
# WRONG: this blocks every subsequent route
app.mount("/", StaticFiles(directory="static", html=True))
app.include_router(cards.router, prefix="/api")

# RIGHT: API routes register first, mount last
app.include_router(cards.router, prefix="/api")
app.mount("/", StaticFiles(directory="static", html=True))
```

If you ever get a baffling 404/405 across all your routes and `curl
http://localhost:8000/openapi.json` shows nothing, this is the reason. See
`app/main.py` for the inline comment explaining it.

---

## 6. The 204-with-None trap

```python
# WRONG: import-time AssertionError, "Status code 204 must not have a response body"
@router.delete("/{id}", status_code=204)
def delete_card(...): ...

# RIGHT
@router.delete(
    "/{id}",
    status_code=204,
    response_class=Response,
)
def delete_card(...) -> Response:
    ...
    return Response(status_code=204)
```

FastAPI enforces that 204 routes don't produce a body. The `-> None`
annotation counts as a body. See `app/routers/cards.py` for the working
form.

---

**Last updated:** 2026-10-21