# GitHub Copilot instructions

## Canonical instructions

The authoritative project rules live in **`AGENTS.md` at the repo root**.
Read it first. This file exists only because Copilot does not read `AGENTS.md`.

## Copilot-specific notes

- You complete code inside a single editor buffer. Before you suggest a change,
  reference the file path you are editing.
- Keep suggestions minimal and local. Do not propose a refactor that touches
  files outside the current change unless asked.
- Follow the `response_model` and Alembic rules in `AGENTS.md` without exception —
  they exist because Copilot's most common failure here is inventing a migration.

## Commands

See `AGENTS.md`. In short: `make dev`, `make test`, `make lint`, `make migrate`.