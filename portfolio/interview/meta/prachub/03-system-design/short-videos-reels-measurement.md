# Evaluate Impact of Short Videos in Feed (Reels A/B Test Design)

## 1. Simple way to think

- Imagine Instagram's main feed has always been photos. Now they want to add short videos ("Reels") into the mix. Two big questions: will it work, and how do we know it worked?
- "Will it work" is a measurement problem. You can't just ship it to everyone and hope — you'd ruin the app for millions if it's bad. So you run an **A/B test**: 1% of users get the new feature, 99% don't, then you compare.
- The question is *what to compare*. That's where it gets interesting. There are two kinds of metrics: **success metrics** (did Reels do its job?) and **guardrail metrics** (did Reels break anything?).
- Success metrics for Reels: do people watch? do they come back? do they share? do they create their own? The classic framework: **reach → engagement → retention → creation**.
- Guardrail metrics: did photo views drop? did time-spent get cannibalized? did uninstalls spike? did latency get worse? These are the "don't break the existing product" numbers.
- A/B tests have a dirty secret: **novelty effects**. Anything new gets a temporary bump. Users try it, get bored, and numbers drop. You need to wait — usually 2-4 weeks — before you trust the data.
- A/B tests have another secret: **statistical significance**. If your variant has 0.1% more engagement, is that real or noise? You need enough users and enough time to be sure.
- A concrete example: TikTok's rise proved short video is sticky. Instagram launching Reels isn't "will it work?" — it's "how much will it cannibalize the existing feed, and does the net engagement go up?"

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Before I design the test, let me confirm: are we measuring engagement lift on the feed as a whole, or Reels-specific behavior? And what's the launch plan — 1% canary, then ramp? I'll design a randomized controlled experiment with holdout groups."

**Hypothesis.** "Adding short-form video to the main feed will increase total time-spent and session frequency without cannibalizing photo/video engagement."

**Metric framework — North Star + OEC.** Overall Evaluation Criterion (OEC): **daily active minutes per user**, a composite that captures both engagement breadth and depth.

**Success metrics (decision drivers).**

| Tier | Metric | Why |
|------|--------|-----|
| Primary | DAU | New content brings lapsed users back |
| Primary | Avg time-spent / session | Direct engagement measure |
| Secondary | Sessions per day | Frequency lift |
| Secondary | Reels completion rate | Quality of recommendations |
| Secondary | Reels creation rate | Supply-side health |
| Secondary | Share rate | Virality signal |

**Guardrail metrics (must not regress).**

| Metric | Threshold |
|--------|-----------|
| Photo view-through rate | -2% |
| Stories view rate | -2% |
| 7-day retention | -1% |
| Uninstalls | +0.5% |
| App crash rate | +0.1% |
| Feed load latency p95 | +50ms |

**A/B test design.**

```
Population: 100% of DAU
├── Control (80%): existing feed, no Reels
├── Treatment 1 (10%): 1 Reel per 10 posts in feed
├── Treatment 2 (10%): 1 Reel per 5 posts in feed
└── Holdout (5%): control but excluded from all feature rollouts long-term
```

Wait — to keep it cleaner:

- **Control (50%)**: no Reels in feed.
- **Treatment A (25%)**: Reels in slot position 5.
- **Treatment B (25%)**: Reels in slot positions 3 and 7.
- **Long-term holdout (5%)**: never gets Reels, used for 90-day impact measurement.

**Experiment duration.** Compute via power analysis: with 50M DAU split 50/50, we can detect a 0.5% lift in time-spent with 95% confidence in 7 days. **Run for 28 days** to wash out novelty and capture day-of-week effects.

**Data pipeline.**

```
[Client] -> event SDK -> Kafka -> Flink
   │                                   │
   │                                   ├──> experiment assignment table
   │                                   │
   │                                   ├──> user_daily_metrics (with variant column)
   │                                   │
   │                                   └──> Reels-specific events (impression, play, complete, like, share, create)
                                              │
                                              v
                                       Snowflake / BigQuery
                                              │
                                       ┌──────┴──────┐
                                       v             v
                              A/B dashboard    Significance engine
                              (Tableau/Looker)  (frequentist + Bayesian)
```

