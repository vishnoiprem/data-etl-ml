# DIRECTORY — Full file index

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

This file lists every artifact in the AWS EC2 + Load Balancing
Crash Course. Use `find` if you want a live listing.

## Top level

- `README.md` — course overview, what you build, quick start
- `SYLLABUS.md` — authoritative L-ID ↔ file map
- `DIRECTORY.md` — this file
- `CHANGELOG.md` — v1.0 release notes
- `requirements.txt` — boto3 + moto + pytest

## Sections (8)

| Folder | Title | Lectures | Code |
|---|---|---|---|
| `01_intro_to_ec2/` | Introduction to EC2 | L01–L03 | – |
| `02_ec2_fundamentals/` | EC2 Fundamentals | L04–L08 | `region_az_demo.py` |
| `03_creating_ec2/` | Creating an EC2 Instance | L09–L18 | `launch_instance.py` + tests |
| `04_ec2_pricing/` | EC2 Pricing | L19–L22 | `pricing_calc.py` |
| `05_managing_ec2/` | Managing EC2 | L23–L26 | `snapshot_ami_demo.py` + tests |
| `06_load_balancing_nlb/` | Load Balancing + NLB | L27–L30 | `nlb_create.py` + tests |
| `07_load_balancing_alb/` | ALB | L31–L35 | `alb_create.py` + tests |
| `08_load_balancing_gwlb/` | GWLB + wrap-up | L36–L38 | `gwlb_create.py` + tests |

## Quizzes

- `quizzes/section_1.md` (8 questions)
- `quizzes/section_2.md` (10 questions)
- `quizzes/section_3.md` (12 questions)
- `quizzes/section_4.md` (10 questions)
- `quizzes/section_5.md` (10 questions)
- `quizzes/section_6.md` (10 questions)
- `quizzes/section_7.md` (10 questions)
- `quizzes/section_8.md` (10 questions, final)

## Diagrams (mermaid, in `diagrams/`)

- `ec2_anatomy.mmd`
- `regions_azs.mmd`
- `ha_across_azs.mmd`
- `alb_request_flow.mmd`
- `nlb_request_flow.mmd`
- `gwlb_request_flow.mmd`

## Scripts

- `scripts/run_all_tests.py` — runs every `test_*.py`
- `scripts/bootstrap.sh` — venv + pip + test run

## Assignments and downloads

- `assignments/assignment_1_ha_webapp.md` — optional extension exercise
- `downloads/slides.pdf` — placeholder for the published PDF slides
