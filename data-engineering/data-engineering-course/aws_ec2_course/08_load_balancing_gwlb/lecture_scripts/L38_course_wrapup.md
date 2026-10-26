# L38 — Course Wrap-Up + Final Quiz

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 08
> **Duration target:** 10:00
> **Lecture ID:** L38

## Status

Authored.

## Prereqs

- All previous lectures (L01–L37).

## Key terms

- **Section quiz pass bar** — `7 / 10` for the final quiz in
  `quizzes/section_8.md`.
- **Cert roadmap** — Solutions Architect Associate (SAA-C03),
  SysOps Administrator Associate (SOA-C02), Advanced Networking —
  Specialty (ANS-C01).
- **Hands-on reinforcement** — the 6 working code samples in this
  course (region_az_demo, launch_instance, pricing_calc,
  snapshot_ami_demo, nlb_create, alb_create, gwlb_create) are the
  foundation for the certification labs.

## Lecture

We have reached the end. Let me recap what we covered across the
eight sections of the course, then point you at the natural next
steps.

### Section-by-section recap (L01–L38)

- **Section 1 — Introduction to EC2 (L01–L03).** The 60-second
  pitch, the 38-lecture map, the audience. The mental model: EC2
  gives you a Linux or Windows VM in the AWS cloud, on demand, in
  any region, billed by the second.

- **Section 2 — EC2 Fundamentals (L04–L08).** Virtual machines,
  hypervisors, managed vs. unmanaged services, regions, AZs, and
  instance type families (general purpose, compute optimized,
  memory optimized, storage optimized, accelerated). The
  `region_az_demo.py` artifact is the one you can run anywhere to
  prove you understand which region / AZ you are in.

- **Section 3 — Creating an EC2 instance end-to-end (L09–L18).**
  The wizard walkthrough: AMI, instance type, network, storage,
  user data, key pair, security group. The `launch_instance.py`
  artifact shows the same flow via boto3.

- **Section 4 — EC2 Pricing (L19–L22).** On-Demand, Reserved
  Instances, Savings Plans, Spot. The `pricing_calc.py` artifact
  shows you how to model the bill for a workload across the four
  pricing models.

- **Section 5 — Managing EC2 (L23–L26).** Stop, start, resize,
  terminate, EBS snapshots, custom AMIs. The
  `snapshot_ami_demo.py` artifact shows the snapshot → register
  AMI flow.

- **Section 6 — Load Balancing intro + NLB (L27–L30).** What a
  load balancer is, target groups, health checks, then NLB theory
  and `nlb_create.py` hands-on. NLB is L4 (TCP/UDP/TLS), preserves
  the client source IP, supports static IPs and elastic IPs, and
  is the right choice when you need millions of packets per second
  with low latency.

- **Section 7 — Application Load Balancer (L31–L35).** ALB
  theory, ALB create, host- and path-based rules, cross-zone
  load balancing, and the `alb_create.py` hands-on with a
  failure-simulation lab. ALB is L7 (HTTP/HTTPS), supports
  content-based routing, WebSocket, and is the right choice for
  modern web apps and microservice architectures.

- **Section 8 — Gateway Load Balancer + Wrap-up (L36–L38).**
  GWLB theory, `gwlb_create.py` hands-on, and this wrap-up. GWLB
  is L3 (GENEVE/UDP/6081), transparent, and exists to scale
  third-party virtual appliances (firewalls, IDS/IPS, NAT).

### The 6 working code samples

By the end of this course you have six runnable, tested boto3
artifacts. Each one is paired with a pytest suite that uses
`moto.mock_aws` so you can run them offline:

| # | Sample | Tests | Section |
|---|---|---|---|
| 1 | `region_az_demo.py` | – | 2 |
| 2 | `launch_instance.py` | yes | 3 |
| 3 | `pricing_calc.py` | – | 4 |
| 4 | `snapshot_ami_demo.py` | yes | 5 |
| 5 | `nlb_create.py` | yes | 6 |
| 6 | `alb_create.py` | yes | 7 |
| 7 | `gwlb_create.py` | yes | 8 |

(That's actually 7 — `region_az_demo` and `pricing_calc` are
read-only demos and do not have a pytest suite.)

### What to do next

The natural follow-on certifications are:

