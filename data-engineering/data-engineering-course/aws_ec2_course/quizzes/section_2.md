# Section 2 Quiz — EC2 Fundamentals (L04–L08)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Pass bar:** 7 / 10
> **Time limit:** 15 minutes
> **Format:** 10 multiple-choice and short-answer questions

## Instructions

- 10 questions, one point each.
- Pass mark is **7 out of 10** (70%).
- Closed book. Lecture scripts and the `region_az_demo` script
  are fair game as references.
- Answers are at the bottom of this file. **No peeking.**

---

### Q1 — Hypervisor type

Which type of hypervisor runs directly on physical hardware with
no host operating system underneath?

- A. Type-2 (hosted)
- B. Type-1 (bare-metal)
- C. Type-3 (microkernel)
- D. Type-0 (firmware)

### Q2 — AWS hypervisor evolution

Which hypervisor technology does AWS currently use for EC2, and
what problem does it solve compared to the historical choice?

- A. VirtualBox, because it is open source
- B. KVM, because it is the fastest open-source hypervisor
- C. Nitro, which offloads networking, storage, and security to
  dedicated hardware, freeing CPU for customer workloads
- D. Hyper-V, because it is the same one Azure uses

### Q3 — Managed vs unmanaged

Which of the following responsibilities **does** AWS take on for
a vanilla EC2 instance? (Pick the most complete answer.)

- A. OS patching, security group rules, and EBS volume management
- B. Hardware, hypervisor, and data-center physical security
- C. Application monitoring, log aggregation, and scaling
- D. Everything; EC2 is a fully managed service

### Q4 — Shared responsibility

Under the AWS shared responsibility model, which of the
following is **the customer's** responsibility for EC2? (Pick
the most complete answer.)

- A. Physical security of the data center
- B. The hypervisor and the Nitro cards
- C. Patching the guest operating system, configuring security
  group rules, and rotating IAM credentials
- D. Power and cooling in the AWS region

### Q5 — Region vs AZ

An Availability Zone is best described as:

- A. A separate AWS account in the same organization
- B. A geographic AWS region
- C. One or more discrete data centers in a region with
  independent power, cooling, and networking
- D. A virtual private cloud (VPC) inside one data center

### Q6 — AZ IDs

Why does AWS randomize the mapping from AZ name (e.g.
`us-east-1a`) to AZ ID (e.g. `use1-az1`) per AWS account?

- A. To save storage in the control plane
- B. To charge customers a "randomization fee"
- C. To distribute load across data centers and reduce the blast
  radius of any one account's actions
- D. To comply with GDPR

### Q7 — Region selection

You are building a workload for users in Germany that must
comply with GDPR. Which region should you pick first, and why?

- A. `us-east-1`, because it is the cheapest
- B. An EU region (e.g. `eu-central-1` Frankfurt, `eu-west-1`
  Ireland), because data must stay inside the EU to meet GDPR
  data-residency requirements
- C. `ap-northeast-1` Tokyo, because it has the lowest latency
  from Germany
- D. It does not matter; GDPR is enforced by AWS everywhere

### Q8 — Instance type naming

The instance type `c5.xlarge` decodes as:

- A. Compute-optimized, 5th generation, xlarge size — 4 vCPUs
  and 8 GiB of RAM
- B. Compute-optimized, 5th generation, xlarge size — 2 vCPUs
  and 4 GiB of RAM
- C. Cost-optimized, generation 5, xlarge — 4 vCPUs and 8 GiB
- D. Compute-optimized, version 5, xlarge — 8 vCPUs and 16 GiB

### Q9 — Instance family fit

A workload holds a 200 GB in-memory working set (a Redis
cache) and serves a moderate number of small requests. Which
instance family is the best fit?

- A. Compute optimized (C) — Redis is CPU-bound
- B. General purpose (T or M) — balanced workloads always win
- C. Memory optimized (R or X) — Redis holds data in RAM, so
  pick a family with a high memory-to-vCPU ratio
- D. Storage optimized (I or D) — Redis needs fast disk

### Q10 — `region_az_demo.py`

You run `python region_az_demo.py` on a fresh laptop with no AWS
credentials configured. What happens?

- A. The script raises `NoCredentialsError` and exits with a
  non-zero status
- B. The script prints a friendly message explaining how to
  configure credentials, then exits with status 0
- C. The script hangs forever waiting for input
- D. The script deletes the local `~/.aws/credentials` file

---

## Answer key

1. **B** — Type-1 (bare-metal) hypervisors run directly on the
   hardware. VirtualBox, VMware Workstation, and Parallels are
   type-2 (hosted) and run on top of a host OS.
2. **C** — AWS uses **Nitro**, which offloads networking, EBS,
   encryption, and security to dedicated hardware cards. The
   hypervisor is now tiny (it just schedules vCPUs), so more CPU
   is available for the customer.
3. **B** — AWS is responsible for the hardware, the hypervisor,
   and the data-center physical security. Everything above the
   hypervisor (OS, application, monitoring, scaling, patching) is
   the customer's job.
4. **C** — Patching the guest OS, configuring security groups, and
   rotating IAM credentials are all the customer's responsibility.
   Physical security, the hypervisor, power, and cooling are AWS's.
5. **C** — An AZ is one or more discrete data centers in a region
   with independent power, cooling, and networking. Most regions
   have 3 AZs; some have 2, a few have 6.
6. **C** — AWS randomizes the AZ-name-to-AZ-ID mapping per
   account to (1) distribute load across data centers (so every
   new account's "first click" doesn't land on one box) and (2)
   reduce the blast radius when one physical data center has an
   issue.
7. **B** — GDPR requires EU personal data to stay within the EU,
   so pick an EU region. Latency and cost are secondary. `us-east-1`
   would be a compliance violation; `ap-northeast-1` is in Asia;
   AWS does not enforce GDPR for you.
8. **A** — `c` = compute-optimized family, `5` = 5th generation,
   `xlarge` = 4 vCPUs / 8 GiB. (`c5.large` is 2 vCPUs / 4 GiB.)
9. **C** — Redis is in-memory, so memory-optimized (R or X) is
   the right family. The whole point of those families is a high
   memory-to-vCPU ratio, which lets you size for the working set
   without paying for CPU you don't need.
10. **B** — The script's `main()` calls `_has_credentials()` and,
    on miss, prints a friendly message and exits 0. The
    `test_main_returns_zero_when_no_credentials` test in
    `test_region_az_demo.py` covers exactly this case.
