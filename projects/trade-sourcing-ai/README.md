# Trade-Sourcing AI

> **A sourcing agent that compares real supplier quotes against a real margin
> model, recommends one supplier with an auditable rationale, and tells you
> what the decision was worth.**

Runs offline on a laptop CPU. No API key. No cloud account. No Docker.

---

## The problem this solves

The `trade-finder` business in this repo already has real economics: a margin
model over 36 products and 15 countries, a verification scoring pass over 10
candidate suppliers, an India demand lookup, and a 10,000-cycle Monte-Carlo
shortlist. The numbers are good. The **decision** is manual.

Today the loop is:

1. Read `reports/supplier_shortlist.md` and pick the top 3.
2. Send RFQs (there is a quote tracker for it).
3. Wait for replies.
4. **Hand-compare the incoming quotes against the margin model.**
5. Pick one, and work out whether the order is worth placing.

Step 4 is the expensive one, and it is the one that goes wrong quietly. A
quote at the wrong unit price, a quote from a supplier that carries a risk
flag, a quote whose lead time cannot meet the delivery deadline — each of
those is a decision that looks like arithmetic until you have priced it
properly.

This project automates step 4 and makes step 5 measurable.

---

## What it is, in one sentence

Given a set of supplier quotes for a product and destination market, it
recomputes the landed margin for each quote using the **real** trade-finder
pricing model, disqualifies quotes that fail the margin, risk, MOQ or
deadline bar, recommends the best survivor, and reports the cost of the
decision and the margin it captured against two baselines.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Corpus size, which retrieval paths are live, active router |
| GET | `/suppliers` | The verified supplier pool, ranked by composite score |
| POST | `/search` | Hybrid BM25 + dense retrieval over products, suppliers, reputation |
| POST | `/suppliers/find` | The sourcing plan for a product: Alibaba search + a ready-to-send RFQ |
| GET | `/suppliers/coverage` | Which viable routes have a verified supplier, and which need sourcing |
| POST | `/quotes/compare` | Compare quotes → recommendation, rationale, conflicts, value |
| POST | `/value/report` | The business view only: cost, time saved, margin captured |
| GET | `/decisions` | The audit ledger, plus an aggregate summary |

---

## How to run it

```bash
cd projects/trade-sourcing-ai

make up      # install dependencies into the shared repo venv
make test    # 268 tests, offline, no API key
make demo    # the full walkthrough: corpus → retrieval → sourcing → decision → value
make eval    # retrieval metrics + decision accuracy, with acceptance gates
make api     # serve on :8000
```

`make demo` prints the whole story. It starts with the gap, then the plan
to close it, then the decision:

