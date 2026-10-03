# Measure Game Monetization and Validate a Reporting Repair

## 1. Simple way to think
- A "game monetization product" is anything that makes money: in-app purchases, ads, subscriptions, battle passes.
- The headline metric is usually ARPDAU (Average Revenue Per Daily Active User) — total revenue divided by DAU.
- But revenue has layers: payer conversion (% who buy), ARPPU (revenue per paying user), and frequency of purchase.
- A "broken" report means the number on the dashboard doesn't match the truth — maybe a payment processor dropped events, or a currency-conversion rate updated, or a new SKU isn't classified.
- Repairing a report is detective work: find the first day the metric diverged from a known-good baseline, then bisect.
- "Validate" means proving the new number is right — reconcile against a second source (e.g., payment processor raw logs).
- Don't trust a single dashboard; the truth lives in the raw event stream.

## 2. Interview write-up (how to solve it)
**Core metrics:**
- ARPDAU = Gross Revenue / DAU.
- Payer conversion rate = Paying Users / DAU.
- ARPPU = Gross Revenue / Paying Users.
- Average transactions per payer; median revenue per payer (skew-resistant).
- LTV (30/60/180-day) and payback period (days to recover UA cost).

**Segments to report:**
- New vs. returning users; platform (iOS vs. Android); geo (FX-sensitive); acquisition channel; player level/cohort.

**How to detect a broken report:**
- Compare the dashboard metric to (a) the same metric from raw events, (b) the payment processor's settlement report, and (c) a parallel calculation in a separate pipeline. Any unexplained divergence > 0.5% triggers investigation.
- Sudden step-changes without product changes, or a metric that no longer correlates with its components (e.g., ARPPU drops while transactions and payer count are flat), are red flags.

**Repair workflow:**
1. Identify the divergence date (last "known good" → first "diverged").
2. Bisect: split the period in half and check each half independently — pinpoints the change.
3. Inspect the diff: schema change, upstream job failure, currency table staleness, new SKU unmapped, attribution window shift.
4. Backfill: rerun the broken job with corrected logic for the affected window.
5. Validate: reconcile the backfilled numbers against the alternative source within an acceptable tolerance.
6. Document and add a regression test so the same bug can't recur silently.

## 3. Best optimized solution
- **Statistical caveats:** revenue is heavy-tailed — a single whale can swing ARPPU by 10×. Always report **median revenue per payer** alongside the mean, and use **trimmed means** for alerting. Watch for **selection bias** in cohort LTV (early purchasers aren't representative of all users).
- **Novelty / launch effects:** a new bundle or event spike creates non-stationary baselines; use rolling 28-day windows, not point-in-time comparisons.
- **Validate metric quality:** run a parallel "shadow" pipeline using a different code path; alert when the two diverge by > 0.25% daily. Maintain a daily reconciliation against the payment processor's raw settlements — this is the gold standard.
- **Segmentation strategy:** always break out by platform and geo because FX rates and store fees distort the global number; new SKUs and promos need their own attribution windows to avoid double-counting.
- **Alerting thresholds:** page on-call if ARPDAU moves > 3σ from the 28-day baseline for > 4 hours; ticket at 2σ for 24 hours. Different alert for "metric dropped" vs. "metric rose suspiciously" — both can be bugs.
- **Why it's optimal:** builds defense in depth — a primary metric, a parallel shadow calculation, and an external reconciliation source — so any single failure is caught by the other two. The bisect-and-backfill workflow is the fastest known way to repair a reporting break without re-deriving the entire pipeline.

**Common mistakes:** Using a single source of truth (one pipeline, no reconciliation), so silent failures go undetected for weeks; alerting on raw ARPDAU without segmentation, so a small geo's FX shock looks like a global crisis; confusing gross and net revenue (after store fees and refunds); repairing a report forward-only without backfilling, so the historical comparison is broken; and not adding a regression test, so the same bug recurs the next time the upstream schema changes.
