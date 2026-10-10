# Assignment 1 — Build a Highly Available Web App

> **Optional extension exercise.** Combines everything in sections 3–8.

## Goal

Stand up a 2-AZ web application with an internet-facing ALB, an internal
NLB for an internal microservice, and a Gateway Load Balancer fronting
a third-party firewall appliance — all driven by boto3 and
CloudFormation.

## Steps

1. Create a VPC with two public and two private subnets spanning
   two AZs (use the AWS console or CloudFormation).
2. Launch two EC2 instances in the private subnets (one per AZ)
   running a simple HTTP server (Python `http.server` is fine).
3. Create an **internet-facing ALB** in the public subnets and register
   both instances in a target group. Path-based rule: `/api/*` →
   instances, default → fixed 404 page.
4. Create an **internal NLB** between the ALB and a downstream internal
   microservice. Register one EC2 instance per AZ.
5. Create a **Gateway Load Balancer** in front of a third-party
   firewall appliance (you can use a t3.micro with `iptables` as a
   stand-in).
6. Verify end-to-end with `curl` from a bastion host.

## Deliverable

A GitHub PR that adds:
- `cloudformation/ha_webapp.yaml` (or CDK equivalent)
- A `Makefile` or `bootstrap.sh` that runs `aws cloudformation deploy`
- A `tests/test_ha_webapp.py` that uses moto to assert the stack
  builds and the listeners route correctly
- A short `NOTES.md` with one architecture decision you made and why

## Bonus

- Add an HTTPS listener with a self-signed cert and SNI.
- Add a CloudWatch alarm that pages you when a target becomes
  unhealthy for more than 2 minutes.