```
3. THE SOURCING GAP — where the verified pool does not reach
Viable CN→IN routes: 11
Covered by a verified supplier: 1  (9.1%)

product                     margin demand  sells on  suppliers
----------------------------------------------------------------------------
phone case silicone          39.5%     82   flipkart  — none, must be sourced —
compression socks            32.4%     46   flipkart  — none, must be sourced —
reusable shopping bag         29.6%     50   flipkart  — none, must be sourced —
wooden hair brush            28.1%     46   flipkart  — none, must be sourced —
reusable water bottle        23.2%     60   flipkart  — none, must be sourced —
pet harness                  19.6%     44   flipkart  Guangzhou Bison Technology Co., Ltd.

4. THE SOURCING PLAN — an RFQ you can actually send
Alibaba category: Consumer Electronics > Mobile Phone Accessories > Phone Cases
Search queries:   phone case silicone, silicone phone case, TPU soft phone case, silicone phone case Shenzhen
City cluster:     Shenzhen, Dongguan, Guangzhou
Filters:          Trade Assurance, Gold Supplier, Verified Supplier, 3+ years on Alibaba
MOQ band:         standard (max 1000 units)

Target FOB:  $0.45
Max FOB:     $0.82 (above this the route dies)
Sells on:    flipkart at $2.02 retail

5. THE DECISION — three quotes in, one supplier out
Product: phone case silicone  →  IN  (500 units)

  ✓ Shenzhen Gold Star Technology Co., Ltd. $0.44 FOB  margin  36.2%  lead 19d  score 0.890  risk LOW
  ✓ Shenzhen OCOM Technology Co., Ltd.     $0.52 FOB  margin  30.9%  lead 18d  score 0.819  risk LOW
  ✓ Shenzhen Qiyang Technology Co., Ltd.   $0.38 FOB  margin  40.2%  lead 25d  score 0.895  risk LOW

  → RECOMMENDED: Shenzhen Qiyang Technology Co., Ltd.
    confidence:  0.61

  • Recommend Shenzhen Qiyang Technology Co., Ltd. (qytech_2014) at $0.38 FOB for 500 units.
  • Modelled margin is 40.2% ($0.81/unit, $406 on this order), clearing the 15.0% floor.
  • Landed cost is $1.21 ($0.38 FOB + $0.25 shipping + $0.13 tariff + $0.44 platform fee)
    against a $2.02 destination price.
  • Supplier composite score is 8.476/10 with risk level LOW, on a 25-day lead time.
  • Ran against Shenzhen Gold Star Technology Co., Ltd. (score 0.8903 vs 0.8952); the margin
    gap is $0.08/unit, or $40 on this order.
  • Note: Quoted FOB is 15.6% below the $0.45 baseline source cost for this product —
    confirm the specification is unchanged before trusting this price.
```

Read the confidence: **0.61**. The winning quote is only $40 better across a
500-unit order and it has the slowest lead time of the three. That is a close
call, and the number says so. It also flags that the quoted FOB is 15.6%
below the modelled baseline source cost — the kind of thing that turns out
to be a specification change rather than a bargain.

---

## How a consumer calls it

```python
import httpx

quotes = [
    {
        "alibaba_id": "goldstar_2010",
        "supplier_name": "Shenzhen Gold Star Technology Co., Ltd.",
        "product": "phone case silicone",
        "dest_country": "IN",
        "order_units": 500,
        "fob_usd": 0.44,
        "lead_time_days": 19,
        "moq": 100,
        "payment_terms": "30% deposit, 70% before shipment",
    },
    # ... the other quotes
]

response = httpx.post(
    "http://localhost:8000/quotes/compare",
    json={"quotes": quotes, "status_quo_alibaba_id": "goldstar_2010"},
    timeout=30.0,
)
body = response.json()

print(body["recommended"]["supplier_name"])          # Shenzhen Qiyang Technology Co., Ltd.
print(body["confidence"])                            # 0.6147
print(body["value"]["margin_captured_vs_status_quo_usd"])  # 0.08
for line in body["rationale"]:
    print(line)
```

---

## The design decision that matters

**The LLM does not pick the supplier.**

The recommendation is computed in plain Python, against the trade-finder's
own landed-cost arithmetic. The model only *narrates* a decision that has
already been made, and the structured rationale sits right next to the
narrative in every response.

This is deliberate:

| | Deterministic decision layer | LLM decision layer |
|---|---|---|
| Reproducible | yes | no |
| Testable | yes | no |
| Auditable | yes | only via the narration |
| Cost per decision | $0.00 local | non-zero |
| Cost of a wrong answer | a bug in the scoring weights | a wrong purchase order |

If you replace `quote_agent.recommend()` with a model call, you lose every
property in the right-hand column. The narration is where a model earns its
keep; the decision is not.

---

## How the corpus is built

Every document traces back to a file in this repo, and carries the source
path and line so a citation can be checked by hand.

| Type | Count | Source |
|---|---|---|
| `product` | 168 | `trade-finder/find_opportunities.py` — 36 products × viable CN/VN → IN/UK/US routes |
| `supplier` | 10 | `trade-finder/verify_suppliers.py` — verified scores, risk flags, MOQ, lead times |
| `reputation` | 3 | `trade-finder/reports/supplier_shortlist.md` — 10,000-cycle Monte-Carlo stats |

