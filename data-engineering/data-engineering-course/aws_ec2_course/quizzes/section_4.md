# Section 4 Quiz — EC2 Pricing

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Pass bar:** 7 / 10

Ten multiple-choice questions. Pick exactly one answer per question. The pass bar is 7 correct answers.

---

## Q1

How many EC2 pricing models does AWS expose today?

- A) 3
- B) 4
- C) 5
- D) 6

## Q2

Which EC2 pricing model is the default — i.e., what you get if you launch an instance without specifying a pricing plan?

- A) Reserved Instance
- B) On-demand
- C) Spot
- D) Compute Savings Plan

## Q3

What is the typical interruption warning time for a Spot Instance?

- A) No warning at all
- B) About 30 seconds
- C) About 2 minutes
- D) About 15 minutes

## Q4

Which pricing model gives the largest discount in exchange for a 3-year term commitment?

- A) On-demand
- B) Reserved Instance (3-year, all upfront)
- C) Compute Savings Plan (3-year)
- D) Spot

## Q5

A workload runs 24/7 for the next 18 months on a known instance family in one region. Which pricing model is the strongest fit for the *baseline* of that workload?

- A) Spot
- B) On-demand
- C) Compute Savings Plan (3-year)
- D) Dedicated Host

## Q6

Which of the following is the standard Reserved Instance payment option that gives the **smallest** discount?

- A) All upfront
- B) Partial upfront
- C) No upfront
- D) Convertible upfront

## Q7

A team is running a stateless web API tier behind an Application Load Balancer. The API is fault-tolerant and can tolerate a brief drop in capacity. Which pricing model is the most cost-effective *additional* layer beyond an on-demand baseline?

- A) Dedicated Host
- B) Spot
- C) Reserved Instance, 1-year no upfront
- D) On-demand at higher utilization

## Q8

In `pricing_calc.py`, if you call `spot("t3.micro", 730)` without a `spot_price` argument, what does it use as the hourly rate?

- A) The full on-demand rate ($0.0104)
- B) 30% of the on-demand rate
- C) 70% of the on-demand rate
- D) It raises an error because `spot_price` is required

## Q9

`compute_savings_plan_apply_to_which_service` — Compute Savings Plans can apply to all of the following EXCEPT:

- A) Amazon EC2
- B) AWS Fargate
- C) AWS Lambda
- D) Amazon S3 PUT requests

## Q10

A pricing calculator returns $30.00 for an on-demand workload and $9.00 for the same workload under Spot. What is the effective Spot discount versus on-demand?

- A) 9%
- B) 30%
- C) 70%
- D) 90%

---

## Answer key

> For instructor / self-grading use. Keep this section collapsed or move it to a separate file when distributing to students.

1. **C** — five models: on-demand, reserved, savings plans, spot, dedicated hosts.
2. **B** — on-demand is the default.
3. **C** — about 2 minutes (the interruption notice).
4. **B** — Standard RI 3y all-upfront gives the deepest discount (~60%). Spot is bigger but is interruptible, not the same kind of commitment.
5. **C** — known family, 24/7, multi-year baseline: a Savings Plan is the textbook fit.
6. **C** — no upfront has the smallest discount; all upfront has the largest.
7. **B** — stateless + behind an ALB is the canonical Spot use case.
8. **B** — 30% of on-demand (i.e., a 70% discount) when `spot_price` is not passed.
9. **D** — S3 PUT requests are billed under S3 pricing, not Savings Plans.
10. **C** — `(30 - 9) / 30 = 0.70`, i.e., 70%.
