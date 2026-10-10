# L20 — On-Demand, Reserved Instances, and Savings Plans

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 04
> **Duration target:** 12:00
> **Lecture ID:** L20

## Status

Authored.

## Prereqs

- L19 (the five-model overview).

## Key terms

- **On-demand** — pay-as-you-go, billed per second after the first minute, no commitment.
- **Standard Reserved Instance** — 1- or 3-year term; tied to a specific family, region, and (optionally) AZ; cheapest RI; capacity reserved in the chosen AZ; cannot be changed once purchased.
- **Convertible Reserved Instance** — same 1- or 3-year term but allows you to change instance family, OS, or tenancy mid-term. Smaller discount (~45% vs ~60% on standard 3y all-upfront).
- **Payment options for RIs** — *no upfront* (smallest discount, monthly bill), *partial upfront* (some on signing, balance on hourly), and *all upfront* (one-time payment, biggest discount).
- **Compute Savings Plan** — 1- or 3-year commitment to a $/hour spend; applies automatically to EC2, Fargate, and Lambda across any region and any family. Discount ~27%.
- **EC2 Instance Savings Plan** — same idea but tied to a specific region + family. Discount ~37%.

## Lecture

This lecture is about the three pricing models you use when you actually know roughly what your workload will do. Spot stays in L21 because its trade-offs are different.

**On-demand, in depth.** When you launch an instance without specifying a pricing plan, it is on-demand. You are billed per second after the first minute (Linux instances; Windows is billed per hour even today). The price varies by region, instance type, and OS. Linux on-demand is the cheapest variant; Windows and RHEL carry a surcharge that is itself priced per-hour. The on-demand rate is what every other model discounts against, so it is the baseline for the rest of this lecture.

A useful mental model: on-demand is "rental car, full insurance, drop it back whenever." No commitment, no early-termination fee, no risk. But you pay for that flexibility. For a `t3.micro` at roughly $0.0104/hour that is about $7.60/month if it runs 24/7. For an `m5.large` at ~$0.096/hour that is ~$70/month. The arithmetic is unfussy; what matters is matching this spend to a model that fits the workload.

**Reserved Instances.** Reserved Instances are the original commitment product, and they still exist for two reasons: (1) the biggest absolute discount of any model, and (2) the *capacity reservation* feature, which is the only way to guarantee an instance can launch into a specific AZ during a surge.

There are two product families:
- *Standard RIs* — can be purchased for a specific instance family in a specific region (region-wide), or for a specific AZ (which also reserves capacity). They are the cheapest. They cannot be modified, but they can be sold in the Reserved Instance Marketplace if you no longer need them.
- *Convertible RIs* — same term, same idea, but you can exchange them for a different family/OS/tenancy partway through. Smaller discount because that flexibility has a price.

Three payment options line up with three discount tiers, in roughly this order:
- **No upfront** — pay nothing on signing; AWS bills you a discounted hourly rate for the term.
- **Partial upfront** — pay a slice on signing; smaller hourly rate for the remainder.
- **All upfront** — pay the whole thing on signing; lowest effective hourly rate (or zero hourly rate).

Two terms: 1-year and 3-year. The 3-year term gets roughly twice the discount of the 1-year term at the same payment option. A `m5.large` running 24/7 in us-east-1 might cost ~$70/month on-demand, ~$42/month on a 1-year no-upfront RI, ~$32/month on a 1-year all-upfront, and ~$28/month on a 3-year all-upfront. Rough numbers; real pricing varies.

The risk: RIs are a sunk cost. If you terminate the instance, the RI stays. You still pay for the term. AWS does not refund the upfront portion if you terminate mid-term (you can sell standard RIs on the marketplace for the unused portion). So RIs are only correct when you are confident the workload will exist for the full term.

**Savings Plans.** Savings Plans were introduced in late 2019 as a more flexible alternative to RIs. You commit to a $/hour spend for a 1- or 3-year term, and AWS applies the discount automatically to any qualifying usage. No specific instance family, no specific AZ, no specific service — just a $/hour number.

Two flavors:
- **Compute Savings Plans** — the most flexible. Discount applies to EC2, Fargate, and Lambda, in any region and any family. About **27% off on-demand** for a 3-year term.
- **EC2 Instance Savings Plans** — tied to a specific region and family. About **37% off on-demand** for a 3-year term.

The discount is applied per-hour to whatever usage falls under the plan. If your actual usage exceeds the commitment, the excess is billed at on-demand. If your actual usage is below the commitment, you still pay the commitment — the unused portion is wasted, just like an RI.

The choice between Savings Plans and RIs is mostly a choice between *flexibility* and *maximum discount*. If you are confident about the family and want the biggest discount, RI is fine. If you want to be able to move workloads between families, or to Fargate, or to other regions, Savings Plans are safer. The Capacity Blocks feature also exists for very specific short-term reservation needs (e.g., a planned event on a known date), but that is not part of this section.

**How to think about it.** Run the workload on-demand for a few weeks, look at the bill, and find the baseline — the floor of usage that is always there, even on weekends and at 3 a.m. That baseline is what you commit to. The peak above the baseline is what stays on on-demand (or on spot, see L21). Most teams should default to a Compute Savings Plan for the baseline and let the rest burn on-demand.

## Hands-on

None. We use `pricing_calc.py` in L22 to compare.

## Quiz prep

- What are the three RI payment options, in increasing discount order?
- What is the main difference between Standard and Convertible RIs?
- What is the rough discount for a 3-year Compute Savings Plan versus on-demand?
- If your usage exceeds your Savings Plan commitment, what happens to the excess?
- Why might you pick a Savings Plan over an RI even though RIs are cheaper per-hour?

## Further reading

- AWS Reserved Instances — https://aws.amazon.com/ec2/pricing/reserved-instances/
- AWS Savings Plans FAQ — https://aws.amazon.com/savingsplans/faq/
- AWS Compute Savings Plans — https://aws.amazon.com/savingsplans/compute/
