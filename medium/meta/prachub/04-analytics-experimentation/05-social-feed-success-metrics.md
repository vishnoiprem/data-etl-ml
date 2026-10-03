# Define Success Metrics for a Social Feed Feature

## 1. Simple way to think
- The "main social feed" is the first thing users see when they open the app — change it carefully, because it touches everyone.
- A "north-star" is the single number that, if it goes up, the company wins — for a feed, that's typically daily active users and the time they spend.
- Supporting metrics explain *why* the north-star moved — are people seeing more posts, liking more, posting more?
- Guardrails are the things you refuse to break even if the north-star lifts (e.g., negative feedback, hide-rate, creator health).
- A rollout plan is how you ship without betting the company: 1% → 5% → 20% → 100%, watching metrics at each step.
- "Engagement" sounds good but is dangerous — you can lift it by making people angry. Always pair it with a quality signal.
- Power analysis tells you how long to run the test so you don't call a winner too early or waste weeks on noise.

## 2. Interview write-up (how to solve it)
**North-star metric:** Daily Active Users (DAU) of the feed surface, paired with average qualified feed time per DAU.

**Supporting metrics:**
- Posts seen per session, % of sessions with ≥ 1 like/comment/share.
- Follows from feed per 1k impressions.
- D1, D7, D28 retention of feed openers.
- Negative feedback rate (hides, "show me less") per 1k impressions.
- Creator-side: % of creators posting ≥ 1x/week who keep posting (creator health).

**Guardrails:**
- Hide-rate, report-rate, time-to-first-unfollow.
- DAU of adjacent surfaces (Stories, Reels) — don't let feed gains cannibalize the rest.
- App-store rating and crash-free sessions.

**Segmentation:**
- Power users vs. casual; new vs. tenured; high vs. low baseline engagement; mobile vs. web.

**Rollout plan:**
- 1% canary for 48 hours — checks for crashes and gross metric movement.
- 5% for 7 days — first read on engagement and guardrails.
- 20% for 7 days — power analysis target met; ship/no-ship decision.
- 50% → 100% after 14 days, monitoring long-term retention curves.

**Decision framework:** Ship if north-star DAU lifts > 0.3% with p < 0.05 AND no guardrail moves > 0.2% in the wrong direction AND retention curves look healthy. Otherwise, hold or roll back.

## 3. Best optimized solution
- **Statistical caveats:** use a clustered bootstrap at the user level (users are not i.i.d. within a household or device cluster). Watch for **novelty effects** — feed changes often look great for 7–14 days then fade as users habituate; run ≥ 14 days before deciding.
- **Selection bias** in canary: 1% users may be on different networks or device mixes; reweight using inverse propensity weighting before extrapolating.
- **Simpson's paradox** risk: a global lift can hide a regression in a high-value segment (e.g., teens). Always pre-register segment-level analyses.
- **Validate metric quality:** A/A test the new metric definition before launch; reconcile the new feed-time computation against the legacy one on overlapping users to confirm the comparison is apples-to-apples.
- **Power analysis:** for a 0.3% DAU lift, with Meta's traffic, even 5% rollout for 7 days is over-powered. For a 0.1% guardrail regression, you need ≥ 14 days at 20% to detect.
- **Alerting thresholds:** auto-pause ramp if guardrail regresses > 0.5% within 24h, or if crash rate > 1.5× baseline.
- **Why it's optimal:** pairs an outcome metric (DAU) with a depth metric (time), explicit guardrails to prevent engagement-at-any-cost, segment-level pre-registration to avoid p-hacking, and a staged rollout that catches both technical and behavioral regressions early.

**Common mistakes:** Optimizing session length (rewards doom-scrolling); forgetting to gate on retention not just DAU; running the test too short and mistaking novelty for impact; treating "engagement" as one number when it has quality and quantity components; rolling back too late because no one watched the guardrails; not stratifying by tenure, where the effect is usually largest and most informative.
