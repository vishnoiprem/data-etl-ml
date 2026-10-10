# SYLLABUS — AWS EC2 + Load Balancing Crash Course

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Format:** 8 sections, 38 lectures, 6 working code demos
> (boto3 + moto), 5 mermaid diagrams, 8 quizzes, 1 assignment, 1 download.
> **Source:** Udemy-published curriculum "AWS EC2 Crash Course + Load
> Balancing with Demos" (October 2026 edition).

This is the **authoritative lecture-to-file map**. The lecture order is
preserved exactly as L01–L38 below. Section folders are numbered to
match the course's 8 logical sections.

| Section | Lectures | Title | Working artifact |
|---|---|---|---|
| 1 | L01–L03 | Introduction to EC2 | – |
| 2 | L04–L08 | EC2 Fundamentals (VMs, hypervisors, regions, AZs, instance types) | `region_az_demo.py` |
| 3 | L09–L18 | Creating an EC2 instance end-to-end | `launch_instance.py` + tests |
| 4 | L19–L22 | EC2 Pricing deep dive | `pricing_calc.py` |
| 5 | L23–L26 | Managing EC2 (stop/start/resize, snapshots, custom AMI) | `snapshot_ami_demo.py` + tests |
| 6 | L27–L30 | Load Balancing intro + Network Load Balancer | `nlb_create.py` + tests |
| 7 | L31–L35 | Application Load Balancer (ALB) | `alb_create.py` + tests |
| 8 | L36–L38 | Gateway Load Balancer + course wrap-up | `gwlb_create.py` + tests |

**Total: 38 lectures, 8 quizzes, 6 working code samples + tests.**

---

## Section 1 — Introduction to EC2 (L01–L03)

| L# | Title | File |
|---|---|---|
| L01 | Course Overview | `01_intro_to_ec2/lecture_scripts/L01_course_overview.md` |
| L02 | What You'll Learn | `01_intro_to_ec2/lecture_scripts/L02_what_youll_learn.md` |
| L03 | Who This Course Is For | `01_intro_to_ec2/lecture_scripts/L03_who_this_course_is_for.md` |

## Section 2 — EC2 Fundamentals (L04–L08)

| L# | Title | File |
|---|---|---|
| L04 | VMs, Hosts, and Hypervisors | `02_ec2_fundamentals/lecture_scripts/L04_vms_hosts_hypervisors.md` |
| L05 | Managed vs Unmanaged Services (and where EC2 fits) | `02_ec2_fundamentals/lecture_scripts/L05_managed_vs_unmanaged.md` |
| L06 | Regions and Availability Zones | `02_ec2_fundamentals/lecture_scripts/L06_regions_and_azs.md` |
| L07 | EC2 Instance Types (families, sizes, use cases) | `02_ec2_fundamentals/lecture_scripts/L07_instance_types.md` |
| L08 | Section Recap + `region_az_demo.py` | `02_ec2_fundamentals/lecture_scripts/L08_section_recap.md` |

## Section 3 — Creating an EC2 Instance (L09–L18)

| L# | Title | File |
|---|---|---|
| L09 | The EC2 Creation Wizard (overview) | `03_creating_ec2/lecture_scripts/L09_creation_wizard.md` |
| L10 | Choosing an AMI | `03_creating_ec2/lecture_scripts/L10_choosing_ami.md` |
| L11 | Choosing an Instance Type | `03_creating_ec2/lecture_scripts/L11_choosing_instance_type.md` |
| L12 | Configuring Network Settings | `03_creating_ec2/lecture_scripts/L12_network_settings.md` |
| L13 | Configuring Storage Volumes | `03_creating_ec2/lecture_scripts/L13_storage_volumes.md` |
| L14 | Advanced Settings | `03_creating_ec2/lecture_scripts/L14_advanced_settings.md` |
| L15 | User Data Scripts | `03_creating_ec2/lecture_scripts/L15_user_data.md` |
| L16 | Key Pairs | `03_creating_ec2/lecture_scripts/L16_key_pairs.md` |
| L17 | Security Groups | `03_creating_ec2/lecture_scripts/L17_security_groups.md` |
| L18 | Recap + `launch_instance.py` + tests | `03_creating_ec2/lecture_scripts/L18_section_recap.md` |

## Section 4 — EC2 Pricing (L19–L22)

| L# | Title | File |
|---|---|---|
| L19 | EC2 Pricing Models Overview | `04_ec2_pricing/lecture_scripts/L19_pricing_models.md` |
| L20 | On-Demand, Reserved, Savings Plans | `04_ec2_pricing/lecture_scripts/L20_on_demand_reserved_sp.md` |
| L21 | Spot Instances | `04_ec2_pricing/lecture_scripts/L21_spot_instances.md` |
| L22 | Recap + `pricing_calc.py` | `04_ec2_pricing/lecture_scripts/L22_section_recap.md` |

## Section 5 — Managing EC2 (L23–L26)

| L# | Title | File |
|---|---|---|
| L23 | Stop, Start, Resize, Terminate | `05_managing_ec2/lecture_scripts/L23_stop_start_resize_terminate.md` |
| L24 | EBS Snapshots | `05_managing_ec2/lecture_scripts/L24_ebs_snapshots.md` |
| L25 | Custom AMIs | `05_managing_ec2/lecture_scripts/L25_custom_amis.md` |
| L26 | Recap + `snapshot_ami_demo.py` + tests | `05_managing_ec2/lecture_scripts/L26_section_recap.md` |

## Section 6 — Load Balancing Intro + NLB (L27–L30)

| L# | Title | File |
|---|---|---|
| L27 | What is a Load Balancer? | `06_load_balancing_nlb/lecture_scripts/L27_what_is_a_load_balancer.md` |
| L28 | Target Groups and Health Checks | `06_load_balancing_nlb/lecture_scripts/L28_target_groups_health_checks.md` |
| L29 | Network Load Balancer (NLB) | `06_load_balancing_nlb/lecture_scripts/L29_nlb_theory.md` |
| L30 | NLB Hands-On + `nlb_create.py` + tests | `06_load_balancing_nlb/lecture_scripts/L30_nlb_hands_on.md` |

## Section 7 — Application Load Balancer (L31–L35)

| L# | Title | File |
|---|---|---|
| L31 | ALB Theory + Internet-Facing vs Internal | `07_load_balancing_alb/lecture_scripts/L31_alb_theory.md` |
| L32 | ALB Hands-On: Create the Load Balancer | `07_load_balancing_alb/lecture_scripts/L32_alb_create.md` |
| L33 | ALB Rules (host- and path-based) | `07_load_balancing_alb/lecture_scripts/L33_alb_rules.md` |
| L34 | Cross-Zone Load Balancing | `07_load_balancing_alb/lecture_scripts/L34_cross_zone.md` |
| L35 | ALB Failure Simulation + `alb_create.py` + tests | `07_load_balancing_alb/lecture_scripts/L35_alb_failure_sim.md` |

## Section 8 — Gateway Load Balancer + Wrap-Up (L36–L38)

| L# | Title | File |
|---|---|---|
| L36 | Gateway Load Balancer (GWLB) Theory | `08_load_balancing_gwlb/lecture_scripts/L36_gwlb_theory.md` |
| L37 | GWLB Hands-On + `gwlb_create.py` + tests | `08_load_balancing_gwlb/lecture_scripts/L37_gwlb_hands_on.md` |
| L38 | Course Wrap-Up + Final Quiz | `08_load_balancing_gwlb/lecture_scripts/L38_course_wrapup.md` |
