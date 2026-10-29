# L19 — EC2 Pricing Models Overview

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 04
> **Duration target:** 10:00
> **Lecture ID:** L19

## Status

Authored.

## Prereqs

- L09–L18 (creating EC2). You should be comfortable launching an instance and knowing roughly what an instance type and region do to the bill.

## Key terms

- **On-demand** — pay per second (minimum 60 s) for compute capacity you use, with no commitment. Highest per-hour cost, zero risk of being interrupted by AWS.
- **Reserved Instance (RI)** — a 1- or 3-year commitment to a specific instance family + region (or region-agnostic) in exchange for a discount of roughly 30–60% versus on-demand. Capacity is reserved for *standard* RIs in a single AZ.
- **Savings Plan (SP)** — a 1- or 3-year commitment to a steady $/hour spend that applies automatically to any matching compute usage. Discounts around 27% for Compute Savings Plans, more for EC2 Instance Savings Plans.
- **Spot Instance** — bid on spare AWS capacity at a market-driven price (often 60–90% off on-demand). AWS can reclaim the instance with a 2-minute warning when it needs the capacity back.
- **Dedicated Host** — a physical server reserved for your use. Required for some compliance scenarios (BYOL licensing, per-socket licensing). Most expensive option, but unique in that you are paying for a *host*, not an instance.

## Lecture

EC2 is one of the oldest AWS services, and over the years AWS has layered five distinct pricing models on top of the same underlying compute primitive. The model you pick is one of the largest single levers you have on your AWS bill — more impactful than instance family choice, region choice, or storage choice. The wrong model can cost you 3x the right one for the same workload.

The five models are: **on-demand**, **reserved instances**, **savings plans**, **spot**, and **dedicated hosts**. They are not mutually exclusive — a single account typically runs a mix.

**On-demand** is the default. It is the price you see quoted on the EC2 pricing page. You pay only for what you use, billed per second after the first minute. There is no commitment, no upfront cost, and no risk of interruption. The downside is the price: it carries the highest per-hour rate because you are paying AWS for the optionality to scale up and down whenever you want. The classic use case is short-lived workloads, dev/test environments, traffic you cannot predict, and any workload you have not yet characterized.

**Reserved Instances** are the historical commitment model. You commit to a specific instance family and region (or a specific AZ, which additionally reserves capacity) for either 1 or 3 years, and AWS gives you a discount of roughly 30–60% versus on-demand. The longer the term and the larger the upfront payment, the bigger the discount. There are two flavors: *standard* RIs (cheapest, but cannot be resold or exchanged), and *convertible* RIs (a smaller discount, but you can change the instance family mid-term). RIs are best for steady-state, predictable workloads that you know you will run for at least a year.

**Savings Plans** are the modern, more flexible commitment model. Instead of committing to a specific instance family, you commit to a steady $/hour spend, and AWS applies your discount automatically to any matching usage — EC2, Fargate, or Lambda. Compute Savings Plans are the most flexible (any region, any family, any compute service) and give about 27% off. EC2 Instance Savings Plans tie you to a region + family but give a bigger discount (around 37%). They are the right default for most steady-state workloads today.

**Spot** is the wholesale market. AWS always has some spare capacity that paid customers are not using; spot lets you bid for that capacity at a market-clearing price that is typically 60–90% below on-demand. The catch is that AWS can take the instance back with a 2-minute notice whenever it needs the capacity. The right workload for spot is anything that is fault-tolerant, stateless, or can checkpoint — CI runners, batch jobs, web server fleets behind an ALB, big-data workers, render farms.

**Dedicated Hosts** are the niche model. You pay for an entire physical server that only you can run instances on. They exist for compliance and licensing scenarios — for example, Windows Server licenses that are priced per socket, or legacy software that is licensed per physical host. They are the most expensive option per vCPU and are not interchangeable with the other four models.

The decision rule of thumb:

- **Don't know what the workload will look like** -> on-demand.
- **Know it will run 24/7 for at least a year** -> Savings Plan (Compute or EC2 Instance).
- **Have a strict family and AZ for compliance** -> standard RI for capacity, convertible RI for flexibility.
- **Workload is fault-tolerant, batch, or stateless** -> spot, ideally mixed with on-demand for the baseline.
- **Need a physical server for licensing** -> dedicated host.

In L20 we will get into the on-demand / RI / Savings Plans details, and in L21 we will cover spot end-to-end. L22 will put a calculator in your hands so you can see the numbers.

## Hands-on

None. L22 has the only hands-on in this section.

## Quiz prep

- Name the five EC2 pricing models and the default one.
- Which model is interruptible and what is the warning time?
- Which model is appropriate for a workload you know will run 24/7 for 18 months?
- Roughly what discount does Compute Savings Plans give versus on-demand?
- Which model lets you run instances on a physical server you exclusively own?

## Further reading

- AWS EC2 Pricing — https://aws.amazon.com/ec2/pricing/
- AWS Savings Plans overview — https://aws.amazon.com/savingsplans/
- AWS Spot Instances overview — https://aws.amazon.com/ec2/spot/
