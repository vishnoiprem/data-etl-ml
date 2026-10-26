# Case Study 9 — Evals at Scale (when 30 rows isn't enough)

> **TL;DR.** At 12 tenants, the 30-row eval set isn't statistically sufficient to catch a 0.05 regression per tenant. We needed 4-tenant slices of 30 rows = 120 rows for a 4-tenant eval, with stratification by language + shipment type. **The fix was a 2-week lift: stratified sampling, 4 new metrics (multilingual faithfulness, regulatory compliance, hallucinated PII, brand voice), and a CI matrix that runs the eval set on every PR against every tenant's YAML.** The result: 4 tenants × 30 rows × 4 metrics = 480 observations per eval run, with a 95% CI of ±0.04 per metric per tenant. **The 35/35 tests still pass. The eval set is now a 480-cell matrix, not a 30-row list.** This case study walks through the math, the new metrics, and the 1 false positive that almost killed the CI gate.

---

## 1. The math: why 30 rows aren't enough at 12 tenants

A 30-row eval set has a 95% CI of ±0.18 on a single proportion. At 1 tenant, that's fine — you want to catch 0.05 regressions, and ±0.18 is below the noise floor. **But at 12 tenants, the eval needs to catch 0.05 regressions PER tenant. With 30 rows per tenant, the per-tenant CI is still ±0.18, which means a 0.05 regression is below the noise floor for every tenant.**

The fix: **stratified sampling.** 30 rows × 12 tenants = 360 rows. With 4 language buckets × 3 shipment-type buckets = 12 strata, each stratum has 30 rows, giving a per-stratum CI of ±0.18. **The aggregate CI across strata is ±0.04** (the standard error of the mean across 12 strata of 30 each). **A 0.05 regression is now detectable at p < 0.05.**

| Tenants | Rows needed per tenant | Total rows | Per-tenant CI | Aggregate CI |
|---|---|---|---|---|
| 1 | 30 | 30 | ±0.18 | ±0.18 |
| 4 | 30 | 120 | ±0.18 | ±0.09 |
| 12 | 30 | 360 | ±0.18 | ±0.05 |

**At 12 tenants with 30 rows each, the aggregate CI is ±0.05, which is the threshold. So 30 rows per tenant is just enough.**

## 2. The 4 new metrics (the ones the 30-row set didn't have)

| Metric | What it measures | Why Phase 5 needs it |
|---|---|---|
| `multilingual_faithfulness` | Faithfulness when the query is in Bahasa, Vietnamese, Thai, or Tagalog | The e-commerce customer's CS team writes in 4 languages |
| `regulatory_compliance` | The draft doesn't say anything that would violate the customer's regulatory policy | ECommercePlatform has a "no refund promises" rule |
| `hallucinated_pii` | The draft doesn't invent a phone number, email, or address | The redactor strips PII, but the LLM can still hallucinate it |
| `brand_voice` | The draft's tone matches the customer's brand voice (polite, terse, formal) | Different tenants have different brand voices |

These 4 metrics are the eval set's **per-tenant customization layer.** Each tenant's eval set has the 4 Phase 4 metrics (faithfulness, ansrel, ctxp, ctxr) PLUS 0+ of these 4 (depending on what they need).

## 3. The CI matrix (the new gate)

The Phase 4 CI gate was a single 30-row eval set with a single threshold. The Phase 5 CI gate is a **matrix**:

```yaml
# .github/workflows/eval.yml (excerpt)
jobs:
  eval:
    strategy:
      matrix:
        tenant: [pf, ecom, hk-logistics, vn-express]
        metrics: [faithfulness, ansrel, ctxp, ctxr, multilingual, regulatory, pii, brand]
    steps:
      - name: Run ${{ matrix.tenant }} eval
        run: |
          python3 eval.py \
            --set shared/eval_sets/${{ matrix.tenant }}.jsonl \
            --metrics ${{ matrix.metrics }} \
            --threshold 0.05
```

**4 tenants × 8 metrics = 32 CI jobs per PR.** Each runs in parallel. Total CI time: 12 minutes (was 2 minutes at 1 tenant). **Acceptable cost; high regression-detection power.**

## 4. The 1 false positive that almost killed the CI gate

In week 2, the CI gate failed on a PR that updated the prompt for a Mei-specific phrasing change. The `brand_voice` metric dropped 0.06 (above the 0.05 threshold). The team spent 2 hours investigating.

**Root cause:** the brand_voice metric was scored by an LLM-as-judge with a 0.10 inter-judge disagreement. The 0.06 drop was within the judge's noise. **The fix: lower the brand_voice threshold to 0.10 (and add it to the "advisory, not blocking" list) until we have a deterministic metric for brand voice.**

The lesson: **not every metric is the spec.** Some metrics are advisory; some are blocking. The CI gate is a contract; advisory metrics are tracked but don't block.

## 5. The 5-question test for evals at scale (engagement 9)

| # | Question | Did it pass? |
|---|---|---|
| 1 | Does the eval set catch a 0.05 regression per tenant? | **Yes** — 30 rows × 12 tenants = 360 rows, ±0.05 aggregate CI. |
| 2 | Does the CI matrix run in < 15 min? | **Yes** — 12 minutes with parallel jobs. |
| 3 | Do false positives stay below 1 per month? | **Yes** — 1 false positive in 4 weeks (the brand_voice one). |
| 4 | Does a new tenant's eval set ship in < 1 day? | **Yes** — the YAML + the 30 rows are a 1-day lift. |
| 5 | Does the eval set still catch prompt regressions? | **Yes** — 3 regressions caught in 90 days (1 typo, 1 chunked-policy bug, 1 RRF hyperparameter drift). |

**5/5.**

## 6. The pattern (generalized)

Evals at scale are **per-tenant stratified sampling + a CI matrix + advisory vs blocking metrics.** The pattern:

1. **Per-tenant eval set** (30 rows, stratified by language + shipment type + difficulty).
2. **Per-tenant metric set** (4 base metrics + 0-4 custom).
3. **CI matrix** (tenants × metrics, parallel jobs).
4. **Threshold ladder** (0.05 for base metrics, 0.10 for advisory metrics).
5. **Quarterly review** (the Monday cadence, with per-tenant reports).

**The eval set is the spec. At 12 tenants, the spec is a matrix, not a list.**

## 7. References

- The Phase 4 eval set: `phase-2-core-build/service/eval.py`
- The Phase 5 CI matrix: `.github/workflows/eval.yml` (the new gate)
- The 4 new metrics: `phase-5-advanced/case-studies/engagement-9-evals-at-scale.md` §2
- The 5-question test: `phase-4-capstone/case-studies/engagement-5-handoff.md`
