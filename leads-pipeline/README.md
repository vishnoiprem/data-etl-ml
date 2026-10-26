# leads-pipeline/

Vietnam-based AI/data consulting — engineer placement lead-generation pipeline. Daily drop of fresh remote leads, copy-paste outreach templates, and a tracker that turns "I sent it" into auditable status.

## Shape

```
   ┌────────────────────┐    lead-finder-scout     ┌──────────────────┐
   │  prompt: "find me  │  ───────────────────────▶│  WebSearch +     │
   │  20+ fresh leads"  │                          │  WebFetch x N    │
   └────────────────────┘                          └────────┬─────────┘
                                                            │ verify
                                                            ▼
                                                  ┌──────────────────┐
                                                  │  2026-10-10/     │
                                                  │  full-leads.md   │
                                                  │  leads-tracker.  │
                                                  │  csv             │
                                                  └────────┬─────────┘
                                                           │ copy-paste
                                                           ▼
                                                  ┌──────────────────┐
                                                  │ outreach-tpls /  │
                                                  │ 6 emails + 5 DMs │
                                                  └────────┬─────────┘
                                                           │ send + mark
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  status/         │
                                                  │  tracker         │
                                                  └──────────────────┘
```

## What this directory contains

```
leads-pipeline/
├── README.md                    ← you are here
├── avilx-one-pager.md           ← 1-page capability statement for cold outreach
├── capability-statement.md      ← longer version (gov / enterprise context)
├── X-STRATEGY.md                ← the X / Twitter content + DM strategy
├── pinned-tweet-variations.md   ← copy-paste tweet variants
├── 2026-10-10/                  ← today's lead drop
│   ├── full-leads.md            ← 27 verified leads + cover letters
│   ├── initial-leads.md         ← first 14 leads (pre-WebFetch)
│   └── leads-tracker.csv        ← CSV for Sheets/Excel
├── 2026-10-10-RERUN/            ← second sweep of the same day
├── draft-cron/                  ← the autopilot cron job (deployable)
├── outreach-templates/          ← copy-paste ready
│   ├── email-templates.md       ← 6 email templates
│   └── x-dm-templates.md        ← 5 X/Twitter DM templates
├── platform-links/              ← 20 platform setup URLs
└── status/                      ← submission tracking
```

## Quick start

1. **Open** `2026-10-10/full-leads.md` — 27 leads with apply links.
2. **Send today** — 6 top matches (see Top 6 in `full-leads.md`).
3. **Update status** — mark each lead in `status/README.md` after sending.
4. **Re-run tomorrow** — say "find me 20+ fresh leads" to re-trigger.

## Profile

- **Entity:** Vietnam LLC + Payoneer
- **Bench:** 6–20 W-2 engineers
- **Stacks:** AI/LLM, RAG/agents/evals, React+Python+AWS, Databricks, Snowflake, MLOps, data eng, data analyst, data architect, AWS data
- **Rate tiers:** Founder $80–150/hr, Senior $40–70/hr, Mid $25–45/hr
- **Delivery:** Vietnam → worldwide
- **Filters:** Drop US-only, W-2-only, clearance, on-site, hybrid-city, <$25/hr

## Cadence

- **Daily:** 6 emails + 5 X DMs + 2 APAC + 5 platform = 18 touchpoints
- **Weekly:** 100+ submissions
- **30-day:** 1–3 contracts closed = $20–60K gross

## Re-run

To refresh tomorrow's leads:
> "find me 20+ fresh global-remote AI/data leads"

The lead-finder-scout agent will re-scan with full WebFetch access.

## Honest constraints

- I cannot send emails or DMs on your behalf (no email tool, no X API access).
- WebFetch is blocked to Braintrust/Arc/Lemon/Turing/Glints/JobStreet — would need allowlist expansion.
- WebFetch to x.com is blocked — DM-open status needs manual verification.
- WebSearch sometimes returns noise — agent filters aggressively.

## Source yield (last 24h)

| Source | Verified | Notes |
|---|---|---|
| weworkremotely.com | 9 | Best source |
| A.Team (WWR cross-link) | 2 | $90–170/hr |
| RemoteOK API | 1 | Direct feed |
| HN "Who's hiring" Oct 2026 | 8 | Ashby/Lever/Greenhouse |
| Remotive | 1 | Snippets only |
| APAC (herp, perform.ai, landing.jobs) | 4 | Timezone match |
| X / Twitter | 5 | DM-open needs verify |
| Braintrust/Arc/Lemon/Turing/Glints/JobStreet | 0 | WebFetch blocked |
| **Total** | **27** | — |

---

## What this is NOT

- **Not an ATS / CRM.** This pipeline produces *leads* and tracks *send status*. It does not track replies, schedule calls, or store candidate profiles. That's a different system (and the right tool there is a real ATS, not a Markdown tracker).
- **Not an email-sender.** No SMTP, no SendGrid, no X API. You copy-paste from the templates and send manually. Automating that step is a separate, larger project — and one that requires deliverability work that doesn't fit in this folder.
- **Not a scraping tool.** The lead-finder-scout is an agent (LLM + WebFetch), not a headless scraper. It cannot bypass Cloudflare, log into gated boards, or scale to thousands of sources. It produces 20–30 *quality* leads per run, not 2000 noisy ones.
- **Not a substitute for the actual deployment.** The `draft-cron/` directory is the codification of the daily drop as a cron job; the production version of that lives behind a CD workflow and a real database. This folder is the *content* of the outreach operation.

---

## Related directories

- [`./draft-cron/`](./draft-cron/) — the autopilot cron job (Python 3, runs the daily drop programmatically). The codification of the manual flow above.
- [`./platform-links/`](./platform-links/) — 20 platform setup URLs (Upwork, Toptal, A.Team, etc.) for expanding the lead surface.
- [`./status/`](./status/) — the per-lead submission tracker; the only state that survives the day.
- [`../realtime-stock-pipeline/trade-finder/`](`../realtime-stock-pipeline/trade-finder/`) — the trading cousin of this pipeline: same lead-finder-agent pattern, applied to trade opportunities instead of consulting leads.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