Product documents are enriched with the India demand score from
`trade-finder/demand_in.py`, so a retrieval hit carries the demand signal as
well as the economics.

---

## How retrieval works

Three stages, each independently inspectable, with per-stage timings in every
response.

**BM25** — implemented directly (~60 lines) rather than pulled from a
dependency, so the ranking behaviour is readable. The corpus is small and the
stopword list and IDF behaviour matter more than scale here.

**Dense** — `sentence-transformers/all-MiniLM-L6-v2`, local, CPU. If the
package or the weights are missing, the retriever **degrades to BM25-only**
and reports `dense_enabled: false` with the reason. A sourcing decision
should not die because an embedding model was not downloaded.

**Fusion** — reciprocal rank fusion (k=60), the same approach as the
repo's enterprise-search agent. RRF uses rank positions rather than score
magnitudes, so a BM25 score of 14.2 and a cosine similarity of 0.83 can be
combined without one swamping the other.

Filters (`dest_country`, `category`, `min_margin`, `max_lead_time_days`) are
applied **before** fusion, so an irrelevant route cannot occupy a top-k slot.

### Measured on the labelled gold set

```
Recall@5:     0.8333
Precision@5:  0.2750
nDCG@5:       0.6909
MRR:          0.7292
```

Precision@5 is low on purpose: it divides by `k`, not by the number of
hits, so returning three excellent documents instead of five cannot inflate
the score. Two of the eight gold queries accept any of three suppliers, and
precision correctly penalises returning only one of them.

---

## The business case

`POST /value/report` answers three questions, and marks which answers are
measured and which are assumed.

**What did the decision cost?**

```
Agent cost:      $0.0000  (0.5 ms, $0.00 model spend)
```

Local compute priced at the operator rate, plus model spend, which in the
offline path is genuinely zero.

**What did it save?**

```
Manual baseline: 90 min = $112.50
Time saved:      90.0 min = $112.46
```

The manual baseline is an **assumption**, not a measurement, and it is
labelled as one in every report. Time saved is capped at the baseline.

**Was it worth it?**

```
Margin (recommended):  $0.81/unit
Margin (cheapest):     $0.81/unit   ← the naive "pick the lowest price" strategy
Margin (status quo):   $0.73/unit   ← the current shortlist's first pick
Captured vs status quo: $0.08/unit = $40 on this order
```

Two baselines, because they answer different questions:

- **The naive baseline** is what you get by always picking the cheapest
  quote. Here the agent *did* pick the cheapest quote, so it captures $0
  against this baseline. Reporting that honestly matters more than inflating
  it.
- **The status-quo baseline** is what the current shortlist's first pick
  would give. The agent captures $0.08/unit — $40 on this order — by taking a
  quote the shortlist did not rank first.

Scenarios are projected against the **stronger** of the two baselines, with
the assumption stated for each:

```
pessimistic  $0.04   Half the modelled margin gap is realised. The competing
                     quote turns out to be a genuine price, not a one-off...
base         $0.08   The modelled margin holds as priced, measured against
                     the status quo shortlist...
optimistic   $0.12   The margin gap holds and the agent's time saving is
                     spent on additional sourcing decisions...
```

---

## What disqualifies a quote

A quote is rejected — not silently ignored — with the reason attached:

- **Margin below the floor.** The quoted FOB is pushed through the real
  landed-cost model. If the margin falls below the threshold, the quote is
  rejected regardless of anything else about it.
- **Risk level HIGH or UNKNOWN.** A cheap quote from a risky supplier is not
  a cheap quote.
- **Order below the supplier's MOQ.**
- **Lead time cannot meet the deadline.** A quote that arrives too late is
  not a quote.
- **No destination price in the model.** Some products have no India price;
  without one the margin cannot be computed, so the quote cannot be priced.

The rejection case is in the demo, and it is the more important half:

