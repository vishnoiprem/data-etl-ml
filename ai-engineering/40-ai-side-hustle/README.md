# AI Side Hustle — Three Revenue Streams, One AI Worker

> **Make money with AI on day one. No audience required.**

This project is a self-contained "side hustle factory" that uses AI to
generate revenue across three independent streams. Each stream runs
autonomously, has its own dashboard, and ships in offline-stub mode by
default so you can see the whole pipeline work end-to-end without an
API key.

## The three streams

```
   ┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
   │ 1. SEO Content Engine   │   │ 2. Micro-SaaS Scaffolder│   │ 3. Digital Product Shop │
   │                         │   │                         │   │                         │
   │ • find profitable kws   │   │ • scrape trending tools │   │ • turn prompts → ebooks │
   │ • write long-form SEO   │   │ • generate landing copy │   │ • generate lead magnets │
   │ • publish to blog/CMS   │   │ • scaffold MVP repo     │   │ • list on Gumroad/Lemon │
   │                         │   │                         │   │                         │
   │ Revenue: ad/sponsor $   │   │ Revenue: subscription $ │   │ Revenue: one-time $     │
   │ Time-to-$: 30–90 days   │   │ Time-to-$: 14–60 days   │   │ Time-to-$: 1–7 days     │
   └─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
            │                                │                              │
            └────────────────────────────────┴──────────────────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │  Revenue Dashboard   │
                                  │  $ / day / stream    │
                                  │  cumulative total $  │
                                  │  best/worst stream   │
                                  └──────────────────────┘
```

## Why these three?

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

## Quick start

```bash
cd ai-engineering/40-ai-side-hustle
pip install -r requirements.txt
make demo        # run all 3 streams on sample data, print revenue dashboard
make test        # 13 unit tests, no network
make stream-1    # run only the SEO content engine
make stream-2    # run only the SaaS scaffolder
make stream-3    # run only the digital product factory
```

## Money math

```
   Stream 1 — SEO articles
     Revenue    = pageviews × RPM / 1000
     RPM        = $5–$30 (info niche) for affiliate-heavy sites
     Time-to-1$ = 30–90 days (Google index + rank)

   Stream 2 — Micro-SaaS
     Revenue    = paying_customers × monthly_price
     Target     = 100 customers × $19/mo = $1,900/mo
     Time-to-1$ = 14–60 days (launch + first 5–10 paid)

   Stream 3 — Digital products
     Revenue    = units_sold × price
     Target     = 50 sales/mo × $19 = $950/mo
     Time-to-1$ = 1–7 days (list it, share it, sell it)
```

## Cost model

For 3 streams × 10 outputs/day with `claude-3-5-haiku`:
- SEO articles (1,500 tok): 10 × $0.001 = $0.01/day
- SaaS scaffolds (2,000 tok): 10 × $0.002 = $0.02/day
- Product copy (1,000 tok): 10 × $0.0008 = $0.008/day
- **Total: ~$0.04/day** to run the whole factory

At a conservative $50/mo across all streams, that's a **3,750:1 ROI**.

## Project layout

```
40-ai-side-hustle/
├── src/
│   ├── router.py          # LLM provider router (stub / Anthropic / OpenAI)
│   ├── ledger.py          # SQLite revenue ledger (the source of truth)
│   ├── stream_seo.py      # keyword research + article generation
│   ├── stream_saas.py     # idea discovery + MVP scaffold
│   ├── stream_product.py  # prompt → eBook / template / printable
│   ├── dashboard.py       # revenue dashboard across all 3 streams
│   └── publisher.py       # mock publishers (Gumroad, blog CMS, etc.)
├── scripts/
│   └── run_factory.py     # end-to-end orchestrator
├── tests/                 # 13 unit tests
├── sample_data/           # ideas, keywords, product briefs
├── output/                # generated articles, scaffolds, products
├── Makefile
├── requirements.txt
└── README.md
```

## License

MIT.
