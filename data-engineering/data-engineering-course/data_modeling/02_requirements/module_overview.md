# Module 02 — Gathering Business Requirements

> **8 lessons · 0 videos · ~3 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

The data modeling interview is, at its core, a requirements-gathering
exercise disguised as a schema-design exercise. The candidate who
gathers the requirements well draws a better schema in half the time.
The candidate who skips requirements draws a wrong schema and spends
the rest of the round being corrected.

This module teaches you how to gather requirements. You'll build a
`RequirementsDoc` helper, learn a bank of 50+ discovery questions,
and walk through three end-to-end examples (e-commerce, ride-sharing,
subscription).

---

## What this module covers

| # | Lesson | What you'll learn |
|---|---|---|
| [05](design/05_why_requirements_first.md) | Why Business Requirements Come First | The cost of skipping requirements, in concrete time and points. |
| [06](design/06_discovery_questions.md) | Discovery Questions: 5W+H | A bank of 50+ questions, grouped by category. |
| [07](design/07_sample_ecommerce.md) | Sample: E-Commerce SaaS | A worked discovery session for an e-commerce warehouse. |
| [08](design/08_sample_rideshare.md) | Sample: Ride-Sharing | A worked discovery session for a ride-sharing warehouse. |
| [09](design/09_sample_subscription.md) | Sample: Subscription Product | A worked discovery session for a SaaS subscription. |
| [10](design/10_requirements_to_entities.md) | Translating Requirements to Entities | How to go from "MAU per month" to "fact_user_activity + dim_users + dim_date." |
| [11](design/11_requirements_doc_template.md) | The Requirements Document Template | The `RequirementsDoc` helper, line by line. |
| [12](design/12_ambiguous_requirements.md) | When Requirements Are Ambiguous | The single most useful skill: making a defensible assumption, out loud. |

---

## How the code is organized

```
02_requirements/
├── code/
│   ├── requirements_doc.py    # the RequirementsDoc helper
│   └── discovery_questions.py # 50+ question bank
└── tests/
    └── test_requirements.py
```

Run the tests:

```bash
python3 -m unittest data_modeling/02_requirements/tests/test_requirements.py
```

The tests pin down the API of the helper so you can build it into
your own interview-prep workflow (rendering docs, picking random
discovery questions for practice, etc.).

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