```
No supplier recommended — correctly.
  • No quote cleared the bar. Every quote was disqualified.
  • Shenzhen Gold Star Technology Co., Ltd.: Margin -217.4% is below the
    15.0% floor at the quoted FOB of $8.50.
  • Shenzhen Qiyang Technology Co., Ltd.: Margin -428.9% is below the 15.0%
    floor at the quoted FOB of $7.40.
```

---

## How to find a supplier in the first place

Everything above assumes quotes have already arrived. They usually have not.
So the agent also answers the question that comes *before* the decision:
**who do we contact, what do we ask them, and would the numbers work if they
said yes?**

`POST /suppliers/find` returns three things for a product and destination:

**A search strategy** — the Alibaba category path, the city cluster that
actually makes that product, the platform filters, and a MOQ band that scales
with the order size.

**An RFQ you can send** — a real email body with the target price, the
ceiling, the volume ladder, the payment terms the business plan wants, and
**product-specific questions** that a generic RFQ would not ask:

```
Is the $0.45 target for soft-touch silicone, or hard TPU?
Per-SKU pricing — is that the generic case or a specific model
(iPhone 15/16, Samsung S24/S25)? A fitted case costs more.
Camera cutout: raised lip protection, 1.5mm?
Inner microfibre lining?
Non-yellowing tested to 6 months?
Does the price include the retail box and a barcode label on the
outer box (needed for marketplace fulfilment)?
```

The last question is the difference between a quote and a usable quote.

**The economics** — the target FOB, the maximum affordable FOB, and the
**negotiation room** between them.

### Some routes have no room to negotiate

The gap between the target and the ceiling is not a constant — it is a
function of how much of the destination price the shipping and the
marketplace fee already eat. And it decides which RFQs are worth sending:

| Product | Target | Ceiling | Room |
|---|---|---|---|
| compression socks | $1.10 | $1.61 | **+$0.51** |
| phone case silicone | $0.45 | $0.82 | **+$0.37** |
| reusable water bottle | $1.50 | $1.87 | **+$0.37** |
| wooden hair brush | $1.20 | $1.63 | **+$0.43** |
| reusable shopping bag | $0.60 | $0.87 | **+$0.27** |
| pet harness | $1.80 | $1.99 | **+$0.19** |
| canvas tote bag | $1.40 | $1.49 | +$0.09 |
| LED strip light 5m | $1.20 | $1.27 | +$0.07 |
| smart plug wifi | $1.50 | $1.53 | +$0.03 |
| magnetic phone charger | $2.20 | $2.21 | +$0.01 |
| **car phone mount** | **$1.80** | **$1.80** | **$0.00** |

A car phone mount is priced so that the target FOB already sits exactly on
the margin floor. A supplier who quotes a cent more makes the route
unviable, and there is nothing to concede elsewhere. The plan says so
rather than letting you send an RFQ with a number that cannot move.

A $0.51 gap and a $0.00 gap are both "15% margin" in a spreadsheet, and
they are completely different businesses.

### Where you actually sell

For India there are two shops, and the repo documents them as such:
**Amazon.in** (22% fee) and **Flipkart** (18%). Those are the only two
worth modelling — Etsy's 12% is a Western rate and Etsy does not sell in
India.

The plan returns every marketplace with what it earns, not just the
winner, because the runner-up is a real second option and the failing one
is the shop where the route dies:

```json
"marketplaces": [
  {"platform": "flipkart",  "fee_pct": 18.0, "landed_cost_usd": 1.22, "margin_pct": 0.3955, "clears_floor": true},
  {"platform": "amazon_in", "fee_pct": 22.0, "landed_cost_usd": 1.30, "margin_pct": 0.3555, "clears_floor": true}
]
```

**Flipkart wins on all eleven products**, because the 4-point fee
difference compounds with every product that is already thin. And for
five of them it is the difference between a route and no route:

| Product | Amazon.in | Flipkart |
|---|---|---|
| canvas tote bag | 13.8% ✗ | **17.8%** ✓ |
| LED strip light 5m | 13.3% ✗ | **17.3%** ✓ |
| smart plug wifi | 12.1% ✗ | **16.1%** ✓ |
| magnetic phone charger | 11.3% ✗ | **15.3%** ✓ |
| car phone mount | 11.1% ✗ | **15.1%** ✓ |

