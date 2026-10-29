# Tooling Cheatsheet

> AI coding assistants compared: Cursor, Claude Code, GitHub Copilot, OpenAI Codex, Amazon Q Developer, Aider, Continue.dev. Setup tips and where each shines.

---

## The landscape (2026)

| Tool | Best for | Strength | Weakness |
|---|---|---|---|
| **Cursor** | IDE-first coding | Inline edits, multi-file refactors, agentic flows | Cost at scale; learning curve for advanced features |
| **Claude Code** | Terminal-first repo work | Whole-repo context, plan-then-act, hooks | Less mature editor integration |
| **GitHub Copilot** | Inline completion | Fastest in-IDE; widely deployed | Less agentic; weaker multi-file |
| **OpenAI Codex (Cloud)** | Background agent tasks | Async, sandboxed, GitHub-native | Less interactive; newer |
| **Amazon Q Developer** | AWS-only shops | AWS context, security scanning | AWS-only |
| **Aider** | CLI repo refactor | Git-aware, multi-file, cheap | CLI-only, less IDE integration |
| **Continue.dev** | Self-hosted, customisable | Open-source, BYO models | Setup overhead; smaller community |

Pick **one primary** (the one that lives in your editor) + **one agentic** (the one that owns the repo) — don't spread your AI attention across 5 tools.

---

## The "rules file" pattern (.cursorrules / CLAUDE.md)

Every AI tool reads a **rules file** at the repo root. This is the **highest-ROI setup activity** in any AI-assisted workflow.

```
   /repo-root/
   ├── .cursorrules        # Cursor reads this
   ├── CLAUDE.md           # Claude Code reads this
   ├── AGENTS.md           # generic / Codex
   └── ...
```

### Sample .cursorrules / CLAUDE.md skeleton

```markdown
# Project: NAME
# Stack: Python 3.11, dbt-core 1.8, Snowflake, Airflow 2.9
# Conventions below. Follow these unless the user explicitly says otherwise.

## Identity
You are a senior data engineer helping on this repo. Be concise. Code first, prose second.

## Code style
- Type hints mandatory on all Python.
- No bare except: `except Exception as e: ... raise ... or log with context`.
- Functions < 50 lines. Classes < 200 lines.
- Docstrings only on public functions (PEP 257).
- Imports: stdlib, 3rd-party, local — three groups, alphabetical.

## dbt conventions
- Schema name = `staging_<source>`, `intermediate`, `marts`.
- Every model has a corresponding _model.yml with description + tests.
- Materialisations: view for staging, table for marts, incremental for time-series.
- Tests: not_null + unique on PKs, accepted_values on enums, relationships on FKs.

## SQL conventions
- Use CTEs, not nested subqueries.
- Use TIMESTAMP, not VARCHAR, for date math.
- Always include ORDER BY for "top N".
- Reserved words in UPPER_SNAKE_CASE.

## Airflow conventions
- TaskFlow API throughout. No PythonOperator unless legacy.
- id = snake_case, descriptive: extract_kafka_events, not task1.
- Sla on every load task. on_failure_callback posts to #data-oncall.
- No XCom for large payloads.

## AI constraints
- DO NOT generate happy-path-only code. Always include failure paths.
- DO NOT use SELECT * in production SQL.
- DO NOT hardcode credentials, paths, or org names.
- DO NOT skip tests, docstrings, or descriptions.
- After generating: list 3 things you didn't handle and the user should review.

## Output format
- Explain in 1-2 sentences what you did.
- Show the diff or full code, ready to paste.
- If unsure: "I'd need to see ___ to confirm."
```

A good rules file is **150–400 lines**, project-specific, and updated as conventions evolve.

---

## Cursor tips

```
   SHORTCUTS
   ─────────
   Cmd+L         open chat (command palette + chat)
   Cmd+K         inline edit (select code → Cmd+K → prompt)
   Cmd+I         composer (multi-file, agent mode)
   Cmd+Shift+I   @ mention a file or folder

   PATTERNS
   ────────
   @Codebase     "explain how events flow from Kafka to the lake"
   @file         "what does this function do?"
   @folder       "list all dbt models with their materialisation"
   @git          "what changed in the last commit? any test gaps?"
   @doc          "summarise the schema for tickets table"

   MODELS
   ──────
   Cursor 1.x:   Claude 4 / Sonnet / GPT-4o / Gemini 2.5 / "Auto"
   Pick "Auto" for most tasks — Cursor routes per request.

   EDIT MODES
   ──────────
   Inline (Cmd+K):  select + edit. Best for surgical changes.
   Chat (Cmd+L):    ask, paste code, iterate.
   Composer (Cmd+I): agent mode; multi-file; "build a feature."

   RULES
   ─────
   .cursorrules at repo root. 150–400 lines. Re-summarise quarterly.
   /generate-rules → paste your README + a few code samples → commit.
```

---

## Claude Code tips

