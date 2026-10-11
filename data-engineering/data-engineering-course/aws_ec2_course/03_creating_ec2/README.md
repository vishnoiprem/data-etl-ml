# Section 3 — Creating an EC2 Instance (L09–L18)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Total duration:** ~94 minutes across 10 lectures
> **Working artifact:** `code/launch_instance/launch_instance.py` + 6 moto tests
> **Quiz:** `../../quizzes/section_3.md` (12 questions, pass bar 8 / 12)

This is the **longest section in the course** and the first one where
you build something real. Section 2 (EC2 Fundamentals) gave you the
mental model: what a VM, host, hypervisor, AMI, instance type, region,
and AZ are. Section 3 turns that mental model into a working
`boto3` script that launches an EC2 instance, waits for it to enter
the `running` state, and returns the instance id.

By the end of L18 you will:

1. Know the **7-step EC2 creation wizard** in the AWS console, top to
   bottom.
2. Be able to choose between **Amazon Linux 2, Ubuntu LTS, Windows,
   custom, and Marketplace** AMIs.
3. Be able to read the **instance type matrix** and right-size
   (CPU, memory, network, storage).
4. Understand **networking decisions**: VPC, subnet, public IP, AZ.
5. Understand **EBS storage choices**: gp3 vs io2, root vs additional,
   encryption.
6. Know the **advanced settings** that prevent costly accidents:
   termination protection, shutdown behavior, IAM role, user data,
   detailed monitoring.
7. Be able to write an **idempotent cloud-init user-data script**.
8. Be able to create and use an **EC2 key pair** for SSH.
9. Be able to design an **EC2 security group** (stateful firewall)
   with the principle of least privilege.
10. Be able to run the `launch_instance.py` script end-to-end, with
    both **moto (offline)** and **real AWS**.

## Lecture map

| L# | Title | Duration | File |
|---|---|---|---|
| L09 | The EC2 Creation Wizard (overview) | 8:00 | `lecture_scripts/L09_creation_wizard.md` |
| L10 | Choosing an AMI | 10:00 | `lecture_scripts/L10_choosing_ami.md` |
| L11 | Choosing an Instance Type | 10:00 | `lecture_scripts/L11_choosing_instance_type.md` |
| L12 | Configuring Network Settings | 10:00 | `lecture_scripts/L12_network_settings.md` |
| L13 | Configuring Storage Volumes | 10:00 | `lecture_scripts/L13_storage_volumes.md` |
| L14 | Advanced Settings | 8:00 | `lecture_scripts/L14_advanced_settings.md` |
| L15 | User Data Scripts | 10:00 | `lecture_scripts/L15_user_data.md` |
| L16 | Key Pairs | 8:00 | `lecture_scripts/L16_key_pairs.md` |
| L17 | Security Groups | 12:00 | `lecture_scripts/L17_security_groups.md` |
| L18 | Section Recap + `launch_instance.py` | 8:00 | `lecture_scripts/L18_section_recap.md` |

## How to read this section

1. **Read in lecture order.** Each lecture builds on the previous
   one's terminology. L09 introduces the wizard steps; L10–L17 deep-dive
   one step each; L18 ties it all together with a script.
2. **Open the AWS console in another tab** as you read. L09–L17 are
   written so you can mirror each step in the console. No step requires
   a paid resource — every lecture can be read without launching
   anything.
3. **Run the tests after L18.** From the repo root:

   ```bash
   pytest -v 03_creating_ec2/code/launch_instance/
   ```

   Expected: **6 passed** in under 5 seconds, zero AWS calls.
4. **Take the section quiz** in `../../quizzes/section_3.md`. Pass bar
   is **8 / 12**.

## Working artifact

The `code/launch_instance/` directory contains:

- `launch_instance.py` — boto3 script that calls `run_instances()`,
  tags the instance, waits for `running`, returns the id.
- `test_launch_instance.py` — 6 `moto`-based pytest tests.
- `README.md` — how to run against real AWS (IAM policy, CLI args,
  example commands).

## What's next

Section 4 (`04_ec2_pricing/`) covers the **money**: on-demand, reserved
instances, savings plans, and spot. Section 3 shows you how to
*create* an instance; section 4 shows you how to *price* one before
you click "Launch".