**One caveat.** The demand scores are a *combined* Amazon.in + Flipkart
bestseller ranking — the repo's `demand_in.py` documents them as
"composite of Amazon.in / Flipkart bestseller rankings". They say a
category sells well in India; they do not say which shop's buyers want
your product. Choosing the shop on margin is sound. Choosing it on demand
is not something this data can support.


### The price ceiling is solved, not searched

The most useful number in the RFQ is the ceiling: the highest FOB at which the
route still clears the 15% margin floor. It is derived algebraically from the
margin model rather than found by trial:

```
max_fob = (price × (1 − floor) − shipping − platform_fee) / (1 + tariff_rate)
```

For phone case silicone to India that is **$0.82** against a target of
**$0.45**. A test recomputes the margin at the computed ceiling across
every viable India route and asserts it lands on exactly 15.00% — if the
formula and the margin model ever drift apart, the suite fails.

This is what lets you negotiate. "We are looking at $0.45, and $0.82 is the
most the maths allows" is a very different message from "make us an offer".

### The marketplace is a decision, not a default

The trade-finder's `_platform_for` picks the highest-*volume* marketplace per
category, which answers "where do the most buyers are". It does not answer
"where does this route actually make money", because Amazon.in charges 22%
and Flipkart charges 18%.

So both are modelled and the better margin wins. For phone cases that is
Flipkart: **39.5% margin instead of 35.5%**, and a ceiling of $0.82 instead
of $0.76. It also decides which routes exist at all — an LED strip light is
13.3% on Amazon.in (dead) and 17.3% on Flipkart (alive).

Only Amazon.in and Flipkart are considered for India, because those are the
two the repo documents. Etsy's 12% fee is a Western rate and Etsy does not
sell in India, so pricing an India route with it would invent margin that is
not there. Every route reports the marketplace it was priced against, and
the margin and the ceiling always use the same one.

### The honest finding: the verified pool barely covers the opportunity

`GET /suppliers/coverage` measures how much of the India opportunity the
verified supplier pool actually reaches:

```
Viable CN→IN routes: 11
Covered by a verified supplier: 1  (9.1%)
```

The one covered route is pet harness (Guangzhou Bison, LOW risk, 19.6%
margin). The other ten need sourcing from scratch — including phone case
silicone, which is the product the demo runs on end to end.

That gap is not a bug in the data, it is the business case. The verified pool
covers the smart-watch and fitness-band line, and smart watch is a **−2.6%
loss** in India (35% tariff against a $12.80 price point). The pool and the
India opportunity set barely overlap. So the agent has to find suppliers, not
just rank the ones it has.

---

## When this is the right pattern

**Right when:**
- The decision is a repeatable comparison over a bounded set of candidates.
- The economics are modelled well enough that a quote can be priced
  mechanically.
- You need to explain the decision to a human who is accountable for it.
- The margin per decision is large enough that minutes of agent time matter.

**Not right when:**
- The economics cannot be modelled — if you cannot price a quote, you cannot
  rank it, and no amount of retrieval helps.
- There is one candidate and no trade-off. Just buy from them.
- The decision is a one-off with no repeated value. The agent's value comes
  from being run again.
- The data is not there. This project is only as good as the corpus.

---

## What this project is NOT

- **Not a chatbot.** There is no chat endpoint. The interface is a request
  and a structured response.
- **Not an LLM that picks suppliers.** The model narrates. The Python picks.
  See the design table above.
- **Not a supplier scraper.** The discovery endpoints produce a search plan
  and an RFQ; they do not call Alibaba and they do not harvest listings. The
  verified supplier pool is the 10 suppliers in `verify_suppliers.py`.
- **Not trained on live market data.** The demand scores in
  `demand_in.py` are a curated, documented lookup, not a live scrape. The
  supplier economics and the product prices are real; the *quotes* in
  `data/quotes.json` are synthetic and labelled as such in the file.
