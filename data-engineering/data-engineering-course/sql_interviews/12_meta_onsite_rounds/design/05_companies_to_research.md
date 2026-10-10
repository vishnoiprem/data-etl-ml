# Lesson 5 — Which Meta Org Each Question Comes From

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source:** Cross-referenced from [Interview101 (2026)](https://www.interview101.com/interviews/meta/data-engineer), [Aced (2026)](https://www.aced.io/guides/meta-data-engineer-interview), [Tryexponent (2026)](https://www.tryexponent.com/guides/meta-data-engineer-interview), [Glassdoor 2026](https://www.glassdoor.com/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm)

The Meta DE loop is uniform across orgs, but each *product surface* has
its own flavor of question. When you get "design a star schema to
track X", the interviewer is testing whether you've worked on the
surface their team owns.

This lesson maps each of the 5 most-asked questions to the Meta org
that typically asks it, so you can read the team's recent tech blog
posts and look like you've been there.

## The 5 surfaces

### 1. Instagram Reels — IG / Reels org

- **Owning team:** Instagram Reels Data Eng
- **Surface:** Reels feed ranking, watch-time, retention
- **Most-asked question:** "Design a star schema to track Instagram Reels performance metrics across different recommendation algorithms." ([Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer))
- **What to read:**
  - [Meta Engineering blog — Instagram category](https://engineering.fb.com/category/instagram/) (filter by "data" tag for the data-warehouse posts)
  - Internal: "Reels Data Warehouse" wiki (ask your recruiter for the link)
  - Recent talks at [Re-Engineering the Code @ Scale](https://atscaleconference.com/) (search for the latest year)
- **The killer follow-up:** "How would you handle the slowly changing dimension of algorithm parameters?" (this is the SCD2 probe — see `04_concrete_solutions.md` Q1)

### 2. Cross-platform user behavior — UA / Identity org

- **Owning team:** Unified Analytics / Identity Resolution
- **Surface:** the unified-user-id graph, FB/IG/WA cross-platform analytics
- **Most-asked question:** "Meta wants to build a unified data model for cross-platform user behavior analysis (FB, IG, WA)." ([Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer))
- **What to read:**
  - [Meta Engineering blog — Data Infrastructure](https://engineering.fb.com/category/data-infrastructure/) (filter for "identity" and "warehouse")
  - Internal: "UA Data Warehouse" wiki (ask your recruiter)
  - The annual [VLDB](https://vldb.org/) / [SIGMOD](https://sigmod.org/) proceedings — Meta publishes 5-10 data-infra papers per year
- **The killer follow-up:** "How do you de-dupe a user_id that appears on 2 platforms?" (the bridge-table probe — see `04_concrete_solutions.md` Q2)

### 3. Ads Auction — Ads / Monetization org

- **Owning team:** Ads Ranking / Auction Infra
- **Surface:** real-time bid optimization, historical campaign performance
- **Most-asked question:** "Design an event-driven data model for Meta's advertising auction system that supports real-time bid optimization and historical campaign performance analysis." ([Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer))
- **What to read:**
  - [Meta Engineering blog — Ads category](https://engineering.fb.com/category/ads/)
  - Internal: "Auction Insights" wiki (ask your recruiter)
- **The killer follow-up:** "How do you support both point-in-time and current-state queries?" (the time-travel probe — see `04_concrete_solutions.md` Q3)

### 4. Ride-sharing (proxy for Move / Marketplace) — Marketplace org

- **Owning team:** Marketplace Data Eng (the "ride-sharing app" question is a proxy for any transactional marketplace: ride-share, food delivery, classifieds)
- **Surface:** transactional funnels, real-time matching, cost optimization
- **Most-asked question:** "Design a data model for a ride-sharing app like Uber. Walk through partitioning at scale." ([Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview))
- **What to read:**
  - Internal: "Marketplace Data Warehouse" wiki
  - Look at any of Meta's published talks on transactional data modeling
- **The killer follow-up:** "How do you keep the hot path (last 24h) fast while still doing backfill on years of cold data?" (the hot/cold partition probe — see `04_concrete_solutions.md` Q4)

### 5. Instagram metric drop — IG / Product Analytics org

- **Owning team:** Instagram Product Analytics
- **Surface:** metric definition, root-cause analysis, segment-level decomposition
- **Most-asked question:** "An Instagram metric is dropping. Walk through your root-cause analysis, the data model that would support it, and the follow-up." ([Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview))
- **What to read:**
  - [Meta Research — Causal Inference publications](https://research.facebook.com/publications/?category=causal-inference) (filter for the most recent 2 years)
  - Internal: "PA Investigation Playbook" wiki (ask your recruiter)
- **The killer follow-up:** "How do you know your counterfactual is the right one?" (the causal-inference probe — see `04_concrete_solutions.md` Q5)

## How to use this map

Before your onsite, ask the recruiter:

> "What team is this loop for? Is it Reels, UA, Ads, Marketplace, or another org?"

The recruiter will usually tell you. Then:

1. Read the team's most recent engineering blog post
2. Find 1-2 papers the team published
3. Look up 1-2 open-source repos the team maintains (Meta has hundreds on GitHub)
4. Bring that flavor into your answer — the interviewer will notice

## The 4 less-common but real surfaces

| Surface | Org | Flavor of question |
|---|---|---|
| Reality Labs (VR/AR) | RL | "Design a data model for Quest telemetry" |
| WhatsApp Business | WA Biz | "Real-time per-business metrics dashboard" (Module 11.5 has the worked example) |
| Privacy / Compliance | Privacy | "Design a data model that supports right-to-be-forgotten" |
| Infra / Presto | Infra | "Design the catalog layer for a Presto cluster serving 50K queries/day" |

These come up less often but show up in 10-15% of loops. Read the
relevant wiki before your onsite.

## How to answer the "what team are you on?" question

If the interviewer asks, *don't lie*. Say: "I prepared for the
data-modeling round generically — Reels, UA, Ads, Marketplace, all
five flavors. I'd love to hear which team this is for so I can ask
more targeted follow-ups."

The interviewer will tell you. Then *use* that — the candidate who
asks the most relevant follow-up question is the one who gets the
strong hire.

## What to study next

- **Module 11.5** — `05_meta_system_design_walkthrough.ipynb` for the full WA Business worked example.
- **Module 4 in `data_modeling/`** — `04_high_level_diagrams` for the dimensional-modeling reference.
- **Module `behavioral_interviews/05_practice/`** — the 14 lessons + 40-question taxonomy for the broader behavioral prep.
