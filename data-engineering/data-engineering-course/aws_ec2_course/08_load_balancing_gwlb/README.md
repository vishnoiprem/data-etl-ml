# Section 8 — Gateway Load Balancer + Course Wrap-up

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 08 of 08
> **Lectures:** L36 – L38 (3 lectures, ~34 minutes total)
> **Working artifact:** `code/gwlb_create/gwlb_create.py` + 3 pytest tests

This is the **last section** of the AWS EC2 + Load Balancing Crash
Course. We finish the three load-balancer types with the
**Gateway Load Balancer (GWLB)** — the Layer-3 transparent
appliance-insertion service — and then close out the course with
a section-by-section recap and a roadmap of where to go next.

---

## Lecture map

| L# | Title | Minutes | File |
|---|---|---|---|
| L36 | Gateway Load Balancer (GWLB) Theory | 12:00 | [`lecture_scripts/L36_gwlb_theory.md`](lecture_scripts/L36_gwlb_theory.md) |
| L37 | GWLB Hands-On + `gwlb_create.py` + tests | 12:00 | [`lecture_scripts/L37_gwlb_hands_on.md`](lecture_scripts/L37_gwlb_hands_on.md) |
| L38 | Course Wrap-Up + Final Quiz | 10:00 | [`lecture_scripts/L38_course_wrapup.md`](lecture_scripts/L38_course_wrapup.md) |

**Section total: 34 minutes of lecture.**

---

## Code artifact

| File | Purpose | Tests |
|---|---|---|
| [`code/gwlb_create/gwlb_create.py`](code/gwlb_create/gwlb_create.py) | boto3 function that creates a GWLB + GENEVE target group + listener. | [`code/gwlb_create/test_gwlb_create.py`](code/gwlb_create/test_gwlb_create.py) |
| [`code/gwlb_create/README.md`](code/gwlb_create/README.md) | The appliance-vendor pattern + how to run the script. | – |

### What `gwlb_create.py` does

A single function, `create_gwlb(name, subnet_ids, vpc_id, ...)`, that
performs three API calls in order:

1. `create_target_group(Protocol='GENEVE', Port=6081, HealthCheckProtocol='HTTP', HealthCheckPath='/health', ...)`.
2. `create_load_balancer(Type='gateway', Subnets=<2 subnets in 2 AZs>, ...)`.
3. `create_listener(DefaultActions=[{'Type':'forward', 'TargetGroupArn':<TG>}])`.

The listener `Protocol` and `Port` are intentionally **omitted** —
real AWS pins a GWLB listener to GENEVE/6081 and rejects any
override. The script reflects that.

### What the tests assert

| Test | Asserts |
|---|---|
| `test_gwlb_type_is_gateway` | The load balancer's `Type == 'gateway'` and that it is deployed in exactly the two subnets we passed in. |
| `test_target_group_protocol_geneve` | The target group uses `Protocol='GENEVE'`, `Port=6081`, `HealthCheckProtocol='HTTP'`, `HealthCheckPath='/health'`, and lives in the right VPC. |
| `test_listener_forwards_to_target_group` | The listener has exactly one default action of type `forward` that points at the target group ARN. |

### Run the tests

From the `code/gwlb_create/` directory:

```bash
python -m pytest test_gwlb_create.py -v
```

You should see:

```
test_gwlb_create.py::test_gwlb_type_is_gateway              PASSED
test_gwlb_create.py::test_target_group_protocol_geneve      PASSED
test_gwlb_create.py::test_listener_forwards_to_target_group PASSED
3 passed
```

The tests run under `moto.mock_aws` and need no real AWS
credentials. Total runtime is ~2-3 seconds.

---

## How to read this section

1. **Watch L36 first.** It is pure theory — no terminal, no console.
   The mental model you need for the hands-on is:
   - GWLB is **Layer 3, transparent, inline**.
   - The protocol is **GENEVE on UDP 6081**.
   - The deployment pattern is a **service VPC with a VPC endpoint
     service** that consumers connect to via PrivateLink.
   - The actual firewall / IDS / NAT logic lives in a **third-party
     virtual appliance** from AWS Marketplace (Palo Alto, Fortinet,
     Check Point, etc.).

2. **Then watch L37.** It walks through `gwlb_create.py` line by
   line and runs the three tests live. The boto3 calls are simpler
   than ALB or NLB because the GWLB listener is fully implicit
   (GENEVE/6081).

3. **Finish with L38.** The course wrap-up. It recaps all 8
   sections in 10 minutes, lists the 6 (actually 7) working code
   samples, and points you at the natural next cert
   (**SAA-C03 → ANS-C01** if you liked Section 8, or
   **SAA-C03 → SOA-C02** if you liked the EC2-management
   sections).

4. **Take the final quiz** at
   [`../../quizzes/section_8.md`](../../quizzes/section_8.md). The
   quiz is **cumulative** (covers sections 1-8) and the pass bar
   is `7 / 10`.

---

## Key takeaways

- GWLB is the **third AWS load balancer type**, after ALB and NLB.
- GWLB is **transparent** at L3 — the customer source and
  destination IPs are preserved.
- The protocol is **GENEVE on UDP 6081**.
- GWLB is always deployed across **two subnets in two AZs**.
- Production consumption is via a **VPC endpoint service
  (PrivateLink)** — the consumer VPC never peers with the service
  VPC.
- The "smart" of the GWLB is not the load balancer itself — it's
  the third-party **appliance** that runs in the target group.