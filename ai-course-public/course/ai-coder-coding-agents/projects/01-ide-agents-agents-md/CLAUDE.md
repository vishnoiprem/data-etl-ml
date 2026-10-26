# CLAUDE.md — Claude Code project instructions

> Claude Code reads `CLAUDE.md`. Cursor reads `AGENTS.md` (and `.cursorrules`).
> Copilot reads `.github/copilot-instructions.md`.
> **This file is a thin pointer, not a copy.** See `notes/context-strategy.md`
> for why duplicating the rules across four files is the single most common
> cause of agents contradicting themselves.

---

## Canonical instructions

The authoritative project rules live in **`AGENTS.md` at the repo root**.

Read it before making any change. It defines the stack, the hard rules, the
project layout, and the definition of done.

## What is different about Claude Code specifically

- You have shell access. Prefer running `make test` over predicting its output.
- You can read files before editing. Do that. The cost is far lower than the cost
  of a wrong edit to a file you never opened.
- You have web access. Use it for library documentation, not for guessing APIs.

## Session hygiene

- Check `git status` before editing. If the tree is dirty in files you did not
  touch, mention it — do not overwrite someone else's work.
- At the end of a task, report what actually changed and what was actually run.
  Do not report intent as accomplishment.