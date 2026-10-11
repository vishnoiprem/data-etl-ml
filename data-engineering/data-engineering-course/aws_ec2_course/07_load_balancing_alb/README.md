# Section 7 — Application Load Balancer (ALB)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Lectures:** L31–L35
> **Working artifact:** `code/alb_create/alb_create.py` + 4 moto tests
> **Quiz:** `quizzes/section_7.md` (pass bar **7 / 10**)

This section takes you from "what is an ALB?" all the way to a working
boto3 script that creates a real Application Load Balancer, attaches
two routing rules to it, and proves it works using `moto` mocks — no
AWS account required.

## Lecture map

| L#  | Title                                                 | Min | File                                                                       |
| --- | ----------------------------------------------------- | --- | -------------------------------------------------------------------------- |
| L31 | ALB Theory + Internet-Facing vs Internal              | 12  | `lecture_scripts/L31_alb_theory.md`                                        |
| L32 | ALB Hands-On: Create the Load Balancer                | 10  | `lecture_scripts/L32_alb_create.md`                                        |
| L33 | ALB Rules (host- and path-based)                      | 12  | `lecture_scripts/L33_alb_rules.md`                                         |
| L34 | Cross-Zone Load Balancing                             |  8  | `lecture_scripts/L34_cross_zone.md`                                        |
| L35 | ALB Failure Simulation + `alb_create.py` + tests      | 12  | `lecture_scripts/L35_alb_failure_sim.md`                                   |

**Section total:** 54 min of video-equivalent reading, 1 working boto3
script, 4 moto-backed pytest tests, 1 quiz.

## How to read this section

1. **Read L31 first.** It anchors the vocabulary (Layer 7, content-based
   routing, target group, listener, rule, internet-facing, internal) and
   the mental model that the rest of the section assumes you have.
2. **L32 is the lab walkthrough.** Open the AWS console alongside it
   and click through the 4-step creation flow. You do not need to
   spend a cent — every step has a `moto` equivalent in
   `alb_create.py`.
3. **L33 is where ALB earns its keep.** Rules let you host several
   services behind a single DNS name, switch traffic by URL prefix or
   hostname, and even redirect or return fixed responses. This is the
   one lecture to re-read if you remember nothing else.
4. **L34 is short but important.** Cross-zone load balancing behaves
   differently between ALB and NLB, and it surprises people in
   production. Five minutes here will save you a 2 a.m. page later.
5. **L35 is the recap + the demo.** Walk through `alb_create.py` line
   by line, then read the failure-simulation section to see how
   health checks surface unhealthy targets.

## Working code

```
code/alb_create/
├── README.md              ← how the demo maps to the lectures
├── alb_create.py          ← boto3 script (create_alb_and_rules)
└── test_alb_create.py     ← 4 moto-backed pytest tests
```

Run the tests locally (no AWS account needed):

```bash
cd 07_load_balancing_alb/code/alb_create
python -m pytest -v
```

Expected: **4 passed** in under 2 seconds.

## What you will be able to do after this section

- Explain the difference between an NLB (L4) and an ALB (L7) and pick
  the right one for a given workload.
- Create an ALB, target group, listener, and rules by hand in the AWS
  console.
- Read and modify a boto3 script that provisions an ALB end-to-end
  using the `elbv2` client.
- Diagnose a "502 Bad Gateway" coming back from an ALB and trace it
  back to an unhealthy target in the right target group.
- Decide whether cross-zone load balancing helps or hurts your
  deployment and configure it accordingly.

## Connections to other sections

- **Section 6 (L27–L30)** is the prerequisite: it introduces load
  balancers, target groups, health checks, and the NLB. ALB shares
  all of those concepts and adds Layer 7 routing on top.
- **Section 8 (L36–L38)** covers the third AWS load balancer — the
  Gateway Load Balancer (GWLB) — which is a Layer 3 appliance
  load balancer used for third-party firewalls and intrusion
  detection.
