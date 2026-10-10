# Section 6 — Load Balancing Intro + NLB (L27–L30)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Format:** 4 lectures, 1 working boto3 + moto demo (`nlb_create.py` + 4 tests)
> **Total runtime:** ~44 minutes of lecture + ~10 minutes of hands-on
> **Working artifact:** `code/nlb_create/nlb_create.py` (NLB + target group + listener)
> **Quiz:** `quizzes/section_6.md` — 10 questions, pass bar **7 / 10**

This section opens the load-balancing half of the course. You already
know how to launch, stop, start, snapshot, and rebuild EC2 instances
(Sections 2–5). Now we need a way to put **a stable, named endpoint**
in front of those instances so that:

- Traffic is **spread** across multiple healthy instances (horizontal scale).
- One **failing instance** does not take the website down (health checks).
- The single public IP / DNS that users hit **does not change** when you
  add or replace backend instances.

That "stable endpoint" is the job of a **load balancer**. AWS offers
three flavours, and this section focuses on the simplest and fastest:
the **Network Load Balancer (NLB)**, a Layer-4 (TCP/UDP/TLS) load
balancer.

## Lecture map

| L# | Title | Duration | File |
|---|---|---|---|
| L27 | What is a Load Balancer? | 10:00 | `lecture_scripts/L27_what_is_a_load_balancer.md` |
| L28 | Target Groups and Health Checks | 12:00 | `lecture_scripts/L28_target_groups_health_checks.md` |
| L29 | Network Load Balancer (NLB) | 12:00 | `lecture_scripts/L29_nlb_theory.md` |
| L30 | NLB Hands-On + `nlb_create.py` + tests | 10:00 | `lecture_scripts/L30_nlb_hands_on.md` |

## How to read this section

1. **L27** is the mental model: why a load balancer, single-AZ vs
   multi-AZ, and the two schemes (internet-facing vs internal). If you
   have ever put a CNAME in front of a Heroku app, you already know the
   shape — we just formalize it for AWS.
2. **L28** is the indirection layer. Almost every AWS load balancer
   uses a *target group* to hold the actual EC2 instances, and a *health
   check* to know which ones are still alive. This lecture teaches the
   five health-check knobs you will tune in real life: protocol, path,
   interval, timeout, healthy/unhealthy threshold, and matcher.
3. **L29** is the theory deep-dive on the NLB: Layer 4, static IPs,
   preserve-client-source-IP, ultra-low latency, and the NLB vs ALB
   decision matrix.
4. **L30** is the hands-on lecture. You walk through `nlb_create.py`,
   run the four pytest tests, and — if you have an AWS account — point
   the script at your own VPC.

## Working artifact

`code/nlb_create/nlb_create.py` is a single-file boto3 script that
creates the three resources a real-world NLB needs:

1. A **target group** (TCP/80) that will hold the EC2 instances.
2. An **NLB** itself (Type=`network`, Scheme=`internet-facing`,
   spread across two subnets in two AZs).
3. A **TCP listener** on port 80 that forwards to the target group.

It also calls `register_targets` if you pass a list of instance IDs.
The `main()` function prints the NLB DNS name — that DNS name is the
"stable endpoint" from L27.

```bash
cd 06_load_balancing_nlb/code/nlb_create
python -m pytest test_nlb_create.py -v   # 4 tests, all pass
```

## Connection to later sections

- **L31–L35 (Section 7)** swap the NLB for an ALB and add host-based
  and path-based routing.
- **L36–L37 (Section 8)** introduce the third flavour, the Gateway
  Load Balancer (GWLB), for third-party virtual appliances.

You will reuse the same `target group → listener → load balancer`
trinity for all three. Learning it well in Section 6 means the
remaining load-balancing sections are 90% review.