- **Not multi-tenant.** No auth, no rate limiting, no request isolation. It
  is a reference implementation.
- **Not exercised against Ollama in CI.** The optional Ollama path is
  implemented and reachable, but CI proves the deterministic stub path only.
  A local model server is not a CI dependency.
- **Not a trading system.** It prices an order. It does not place one.

---

## File layout

```
projects/trade-sourcing-ai/
├── README.md                    ← this file
├── Makefile                     ← up / test / demo / eval / report / api / lint
├── app.py                       ← the FastAPI app (137 lines)
├── requirements.txt             ← lower-bound pins, house style
├── pytest.ini                   ← testpaths = tests, addopts = -q
├── conftest.py                  ← puts src/ and the trade-finder dir on the path
├── data/
│   └── quotes.json              ← quote fixtures, labelled synthetic
├── src/trade_sourcing_ai/
│   ├── __init__.py
│   ├── config.py                ← paths, business assumptions, FX fallback
│   ├── corpus.py                ← real trade-finder data → documents + provenance
│   ├── retrieval.py             ← BM25 + dense + RRF fusion + filters
│   ├── supplier_discovery.py    ← search strategy, RFQ, coverage gaps, price ceiling
│   ├── quotes.py                ← quote parsing and validation
│   ├── quote_agent.py           ← the decision: margin, risk, deadline, rationale
│   ├── llm.py                   ← LLMRouter / StubRouter / OllamaRouter
│   ├── explain.py               ← prompt building + narration
│   ├── audit.py                 ← append-only JSONL decision ledger
│   ├── value.py                 ← cost, time saved, margin captured, scenarios
│   ├── service.py               ← the composition root
│   └── evaluation.py            ← retrieval + decision eval harness
├── tests/                       ← 268 tests, offline
│   ├── conftest.py
│   ├── test_corpus.py
│   ├── test_retrieval.py
│   ├── test_supplier_discovery.py
│   ├── test_quotes.py
│   ├── test_quote_agent.py
│   ├── test_llm.py
│   ├── test_value.py
│   ├── test_evaluation.py
│   ├── test_end_to_end.py
│   └── test_api_smoke.py
└── scripts/
    └── run_demo.py              ← the offline end-to-end walkthrough
```

---

## Using a local model instead of the stub

```bash
# Requires a running Ollama with the model pulled.
ollama pull qwen2.5:7b-instruct

export TRADE_AI_LLM_PROVIDER=ollama
export TRADE_AI_OLLAMA_MODEL=qwen2.5:7b-instruct
make demo
```

If the server is unreachable the router falls back to the stub rather than
failing the decision. The recommendation is identical either way — only the
narration changes.

---

## Deployment notes

The service is a stateless FastAPI app plus an append-only JSONL ledger. For
anything beyond a laptop:

- Put the ledger on durable storage (GCS, or a volume) rather than a local
  path.
- The dense index is rebuilt on start (~3 s for 181 documents). Cache the
  embeddings if the corpus grows.
- The corpus depends on the sibling `trade-finder` project being present at
  the configured path. In a container, ship both.

---

## Related directories

- [`../realtime-stock-pipeline/trade-finder/`](../realtime-stock-pipeline/trade-finder/) —
  the margin model, supplier verification and demand lookup this project reasons over
- [`../../learning/agentic-ai/2-enterprise-search-agent-full/`](../../learning/agentic-ai/2-enterprise-search-agent-full/) —
  the reciprocal-rank-fusion retrieval pattern reused here
- [`../../learning/ai-engineering/40-ai-side-hustle/`](../../learning/ai-engineering/40-ai-side-hustle/) —
  the offline-stub LLM router pattern and the scenario-projection style
- [`../../learning/agentic-ai/apex-rag-omni/`](../../learning/agentic-ai/apex-rag-omni/) —
  the eval-harness shape and the append-only audit log

---

**Last updated:** 2026-11-15
**License:** MIT
