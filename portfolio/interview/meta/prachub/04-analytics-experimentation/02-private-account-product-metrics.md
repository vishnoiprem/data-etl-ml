# Analyze Private-Account Product Metrics

## 1. Simple way to think
- A "private account" means only approved followers can see your posts — like Instagram's "close friends" but for the whole profile.
- The product team needs to know: are people using it, are they happier for it, and is it hurting the rest of the network (because less public content = fewer ad impressions, less engagement for others)?
- "Adoption" is just whether someone turns the feature on; "engagement" is whether they keep using the app.
- You can't A/B test privacy on real users without consent, so you rely on natural experiments, geo-rollouts, and matched cohorts.
- Privacy choices are sticky: once you go private, you don't usually go back, so the funnel is mostly one-way.
- Engagement comparisons must distinguish the "user changed behavior" effect from the "people who choose privacy were different to begin with" effect.
- Watch the network externality: when a popular user goes private, their followers post less, comment less, and may churn.

## 2. Interview write-up (how to solve it)
**North-star metric:** % of MAU who have at least one private (non-public) post in the trailing 30 days, weighted by reach.

**Supporting metrics:**
- Adoption: % of accounts with private profile enabled.
- Depth: avg private posts per active private account per week.
- Reach preserved: median (and p10) impressions per post for private vs. public accounts.
- Network spillover: engagement delta of *followers of* private accounts vs. followers of public accounts.

**Segmentation to compare:**
- Pre vs. post opt-in (within-user, the cleanest natural experiment).
- Opt-in vs. matched control (propensity score on follower count, posting frequency, tenure, geo).
- Creator tiers (nano / micro / mid / macro / celebrity) — privacy choice means very different things at each tier.
- New vs. tenured users; safe vs. spam-flagged accounts.

**Diagnosis approach:** Decompose engagement change into (a) fewer impressions (mechanical — only approved followers see it) and (b) engagement *per impression* (true demand). The per-impression rate should be HIGHER for private accounts because the audience is curated. If it's flat or down, the feature isn't delivering value.

**Pitfalls:** Survivorship bias (only happy users stay private), selection bias (people who go private were already disengaging), and Goodhart's law (gaming follower-approval counts).

## 3. Best optimized solution
- Use **difference-in-differences** on the within-user pre/post switch, paired with a synthetic control from lookalike public-account users. This nets out selection bias.
- **Power analysis** for any rollout: even a 1% engagement shift matters at Meta scale, so required sample sizes are modest — but account for network spillover (cluster-randomize at the account level, not the post level).
- **Validate metric quality** with a holdout group: are private-account users who say they're "more comfortable" actually posting more? Run a quarterly survey reconciled with behavioral data.
- **Alerting thresholds:** alert if private-account churn rate exceeds public-account churn by > 2pp; alert if creator-tier "macro+" private adoption crosses 5% (revenue risk).
- **Segmentation strategy:** always report by creator tier and tenure, and use interaction terms in regression to confirm the treatment effect isn't uniform.
- **Why it's optimal:** combines within-user and across-user comparisons to triangulate causality, separates mechanical from behavioral effects, and tracks the second-order (network) impact that pure engagement metrics miss.

**Common mistakes:** Comparing aggregate engagement without adjusting for the mechanical reach drop; treating private-account users as one segment when creators and lurkers behave oppositely; ignoring the spillover on followers; using self-reported satisfaction as the primary metric instead of behavior; and not stratifying by tenure, because new users adopt private at very different rates than veterans.
