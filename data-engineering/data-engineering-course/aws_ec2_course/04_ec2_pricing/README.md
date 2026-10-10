# Section 4 — EC2 Pricing (L19–L22)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 04
> **Lectures:** L19–L22
> **Working artifact:** `code/pricing_calc.py` (pure-Python, no boto3)
> **Quiz:** `../../quizzes/section_4.md` (10 questions, pass bar 7/10)

This section is a focused deep dive into the **five EC2 pricing models** that AWS exposes for compute. By the end of L22 you should be able to look at a workload profile and pick the right pricing model in under a minute, and back that choice up with numbers from `pricing_calc.py`.

## Lecture map

| L# | Title | File | Duration |
|---|---|---|---|
| L19 | EC2 Pricing Models Overview | `lecture_scripts/L19_pricing_models.md` | 10:00 |
| L20 | On-Demand, Reserved, Savings Plans | `lecture_scripts/L20_on_demand_reserved_sp.md` | 12:00 |
| L21 | Spot Instances | `lecture_scripts/L21_spot_instances.md` | 10:00 |
| L22 | Recap + `pricing_calc.py` walkthrough | `lecture_scripts/L22_section_recap.md` | 8:00 |

## How to read this section

If you have **10 minutes**, read L19 — it gives you the mental model of all five models side by side.

If you have **30 minutes**, read L19 → L20 → L21. By the end of L21 you should know what each model is good for and what its trade-offs are.

If you have **40 minutes**, also do L22 and run `code/pricing_calc.py` against the same instance type you would launch for a real workload. The exercise is the point: the math is simple, the judgment is not.

## Working artifact

`code/pricing_calc.py` is a stdlib-only Python module that estimates monthly cost for a given instance type under each pricing model. It is intentionally not a wrapper around the AWS Pricing API — the goal is to *illustrate* the discount structure, not to hit a live endpoint. See `code/README.md` for instructions on extending it to use the real `pricing` API via boto3.

## Quiz

After L22, take `../../quizzes/section_4.md`. The pass bar is **7 out of 10**. If you miss more than three, re-read L19 and re-run `pricing_calc.py` — the questions are designed to be answerable directly from the calculator output.
