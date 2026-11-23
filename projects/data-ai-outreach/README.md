# data-ai-outreach

Outbound business development for **Avilex** (https://avilex.com/) — finding companies with
concrete data/AI delivery or staffing needs and opening business conversations by email.

Focused on Singapore and Southeast Asia.

## What lives where

```
data-ai-outreach/
├── PUKU.md          ← the project brief. Read this first.
├── run.sh           ← wrapper over the pipeline. Start here.
├── drafts/          ← approved-to-send email drafts (per lead)
├── sent/            ← copy of everything actually sent
├── state/           ← working state that isn't in Postgres
└── reports/         ← generated reports
```

The execution engine lives separately, in
[`../leads-pipeline/draft-cron/`](../leads-pipeline/draft-cron/) — git-tracked and canonical.
This directory is the brief and the operator surface; the pipeline is the machinery.

## Quick start

```bash
# 1. Check the environment
./run.sh doctor

# 2. Preview what would happen (no writes, no sends)
./run.sh preview

# 3. Discover prospects
./run.sh discover

# 4. Read the pipeline state
./run.sh status
```

Sending is deliberately awkward, because it should be:

```bash
./run.sh send pitch_pod 3 SEND
```

The literal `SEND` argument is required. Before it runs, drafts must have been reviewed and
approved by you.

## The two modes

| Mode | `apply_mode` | Pitch |
|---|---|---|
| Pod pitch | `pitch_pod` (default) | Avilex staffs a senior pod for you |
| Personal apply | `apply_personal` | Prem applies for the role himself |

They live in separate queues and never mix.

## Requirements

- Python 3.10+ with `make install` in the pipeline dir
- Postgres on `localhost:5433` (`docker compose up -d` in the pipeline dir)
- `.env` with Gmail SMTP credentials — see the pipeline's `SETUP_GMAIL_SMTP.md`

`./run.sh doctor` reports exactly what's missing.

## Rules

The rules live in [`PUKU.md`](PUKU.md), not here, so there is one source of truth. In short:

- Never guess an email address.
- Never send without explicit approval of the exact draft.
- Never bypass the pre-send guards or the cron lock.
- Every company claim traces to a source URL.

## Agent

The `data-ai-outreach` agent (Alex) drives this project. Its definition is at
`.puku-cli/agents/data-ai-outreach.md`, and its working memory at
`.puku-cli/agent-memory/data-ai-outreach/`.
