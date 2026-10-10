# L06 — Regions and Availability Zones

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 02
> **Duration target:** 12:00
> **Lecture ID:** L06

## Status

Authored.

## Prereqs

- L04 (VMs and hypervisors).
- L05 (EC2 is IaaS — you choose a region, you choose an AZ).

## Key terms

- **Region** — a geographic area where AWS clusters data centers.
  Each region is a separate, isolated geographic market: `us-east-1`
  (N. Virginia), `us-west-2` (Oregon), `eu-west-1` (Ireland),
  `ap-southeast-2` (Sydney), and so on. As of October 2026, AWS
  has 30+ regions.
- **Availability Zone (AZ)** — one or more discrete data centers
  within a region, each with independent power, cooling, and
  networking. A region contains 2–6 AZs (most have 3).
- **AZ name** — the human-readable label like `us-east-1a`. This is
  the *map label*, the conventional name.
- **AZ ID** — the per-account randomized identifier like `use1-az1`,
  `use1-az2`. This is the *physical* identifier. Different AWS
  accounts can map the same `us-east-1a` to different AZ IDs —
  AWS does this on purpose to distribute load and reduce the blast
  radius of any one account's actions.
- **Local Zone** — a smaller AWS extension placed in a metro area
  near a region, for low-latency workloads. Tagged with a different
  code (e.g., `us-west-2-lax-1a`).
- **Wavelength** — AWS infrastructure embedded inside a
  telecommunications provider's 5G network, for ultra-low-latency
  edge compute. Mentioned for completeness; you will not use it in
  this course.
- **Data residency / sovereignty** — the requirement (legal or
  contractual) that data stays within a specific geographic
  boundary. Region choice is the primary tool you have to satisfy
  this requirement.

## Lecture

AWS does not run one giant cloud. AWS runs **a federation of
isolated geographic regions**, and every AWS resource you create
lives in exactly one of them. When you launch an EC2 instance, you
do not just pick an instance type — you also pick a region, and
within that region you pick a subnet, and that subnet lives in one
Availability Zone. Two of the three knobs (region and AZ) are
geographic decisions, and they have consequences for latency,
cost, compliance, and availability. Get them wrong and you either
break a compliance regime, or pay too much, or both.

A **region** is a geographic area. `us-east-1` is N. Virginia,
`us-west-2` is Oregon, `eu-west-1` is Ireland, `ap-southeast-2` is
Sydney, `me-south-1` is Bahrain. Each region is fully independent:
it has its own APIs (well, shared APIs but isolated data planes),
its own pricing, its own set of services (not every service is in
every region, and new services usually roll out to a subset of
regions first), and — critically — **its own blast radius**. A
catastrophic outage in `us-east-1` does not take down `us-west-2`
or `eu-west-1`. That isolation is the entire point of having
multiple regions.

A region is made up of **Availability Zones**. An AZ is one or
more discrete data centers, each with independent power, cooling,
and network connectivity. Most regions have 3 AZs; some have 2, a
few have 6. AZs within a region are connected to each other with
low-latency, high-bandwidth, private fiber — typically under 2 ms
of round-trip time between any two AZs in the same region. That
private fiber is what makes "multi-AZ" deployments work: you can
have a primary database in `us-east-1a` and a synchronous standby
in `us-east-1b` and the replication happens over a link that AWS
operates and that you do not pay bandwidth charges for, in either
direction, within a region.

The names of AZs are where students get tripped up, so pay
attention.

The **AZ name** is the human-readable label. You will see
`us-east-1a`, `us-east-1b`, `us-east-1c` in the console. This is
the *map* name. It is a convenient fiction.

The **AZ ID** is the per-account, randomized, physical identifier
that AWS actually uses internally. It looks like `use1-az1`,
`use1-az2`, `use1-az4`. Different AWS accounts see **different
mappings** from AZ name to AZ ID. Your `us-east-1a` might be
`use1-az1` in your account but `use1-az4` in my account. Same
name, different physical data center.

Why does AWS do this? Two reasons. First, **load distribution**: if
everyone's `us-east-1a` pointed to the same physical data center,
that one data center would be overwhelmed by the predictable
"click here first" behavior of users new to AWS. Second, **blast
radius reduction**: if a single physical data center has a problem,
fewer accounts are affected, because accounts are spread across AZs
even when they all typed "a".

The practical consequence for you is that **AZ names are not
portable across accounts**. If you write CloudFormation or
Terraform that says "deploy to `us-east-1a`," and you share it
with a colleague, it might land in a different physical location
for them. This is usually fine — same region, same private
backbone, same SLA — but it bites you when you assume AZ names
uniquely identify a data center.

When do you pick a region? The decision is a function of four
factors, in roughly this order of importance:

1. **Compliance / data residency.** If you have a legal requirement
   to keep data inside the EU, you must use an EU region
   (Frankfurt, Ireland, Paris, Stockholm, Milan, Spain, Zurich, or
   the dedicated `eu-central-2` / `eu-south-1` / `eu-south-2`).
   This is a hard constraint.
2. **Latency to your users.** Pick the region closest to where
   your traffic comes from. East-coast US users → `us-east-1` or
   `us-east-2`. London users → `eu-west-2` (London) or `eu-west-1`
   (Ireland). Tokyo users → `ap-northeast-1` (Tokyo).
3. **Service availability.** Newer services and features land in
   `us-east-1` first, and in N. Virginia / Ohio / Oregon before
   they reach Asia-Pacific or South America. If you need a
   brand-new service, you may be forced into a specific region.
4. **Cost.** Pricing varies by region. `us-east-1` is typically
   the cheapest; smaller or newer regions can be 20–50% more
   expensive.

And then, within a region, you pick AZs. The standard pattern for
high availability is to spread your workload across at least two
AZs (ideally three) so that the loss of one data center does not
take down the service. The tradeoff is complexity: multi-AZ means
more subnets, more routing, more replication, and more places for
things to go wrong. For non-critical workloads — a dev environment,
a personal blog — single-AZ is fine.

## Hands-on

Theory lecture, but do these two things in parallel:

1. Look at the **region selector in the top-right of the AWS
   console**. Click through three regions and notice that EC2
   shows different instance counts, different AZs, and
   potentially different services. The data is not shared across
   regions.
2. From your laptop, with AWS credentials configured, run:
   ```bash
   aws ec2 describe-availability-zones \
       --region us-east-1 \
       --output table
   ```
   You will see both the AZ name (`us-east-1a`) and the AZ ID
   (`use1-az1` or similar) for each zone. The mapping you see is
   specific to *your* account.

In the L08 recap we'll run the boto3 version of this and print a
small table.

## Quiz prep

- Define region and Availability Zone. How are they different?
- Why does AWS randomize AZ IDs per account? Give two reasons.
- Given a scenario ("EU users, GDPR-regulated data, low budget,
  need a managed database"), which region would you pick and why?
- If you deploy an EC2 instance into `us-east-1a`, and a colleague
  in another account deploys into their `us-east-1a`, are you in
  the same physical data center? How can you tell?
- What is the typical inter-AZ latency within a region? Why does
  it matter for multi-AZ designs?

## Further reading

- AWS: [Regions and Availability Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- AWS: [AWS Global Infrastructure](https://aws.amazon.com/about-aws/global-infrastructure/regions/)
- AWS: [AZ IDs and account-specific mapping](https://docs.aws.amazon.com/ram/latest/userguide/working-with-az-ids.html)