# Trade Finder — Global Trade Opportunity Engine

> **An always-on system that finds cheap-source ↔ expensive-destination
> product pairs, computes landed cost + margin, ranks opportunities,
> and drafts outreach emails to either the buyer or the supplier.**
> Free public data only (no paid APIs). Two run modes: one-shot and
> 24/7 autopilot.

The trade-finder is the global-trade lead-generation half of the
`realtime-stock-pipeline/`. The stock pipeline (Kafka → Flink →
TimescaleDB → Grafana) is the streaming-data reference build. The
trade-finder is a separate process that lives on top of the same
machine, runs continuously, and writes leads + outreach to disk so
the human can act on them.

The current focal opportunity is **fitness bands / smartwatches
sourced from China and India and sold into the UK, US, EU, and AU
markets**, with a 35%+ gross margin filter and a 12-axis supplier
verification step.

---

## The shape

```
              ┌────────────────────────────────────────────────────┐
              │         trade-finder (this directory)              │
              │                                                     │
              │  find_opportunities.py  ──►  data/  (CSV, JSON)     │
              │  verify_suppliers.py    ──►  reports/ (12 axes)     │
              │  run_autopilot.sh       ──►  logs/   (autopilot log)│
              │  business-plan/         ──►  90-day launch plan     │
              │                                                     │
              │  Data sources:                                       │
              │    - exchange-rates.host      (FX rates, daily)      │
              │    - restcountries.com        (country / currency)  │
              │    - Wikipedia / static       (HS code → tariff)    │
              │    - Built-in price list      (CN, IN, VN, TR, MX)  │
              │    - Built-in dest prices     (US, UK, EU, AU, JP)  │
              └────────────────────────────────────────────────────┘
```

The autopilot runs every 60 minutes by default. Each cycle:
1. Refreshes FX rates.
2. Re-computes landed cost + margin for every (source, product,
   destination) triple.
3. Filters to margin ≥ 35%.
4. Diffs against the last run — only new or changed opportunities
   get new outreach drafts.
5. Cleans up emails older than 7 days from `reports/`.
6. Writes a per-cycle report and appends to `logs/`.

If the script dies, the autopilot restarts it (up to a configured
budget of restarts per window). If it stays dead, the failure
shows up in the run log and the next human check notices it.

---

## The four scripts (and when you'd run each)

| Script | What it does | When to run it |
|--------|--------------|----------------|
| `find_opportunities.py` | The core: find cheap-source ↔ expensive-destination pairs, compute margin, draft emails | `--once` to spot-check; `--loop` for the 24/7 autopilot |
| `verify_suppliers.py` | Score and rank real Chinese suppliers on 12 verification axes (Alibaba data) | Before you contact any supplier; before you place a PO |
| `stress_test.py` | 10,000-cycle cross-verification of the supplier ranking | Before trusting the ranking in a buying decision |
| `run_autopilot.sh` | The wrapper that keeps `find_opportunities.py` alive 24/7 | When you want the system to run unattended |

Plus, in `business-plan/`:

| File | What it is |
|------|------------|
| `01_business_plan_sg_uk_fitness_band.md` | The 90-day plan: market, customer, offer, economics |
| `02_supplier_outreach_emails.txt` | Copy-paste outreach emails to suppliers |
| `03_financial_model.csv` | Revenue / cost / margin / break-even in a spreadsheet |
| `04_90day_launch_checklist.md` | Week-by-week launch checklist |

---

## How to run it

```bash
# One-shot: find opportunities, write data/, exit
python3 find_opportunities.py --once

# Loop: re-run every 60 minutes, 24/7
bash run_autopilot.sh

# Verify a specific supplier ranking (Alibaba data)
python3 verify_suppliers.py

# Stress-test the supplier ranking (10k cycles)
python3 stress_test.py
```

The `--once` mode is the right entry point — it shows you the
output, lets you tune the source/destination lists, and tells you
whether the margin model is calibrated for your products before
you let the autopilot run.

The `--loop` mode is the right production mode. Output goes to
`logs/`, leads go to `data/`, draft emails go to `reports/`.
Old emails (> 7 days) are cleaned up on each cycle.

---

## What the margin model does

`find_opportunities.py` uses a deterministic cost stack:

