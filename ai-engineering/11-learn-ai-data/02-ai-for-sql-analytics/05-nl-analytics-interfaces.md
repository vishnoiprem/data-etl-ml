# Lesson 5 — NL Analytics Interfaces

> **Type:** Article · Module 2 · AI for SQL & Analytics
> Building "ChatGPT for our data" that actually works. The semantic layer, the eval harness, and the failure modes that kill the project.

---

## Why this lesson

Every data leader has the same dream: *"let business users ask questions in plain English, get answers instantly, free up analyst time."* Every data leader has watched this project die.

This lesson is about **how to make it work** — and the conditions under which you should not even try.

---

## The honest landscape

```
   "ChatGPT for our data" projects that ship:
   ──────────────────────────────────────────
   ✅ Over a curated semantic layer, 10-50 metrics, single product area
   ✅ With human-in-the-loop for ambiguous questions
   ✅ With eval harness before launch
   ✅ With usage telemetry + feedback loop
   ✅ With a clear owner (data team, not "everyone")

   "ChatGPT for our data" projects that fail:
   ──────────────────────────────────────────
   ❌ Over the raw 200-table warehouse
   ❌ Without a semantic layer
   ❌ Without eval
   ❌ Without an owner
   ❌ Without business involvement in metric definitions
```

---

## The architecture

```
   USER (business stakeholder)
        │
        ▼  natural-language question
   ┌──────────────┐
   │  NL UI       │  Streamlit / Slack bot / internal web app
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Question    │  classify: known metric, ad-hoc, or unsupported
   │  Classifier  │  route accordingly
   └──────┬───────┘
          │
   ┌──────┴─────────────────────┐
   ▼                            ▼
known metric             ad-hoc question
   │                            │
   ▼                            ▼
metric_registry          semantic layer + LLM
returns canonical SQL    (text-to-SQL with retrieval)
   │                            │
   └─────────────┬──────────────┘
                 ▼
            ┌──────────────┐
            │  Validator   │  run, check row count, check NULLs
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  Answer +    │  with confidence score + caveats
            │  caveats     │
            └──────────────┘
                   │
                   ▼
            ┌──────────────┐
            │  Eval log    │  every interaction logged
            │  + feedback  │  for ongoing improvement
            └──────────────┘
```

The classifier is the most important piece. **Most NL queries are repeats** of the same 20 questions. Handle those with 100% accuracy. Let the LLM handle the long tail with appropriate confidence flags.

---

## The semantic layer is non-negotiable

Without a semantic layer, you're betting on the LLM to invent metric definitions correctly. It won't. Every metric needs:

| Field | Example |
|---|---|
| Name | `gross_revenue_monthly` |
| Definition | `SUM(fct_orders.gross_amount) WHERE status IN ('PAID','FULFILLED') GROUP BY DATE_TRUNC(created_at, MONTH)` |
| Owner | Finance team |
| Freshness SLA | daily by 06:00 UTC |
| Tests | matches Finance team's monthly close within 0.1% |
| Documentation | why refunds are excluded |

Build this **before** you build the NL UI.

---

## The eval harness — build it first

You cannot ship a NL analytics product without an eval set. Build it **before** the product.

### Eval set structure

```json
{
  "question": "What was our gross revenue last month?",
  "expected_metric": "gross_revenue_monthly",
  "expected_filters": ["last_month"],
  "expected_sql_template": "SELECT SUM(gross_amount) FROM ... WHERE created_at >= ... AND status IN ...",
  "tolerance": "exact match required",
  "notes": "exclude refunds per Finance definition"
}
```

### Eval dimensions

- **Metric accuracy** — does the right metric get returned?
- **Filter accuracy** — do the right filters apply?
- **Time accuracy** — does "last month" resolve correctly?
- **SQL validity** — does the SQL run?
- **Number reasonableness** — is the answer in the expected ballpark?
- **Caveat quality** — does it mention uncertainty when appropriate?

Run eval on every prompt change. Track over time. Alert on regression.

---

## The "I don't know" pattern

The most important thing the LLM can do is **say "I don't know"**. Most NL products fail because the LLM hallucinates answers instead.

```text
SYSTEM PROMPT (excerpt):
- If the question maps to a known metric in the registry, return that metric.
- If the question is ambiguous (could mean 2+ metrics), ask for clarification.
- If the question is not supported by any known metric, return:
  "I don't have that metric defined. The closest is X. Want me to
   escalate to the data team?"
- Never invent a metric definition.
- Never fabricate a number.
```

This single instruction is the difference between a useful product and a liability.

---

## The human-in-the-loop patterns

```
   TIER 1 — fully automated
   ───────────────────────
   Known metric, simple filter.
   Example: "What was revenue last week?"
   → Answer directly.

   TIER 2 — answer with caveats
   ───────────────────────────
   Ad-hoc but supportable from the semantic layer.
   Example: "What's the conversion rate for Q1 by region?"
   → Answer + caveat "based on 'conversion' as session_to_order; confirm with analyst"

   TIER 3 — escalate to human
   ──────────────────────────
   Out of scope or ambiguous.
   Example: "Why did churn spike in March?"
   → "I can't answer 'why' from data alone. Escalating to analyst."
```

---

## The "this will fail" red flags

Stop the project if any of these are true:

- ❌ No semantic layer exists
- ❌ No one owns the metric definitions
- ❌ No eval harness
- ❌ The warehouse is undocumented (200+ tables, no schema docs)
- ❌ "Self-service analytics" was promised in a quarter
- ❌ The exec sponsor expects 95%+ accuracy on day 1

---

## The success criteria that actually matter

- **% of repeated questions answered correctly** (target: 95%+ on the top 20 questions)
- **Time saved per question** (vs. analyst doing it)
- **User trust score** (do people actually use it twice?)
- **Number of metrics that move from "ask the analyst" to "ask the bot"**

If your NL interface isn't moving metrics out of analyst workload, it's not working.

---

## What Comes Next

> Lesson 6 — **AI Data Quality** — drift, anomaly detection, freshness monitoring, and where AI-driven data quality beats hand-written assertions.
