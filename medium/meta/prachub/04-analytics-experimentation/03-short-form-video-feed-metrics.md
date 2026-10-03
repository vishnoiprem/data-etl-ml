# Define and Analyze Product Metrics for a Short-Form Video Feed

## 1. Simple way to think
- A short-form video feed (Reels, TikTok, Shorts) is an infinite vertical scroll of 5–90 second clips — success means people keep swiping.
- The feed is a recommendation problem: if the algo shows you videos you love, you stay; if it misses, you bounce.
- "Engagement" here isn't clicks — it's watch time, completion rate, and whether you come back tomorrow.
- Two users on the same feed see different videos, so metrics have to be defined at the impression level, not the user level.
- You can't just optimize for "more views" because that pushes clickbait; you need a quality signal underneath.
- Every metric you define will be gamed by creators or the algo, so you need guardrails next to your goals.
- The biggest leverage point is retention (D1, D7, D28), not session length, because session length can be inflated by infinite scroll without satisfaction.

## 2. Interview write-up (how to solve it)
**North-star metric:** Daily Active Viewers (DAV) of the short-form surface, with average qualified watch time per DAV as a paired quality indicator.

**Supporting engagement metrics:**
- % of DAV who watch ≥ 10 videos per day (depth, not just sessions).
- Average % of video watched (completion rate, weighted by video length).
- Share / remix rate per 1k impressions (active engagement vs. passive).
- D1, D7, D28 retention of new feed openers.
- Follows-from-feed per 1k impressions (the algo is building relationships, not just sessions).

**Segmentation:**
- New vs. existing users (cold-start problem is different).
- Heavy vs. light engagers (the top 1% likely behaves like a different product).
- Creator tier (consumption patterns differ by who you follow).
- Geolocation, device class, network type.

**Experiment proposals:**
- **Personalization A/B:** New retrieval model vs. control. Primary: D7 retention of new openers. Guardrails: report rate, hide rate, creator churn.
- **Length mix test:** Vary the % of videos served that are <15s vs. >30s. Primary: qualified watch time. Risk: longer videos inflate watch time mechanically.
- **Creator-surfacing test:** Boost new creators. Primary: 28-day survival of newly surfaced creators. Guardrail: DAV.

**Pitfalls:** Position bias (videos at slot 1 always win), novelty effects (new algo looks great for 2 weeks then regresses), and survivorship bias in the recommendation funnel.

## 3. Best optimized solution
- Use **qualified watch time** = Σ(min(watched, video_length)) — caps each video at its true length, so a 60s video can't "earn" 5 minutes of phantom watch time.
- **De-bias the metric:** use inverse propensity weighting or a holdout position-randomization to neutralize position bias in completion-rate comparisons.
- **Validate metric quality** by tying it to long-term retention with a lagged correlation analysis; if D7 retention doesn't budge when your metric moves, your metric is vanity.
- **Power analysis:** for a 0.5% lift in D7 retention, with Meta-scale traffic, a 7-day test is enough; for new-user cold-start metrics, run 28 days to capture novelty decay.
- **Guardrails:** time-spent-on-Instagram overall (cannibalization), negative-feedback rate, creator earnings, and a brand-safety metric for unsuitable content surfacing.
- **Decision framework:** ship if primary metric lifts > 0.5% with p < 0.05 AND no guardrail regresses > 0.2%; else iterate. Hold launches for full retention curves, not in-test lifts.
- **Why it's optimal:** anchors on retention (the only metric that pays the bills long-term), debiases for known confounds, and pairs each test with explicit guardrails — preventing the classic "we lifted engagement and tanked creator health" failure mode.

**Common mistakes:** Optimizing average session length (rewarding doomscroll and low-quality loops); ignoring position bias in completion-rate comparisons; calling a test "won" before the novelty effect decays; forgetting cannibalization against the rest of the app; and using impressions as the denominator for engagement, which inflates with low-quality serves.
