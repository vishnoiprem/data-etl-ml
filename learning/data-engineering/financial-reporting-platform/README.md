# Real-Time Financial Reporting Platform

> **A complete, runnable data pipeline for financial reporting
> across multiple countries.** Six layers: ingestion → ledger →
> processing → reporting → monitoring → tests. Synthetic data
> by default; pluggable to a real ledger. Multi-country (TH,
> VN, ID) with currency conversion and country-specific
> reporting templates.

This is the "show me a full data pipeline, soup to nuts, in one
project" reference. It's not the most sophisticated project in
the repo — that would be `scb_aml_platform/`. It's the most
*readable*. Every layer is in its own module, every layer has
a smoke test, the whole thing comes up with `make up && make
smoke`.

---

## The 6 layers

```
┌──────────────────────────────────────────────────────────┐
│  1. ingestion/  — synthetic + real-world data extractors  │
│     - bank statement CSV / PDF parsers                    │
│     - card transaction webhook receiver                   │
│     - FX rate fetcher (exchangerate.host)                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  2. ledger/     — append-only, double-entry, country-     │
│                   aware                                    │
│     - journal (immutable postings)                        │
│     - chart-of-accounts per country                       │
│     - reconciliation job (sums must equal zero)           │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  3. processing/ — enrichment + categorization              │
│     - country-specific VAT/GST rules                      │
│     - currency normalization to base currency             │
│     - anomaly detection on the stream                     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  4. reporting/  — outputs the human consumes              │
│     - HTML dashboard (Plotly)                            │
│     - Excel export (openpyxl)                            │
│     - PDF summary report                                 │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  5. monitoring/ — observability                            │
│     - data quality checks (freshness, nulls, distribution)│
│     - pipeline health (lag, retries, errors)              │
│     - alert hook (Slack / email webhook)                  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│  6. tests/      — pytest, every layer has tests           │
│     - unit tests per module                               │
│     - one integration test per layer                      │
│     - one end-to-end test (recon must sum to zero)       │
└──────────────────────────────────────────────────────────┘
```

---

## Quick start

```bash
cd data-engineering/financial-reporting-platform

# 1. Install + smoke
make up
make smoke               # runs the ledger with synthetic data

# 2. Run the full pipeline
python -m src.ingestion.fx_rates
python -m src.ledger.journal
python -m src.processing.enrich
python -m src.reporting.dashboard

# 3. Open the dashboard
open output/dashboard.html
```

The default config ships with synthetic data. To plug in real
data, edit `config.py` and point the ingestion modules at your
real sources.

---

## Design philosophy

Three rules this project holds to, and the larger portfolio
also holds to:

1. **The ledger is the source of truth.** Every report is a
   query against the journal. You can never edit the journal;
   you can only append a correcting entry. This is the same
   pattern as `cqrs-ledger/` and as real banks.
2. **Reconciliation must sum to zero.** Every batch, the
   recon job asserts that the sum of all postings equals zero
   (debits == credits). If it doesn't, the run fails loudly.
   This is the smallest unit test that proves the ledger is
   correct.
3. **Country-aware by default.** Country isn't a column; it's
   a first-class dimension. The chart-of-accounts, VAT/GST
   rules, and reporting templates all vary per country. The
   pipeline is multi-country from the first commit, not
   "multi-country" as a retrofit.

---

## What's in the project

```
financial-reporting-platform/
├── Makefile                 # up, test, smoke
├── docker-compose.yml       # optional: Postgres + Adminer for the ledger
├── requirements.txt
├── config.py                # country / currency / account config
├── run_pipeline.py          # one-shot end-to-end runner
├── run_pipeline.sh          # shell wrapper for cron
├── src/
│   ├── config.py
│   ├── ingestion/
│   ├── ledger/
│   ├── processing/
│   ├── reporting/
│   └── monitoring/
└── tests/
    ├── test_ledger.py       # the recon-must-sum-to-zero test
    ├── test_processing.py
    ├── test_reporting.py
    └── test_pipeline.py     # the one end-to-end test
```

---

## How the layers compose

The pattern is: each layer is a pure function on its input +
the previous layer's output. The pipeline is just
`layer_n+1(layer_n(...))` composed. Every layer can be
re-run from scratch given the same inputs; nothing in the
pipeline depends on hidden state outside the layers.

This is what makes the project small. The same pattern
scales — the 6 layers in this project become 6 layers (or
services, or containers) in a real production system, with
each one running on its own cadence and its own SLAs.

---

## What this is NOT

- **Not a real reporting platform for a real bank.** The
  ledger is correct, but it doesn't have the audit / signing
  / regulatory reporting layers a real bank needs. The
  reference for that is `scb_aml_platform/`.
- **Not a dbt project.** dbt is the right tool for the
  transformation layer; this project uses plain Python
  because the goal is readability. The pattern ports
  directly to dbt if you want it.
- **Not real-time.** The default cadence is end-of-day. If
  you need intraday, the same code composes with Kafka
  between `ingestion/` and `processing/`. The pattern is
  the same; the transport changes.
- **Not multi-tenant.** Each country is a separate logical
  run. For multi-tenant isolation in one logical run, see
  [`../multi-tenant-isolation/`](../multi-tenant-isolation/).

---

## Related directories

- [`../scb_aml_platform/`](../scb_aml_platform/) — the
  production-shaped cousin: 15 countries, MAS 7-year retention,
  the real regulatory reporting layer.
- [`../cqrs-ledger/`](../cqrs-ledger/) — the ledger pattern
  in more detail (this project's `ledger/` is a simplified
  version of that).
- [`../`](../) — the parent `data-engineering/` directory.
  18 projects; this one is the "first thing to read" entry
  point for the data half.