```
   COMMANDS
   ────────
   claude              # interactive shell in repo
   claude --continue   # resume last session
   claude -p "task"    # one-shot prompt, prints + exits

   KEY PATTERNS
   ────────────
   /init      generate CLAUDE.md from the codebase
   /clear     wipe context for a new task
   /plan      draft a plan, get sign-off, then execute
   /review    review a PR or diff

   SHORTCUTS
   ─────────
   Shift+Tab   cycle permission mode (default / accept-edits / auto-accept / plan)

   POWER PATTERNS
   ──────────────
   1. Plan mode: ask Claude to draft a plan BEFORE editing.
      Edit prompts: "/plan explain how to add a new staging model for events"
      Then "go" to execute.

   2. Subagents: ask Claude to delegate:
      "Delegate to a subagent: review tests/test_dq.py for missing cases."
      Great for keeping main context clean.

   3. Custom slash commands: .claude/commands/dq-review.md — single markdown
      file with a /command. Run on demand.

   4. Hooks: PreToolUse / PostToolUse hooks in .claude/settings.json —
      enforce "no SELECT *" or "run pytest on every save" automatically.

   5. Cursor + Claude Code together:
      - Cursor for in-IDE inline edits.
      - Claude Code for whole-repo refactors, code review, test generation.
      They coexist; pick the right tool per task.
```

---

## GitHub Copilot tips

```
   WHEN COPilot SHINES
   ──────────────────
   - Inline autocomplete (the original use case, still the best).
   - Small, well-scoped completions ("write a regex to extract email").
   - Repeated boilerplate (tests, docstrings, type stubs).
   - Co-pilot Chat for quick asks.

   WHEN IT FALLS SHORT
   ──────────────────
   - Multi-file refactors (Cursor Composer / Claude Code win).
   - Whole-repo context ("explain the data flow across all dags/") — limited.
   - Complex debugging across files — limited.

   SETUP
   ─────
   - Copilot Chat: integrated into IDE.
   - Copilot Workspace: GitHub-native agent (newer, more capable).
   - Don't pay for both Cursor AND Copilot if you have either; pick one IDE tool.
```

---

## OpenAI Codex / Codex Cloud tips

```
   USE CASES
   ─────────
   - Background PR reviews and small fixes.
   - "Open a PR that does X" tasks (async agent).
   - Quick scripted jobs.

   PATTERNS
   ────────
   - Push an issue label / specific phrasing to trigger the agent.
   - AGENTS.md at repo root (Codex equivalent of CLAUDE.md).
   - Use Codex's sandbox for any code that touches prod or PII.
```

---

## Amazon Q Developer (AWS)

```
   WHEN IT SHINES
   ──────────────
   - Working entirely in AWS (Boto, Glue, Bedrock, etc.).
   - Security scanning of generated code.
   - AWS-specific refactors and best-practice hints.
   - VPC / IAM awareness.

   WHEN IT FALLS SHORT
   ───────────────────
   - Non-AWS code (Azure, GCP, Snowflake, Databricks).
   - Anything that needs to reason about other clouds.

   SETUP
   ─────
   - Q inline + Q Chat + Q Agent.
   - Tighter integration with CodeWhisperer for non-AWS shops.
```

---

## Aider

```
   WHEN IT SHINES
   ──────────────
   - Multi-file refactors from the CLI.
   - "Make X change across these 12 files" — git-aware diffs.
   - Cheap (BYO model + minimal tool overhead).

   PATTERNS
   ────────
   - $ aider --model claude-3-5-sonnet --git
   - /add file.py:100-150  — work on a range
   - /diff  — show pending changes
   - /commit  — commit with auto-generated message

   WHEN IT FALLS SHORT
   ───────────────────
   - Interactive IDE ergonomics.
   - Long-lived sessions with lots of context.
```

---

## Continue.dev

```
   WHEN IT SHINES
   ──────────────
   - Self-hosted / air-gapped environments.
   - BYO LLM (Ollama, vLLM, etc.).
   - Customisation beyond what Cursor / Copilot allow.

   WHEN IT FALLS SHORT
   ───────────────────
   - Setup overhead.
   - Smaller community than Cursor / Copilot.
```

---

## The "rules file audit" template

Periodically ask the AI to audit your rules file:

```
   AUDIT (ask the AI)
   ──────────────────
   "Read .cursorrules / CLAUDE.md. What feels out of date? What's missing
   for the conventions I've actually been using this quarter? Rewrite a
   tighter version (max 200 lines) that captures the actual conventions.
   Add anything missing that would prevent repeated mistakes."
```

The AI is good at compressing and refining its own rules.

---

## Decision flowchart

```
   ┌────────────────────────────────────────────┐
   │ Where do I spend most of my day?            │
   │                                            │
   │ In the IDE, writing code     ──► Cursor    │
   │ In the terminal, repo-wide   ──► Claude C. │
   │ Inside GitHub               ──► Copilot    │
   │ On AWS, security-sensitive  ──► Amazon Q   │
   │ Background async agent      ──► Codex      │
   │ Self-hosted / air-gap       ──► Continue   │
   │ Multi-file from CLI         ──► Aider      │
   └────────────────────────────────────────────┘

   Most teams: Cursor (IDE) + Claude Code (agent).
```

---

## The "AI on-call" workflow

When a pipeline breaks at 02:00:

```
   1. /clear  (Claude Code or similar)
   2. paste the traceback + the relevant source file
   3. "Hypothesise root cause. List 3 things you would check next."
   4. follow the lead; verify with a sample run
   5. apply fix, run tests
   6. commit

   In < 5 minutes you can usually reach "I know what's wrong" instead of
   "where do I even start."
```
