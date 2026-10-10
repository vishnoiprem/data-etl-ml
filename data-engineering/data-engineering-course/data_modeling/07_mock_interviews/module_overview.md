# Module 07 — Mock Interviews and Practice

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

## Why this module

This module is the *practical exam* for the data
modeling track. The previous six modules taught the
mechanics — grain, dimensions, conformed dimensions,
role-playing dimensions, SCD 2, fact-table types. This
module is where you *apply* those mechanics under
interview conditions. Six full mock interviews, one
per canonical data-warehouse scenario, each one
narrated start to finish the way a senior candidate
would whiteboard it. The goal is to internalize how a
strong candidate *thinks out loud* — not what they
draw, but what they say while they draw. If you can
rehearse three or four of the phrases from each
transcript out loud, you'll be ahead of 80% of
candidates.

The six scenarios — ride-sharing, customer support,
Airbnb, Stripe, Instagram, Amazon — were chosen
deliberately to span the most common system-design
interview topics: a stateful event stream
(ride-sharing, support), a two-sided marketplace
(Airbnb), a payments ledger (Stripe), engagement
at internet scale (Instagram), and a multi-fact
fulfillment lifecycle (Amazon). Together they
exercise every modeling pattern from the first six
modules.

---

## Lessons

| # | Title | What it is |
|---|---|---|
| [31](design/31_ride_sharing_mock.md) | Design a Data Warehouse Schema for a Ride-Sharing Service | Full 30-min transcript, narrated. |
| [32](design/32_customer_support_mock.md) | Design a Data Warehouse Schema for Customer Support | Full 30-min transcript, narrated. |
| [33](design/33_airbnb_mock.md) | Design a Data Warehouse Schema for Airbnb | Full 30-min transcript, narrated. |
| [34](design/34_stripe_mock.md) | Design a Data Warehouse Schema for Stripe | Full 30-min transcript, narrated. |
| [35](design/35_instagram_mock.md) | Design a Data Warehouse Schema for Instagram | Full 30-min transcript, narrated. |
| [36](design/36_amazon_mock.md) | Design a Data Warehouse Schema for Amazon | Full 30-min transcript, narrated. |

---

## Code

All six mock interviews have full working
implementations in
[`code/solutions.py`](code/solutions.py). The tests
in [`tests/test_solutions.py`](tests/test_solutions.py)
assert the invariants of each solution — the grain
of each fact, the SCD 2 versioning, the aggregations
the analyst would actually run.

To run:

```bash
python3 -m unittest data_modeling/07_mock_interviews/tests/test_solutions.py
```

---

## How to use this module

1. **Read the rubric in Module 01 first.** The mock
   interview scoring is built on the 4-bucket rubric.
2. **For each mock interview**, read the prompt in
   the lesson header, set a 30-minute timer, draw the
   diagram on paper, and narrate out loud. *Then*
   read the transcript.
3. **Run the tests.** If you wrote a solution that
   the tests pass, you have a correct answer.

---

## What "narrate" means

The whiteboard round is *spoken*. The interviewer is
grading your *reasoning*, not your handwriting. The
mock interviews show what narration sounds like:

- "Before I draw anything, I want to clarify the
  use case. Are we reporting on engagement,
  retention, or revenue?"
- "I'm picking the trip as the grain because it's
  the smallest unit that still has the measures
  the analyst needs."
- "I'm using SCD 2 on `dim_driver` because the
  driver-vehicle-city combination changes and we
  want to attribute Q1 trips to the driver's Q1
  vehicle, not today's."
- "Money is `BIGINT` minor units, never float —
  float accumulates rounding errors that show up
  in finance audits."
- "The state machine lives in the event fact, not
  the dim. The dim holds the *current* status, the
  fact holds the *trail* of status transitions."

If you can rehearse three or four of those phrases
per mock, you'll be ahead of 80% of candidates.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
