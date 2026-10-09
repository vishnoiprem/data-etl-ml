# Module 03 — Technical Questions for SAs

> **7 lessons · ~6 hours of reading + 2-3 hours of practice**

> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <prem.vishnoi@example.com>

The technical layer under the customer-interaction work.
Module 02 was about the *customer*; this module is about
the *solution*. The two are intertwined — a senior SA
designs for the customer, not for the architecture.

This module covers:
- **Cloud fundamentals** (Lesson 02) — AWS, GCP, Azure
  comparison.
- **API design** (Lesson 03) — the REST API for a snack
  distributor (a real-world case).
- **Database schema design** (Lesson 04) — the pizza
  ordering system schema (a Domino's-style case).
- **Architecture design** (Lesson 05) — the self-serve
  insurance product architecture.
- **Tradeoff frameworks** (Lesson 06) — latency vs cost
  vs consistency, the "it depends" answer.
- **The 30-second decision tree** (Lesson 07) — when to use
  what service.

For system design depth (URL shortener, Twitter, Uber
Eats, etc.), see the cross-link in Module 04 — the
`../system_design/` track has 71 lessons covering every
common system design problem.

---

## Lessons

| # | Lesson | What you'll get out of it |
|---|---|---|
| [01](design/01_intro_to_technical_sa_questions.md) | Intro to Technical SA Questions | The 4 question types, the rubric, what "passing" looks like. |
| [02](design/02_cloud_fundamentals_for_sa.md) | Cloud Fundamentals for SAs | AWS/GCP/Azure comparison, the 6 service categories every SA must know. |
| [03](design/03_rest_apis_snack_distributor.md) | REST API for a Snack Distributor | Real-world API design: resource model, endpoints, errors, auth. |
| [04](design/04_pizza_ordering_db_schema.md) | Pizza Ordering DB Schema | Real-world schema: ER diagram, table definitions, indexes, partitioning. |
| [05](design/05_self_serve_insurance_architecture.md) | Self-Serve Insurance Architecture | Real-world architecture: full system, mermaid diagram, key service choices, DR. |
| [06](design/06_tradeoff_frameworks.md) | Tradeoff Frameworks: Latency vs Cost vs Consistency | The 3-axis tradeoff, the "it depends" answer. |
| [07](design/07_thirty_second_architecture_decision.md) | When to Use What: The 30-Second Architecture Decision | Real decision tree (mermaid) for common service choices. |

---

## How to read this module

1. **Lesson 01 (~10 min).** Sets the scope: what the
   technical SA round tests.
2. **Lesson 02 (~30 min).** The 6 service categories. This
   is *reference* material; come back to it as needed.
3. **Lessons 03-05 (~3 hours total).** Three worked case
   studies (API, DB, architecture). Read once, then re-read
   for the *patterns*.
4. **Lesson 06 (~30 min).** The tradeoff framework.
   Internalize the 3-axis model.
5. **Lesson 07 (~30 min).** The decision tree. Use it as a
   reference; the value is in the *structure*, not the
   memorized answers.
6. **End-of-track exercise:** the architecture write-up in
   `exercise.md`. By the time you finish this module, you
   should be able to design a defensible architecture for
   a 2-3 paragraph scenario in 30 minutes.

---

## What "passing" this module looks like

By the end of Module 03, you should be able to:

- Compare AWS, GCP, and Azure on the 6 core service
  categories.
- Design a REST API for a 2-3 paragraph scenario,
  with resource model, endpoints, error model, auth,
  and pagination.
- Design a database schema for a 2-3 paragraph
  scenario, with ER diagram, table definitions,
  indexes, and partitioning strategy.
- Design an architecture for a 2-3 paragraph scenario,
  with mermaid diagram, key service choices, data flow,
  security model, and DR.
- Articulate the latency-vs-cost-vs-consistency tradeoff
  on any service choice.
- Make a 30-second architecture decision (use X because
  of Y constraint) for common scenarios.

If you can do all 6, the technical SA round is in the
bag.