**Statistical methodology.** Pre-register the analysis plan. Use a **two-proportion z-test** for binary metrics, **Welch's t-test** for continuous, **CUPED variance reduction** to get more sensitive measurements. Pre-experiment covariates (prior 30-day engagement) reduce variance by ~30%.

**Segmentation.** Don't just look at the average. Slice by: country, age, account age, prior Reels use (Instagram has a separate Reels surface — does cannibalization differ?), platform (iOS vs Android). Heterogeneous treatment effects matter a lot.

**Decision framework.** Ship if: primary metric significant at p<0.01 AND no guardrail breach AND effect stable for 2 consecutive weeks. If guardrail breaches, hold launch. If effect is significant but small (<1%), iterate.

**Failure modes.** **SRM (sample ratio mismatch)**: assignment bug. Check on day 1. **Novelty decay**: effects shrink over time — use the last 14 days, not the first. **Spillover**: users in control see Reels in ads or via friends — hard to avoid, log it. **Bot traffic**: filter before analysis. **Multiple testing**: with 20 metrics, expect 1 false positive at p<0.05 — use Bonferroni or FDR correction.

## 3. Best optimized solution

**Refined experimental platform.**

```
[Feature Flag Service] ──> assigns user to variant at session start
   │
   v
[Event SDK] tags every event with experiment_id + variant
   │
   v
[Kafka] -> Flink (dedup, bot filter) -> Iceberg
   │
   ├──> experiment_metrics_daily (pre-aggregated)
   │       │
   │       v
   │   [Stats engine: 1. CUPED adjustment
   │                2. Sequential testing (mSPRT)
   │                3. Bayesian posterior]
   │       │
   │       v
   │   [Decision API: SHIP / ITERATE / KILL]
   │
   └──> long_term_holdout_pool (5% of users, never get treatment, 90-day retention tracked)
```

**Why a long-term holdout?** A 28-day test underestimates long-term retention impact. The holdout (5% never sees Reels) lets you measure 90-day and 180-day retention impact separately — this is the secret weapon Meta uses.

**CUPED variance reduction.** Compute Δy = y_treatment - y_control - θ·(y_pre_treatment - y_pre_control), where θ comes from a regression on pre-experiment data. Reduces required sample size by 30-50%.

**Sequential testing.** Don't wait 28 days to peek. Use **mSPRT** (mixture Sequential Probability Ratio Test) to allow continuous monitoring with valid p-values. Stop early if effect is huge; keep going if marginal.

**Interleaving experiments.** Beyond A/B: for ranking changes, use **interleaving** — show the same user results from both algorithms interleaved, compare click/share rates. 10x more sensitive than A/B, but only works for ranking experiments.

**Dashboard visualization.**

- **Headline tile**: OEC lift with 95% CI, sample size, days running.
- **Funnel**: impression → play → complete → share → create (per variant).
- **Guardrail panel**: red/green status with threshold deltas.
- **Time-series**: effect over experiment days (catch novelty decay visually).
- **Segmentation heatmap**: variant × cohort, color-coded by lift.
- **Long-term holdout panel**: cumulative retention delta vs. control at day 30/60/90.

**Monitoring & SLOs.**
- Experiment assignment balanced within 0.1% (else abort).
- p-values reported with multiple-testing correction.
- Decision deadline: ship decision by day 21, no later (engineering cost of holding).

**Why it's optimal.**
- OEC + tiered guardrails prevents both shipping useless features and killing good ones over noise.
- CUPED + sequential testing cuts experiment duration by ~40% — faster learning, more experiments per quarter.
- Long-term holdout captures what 28-day tests miss: gradual retention effects and ecosystem changes (creator supply).
- Segmentation catches Simpson's paradox — a feature can hurt overall but help teens, and you should ship to teens.

**What the interviewer is really testing:** They want to see product sense *plus* statistical rigor. Can you define an OEC? Do you know about novelty effects and CUPED? Do you design guardrails before launching, not after? Do you segment? Do you reserve a holdout for long-term measurement? At Meta, the answer to "should we ship?" must come from a framework, not vibes. Bonus: do you understand that adding Reels might cannibalize photos and the *net* effect is what matters?
