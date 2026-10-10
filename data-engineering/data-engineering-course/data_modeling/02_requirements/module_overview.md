# Module 02 — Gathering Business Requirements

> **8 lessons · 0 videos · ~3 hours**
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

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
| [05](design/05_introduction_to_requirements_gathering.md) | Introduction to Gathering Business Requirements | Why requirements come first; the cost of skipping them. |
| [06](design/06_recognizing_the_core_business_problem.md) | Recognizing the Core Business Problem | The 5W+H framework and a 50+ discovery-question bank. |
| [07](design/07_analyzing_metrics.md) | Analyzing Metrics | What metrics matter — DAU, MAU, conversion, retention, GMV, LTV. |
| [08](design/08_analyzing_query_patterns.md) | Analyzing Query Patterns | What queries will run, their shapes, their frequencies. |
| [09](design/09_defining_latency_requirements.md) | Defining Latency Requirements | Batch vs near-real-time vs real-time SLAs. |
| [10](design/10_data_volume_and_scalability.md) | Data Volume & Scalability Considerations | Rows/day, rows/year, hot partitions, growth rate. |
| [11](design/11_data_retention_policies.md) | Data Retention Policies & Historical Data Management | 7-year retention, GDPR, cold storage, archival. |
| [12](design/12_example_business_requirements_gathering.md) | Example: Business Requirements Gathering | A single full worked example end-to-end. |

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

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
