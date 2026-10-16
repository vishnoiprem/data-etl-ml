# AI Side Hustle — Four Revenue Streams, One AI Worker

> **Make money with AI on day one. No audience required.**

This project is a self-contained "side hustle factory" that uses AI to
generate revenue across four independent streams. Each stream runs
autonomously, has its own dashboard, and ships in offline-stub mode by
default so you can see the whole pipeline work end-to-end without an
API key.

> **What's new in 0.2.0 (2026-10-13):** [`CHANGELOG.md`](./CHANGELOG.md)
> `LICENSE` (MIT), `.env.example` for the LLM keys, `.gitignore` (no
> more committed 480KB of generated PDFs), 5 new tests for the router
> fallback chain, plus 3 new docs:
> [`docs/FIRST_DOLLAR.md`](./docs/FIRST_DOLLAR.md) (7-day runbook),
> [`docs/PRODUCT_NICHES.md`](./docs/PRODUCT_NICHES.md) (what to ship),
> [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) (when it breaks).

## The four streams

```
   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
   │ 1. SEO Content     │  │ 2. Micro-SaaS      │  │ 3. Digital Product │  │ 4. Print-on-Demand │
   │    Engine          │  │    Scaffolder      │  │    Factory         │  │    Merch           │
   │                    │  │                    │  │                    │  │                    │
   │ • keywords         │  │ • idea discovery   │  │ • eBook/template/  │  │ • slogans + briefs │
   │ • long-form SEO    │  │ • landing copy     │  │   printable        │  │ • for designers    │
   │ • publish to CMS   │  │ • scaffold MVP     │  │ • Gumroad listing  │  │ • Redbubble/Merch  │
   │                    │  │                    │  │                    │  │                    │
   │ $: ad/affiliate    │  │ $: subscription    │  │ $: one-time        │  │ $: royalty         │
   │ T-t-$: 30–90d      │  │ T-t-$: 14–60d      │  │ T-t-$: 1–7d        │  │ T-t-$: 14–30d      │
   └────────────────────┘  └────────────────────┘  └────────────────────┘  └────────────────────┘
            │                        │                        │                        │
            └────────────────────────┴────────────────────────┴────────────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │  Revenue Dashboard   │
                                  │  $ / day / stream    │
                                  │  cumulative total $  │
                                  │  best/worst day      │
                                  │  sparkline (14d)     │
                                  └──────────────────────┘
```

## Why these four?

1. **Digital products** are the *fastest* path to a first dollar — you
   can list something on Gumroad in an afternoon. LLM-generated
   eBooks/notion templates/printables sell for $9–$49 with zero
   inventory and zero shipping.
2. **Micro-SaaS** has the highest *upside* per project. Most fail, but
   one hit at $29/mo × 1,000 customers = $348k/yr. The AI scaffolds
   10× faster than hand-rolled, so the expected value is positive
   even with a 5% hit rate.
3. **SEO content** is the *slowest* but most compounding. An article
   that ranks for "best X for Y" can pull $50–$500/mo indefinitely
   from affiliates, sponsors, or ad networks. It's the annuity.
