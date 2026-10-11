# Section 2 — EC2 Fundamentals

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Lectures:** L04–L08
> **Duration:** ~47 min lecture + 1 working demo

Before we ever click **Launch instance**, you need five mental models in
place: what a virtual machine actually is, what a hypervisor does, what
"managed" really means in an AWS context, how AWS's geographic model of
regions and Availability Zones works, and the taxonomy of EC2 instance
types. Section 2 builds those models so the hands-on work in section 3
feels obvious instead of magical.

## Lecture map

| L# | Title | Min | File |
|---|---|---|---|
| L04 | VMs, Hosts, and Hypervisors | 10 | `lecture_scripts/L04_vms_hosts_hypervisors.md` |
| L05 | Managed vs Unmanaged Services (and where EC2 fits) | 8 | `lecture_scripts/L05_managed_vs_unmanaged.md` |
| L06 | Regions and Availability Zones | 12 | `lecture_scripts/L06_regions_and_azs.md` |
| L07 | EC2 Instance Types (families, sizes, use cases) | 12 | `lecture_scripts/L07_instance_types.md` |
| L08 | Section Recap + `region_az_demo.py` | 5 | `lecture_scripts/L08_section_recap.md` |

## Working code

| Demo | Description |
|---|---|
| `code/region_az_demo/region_az_demo.py` | Lists enabled AWS regions, walks the print class, lists AZs in the current region, and maps the account-specific AZ IDs to the human-readable AZ names. Uses stdlib + boto3 only. |
| `code/region_az_demo/test_region_az_demo.py` | pytest suite using `moto`'s `@mock_aws` to verify the demo behavior in isolation — no real credentials, no surprises. |

## How to read this section

1. **Watch the lectures in order.** L04–L07 are conceptual and build on
   each other (L06 depends on the hypervisor framing from L04; L07
   depends on the "EC2 is IaaS" framing from L05).
2. **Open the console in parallel with L04–L06.** After the VMs lecture,
   go to EC2 → Instances and notice that you cannot see the host or the
   hypervisor — AWS hides both. After the AZ lecture, look at the
   region selector in the top-right of the console and click through two
   regions.
3. **Run the demo at the end (L08).** `python region_az_demo.py` will
   list every region your account can see and every AZ in your default
   region. Then run the tests with `pytest -v` to see the same
   behavior validated against mocked AWS APIs.
4. **Take the quiz.** `../../quizzes/section_2.md` — 10 questions, pass
   bar 7/10.

## What you should be able to do after this section

- Explain the type-1 vs type-2 hypervisor distinction in one sentence and
  tell me which one AWS uses and why (Nitro).
- Define "managed service" and explain why EC2 is **not** a managed
  service — what responsibilities stay with you, the customer.
- Given any AWS account, list the regions it can use and the AZs in any
  one region, and explain why `us-east-1a` in your account might map to
  a different physical data center than `us-east-1a` in mine.
- Given a workload, pick a reasonable instance family (general purpose,
  compute, memory, storage, accelerated) and explain the choice.

## Further reading

- `../../SYLLABUS.md` — authoritative lecture-to-file map.
- `../../README.md` — repo layout and "What you'll build" table.
- AWS docs: [What is EC2?](https://docs.aws.amazon.com/ec2/) and
  [AWS Nitro System](https://aws.amazon.com/ec2/nitro/).