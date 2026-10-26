# AI Revenue Pipeline — Turn Public Signals into Closed Deals

> **The shortest path from "I have AI/data skills" to "I got paid."**

This project is a complete, runnable revenue engine for an independent AI/data
consultant. It continuously scans public signals (job boards, GitHub trending,
HN hiring posts, funding announcements, conference CFPs, RFPs), scores each
opportunity by **revenue probability**, drafts a personalized outreach email
via LLM, and tracks the deal pipeline end-to-end (lead → proposal → won/lost)
with a money dashboard.

## Why this exists

The hardest part of freelancing / consulting isn't the work — it's finding
the *next* client. Most AI/data portfolios stop at "here are my Kaggle
medals." This one goes further: it ships a working system that turns the
public web into a prioritized list of paid opportunities, with a $/week
close-rate you can watch improve over time.

## What it does

```
  Public signals          ┌─────────────────┐          ┌──────────────────┐
  ──────────────          │                 │          │                  │
  • Job boards  ────────▶ │  Lead Ingestor  │ ───────▶ │  AI Qualifier    │
  • HN "hiring" ────────▶ │  (6 sources)    │          │  (LLM scores     │
  • GitHub trends ──────▶ │                 │          │   $ probability) │
  • Funding news  ──────▶ │                 │          │                  │
  • CFPs / RFPs   ──────▶ │                 │          └────────┬─────────┘
  • Inbound  ───────────▶ │                 │                   │
                          └─────────────────┘                   │
                                                                ▼
                          ┌─────────────────┐          ┌──────────────────┐
                          │  Outbox (Gmail/ │ ◀──────  │  Outreach         │
                          │  SES/SendGrid)  │          │  Generator        │
                          └────────┬────────┘          │  (LLM drafts      │
                                   │                   │   personalized    │
                                   ▼                   │   email)          │
                          ┌─────────────────┐          └──────────────────┘
                          │  Revenue        │
                          │  Dashboard      │ ◀──────── reply / outcome
                          │  ($$ / week)    │            (manual + LLM parse)
                          └─────────────────┘
```

## Quick start

```bash
cd ai-engineering/39-revenue-pipeline
pip install -r requirements.txt
make demo       # runs end-to-end on sample data
make test       # 11 unit tests, no network
```

## Core modules

| File | Purpose |
|---|---|
| `src/signals.py` | 6 source-specific scrapers (job boards, HN, GitHub, funding, CFPs, manual inbox) |
| `src/qualifier.py` | LLM-based scoring: 0-100 revenue probability with reasoning |
| `src/outreach.py` | LLM-generated personalized cold email per lead |
| `src/pipeline.py` | SQLite-backed pipeline: lead → qualified → outreach → replied → won/lost |
| `src/dashboard.py` | $/week close rate, conversion funnel, top lead sources |
| `src/router.py` | Pluggable LLM router: real API (Anthropic/OpenAI) or local stub for demos |
| `scripts/run_loop.py` | Cron-style loop: ingest → qualify → outreach → report |
| `tests/test_*.py` | 11 unit tests covering scoring, dedup, persistence, dashboard math |

## Money math

The dashboard tracks the same 4 numbers any sales team tracks:

```
   $$/week closed = (# won per week) × (avg deal size $)
   Pipeline $     = Σ (deal_value × close_probability) for open opportunities
   Time-to-cash  = median days from "lead seen" to "wire received"
   Conv. rate    = (won) / (won + lost)
```

Sample output (after 1 week on autopilot):
```
   $ / week closed:        $0
   $ open in pipeline:     $84,000  (12 leads × $7k avg × 65% median prob)
   Median time-to-cash:    n/a (no wins yet)
   Conversion rate:        n/a
   Top source by $:        HN hiring (5 leads, $42k weighted)
```

## LLM provider

By default uses the **local stub router** (`router.StubRouter`) so the project
runs without an API key. To use a real model:

```bash
export ANTHROPIC_API_KEY=sk-...
# then change router.py's import in scripts/run_loop.py
```

The router interface is the same regardless of provider — swap one line.

## Cost model

For 100 leads/day with `claude-3-5-haiku`:
- Qualify: 100 × 300 tokens = 30k input, 6k output ≈ $0.045
- Outreach: 100 × 500 tokens = 50k input, 20k output ≈ $0.30
- **Total: ~$0.35/day** to qualify + draft outreach for 100 leads

At a 5% reply rate and 30% close, that's $0.35 × 30 = $10.50 per closed deal
(assuming $5k avg). A 50:1 ROI even before repeat business.

## Files

| File | Purpose |
|---|---|
| `src/signals.py` | Source-specific lead ingestion |
| `src/qualifier.py` | LLM-based lead scoring |
| `src/outreach.py` | LLM-generated cold emails |
| `src/pipeline.py` | SQLite-backed state machine |
| `src/dashboard.py` | Revenue dashboard |
| `src/router.py` | Pluggable LLM router |
| `scripts/run_loop.py` | End-to-end orchestrator |
| `tests/test_qualifier.py` | Scoring tests |
| `tests/test_pipeline.py` | State machine + dedup tests |
| `tests/test_dashboard.py` | Money-math tests |
| `tests/test_signals.py` | Parsing tests |
| `sample_data/signals.json` | 8 example leads for the demo |
| `Makefile` | `make demo`, `make test`, `make clean` |
| `requirements.txt` | Pinned deps (minimal — stdlib + httpx + pytest) |

## License

MIT.
