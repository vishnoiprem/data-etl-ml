# CS-01 (Google) — The 3-min pitch to the Knowledge & Information SVP

> **Mapping:** Original CS-01 (CISO pitch). Retargeted to Google's Knowledge & Information SVP (Prabhakar Raghavan).
> **Goal:** 3 minutes. Pitch a unified data + AI platform strategy for Search + Ads + YouTube. Defend the "why now."

## The brief

Prabhakar Raghavan (SVP, Knowledge & Information) has 30 minutes. The first 3 are yours. The room is Pichai's chief of staff, the Cloud CPO, and the Head of DeepMind partnerships. You have one shot to set the conversation.

**Context they're bringing:**
- K&I data lives in `[NEED SOURCE: Spanner, Bigtable, Borg subsystems — frame as "the data estate is fragmented across N internal systems"]` [CONFIRM: get specific names from your homework]
- The Gemini 2.5 launch drove AI Overviews to `[NEED SOURCE: billions of queries]`. The training data is `[CONFIRM: scale]`. The serving infra is `[CONFIRM]`.
- The YouTube creator analytics platform is `[NEED SOURCE]`-scale.
- The Ads reporting stack is `[NEED SOURCE: years old, what stack?]` [CONFIRM].
- The Cloud segment is +30% YoY but the data plane is the bottleneck — `[NEED SOURCE: cite Cloud Next 2025 talk]`.

**Your 3 minutes:**
- Min 1 — the diagnosis (the fragmented data estate is the ceiling on every AI move)
- Min 2 — the strategy (one platform, federated ownership, $X invest over 3 years)
- Min 3 — the ask (what you need from Prabhakar's seat, the 90-day commitment)

## Acceptance criteria (the rubric is the original CS-01's)

- 3 minutes, no overrun
- 0 acronyms in the first 30 seconds
- Diagnosis in the room's language (Search, Ads, YouTube — not "the data platform")
- Strategy with named $XM investment
- 1 ask, specific
- Defend in 60 seconds

## Solution sketch (do not copy — internalize and re-speak)

**Diagnosis (60s).** "Prabhakar, the data estate across K&I is fragmented. `[CONFIRM: N systems — Borg, Spanner, Bigtable, internal Dremel, etc.]`. The cost is `[CONFIRM: $X/year in duplicated infra]`. The opportunity cost is bigger: every AI move — Gemini in Search, AI Overviews, Performance Max — has to re-discover the same data. The data plane is the ceiling."

**Strategy (60s).** "One platform, federated ownership. Center sets standards, contracts, semantic layer. Spokes own delivery to Search, Ads, YouTube. Investment: $XM over 3 years. Payback: `[CONFIRM: 18-24 months via infra consolidation + AI velocity]`. The bar-raiser test: would this raise the average of the team in 12 months? Yes."

**Ask (60s).** "Three things. One, your visible sponsorship of the contracts on the top 5 K&I source systems — without it, the BUs will route around. Two, the $XM Y1 budget approved at the cloud leadership committee. Three, the BU heads held accountable for data quality and adoption in their scorecards. The 90-day commitment: contracts on the top 3 sources, semantic layer MVP, 1 AI in production with revenue impact."

## Q&A — be ready for

- "Why federated and not a single team?" — Per Opinion 1 in `POINT_OF_VIEW.md`. Federation is the destination; the Y1 shape is hub-and-spoke.
- "Why now?" — Gemini 2.5, AI Overviews, the $75B 2025 capex, the Cloud growth. The window is 18-24 months. After that, the AI competitors catch up.
- "What if the Cloud team wants this under their org?" — Joint ownership. The data plane is K&I; the query layer is Cloud. The seam is the BigQuery contract.

## Watch for when you re-listen

- **Did you set the 3 minutes or did it bleed?** A Prabhakar-level exec will interrupt if the 3 minutes is loose.
- **Did you name a real $XM?** Without a number, the pitch is opinion.
- **Did you use K&I language?** "Search, Ads, YouTube" not "the data org."
- **Did you end with the ask?** A pitch without an ask is a status report.

---

**Source:** Adapted from original CS-01 + Google case-study brief (`COMPANY-BRIEF.md`).