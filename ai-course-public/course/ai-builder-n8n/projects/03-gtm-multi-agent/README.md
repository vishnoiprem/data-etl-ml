# Project 03 — GTM Multi-Agent (Scrape → Enrich → Qualify → Book)

> **A multi-agent lead pipeline.** FireCrawl scrapes the target site, Hunter.io enriches contacts, an LLM qualifies the account and drafts a personalised opener, and the workflow books a Google Calendar slot — or rejects the lead to Slack.

---

## What it does

```
POST /gtm/intake  { target_url, intent? } →
  Validate intake (require target_url) →
  Scrape via FireCrawl (clean markdown, maxDepth 1) →
  Extract hints (heuristic emails/phones, domain) →
  Enrich via Hunter.io (domain-search → canonical contacts) →
  Qualify + draft opener (LLM, strict JSON) →
  Route by verdict:
     qualified → validate email shape → Book Google Calendar (Meet link) →
     rejected  → Notify Slack →
  Respond to caller
```

Four "agents" in one workflow — scrape, enrich, qualify, book — each owning one node cluster, coordinated by shared state (`run_id`, `target_url`) rather than by one god-model deciding everything. This is the **Section 3 lesson** in one file: *orchestration by deterministic routing with LLM judgement at exactly two seams* (qualify, and the Slack reject note).

---

## Setup checklist

| Step | Where to do it | Verify by |
|---|---|---|
| 1. Sign up for FireCrawl (free tier = 500 credits/mo) | https://firecrawl.dev | Dashboard shows credits |
| 2. Sign up for Hunter.io (free tier = 25 queries/mo) | https://hunter.io | Verify email → 1 free query/month |
| 3. Create a Google Cloud service account with Calendar scope | console.cloud.google.com | Calendar API enabled |
| 4. Add the calendar scope to the SA and export a token | Google OAuth | Token can insert an event |
| 5. Create a Slack incoming-webhook / bot token for the notify channel | Slack apps | Webhook posts to the channel |
| 6. Create the n8n environment variables (below) | n8n Settings → Variables | `{{ $env.FIRECRAWL_API_KEY }}` resolves |
| 7. Import `workflow.json` | n8n UI | No red nodes |
| 8. Enable the workflow and POST a test target_url | curl | Slack or Calendar confirms the run |

### Environment variables

| Variable | Where it comes from |
|---|---|
| `FIRECRAWL_API_KEY` | FireCrawl dashboard |
| `HUNTER_API_KEY` | Hunter.io dashboard |
| `GOOGLE_CALENDAR_ACCESS_TOKEN` | OAuth token from your SA (expires — see notes) |
| `SALES_OWNER_EMAIL` | You |
| `SLACK_BOT_TOKEN` | Slack app (not the webhook URL — we use the API) |
| `SLACK_NOTIFY_CHANNEL` | e.g. `#gtm-leads` |

---

## The routing contract

The one thing to internalise from this project: **the LLM decides, the workflow disposes.** The model only produces a verdict and an opener; the actual side effects (writing a Calendar event, posting to Slack) live in deterministic Code and HTTP nodes. If the model hallucinates, the worst case is a rejected lead — not a double-booked calendar or a spam blast.

`Route by Verdict` enforces this. It also re-validates the model's email before any booking — a malformed email means automatic reject, no calendar write.

---

## Curl smoke test

```bash
curl -X POST https://<your-n8n-host>/webhook/gtm/intake \
  -H 'Content-Type: application/json' \
  -d '{"target_url":"https://example.com","intent":"qualify-b2b-lead"}'
```

Expect `{"status":"completed","run_id":"run_xxx","qualified":true|false,...}` within ~10–25s (FireCrawl scrape dominates the budget).

---

## MCP note

This skeleton implements the pipeline as a single workflow with FireCrawl called directly. The course's Section 3 also covers wrapping FireCrawl and Hunter.io as **MCP servers** and having the LLM call them as tools. `mcp-server.json` in this folder holds an MCP tool-definition draft for that variant. The single-workflow version above is the better starting point: fewer moving parts, easier to debug, same end behaviour.

---

## What this is NOT

- **Not a cold-outreach bot.** It books a slot on *your* calendar and drafts an opener for a *human* to send. There is no send-email node here on purpose — auto-sending cold email at scale is a deliverability and legal problem, not a learning problem.
- **Not respecting robots.txt by default.** FireCrawl will fetch what you point it at. Only run it against sites you're authorised to scrape.
- **Not Hunter.io-scale-safe.** Free tier = 25 queries/month. The Monday-cadence trigger burns that in ~3 weeks. Check your quota before going live.

---

## Files in this project

```
03-gtm-multi-agent/
├── README.md              ← you are here
├── workflow.json          ← single-workflow orchestration (import this)
├── mcp-server.json        ← MCP tool-def draft (Firecrawl + Hunter as tools)
└── notes/
    └── orchestration.md   ← the routing contract, quotas, OAuth expiry
```

---

**Last updated:** 2026-10-21
**License:** MIT — use freely in your own courses, prototypes, and products.