1. **AWS Certified Solutions Architect — Associate (SAA-C03).**
   This is the most common starting cert. It covers the same
   material we've touched (EC2, load balancing) plus S3, RDS, VPC,
   IAM, CloudFormation, serverless, and basic architecture
   patterns. Expect 60-65 multiple-choice questions in 130 minutes.
   Recommended study time: 4-6 weeks of part-time study after this
   course. Use the Well-Architected Framework whitepaper as your
   primary reference.

2. **AWS Certified SysOps Administrator — Associate (SOA-C02).**
   Heavier on the operations side: CloudWatch metrics and alarms,
   Systems Manager (Parameter Store, Session Manager, Run Command,
   Automation), CloudFormation drift detection, cost-and-usage
   reports, and incident response. Pairs well with this course
   because we've already covered EC2 + load balancing, which is
   the runtime substrate for everything SysOps does.

3. **AWS Certified Advanced Networking — Specialty (ANS-C01).**
   If Section 8 (GWLB + PrivateLink) is the most interesting part
   of the course for you, this is the cert to chase. It covers
   VPC design at scale, transit gateway, Direct Connect, VPN,
   Route 53, PrivateLink, and of course all three load balancer
   types including GWLB. Recommended prereq: SAA first.

4. **AWS Certified Solutions Architect — Professional (SAP-C02).**
   The natural senior step after SAA. Multi-account architectures,
   hybrid networking, cost optimization at scale, security
   governance, and migration strategies. Take this after at least
   6-12 months of production AWS experience.

5. **AWS Certified DevOps Engineer — Professional (DOP-C02).**
   Heavier on CI/CD, CloudFormation/CDK, ECS/EKS, and operational
   observability. Take it after SAA + some hands-on IaC work.

### Hands-on labs to build next

Beyond the cert exams, here are the labs that will round out your
muscle memory:

- Build a **3-tier web app** (ALB → ASG of EC2 → RDS) with
  CloudFormation. Use the `alb_create.py` we wrote here as the
  reference for the ALB block.
- Build a **VPC peering + transit gateway** design with two VPCs
  and an EC2 instance in each, and prove the routing works.
- Build a **GWLB + firewall** in the service-VPC pattern from
  L36 — even a "firewall" that just runs `iptables` is enough to
  prove the GWLB is in the path.
- Build a **CloudWatch dashboard + alarms** for the ALB
  (`HTTPCode_ELB_5XX`, `RequestCount`, `HealthyHostCount`) and
  prove it pages you when a target goes unhealthy.

### The final quiz

The final quiz is in `quizzes/section_8.md`. It is 10 questions,
the pass bar is `7 / 10`, and it is a cumulative quiz — it covers
the whole course (sections 1-8), not just section 8. That is on
purpose: GWLB is the last technical lecture, and the final quiz
makes sure the foundation (EC2, pricing, NLB, ALB) is still solid
in your head.

Good luck.

## Hands-on

L38 has no new code. The hands-on is **taking the final quiz**
(`quizzes/section_8.md`, pass bar `7 / 10`) and, if you want
certification, booking your SAA-C03 exam slot.

## Quiz prep

- Pass bar for the final quiz: `7 / 10`.
- The final quiz is **cumulative** (sections 1-8), not just
  section 8.
- Recommended next cert after this course: **SAA-C03** (Solutions
  Architect Associate).
- The three AWS load balancer types map to the three layers:
  **ALB = L7** (HTTP/HTTPS, content-based routing),
  **NLB = L4** (TCP/UDP/TLS, ultra-low latency, static IP),
  **GWLB = L3** (GENEVE/UDP/6081, transparent appliance insertion).
- The three GWLB-relevant factoids for the quiz: GENEVE on
  **UDP 6081**, **two AZs** required, **VPC endpoint service**
  is the production way to consume.

## Further reading

- AWS — *AWS Certification paths.*
  <https://aws.amazon.com/certification/>
- AWS Well-Architected Framework.
  <https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html>
- AWS — *VPC Endpoint Services (PrivateLink).*
  <https://docs.aws.amazon.com/vpc/latest/privatelink/endpoint-service.html>
- AWS — *Elastic Load Balancing features compared.*
  <https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/load-balancer-types.html>