# AI Coder: Claude Code & Coding Agents — Course Scaffold & Capstones

> **Build production-grade software at extraordinary pace with Cursor, Copilot, Codex, Antigravity, and Claude Code.** Three sections, three capstones, no Node.js, no React prior experience required. ~3 weeks.

> **What this directory is:** the *project skeletons* from the 95-lecture course — the source files, the agent configuration, the orchestration patterns — without the per-lecture narrative. Use it as a starting point that compiles; refer to the video for the why.

---

## What you build

| Section | Project | What it proves | What's runnable here |
|---|---|---|---|
| 1 — IDE agents & `AGENTS.md` | **01 — Kanban (five different agents)** | One task, five agents, comparison on identical input. The deliverable is `AGENTS.md`, not the Kanban. | FastAPI + Postgres Kanban board, 9 tests green |
| 2 — Claude Code + Jira + GitHub MCP | **02 — SaaS from Jira tickets** | Claude Code with a permissions file, sub-agents, slash commands, MCP servers — builds a real SaaS from tickets. | Seed FastAPI app, 4 tests green, full `.claude/` configuration |
| 3 — Multi-agent orchestration | **03 — Five-pole trading pipeline** | Five Claude Code sessions coordinated through a JSONL ledger; risk gates are pure functions; one pole talks to the broker. | `shared/budget.py` + 22 risk-gate tests green |

Each project is **self-contained** — own source tree, own dependencies, own test suite.

---

## File layout

```
ai-coder-coding-agents/
├── README.md                          ← you are here
└── projects/
    ├── 01-ide-agents-agents-md/
    │   ├── README.md
    │   ├── AGENTS.md                  ← canonical project rules
    │   ├── CLAUDE.md                  ← pointer to AGENTS.md
    │   ├── .github/copilot-instructions.md
    │   ├── app/                       ← FastAPI + Postgres
    │   ├── static/                    ← vanilla JS frontend
    │   ├── tests/                     ← pytest, SQLite-backed
    │   └── notes/
    │       └── context-strategy.md    ← the real lecture content
    ├── 02-claude-code-jira-mcp/
    │   ├── README.md
    │   ├── .claude/
    │   │   ├── settings.json          ← permissions, sub-agents, MCP
    │   │   ├── commands/              ← /ship-it, /onboard
    │   │   ├── skills/                ← repo-onboarding
    │   │   └── agents/                ← feature-builder
    │   ├── app/                       ← seed SaaS
    │   ├── tests/
    │   └── notes/
    │       └── permissions.md         ← the real lecture content
    └── 03-multi-agent-orchestration/
        ├── README.md
        ├── CLAUDE.md                  ← orchestrator's contract
        ├── shared/budget.py           ← risk gates, pure
        ├── workers/<pole>/CLAUDE.md   ← 5 poles
        ├── contracts/                 ← JSON Schemas
        ├── shared/notes/ledger/       ← per-cycle JSONL
        ├── tests/
        └── notes/
            └── orchestration.md       ← the real lecture content
```

---

## How to use this

1. **Pick a project.** Don't try all three at once — each uses a different
   skill surface. Project 02 in particular requires Jira and GitHub
   credentials in your environment.
2. **Follow that project's `README.md`** — it lists exactly which agent
   to point at the directory, what tools to install, and what the test suite
   expects.
3. **Run the tests first.** Every project here ships green from a fresh
   venv. If tests fail on first import, environment problem, not a code bug.
4. **Diff against the lecture.** The `notes/` folders carry the *real*
   lecture content — the things students retain six months later — and
   correspond to specific Day X lectures in the course.

---

## What this directory is NOT

- **Not a transcript.** Lecture footage carries the *why* and the *demo*.
  These files carry the *what*. Use them together.
- **Not "the agent does it."** Every project is structured so a human
  notices quickly when the agent drifts. The `notes/` are deliberately not
  pad-yourself-on-the-back success stories; they're the things that broke.
- **Not vendor-neutral.** Cursor / Copilot / Codex / Antigravity / Claude
  Code are the course's. The patterns are portable but the per-tool config
  isn't.
- **Not finished SaaS / finished pipeline.** Week 2 is a seed; Week 3 is a
  scaffold. Real products add database migrations, deployment, auth, and a
  hundred tests. Those happen in your codebase from here.

---

## Source / provenance

The course outline for this directory is a published 95-lecture, 16-hour,
3-week video course titled *"AI Coder: Complete Claude Code & Coding Agents
Course"*. **The instructor/creator is not recorded in the source material I
was given** — fill it in here if you know it.

The project skeletons here are **reverse-engineered from the lecture titles
alone**, plus public documentation for Cursor / Copilot / Codex / Antigravity
/ Claude Code, and the public APIs named in the lectures (FastAPI, Postgres,
Jira, GitHub, Alpaca, Polygon). No lecture footage, transcript, or course
material was available while writing these files.

**Practical consequence:** treat every `AGENTS.md` rule and every pole
contract here as a *strong first draft*, not ground truth. The course spends
a lecture on the contradiction between "the agent keeps going off-topic" and
"the agent finished the feature" — the fix in both cases is the same: write
a tight, narrow, well-tested context. Run `make test` after every change and
paste the real output.

---

## What survives the loop

The three project skeletons are the artifacts. The `notes/` are the
*knowledge*. The thing every student retains is one of three patterns:

1. `AGENTS.md` is the deliverable, not the README — agent behaviour comes
   from a single canonical file, with the others as one-paragraph pointers.
2. Permissions are the safety case — `.claude/settings.json` is one of the
   most powerful files in any project that uses Claude Code, and most
   teams get it wrong by adding things, not denying things.
3. Multi-agent systems fail from a different cause than single-agent ones —
   they don't fail *by hallucinating*, they fail *by stepping on each other*.
   The fix is a file, not a model.

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.