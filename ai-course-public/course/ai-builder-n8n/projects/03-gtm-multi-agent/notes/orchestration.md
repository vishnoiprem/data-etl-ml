# Orchestration notes — Project 03

## The routing contract

This project's whole design rests on one sentence: **the LLM decides, the workflow disposes.**

Two seams get model judgement:

1. `Qualify + Draft Opener` — verdict + opener text
2. `Notify Slack (Rejected)` — the rejection note format (via templating, not a model)

Everything else is deterministic Code or HTTP. The model never touches a calendar, an email send, or a CRM write. Consequences:

- Hallucination blast radius is one rejected lead, not a double-booked calendar
- The workflow is replayable and debuggable without re-billing the model
- You can swap the model without re-testing the side effects

---

## Why single-workflow, not sub-workflows

The course's Section 3 also demos `Execute Workflow` sub-workflow composition (scrape as a sub-workflow, enrich as another, etc.). That pattern is worth learning, but it's the *wrong* starting point here, because:

- A sub-workflow call is a network hop in your debug trace. When FireCrawl times out inside a sub-workflow, the parent shows "sub-workflow failed" with no context.
- Credentials resolve at the sub-workflow's own execution, so a missing Hunter.io key surfaces two levels down.
- The state handoff between sub-workflows (`$node["Previous Run"].data`) is genuinely confusing the first three times you use it.

Build it flat first. Refactor into sub-workflows once each cluster is individually passing and you want them reusable.

---

## Quota reality

| Service | Free tier | This workflow's burn |
|---|---|---|
| FireCrawl | 500 credits/mo | ~1 credit/scrape, 3 pages each → ~160 runs/mo |
| Hunter.io | 25 queries/mo | 1 query/run → **25 runs/mo** |
| OpenAI | $5 free credit | ~1.5k tokens/run → ~3,000 runs |

Hunter.io is the binding constraint by an order of magnitude. At a Monday cadence you exhaust the free tier in three and a half weeks. Options, in order of preference:

1. Only call Hunter for domains that passed the cheap heuristic in `Extract Hints` (add an `if` before the enrichment node) — cuts calls by ~70%
2. Cache enrichment results in a Google Sheet keyed by domain
3. Upgrade to a paid Hunter tier ($49/mo for 500 queries)

Don't just run it hourly and find out later.

---

## OAuth token expiry

`GOOGLE_CALENDAR_ACCESS_TOKEN` is an OAuth **access** token, which expires in ~1 hour. The workflow will start failing with a 401 at `Book Google Calendar Slot` roughly an hour after you set it.

Three ways out, worst to best:

- **Manual refresh** — copy a fresh token into the n8n variable whenever it breaks. Fine for a weekend demo; terrible otherwise.
- **n8n's built-in Google Calendar OAuth2 credential** — use it instead of a raw HTTP node with a bearer token. n8n handles the refresh token dance. This is the right answer; the raw-token version exists here only so the workflow is self-contained and vendor-neutral.
- **Service-account domain-wide delegation** — most robust, most setup. Overkill for one calendar.

If you take one thing from this project: **use n8n's credential system, not environment variables, for anything with a refresh token.** Environment variables are for static API keys (FireCrawl, Hunter, Slack bot token). OAuth is what n8n's credential layer is *for*.

---

## The email-shape re-validation

`Route by Verdict` re-checks the model's `primary_contact.email` against a regex before booking. This looks redundant — the model already returned an email. It isn't:

- LLMs will cheerfully return `"john [at] acme [dot] com"`, `"john@acme"` (no TLD), or a trailing comma
- Hunter.io returned a *canonical* address that the model then retyped from context; one hallucinated character and the calendar invite goes nowhere

Cheap check, real failure prevented. Keep it.

---

## MCP variant

`../mcp-server.json` drafts the FireCrawl + Hunter.io pair as MCP tool definitions, for the course's "wrap your integrations as an MCP server and let the model call them as tools" segment.

The tradeoff, stated plainly:

| | Direct HTTP (this workflow) | MCP tool-calling |
|---|---|---|
| Latency | ~1 hop | ~2 hops (model → MCP server → API) |
| Debuggability | Every HTTP call visible in n8n | Tool calls summarised; failures opaque |
| Model flexibility | Fixed pipeline | Model decides when to scrape vs enrich |
| Cost | Deterministic | Variable, model-dependent |

For a lead pipeline where you know the order of operations, direct HTTP wins. MCP earns its keep when the order genuinely depends on what the model discovers — which is Section 3's actual lesson.

---

**Last updated:** 2026-10-21