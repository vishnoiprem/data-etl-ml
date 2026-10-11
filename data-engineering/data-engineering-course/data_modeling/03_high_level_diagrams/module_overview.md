# Module 03 — High-Level Model Diagrams

> **8 lessons · 0 videos · ~3.5 hours**
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

This module is the heart of the data modeling track. It takes you
from a requirements doc to a working star schema, with six
end-to-end worked examples — one per canonical modeling question.

The pattern in every lesson is the same: high-level model diagram
first, then star schema, then the tradeoffs you'd call out in the
interview. The code in `code/star_schemas.py` is real, runnable
SQLite — not pseudo-DDL.

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [13](design/13_creating_high_level_model_diagrams.md) | Creating High-Level Model Diagrams | The five diagrams (ER, conceptual, logical, physical, dimensional) and when each is the right tool. |
| [14](design/14_evolving_models_based_on_changing_requirements.md) | Evolving Models Based on Changing Requirements | The four moves for schema change (add column, add fact, evolve dim, deprecate) and the expand-contract pattern. |
| [15](design/15_practice_online_advertising.md) | Practice: Online Advertising Platform | Event-grain fact with 0/1 flag measures for impressions/clicks/conversions, advertiser hierarchy denormalized. |
| [16](design/16_practice_ecommerce.md) | Practice: E-commerce Platform | The 5-table star; one row per order line item. |
| [17](design/17_practice_ride_sharing.md) | Practice: Ride-sharing Platform | Two fact tables (trips + cancellations), surge as a measure. |
| [18](design/18_practice_social_media.md) | Practice: Social Media Analytics | Event-grain fact, author + actor as two user keys, factless fact. |
| [19](design/19_practice_cloud_services.md) | Practice: Cloud Services Platform | Multi-fact (usage + billing), cost pre-computed at load, IAM as a separate schema. |
| [20](design/20_practice_video_streaming.md) | Practice: Video Streaming Service | Watch-session events, content/creator hierarchy, recommender dim. |

---

## How the code is organized

```
03_high_level_diagrams/
├── code/
│   ├── star_schemas.py    # 7 build_*_schema(q) functions
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

This builds all 7 schemas in `:memory:` SQLite and prints the
sample fact row from each.

---

## The 7 schemas at a glance

| # | Schema | Fact table | Grain | # dims | # facts |
|---|---|---|---|---|---|
| 1 | E-commerce | `fact_order_items` | one row per order line item | 4 | 1 |
| 2 | Ride-sharing | `fact_trips` | one row per completed trip | 5 | 2 |
| 3 | Social media (Instagram-style) | `fact_post_events` | one row per post event | 4 | 1 |
| 4 | Customer support (legacy) | `fact_ticket_events` | one row per ticket event | 5 | 1 |
| 5 | Video streaming (Spotify-style) | `fact_streams` | one row per stream | 6 | 1 |
| 6 | Cloud services | `fact_usage` | one row per usage event | 5 | 1 |
| 7 | Online advertising | `fact_ad_events` | one row per ad event | 5 | 1 |

The first six schemas are the practice lessons in the current
spec. The seventh (customer support) is a legacy schema kept in
the working code for the test suite — the support prompt is
covered in the mock-interviews module.

By the end of this module you should be able to draw each
practice schema from memory in under 15 minutes.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
