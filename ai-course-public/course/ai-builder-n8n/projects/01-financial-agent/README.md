# Project 01 — Autonomous Financial Agent

> **A scheduled n8n agent that polls MarketStack, decides buy/sell/hold via LLM, and rewrites allocations into Google Sheets.** No broker integration — it writes *target* allocations; a human acts on them.

---

## What it does

```
Every 4h →
  Load tickers (config) →
  MarketStack EOD HTTP fetch (one request per ticker) →
  Compute signals (SMA20/50, momentum, vol) →
  LLM rebalance decision (structured JSON output) →
  Validate & normalise (clamp 2–40%, renormalise to 100) →
  Append to Google Sheets 'Allocations' tab →
  Summarise run
```

The LLM never *fetches* prices — features are computed deterministically upstream. The LLM reasons, it doesn't snooze on a rate-limited API.

---

## Setup checklist

| Step | Where to do it | Verify by |
|---|---|---|
| 1. Sign up for MarketStack (free tier) | https://marketstack.com | Account page shows 100 req/day free quota |
| 2. Create a Google Sheet with a tab called `Allocations` | Google Sheets | Headers: `as_of, symbol, target_pct, action, reason` |
| 3. Create a Google Cloud OAuth2 app with Sheets API + Drive API enabled | https://console.cloud.google.com | OAuth2 client with redirect URI matching your n8n URL |
| 4. Wire the OAuth2 credential into n8n (Credentials → Google Sheets OAuth2) | n8n UI | Test connection returns 200 |
| 5. Create an OpenAI-compatible credential pointing at OpenRouter | n8n UI | Test connection succeeds with a 1-token prompt |
| 6. Set `MARKETSTACK_API_KEY` as an n8n instance variable | n8n Settings → Variables | Echo it in a Code node to confirm |
| 7. Import `workflow.json` into n8n | n8n UI → workflow menu → Import | No red nodes after import |
| 8. Click 'Execute Workflow' once with cron disabled | n8n UI | `Allocations` sheet gains 5 rows |
| 9. Switch trigger to scheduled | n8n UI | `Every 4 Hours` is active |

---

## Local n8n (Docker)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e N8N_HOST=localhost \
  -e N8N_PORT=5678 \
  -e WEBHOOK_URL=http://localhost:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

Then visit http://localhost:5678. Free; no account needed.

---

## The single most failure-prone step

**Google Sheets scope.** A credential with only the spreadsheets scope can't read the OAuth state n8n needs to refresh the token. The error presents as a 401 at the *Sheets write* node, which makes you think the workflow is broken. It isn't — fix the scope. The minimum scopes this workflow needs are:

- `https://www.googleapis.com/auth/spreadsheets` (read + write the sheet)
- `https://www.googleapis.com/auth/drive.file` (n8n's credential refresh path)

If you only add the first, you'll get an opaque token-refresh failure that cost me 40 minutes on the first run.

---

## What this is NOT

- **Not a live trading system.** It writes `target_pct`. It does not place orders.
- **Not back-testable as-is.** If you flip the trigger to "manual + replay", the LLM will see *future* prices if you replay today's data — a leakage bug. Replay only against a frozen dataset.
- **Not immune to LLM hallucination.** If the LLM invents a symbol not in your input or refuses to normalise to 100, the `Validate & Normalise` node throws — that's by design. Your `Allocations` sheet is append-only, so the previous valid day's state is preserved.

---

## Test scenarios

Three runs you should do manually before letting this run unattended:

1. **Happy path** — five large-cap tickers, model returns valid JSON → sheet gains 5 rows.
2. **LLM rebel** — temporarily change the model system message to "Return no JSON" → workflow fails at `Validate & Normalise`, sheet unchanged.
3. **MarketStack 429** — paste a deliberately wrong key into `MARKETSTACK_API_KEY` → `Fetch MarketStack EOD` returns 401 → `Compute Signals` gets no data → `LLM Rebalance Decision` has nothing to act on → `Validate & Normalise` throws. The whole chain fails closed. *Good.*

---

## Files in this project

```
01-financial-agent/
├── README.md                ← you are here
├── workflow.json            ← import into n8n
└── notes/
    └── nodes.md             ← per-node gotchas (read this before opening an issue)
```

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.
