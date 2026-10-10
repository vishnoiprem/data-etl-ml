# `gwlb_create` — Gateway Load Balancer (boto3 demo)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 08 — Gateway Load Balancer + Course Wrap-up
> **Lecture:** L37 — GWLB Hands-On
> **Services:** `elbv2` (Gateway Load Balancer API), `ec2` (VPC/subnets)

A small Python module that creates an AWS Gateway Load Balancer end-to-end
with `boto3`:

1. A **GENEVE target group** on UDP port `6081` with HTTP health checks on
   `/health`.
2. A **Gateway Load Balancer** (`Type='gateway'`) deployed across two
   subnets in two different Availability Zones.
3. A **GENEVE listener** that defaults to forwarding every flow to the
   target group.

`gwlb_create.py` exposes a single function, `create_gwlb(...)`, which
returns a `GwlbResult` dataclass holding the three ARNs.

---

## Files

| File | Purpose |
|---|---|
| `gwlb_create.py` | The module — `create_gwlb()` + `GwlbResult`. |
| `test_gwlb_create.py` | Pytest suite using `moto.mock_aws` (3 tests). |

---

## The appliance-vendor pattern

GWLB exists for one reason — to let you run **third-party virtual
appliances** (firewalls, IDS/IPS, NAT, DDoS mitigation, deep-packet
inspection) at scale **transparently** inside your VPC. The pattern
is:

```
   ┌──────────────┐    GENEVE/6081     ┌──────────────────┐
   │  Customer    │  ───────────────▶  │  Gateway Load    │
   │  workload    │                    │  Balancer        │
   │  (EC2)       │  ◀───────────────  │  (transparent   │
   └──────────────┘    return traffic  │   L3 insertion) │
                                       └─────────┬────────┘
                                                 │ GENEVE/6081
                                                 ▼
                                ┌─────────────────────────────┐
                                │  Target group of appliance  │
                                │  instances (e.g. 3rd-party  │
                                │  firewall VMs from the AWS  │
                                │  Marketplace)               │
                                └─────────────────────────────┘
```

The customer traffic is **GENEVE-encapsulated** (UDP/6081) by the GWLB,
delivered to a healthy appliance instance, the appliance inspects /
modifies the inner packet, and then returns it to the GWLB which
de-encapsulates and forwards it on to its real destination. To the
source and destination workloads the appliance is **invisible** — the
source/destination IPs are preserved end-to-end.

This is why GWLB is sometimes called "transparent inline" — unlike ALB
or NLB, the GWLB does not terminate the connection.

---

## Why GENEVE on UDP 6081?

* **GENEVE** (Generic Network Virtualization Encapsulation, RFC 8926)
  is the modern tunneling protocol that replaced VXLAN for AWS
  appliance insertion. It has flexible metadata headers so vendors
  can carry flow IDs, tenant IDs, or policy decisions.
* **UDP 6081** is the IANA-registered port for GENEVE and is the only
  port a GWLB listener accepts.

In real AWS, when you call `CreateListener` on a Gateway Load
Balancer, you cannot override `Protocol` or `Port` — they are fixed
to `GENEVE / 6081`. The script reflects that.

---

## Run the tests

From this directory:

```bash
python -m pytest test_gwlb_create.py -v
```

Expected output:

```
test_gwlb_create.py::test_gwlb_type_is_gateway              PASSED
test_gwlb_create.py::test_target_group_protocol_geneve      PASSED
test_gwlb_create.py::test_listener_forwards_to_target_group PASSED
3 passed
```

The tests use `moto.mock_aws` to stand up an in-memory AWS account,
build a real VPC + two subnets in two AZs, then call `create_gwlb`
and assert on the returned resources.

---

## Run against a real AWS account

```bash
python gwlb_create.py \
    --name demo-gwlb \
    --vpc-id vpc-0123456789abcdef0 \
    --subnet-a subnet-aaa \
    --subnet-b subnet-bbb \
    --region us-east-1
```

The script prints a dict with `LoadBalancerArn`, `TargetGroupArn`, and
`ListenerArn`. Clean up afterwards with:

```bash
aws elbv2 delete-load-balancer --load-balancer-arn <LB_ARN>
aws elbv2 delete-target-group     --target-group-arn  <TG_ARN>
```

(Note: deleting the LB also deletes its listener.)

---

## What's intentionally **not** in the demo

* **Registering appliances** — you'd typically use the AWS Marketplace
  to subscribe to a vendor (Palo Alto, Fortinet, Check Point, etc.) and
  then `RegisterTargets` against the appliance ENIs.
* **VPC endpoint service** — the production way to expose a GWLB to
  other VPCs (or to on-prem via DX / VPN) is to front it with a VPC
  Endpoint Service backed by the GWLB. That deserves its own lecture
  and is covered in **L36 — GWLB Theory**.
* **Flow stickiness** — GWLB uses a 5-tuple hash so all packets of a
  flow land on the same appliance instance. This is automatic and is
  discussed in L36.