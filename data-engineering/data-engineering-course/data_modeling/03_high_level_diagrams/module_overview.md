# Module 03 — High-Level Model Diagrams

> **8 lessons · 0 videos · ~3.5 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

This module is the heart of the data modeling track. It takes you
from a requirements doc to a working star schema, with five
end-to-end worked examples — one per canonical modeling question.

The pattern in every lesson is the same: ER diagram first, then
star schema, then the tradeoffs you'd call out in the interview.
The code in `code/star_schemas.py` is real, runnable SQLite — not
pseudo-DDL.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [13](design/13_er_diagrams.md) | Entity-Relationship Diagrams (ER) | Chen's notation, the four cardinalities, how to draw on a whiteboard. |
| [14](design/14_er_to_tables.md) | From ER to Tables | The five mechanical translation rules (1-to-1, 1-to-many, many-to-many, multi-valued, derived). |
| [15](design/15_star_vs_snowflake.md) | Star Schema vs Snowflake Schema | When star wins, when snowflake wins, and why star is the default. |
| [16](design/16_ecommerce_star.md) | Designing a Star Schema for E-Commerce | The 5-table star; one row per order line item. |
| [17](design/17_rideshare_star.md) | Designing a Star Schema for Ride-Sharing | Two fact tables (trips + cancellations), surge as a measure. |
| [18](design/18_instagram_star.md) | Designing a Star Schema for Instagram | Event-grain fact, author + actor as two user keys. |
| [19](design/19_support_star.md) | Designing a Star Schema for Customer Support | Ticket events, agents, channel as a dim. |
| [20](design/20_spotify_star.md) | Designing a Star Schema for Spotify (music streams) | Stream events, song/artist/album hierarchy, skip rate. |

---

## How the code is organized

```
03_high_level_diagrams/
├── code/
│   ├── star_schemas.py    # 5 build_*_schema(q) functions
│   ├── er_to_tables.py    # the translator (5 rules)
│   └── diagrams.py        # Mermaid-compatible output
└── tests/
    └── test_schemas.py
```

Run the tests:

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

The tests pin down the schemas end-to-end: every table created,
every required measure present, every fact table joinable to its
dimensions.

Run the demo:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

This builds all 5 schemas in `:memory:` SQLite and prints the
sample fact row from each.

---

## The 5 schemas at a glance

| # | Schema | Fact table | Grain | # dims | # facts |
|---|---|---|---|---|---|
| 1 | E-commerce | `fact_order_items` | one row per order line item | 4 | 1 |
| 2 | Ride-sharing | `fact_trips` | one row per completed trip | 5 | 2 |
| 3 | Instagram | `fact_post_events` | one row per post event | 4 | 1 |
| 4 | Customer support | `fact_ticket_events` | one row per ticket event | 5 | 1 |
| 5 | Spotify | `fact_streams` | one row per stream | 6 | 1 |

These are the five canonical modeling questions from
[`docs/reference/de_interview_canonical_questions.md`](../../../docs/reference/de_interview_canonical_questions.md#data-modeling-questions).
By the end of this module you should be able to draw each one from
memory in under 15 minutes.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
