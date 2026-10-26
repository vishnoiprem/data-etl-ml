# 02 — Claude Code + Jira + GitHub MCP

> **Week 2 capstone.** The product is a real SaaS — the AI Legal Doc Generator,
> FastAPI + React — but the *course deliverable* is the Claude Code
> configuration that builds it. Same scaffold Week 1, deeper wires.

---

## What this is

The Week 2 SaaS exists as a seed app with one route (`/api/healthz`) and a
fully-configured Claude Code environment that produces the rest. The way you
get a real product out of this repository is:

```
/onboard        # load context
[spawn feature-builder sub-agent with a Jira ticket key]
/ship-it        # commit, push, open PR
```

That's the entire pipeline. The course spends Day 4–5 on the wiring.

---

## Files

```
02-claude-code-jira-mcp/
├── .claude/
│   ├── settings.json                ← permissions + sub-agents + MCP servers
│   ├── commands/
│   │   ├── ship-it.md               ← /ship-it — the closed-loop commit+PR helper
│   │   └── onboard.md               ← /onboard — first session in a new repo
│   ├── skills/
│   │   └── repo-onboarding/
│   │       └── SKILL.md             ← the structured version of /onboard
│   └── agents/
│       └── feature-builder.md       ← sub-agent: Jira ticket → PR
├── app/
│   └── main.py                      ← seed FastAPI app, narrow CORS
├── tests/
│   └── test_health.py
├── Makefile
├── pyproject.toml
└── notes/
    └── permissions.md               ← the real lecture content
```

---

## Run it (the seed)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make test          # 4 tests, no DB
```

`/api/healthz` returns `{"status":"ok"}`. That's all there is — the rest is
built from tickets.

---

## How Week 2 actually runs

1. **Open Claude Code in this directory.** It reads `.claude/settings.json`,
   loads the `feature-builder` sub-agent, and connects to the configured Jira
   and GitHub MCP servers.
2. **`/onboard`.** The skill writes the onboarding brief to your conversation.
   It does not modify the repo.
3. **Spawn `feature-builder`** with a ticket key (the course uses `AI-421`).
   It fetches the ticket via the Jira MCP server, plans, implements, writes
   tests, opens a PR that closes the ticket.
4. **`/ship-it`** (optional — `feature-builder` already does this, but the
   command is useful for one-off commits). Validates, commits narrowly, pushes,
   opens a PR.

---

## What is the safety case

Every command that lands in your shell has been pre-approved by `.claude/settings.json`.
Two of the most-loaded things an autonomous session can do — `git push --force`
and any write to `.env` — are `deny`-listed, which means **YOLO mode does not
override them**. See `notes/permissions.md` for the full model.

---

## Test status

```
$ pytest
4 passed
```

---

## What this is NOT

- **Not a finished SaaS.** It's the seed. The point is the *workflow* (Jira →
  sub-agent → PR), not the deployment.
- **Not a McP-from-scratch project.** The MCP servers in `settings.json` are
  third-party (`@modelcontextprotocol/server-jira`, `…/server-github`). The
  course's MCP-from-scratch work lives elsewhere.
- **Not safe by default.** Review the `deny` list before turning YOLO mode on.
  The course's default is `yoloMode: false` and that's correct for first use.

---

**Last updated:** 2026-10-21