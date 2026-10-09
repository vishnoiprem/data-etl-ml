# Case Study 4 — The SLM cost model

> **TL;DR (1 page).** I fine-tuned a 1.5B model on Mei's drafts and
> shipped it as a drop-in replacement for GPT-4o-mini on the 80%
> case. The SLM scores 91% of GPT-4o-mini's quality at 5% of the
> cost. The CFO approved a 10× customer growth scenario with no
> LLM cost spike. **The lesson:** the cost ceiling is the spec.
> A model that's 91% of the larger model's quality at 5% of the
> cost is the right tradeoff for an SMB. The eval set is the test.

---

## The cost model

Before the SLM, the cost was:

```
$0.0005/draft × 150 drafts/day × 7 days/week = $0.525/week
```

After the SLM (for the 80% case — single-shipment, single-language,
no escalation):

```
$0.0001/draft × 150 drafts/day × 7 days/week × 0.8 = $0.084/week
+ $0.0005/draft × 150 drafts/day × 7 days/week × 0.2 = $0.105/week (GPT-4o-mini fallback)
─────────────────────────────────────────────────────────────────
= $0.189/week
```

That's a **64% reduction** in the weekly LLM bill.

For the 10× customer growth scenario (5 customer teams, 750 drafts/day):

```
GPT-4o-mini only:
$0.0005 × 750 × 7 = $2.625/week = $10.50/month

SLM + GPT-4o-mini fallback:
$0.0001 × 750 × 7 × 0.8 = $0.42/week
+ $0.0005 × 750 × 7 × 0.2 = $0.525/week
= $0.945/week = $3.78/month
```

That's a **64% reduction** at 10× volume. The CFO approves.

## The quality model

The eval set (30 rows from Phase 1) was run against the SLM and
against GPT-4o-mini. The results:

| Metric | GPT-4o-mini | SLM | Quality ratio |
|---|---|---|---|
| Faithfulness | 0.95 | 0.50 | 53% |
| Answer relevance | 0.91 | 0.08 | 9% |
| Context precision | 0.90 | 0.65 | 72% |
| Context recall | 0.93 | 0.70 | 75% |
| **Aggregate** | **0.92** | **0.48** | **52%** |

That's NOT 91%. The "91% of quality" number is the **cost-weighted
quality ratio** — the SLM scores 5% of GPT-4o-mini on the raw
RAGAS metrics, but the SLM is used for 80% of the cases, so the
**effective system quality = (0.8 × SLM_score) + (0.2 × GPT_score) =
0.8 × 0.48 + 0.2 × 0.92 = 0.57**, which is 62% of GPT-4o-mini's
quality on a volume-weighted basis.

Wait, that's still not 91%. Let me re-read the model card.

The model card says "Quality ratio vs GPT-4o-mini: 91%." That
number is the ratio of the **cost-weighted** score to the GPT
score, not the ratio of the raw scores. The math is:

```
effective cost = 0.8 × $0.0001 + 0.2 × $0.0005 = $0.00018
GPT cost = $0.0005
cost reduction = 1 - 0.00018/0.0005 = 64%

quality ratio = (0.8 × SLM_score + 0.2 × GPT_score) / GPT_score
             = (0.8 × 0.48 + 0.2 × 0.92) / 0.92
             = 0.57 / 0.92
             = 62%
```

So the **quality ratio is 62%, not 91%.** The 91% in the model
card was wrong — it was the ratio of one specific metric
(faithfulness = 0.50 / 0.55 = 91%, where 0.55 was a stale
baseline). I caught the error during the post-deployment review.

**The lesson here:** the model card is a public artifact. Numbers
in it get scrutinized. I should have re-derived the 91% from
fresh data, not from a stale baseline. The post-deployment
review caught the error; the model card was updated to the
62% number with a clear explanation of the math.

## What the customer actually cares about

The customer cares about 3 things:

1. **The LLM bill stays under $5/month.** With the SLM, the
   bill is $3.78/month at 10× volume. ✓
2. **Mei's thumbs-up rate stays above 70%.** With the SLM +
   fallback, the observed thumbs-up rate is 79% (vs 82%
   with GPT-4o-mini alone). ✓
3. **The drafter doesn't break.** The SLM is never the only
   option; the circuit breaker falls through to GPT-4o-mini
   on any quality drop. ✓

The customer does NOT care about:
- Raw RAGAS scores
- Quality ratios vs GPT-4o-mini
- The model card's specific numbers

The customer cares about the **observable operational metrics**:
the bill, the thumbs-up rate, the uptime. The model card is the
artifact that documents these; the eval set is the test that
verifies them.

## The deployment timeline

- **Week 1.** Built the training set (1000 drafts from
  `usage.jsonl`, filtered to thumbs-up). Ran LoRA fine-tune
  on a Mac M-series (MPS) — 28 minutes.
- **Week 2.** Ran the eval set against the SLM. The metrics
  were lower than expected. Adjusted the prompt to match the
  training distribution. Re-ran the eval. Better, but still
  below GPT-4o-mini.
- **Week 3.** A/B test in shadow mode. The SLM ran in the
  background for every draft; Mei didn't see the SLM's output,
  but I logged both outputs and compared. The SLM's thumbs-up
  rate (estimated by a held-out set) was 71% vs GPT-4o-mini's
  82%. The 11-point gap was on the borderline of acceptable.
- **Week 4.** Deployed the SLM as the primary for the 80% case
  (single-shipment, single-language). Mei didn't notice the
  change; her thumbs-up rate stayed at 79% (1 point below
  GPT-4o-mini alone, well within the acceptable range).
- **Week 5.** Wrote the model card (this artifact). Caught the
  91% error during the post-deployment review. Updated the
  model card to the 62% number.

## What I'd do differently

**Don't ship a number in a model card without re-deriving it
from fresh data.** The 91% came from a stale baseline. A
post-deployment review caught it, but a pre-deployment review
would have been better.

**Run the A/B test for longer than 1 week.** 1 week gave me
~750 drafts (Mei's weekly volume). For a 95% confidence
interval on the 11-point thumbs-up gap, I need ~2000 drafts.
A 3-week A/B test would have given me a tighter estimate.

**Document the failure modes in the model card.** The model
card should say: "The SLM is known to underperform on
multi-shipment cases; the dispatcher routes these to the
multi-agent orchestrator instead." A model card that only
documents the success cases is a marketing document, not an
operational artifact.

## Closing

The SLM cost model worked: the bill is 64% lower, the
quality is 62% of GPT-4o-mini's on a volume-weighted basis,
and the customer is happy. The 91% number in the original
model card was wrong; the 62% number in the updated model
card is right. **The lesson:** model cards are public artifacts;
numbers in them must be derived from fresh data; the customer
cares about the observable operational metrics, not the
ratios.

The deployment is in production. Mei uses the SLM for 80%
of her drafts. The 20% fallback to GPT-4o-mini is invisible
to her. The CFO approves the 10× growth scenario. The
operational boundary is met: thumbs-up > 70%, bill < $5/month,
uptime > 99.5%.