4. **Print-on-demand merch** is the *lowest effort*. No inventory, no
   audience needed (Amazon's organic traffic is the audience), and a
   designer can ship your AI-generated slogans to Merch by Amazon in
   under an hour. Royalty: $2.50–$4.50 per sale.

## Quick start

```bash
cd ai-engineering/40-ai-side-hustle
make help            # see all 13 targets — start here
make install         # pip install -r requirements.txt
make demo            # run all 4 streams on stub data, print dashboard
make simulate-30d    # run streams + inject 30 days of synthetic sales
make stream-1        # run only the SEO content engine
make stream-2        # run only the SaaS scaffolder
make stream-3        # run only the digital product factory
make stream-4        # run only the merch stream
make launchkit       # build Gumroad launch kits (PDF + sales page + tweets) for all products
make test            # unit tests, no network (110 tests, ~3 sec)
```

**Want a real LLM, not the stub?** Copy `.env.example` to `.env`
and set `ANTHROPIC_API_KEY=sk-ant-...` (recommended; ~$0.04/day
at 40 calls/day with `claude-3-5-haiku`). Then uncomment
`# anthropic>=0.30.0` in `requirements.txt` and `make install`.
The router will pick Anthropic first, fall back to OpenAI, then
to `StubRouter` if no key is set. See `.env.example` for details.

**Want to make money this week, not just run a demo?**
Read [`docs/FIRST_DOLLAR.md`](./docs/FIRST_DOLLAR.md) — a literal
7-day runbook that takes you from `make demo` to your first sale
on Gumroad.

## Money math

```
   Stream 1 — SEO articles
     Revenue    = pageviews × RPC (rank × CTR × $/click)
     Projection = volume × P(top10) × CTR × 30% CPC
     Time-to-1$ = 30–90 days (Google index + rank)

   Stream 2 — Micro-SaaS
     Revenue    = paying_customers × monthly_price
     Projection = launch_visitors × trial_rate × trial_to_paid × price
     Time-to-1$ = 14–60 days (launch + first 5–10 paid)

   Stream 3 — Digital products
     Revenue    = units_sold × price
     Projection = impressions × conversion × price
     Time-to-1$ = 1–7 days (list it, share it, sell it)

   Stream 4 — Print-on-demand
     Revenue    = impressions × conversion × royalty
     Royalty    = $4.50 (shirt) / $2.50 (mug/sticker)
     Time-to-1$ = 14–30 days (Amazon review + organic traction)
```

Each projection in `src/projections.py` ships with optimistic and
pessimistic bounds so the dashboard shows a range, not a single
hand-wavy number.

## Cost model

For 4 streams × 10 outputs/day with `claude-3-5-haiku`:
- SEO articles (1,500 tok): 10 × $0.001 = $0.01/day
- SaaS scaffolds (2,000 tok): 10 × $0.002 = $0.02/day
- Product copy (1,000 tok): 10 × $0.0008 = $0.008/day
- Merch briefs (500 tok): 10 × $0.0004 = $0.004/day
- **Total: ~$0.04/day** to run the whole factory

At a conservative $50/mo across all streams, that's a **3,750:1 ROI**.

## Project layout

```
40-ai-side-hustle/
├── src/
│   ├── router.py          # LLM provider router (stub / Anthropic / OpenAI)
│   ├── ledger.py          # SQLite revenue ledger (4 streams)
│   ├── projections.py     # calibrated revenue projection model
│   ├── stream_seo.py      # keyword research + article generation
│   ├── stream_saas.py     # idea discovery + MVP scaffold
│   ├── stream_product.py  # prompt → eBook / template / printable
│   ├── stream_merch.py    # print-on-demand slogans + designer briefs
│   ├── simulator.py       # inject synthetic daily sales events
│   ├── dashboard.py       # revenue dashboard with sparkline
│   ├── indexer.py         # output/INDEX.md generator
│   └── publisher.py       # local file publishers
├── scripts/
│   └── run_factory.py     # end-to-end orchestrator
├── tests/                 # unit tests
├── output/                # generated assets (INDEX.md lists them)
├── Makefile
├── requirements.txt
└── README.md
```

## Documentation

The README is the overview. The docs/ folder is the recipes:

| File | Read it when |
|---|---|
| [`docs/FIRST_DOLLAR.md`](./docs/FIRST_DOLLAR.md) | You have time this week and want a literal 7-day plan to your first Gumroad sale. |
| [`docs/PRODUCT_NICHES.md`](./docs/PRODUCT_NICHES.md) | You're picking a topic and want to know which 3 ship today vs. 7 to try next. |
| [`docs/TROUBLESHOOTING.md`](./docs/TROUBLESHOOTING.md) | `make demo` didn't work like the README claims. 95% of issues are in the first 5 sections. |
| [`CHANGELOG.md`](./CHANGELOG.md) | You want to know what changed between 0.1.0 and 0.2.0. |
| [`LICENSE`](./LICENSE) | MIT — the full text. |

## License

MIT. See [`LICENSE`](./LICENSE).
