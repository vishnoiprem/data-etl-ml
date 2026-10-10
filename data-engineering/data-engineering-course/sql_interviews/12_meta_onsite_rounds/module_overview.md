# Module 12 — Meta Data Engineer Onsite Rounds (2026 Format)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The 60-min CoderPad screen (covered in Module 11) is the gateway. After
the screen, Meta runs **4 onsite rounds** (or **5** per Aced 2026: 4
blended technicals + 1 standalone behavioral):

1. **Data Modeling** (45-60 min, whiteboard)
2. **Product Sense / Full-Stack** (60 min, hardest round)
3. **Advanced SQL / Coding** (45-60 min, paired with the Product Sense)
4. **Behavioral / Ownership** (30-45 min, standalone at E5/E6)

This module covers the **3 onsite content areas** that aren't already in
Module 11: the data-modeling round, the architecture-flavor of the
product-sense round, and the leadership-flavor of the behavior round.

## What this module adds

- `01_data_modeling_round.md` — the 60-min whiteboard, star schema, SCD, the 5 most-asked 2026 questions with worked ER diagrams.
- `02_architecture_round.md` — the system-design flavor of the product-sense round. The 5-step framework with cost model, plus 3 worked examples (WA Business, Reels, Ads Auction).
- `03_leadership_round.md` — the E5/E6 ownership round. 4 question families, 8 worked answers using the ride-share pipeline as the canonical scenario.
- `04_concrete_solutions.md` — sample answers to the 5 most-asked schema design questions.
- `05_companies_to_research.md` — which Meta org (FB / IG / WA / Reality Labs / Ads) does each question come from.

## Pair with

- **Module 11** for the 60-min screen
- **`design/04_onsite_flavoured_sql.md`** in Module 11 for the SQL flavor
- **`design/05_sessionization_pattern.md`** in Module 11 for the most-asked pattern
- **`docs/reference/company_specific_prep.md`** for the master timeline

## Working code

The module ships 3 things:

1. A reusable ER-diagram-as-text convention for whiteboard practice.
2. Sample schemas for the 3 most-asked product surfaces: Reels, WA Business, Ads Auction.
3. 3 Jupyter notebooks that exercise the schemas against the ride-share / Meta schema fixture.

Test count: 6 new tests across 3 files.
