# L03 — Who This Course Is For

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 01
> **Duration target:** 4:00
> **Lecture ID:** L03

## Status

Authored. The audience and prerequisites lecture.

## Prereqs

- L01 and L02 (recommended but not strictly required — the three personas are self-explanatory if you read the README).

## Key terms

- **AWS Solutions Architect** — a role that designs AWS-based systems. The AWS Solutions Architect Associate (SAA-C03) and Professional (SAP-C02) certifications are the two most common EC2-heavy AWS certifications.
- **Cloud Practitioner** — the AWS Foundational-level certification (CLF-C02). It covers EC2 and load balancing at a conceptual, non-deep-technical level.
- **DevOps / SRE** — practitioners who run production systems. They typically interact with EC2 and ELB at the API/CLI level (boto3, Terraform, AWS CDK) rather than the console.
- **boto3** — the AWS SDK for Python. Used throughout this course for code demos. Section 3 covers enough boto3 to launch an instance end-to-end.
- **moto** — a Python library that mocks the AWS API. Every boto3 script in this course is `moto`-mockable, so you can complete the course without an AWS account.

## Lecture

In the last two lectures I told you what the course covers and what you will be able to do. In this one I want to make sure it is the right course for you. The audience is, broadly, **three personas**. If you recognize yourself in one of them, you are in the right place.

**Persona 1 — The EC2 and load-balancing beginner.** You have heard of EC2. Maybe you clicked through the AWS console once and launched a t2.micro, saw the bill, and closed the tab. Maybe you have not even done that. You know that EC2 is "a server in the cloud" and you have a vague sense that load balancers exist, but you are not sure how they fit together. This is the largest persona and it is exactly who section 1 is written for. We start from "what is a virtual machine" in L04, we walk through the entire creation wizard step by step in section 3, and we never assume you have run an instance before. The 6 working boto3 scripts are written to be readable by a beginner, with comments on every non-obvious line. If you are a beginner, you are in the right place.

**Persona 2 — The AWS certification candidate.** You are studying for the AWS Cloud Practitioner (CLF-C02), the Solutions Architect Associate (SAA-C03), or the Solutions Architect Professional (SAP-C02). EC2 and Elastic Load Balancing are tested on all three, and the exam questions are very specific: "which load balancer supports host-based routing", "which pricing model offers the largest discount for a steady-state workload", "which scenario requires a dedicated host". This course is structured to map cleanly onto the exam domains. Sections 2 and 3 cover the EC2 fundamentals domain. Section 4 covers the pricing domain. Sections 6, 7, and 8 cover the load-balancing domain. The section quizzes (8 of them, one per section) are written in the same multiple-choice style as the actual AWS exams. If you are studying for an AWS certification, this course is designed to be your one-stop reference for the EC2 + ELB portions of the syllabus.

**Persona 3 — Anyone who works with AWS infrastructure.** You are a backend engineer, a DevOps practitioner, an SRE, a data engineer, a security engineer, or a solutions architect who already uses AWS daily but wants to firm up the EC2 and load-balancing fundamentals. You have probably launched dozens of instances, you know what a security group is, you have used an ALB in production. What you may not have done is take an EBS snapshot, build a custom AMI, estimate the cost difference between on-demand and savings plans, or stand up a Gateway Load Balancer in front of a third-party firewall. This course is also for you. The pace will feel comfortable through sections 2 and 3; it will pick up in sections 4, 5, 6, 7, and 8, where we cover the parts that are usually glossed over in the AWS getting-started docs.

Now — who this course is **not** for. If you are already a senior cloud architect who designs multi-region active-active deployments for a living, you will find the early sections slow. Skim them. Sections 6, 7, and 8 (load balancing) will probably still be useful because the GWLB coverage is hard to find elsewhere. If you are a complete beginner to cloud computing in general — you have never used any cloud, and "virtual machine" is a new term — sections 2 and 3 will still work, but you may want to set aside an extra hour. If you are looking for a deep dive on the Linux operating system, the networking stack, or the AWS CLI itself, those are not the focus of this course; we use the AWS CLI as a tool, we do not teach it for its own sake.

That is the audience in one minute. If any of the three personas sounded like you, the next stop is section 2 — **L04 — VMs, Hosts, and Hypervisors** — where we start building the mental model for what an EC2 instance actually is.

## Hands-on

No code in this lecture. Your task is a self-check: confirm which of the three personas above best describes you, and skim the **Prerequisites** section of the top-level `../../README.md` to make sure your environment is ready.

## Quiz prep

- The course is designed for three personas: EC2/LB beginners, AWS certification candidates, and practitioners who work with AWS infrastructure.
- EC2 and Elastic Load Balancing are tested on Cloud Practitioner (CLF-C02), Solutions Architect Associate (SAA-C03), and Solutions Architect Professional (SAP-C02).
- Every boto3 demo in the course is `moto`-mockable, so certification candidates can practice the CLI without an AWS account.

## Further reading

- [AWS Certification paths](https://aws.amazon.com/certification/)
- [SAA-C03 exam guide (EC2 + ELB domain coverage)](https://aws.amazon.com/certification/certified-solutions-architect-associate/)
- [`../../README.md`](../../README.md) — Prerequisites section.
