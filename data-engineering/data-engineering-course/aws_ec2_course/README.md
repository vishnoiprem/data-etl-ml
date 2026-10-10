# AWS EC2 + Load Balancing Crash Course

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** 8 sections, 38 lectures, 6 working boto3 + moto code demos,
> 5 mermaid diagrams, 8 quizzes, 1 download.
> **Source:** Udemy-published curriculum "AWS EC2 Crash Course + Load
> Balancing with Demos" (October 2026 edition).

This is a **beginner-friendly, hands-on** AWS course. Every concept is
backed by either a boto3 script you can read end-to-end or a
`pytest`-runnable demo that uses `moto` to mock AWS — so you can learn
EC2 + Elastic Load Balancing without spending a cent on AWS.

## What you will learn

- The mental model: VM, host, hypervisor, AMI, instance type, region, AZ.
- How to **create an EC2 instance** end-to-end: pick an AMI, choose an
  instance type, configure networking, storage, user data, key pair,
  security group.
- How to **take a snapshot**, build a **custom AMI**, resize, stop,
  start, and terminate instances.
- How AWS **prices EC2** (on-demand, reserved, savings plans, spot,
  dedicated) and how to estimate cost.
- How **Elastic Load Balancing** works: **NLB** (L4), **ALB** (L7),
  **GWLB** (third-party appliances), target groups, health checks,
  cross-zone balancing, internet-facing vs internal, routing rules.

## What you build

| # | Section | What runs | Lectures |
|---|---|---|---|
| 1 | Introduction to EC2 | – | L01–L03 |
| 2 | EC2 Fundamentals | `region_az_demo.py` | L04–L08 |
| 3 | Creating an EC2 instance | `launch_instance.py` + 6 moto tests | L09–L18 |
| 4 | EC2 Pricing deep dive | `pricing_calc.py` (no AWS) | L19–L22 |
| 5 | Managing EC2 | `snapshot_ami_demo.py` + 4 moto tests | L23–L26 |
| 6 | Load Balancing intro + NLB | `nlb_create.py` + 4 moto tests | L27–L30 |
| 7 | Application Load Balancer | `alb_create.py` + 4 moto tests | L31–L35 |
| 8 | Gateway Load Balancer + wrap-up | `gwlb_create.py` + 3 moto tests | L36–L38 |

## Quick start (no AWS account needed)

```bash
cd data-engineering-course/aws_ec2_course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run every test in the course
python scripts/run_all_tests.py

# Or just section 3 (creating an EC2 instance)
pytest -v 03_creating_ec2/code/launch_instance/
```

Expected: **~30 tests pass** in under 5 seconds, no AWS calls.

## Layout

```
aws_ec2_course/
├── README.md                       ← you are here
├── SYLLABUS.md                     ← authoritative L-ID ↔ file map
├── DIRECTORY.md                    ← full file index
├── CHANGELOG.md                    ← v1.0
├── requirements.txt                ← boto3 + moto[ec2,elb] + pytest
├── 01_intro_to_ec2/                ← 3 lectures, no code
│   ├── README.md
│   └── lecture_scripts/
├── 02_ec2_fundamentals/            ← 5 lectures + region_az_demo
├── 03_creating_ec2/                ← 10 lectures + launch_instance
├── 04_ec2_pricing/                 ← 4 lectures + pricing_calc
├── 05_managing_ec2/                ← 4 lectures + snapshot_ami_demo
├── 06_load_balancing_nlb/          ← 4 lectures + nlb_create
├── 07_load_balancing_alb/          ← 5 lectures + alb_create
├── 08_load_balancing_gwlb/         ← 3 lectures + gwlb_create + wrap-up
├── quizzes/                        ← one per section
├── diagrams/                       ← 5 mermaid files
├── assignments/                    ← 1 optional exercise
├── downloads/                      ← PDF slide placeholders
└── scripts/
    ├── run_all_tests.py
    └── bootstrap.sh
```

## Prerequisites

- Python 3.10+
- AWS account (only if you want to run the boto3 scripts for real;
  every code sample is `moto`-mockable for offline learning)
- A 30-minute block of time for each section

## Next steps

1. Read `SYLLABUS.md` to find every lecture.
2. Open `01_intro_to_ec2/lecture_scripts/L01_course_overview.md`.
3. Work through the sections in order — each one builds on the previous.
4. Run the section's `code/` tests after reading the lecture.
5. Take the section quiz in `quizzes/section_N.md` before moving on.