```
landed_cost = unit_price
            + shipping_per_kg * weight_kg
            + unit_price * tariff_rate(hs_code, source, dest)
            + platform_fee(unit_price, platform)
            + payment_fee(unit_price, payment_method)
            + 3pl_handling_per_order

margin      = (destination_price - landed_cost) / destination_price
```

Tariff rates are looked up from a built-in HS-code table that
covers ~30 of the most common product categories. Shipping and
3PL rates are configurable per (source, destination) lane. Platform
fees default to Shopify Payments + standard card processing.

The filter is `margin >= 0.35`. Lower the threshold for higher-
velocity, lower-margin products. Raise it for the curated,
high-touch segments.

---

## The 12 supplier verification axes

`verify_suppliers.py` scores every candidate supplier on 12 axes.
The axes are not arbitrary — they're the ones that, when I look
back at my own bad supplier decisions, would have flagged the
problem before the PO went out.

1. `years_on_alibaba` — tenure, baseline legitimacy
2. `transaction_12mo` — US$ of confirmed transactions in 12 months
3. `response_rate` — % of inquiries replied to within 24h
4. `response_time_h` — average response time
5. `trade_assurance` — accepts Trade Assurance (escrow)?
6. `verified_supplier` — third-party verified?
7. `on_site_audit` — Alibaba on-site audit report available?
8. `return_rate` — buyer-reported return rate
9. `complaint_rate` — buyer-reported complaint rate
10. `reorder_rate` — buyer-reported reorder rate
11. `lead_time_consistency` — quoted lead time vs. actual
12. `sample_quality` — quality of pre-Production Sample

The composite score is a weighted sum. The weights are
configurable in the script. `stress_test.py` runs the ranking
10,000 times against bootstrapped historical data to surface
the suppliers that stay in the top quartile under noise.

---

## What this is and what it isn't

**It is:**

- A deterministic lead-generation engine for global trade.
- A 24/7 unattended process that writes to disk; safe to leave
  running on a small VM.
- A reference implementation of "what does good trade
  sourcing look like when the data is free public data only?"
- A working business case for fitness bands (SG/UK), with
  business plan, supplier outreach, and financial model.

**It is not:**

- A real-time stream processing system. (For that, see
  [`../flink/`](../flink/) and the rest of the parent
  `realtime-stock-pipeline/` — Kafka + Flink + TimescaleDB +
  Grafana.)
- A scraping tool. All data sources are free public APIs.
- A payments / escrow / contract system. That's between you
  and the supplier.
- A replacement for due diligence. The 12 verification axes
  catch the common signals; nothing replaces a phone call and
  a sample order.

---

## How it fits in the bigger repo

- [`../`](../) — the parent `realtime-stock-pipeline/`. Kafka +
  Flink + TimescaleDB + Grafana. Different problem (real-time
  market data), same machine.
- [`../../data-engineering/`](../../../learning/data-engineering/) — the
  18 data-platform projects. The trade-finder is closer in
  spirit to `e-commerce-end-2end/` and `bloomberg-symbology/`
  than to the streaming stack.
- [`../../leads-pipeline/`](../../leads-pipeline/) — the
  resume/cold-email pipeline for AI consulting. Same outreach
  patterns, different audience.
- [`../../medium/`](../../medium/) — the long-form articles.
  Several pieces on global trade sourcing live there.

---

## Honest scope notes

- The 12 supplier verification axes are calibrated for **Alibaba
  in 2025-2026**. If Alibaba changes their data fields, or
  if you source from a platform with a different data model
  (IndiaMART, ThomasNet, GlobalSources), the axes need to be
  re-mapped.
- The HS-code → tariff table covers ~30 categories. Anything
  outside that needs a real lookup (e.g., the WTO tariff
  database, or a customs broker).
- The 35% margin filter is a starting point. Real landed costs
  include currency conversion friction, returns, chargebacks,
  and the cost of capital tied up in inventory — none of
  which the script models. The financial model in
  `business-plan/03_financial_model.csv` is where to add those.
- The supplier outreach emails in
  `business-plan/02_supplier_outreach_emails.txt` are
  copy-paste ready but assume a single product / single
  market. For multi-product or multi-market plays, edit
  before sending.

---

**Last updated:** 2026-10-13
**License:** MIT — use freely in your own courses, prototypes, and products.
