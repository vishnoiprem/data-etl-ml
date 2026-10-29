# L10 — Choosing an AMI

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 03
> **Duration target:** 10:00
> **Lecture ID:** L10

## Status

Authored.

## Prereqs

- L04 (VMs, Hosts, and Hypervisors).
- L09 (the 7-step wizard) — Step 2 is "Application and OS Images".

## Key terms

- **AMI** — Amazon Machine Image. A snapshot of a root volume plus
  launch permissions, block device mappings, and (optionally) a
  kernel / ramdisk id.
- **Quick Start AMI** — a curated set of AMIs Amazon publishes for
  common OSes (Amazon Linux 2, Ubuntu LTS, Windows Server, macOS,
  Red Hat, SUSE). Free of charge (you still pay for the instance
  hours).
- **Marketplace AMI** — a paid AMI published by a third party (e.g.
  a pre-hardened nginx, a Datadog agent, a GPU deep-learning stack).
  You pay the publisher's software charge on top of the instance
  cost.
- **Custom AMI** — an AMI you built yourself from a snapshot
  (covered in section 5).
- **Community AMI** — a public AMI published by an AWS customer,
  shared with the world. Use these only from sources you trust.
- **x86_64 vs arm64 (Graviton)** — modern instance types come in
  two CPU architectures. AWS Graviton (arm64) instances are ~20%
  cheaper per vCPU and run most Linux software unchanged, but
  require arm64-native binaries.

## Lecture

Step 2 of the EC2 creation wizard asks you to pick an **AMI**. The
AMI is the single most consequential choice you make on the wizard,
because it determines:

- the operating system (and therefore every package, every path,
  every `/etc/...` file on the instance);
- the architecture (x86_64 vs arm64);
- the root volume type and size baked into the template;
- whether specific AWS agents (SSM, CloudWatch, EFS) are
  pre-installed;
- the price you pay — Marketplace AMIs add a per-hour software
  charge on top of the instance cost.

### The four sources of AMIs in the console

In the AMI selector, AWS groups AMIs into four buckets:

1. **Quick Start** — Amazon-maintained AMIs for the most popular
   operating systems. Always current with security patches, always
   free (you only pay the instance hours).
2. **AWS Marketplace** — paid AMIs from third parties. Each one
   shows a per-hour software price; the price is added to your EC2
   bill.
3. **My AMIs** — AMIs you have created yourself, including any
   "golden images" your team has published.
4. **Community AMIs** — public AMIs published by other AWS
   customers. Powerful but risky: treat them as if you were
   downloading random software from the internet.

### Amazon Linux 2 vs Ubuntu LTS vs Windows vs macOS

The four Quick Start OSes you'll actually pick between:

| OS | Why you'd pick it | Watch out for |
|---|---|---|
| **Amazon Linux 2** | Free; AWS-optimized; comes with SSM agent, AWS CLI v2 pre-installed; long-term support through 2025+. The course default. | RPM-based — `yum`/`dnf`, not `apt`. |
| **Ubuntu Server 22.04 / 24.04 LTS** | Familiar to most developers; huge package archive; Snap pre-installed. | LTS releases are supported for 5 years; non-LTS releases are NOT. |
| **Windows Server** | Required for ASP.NET, MSSQL, RDP-only workflows. | License is included in the instance price but the cost is much higher than Linux. |
| **macOS** | Required for iOS / macOS build agents. Only available on `mac1.metal` / `mac2.metal` host-dedicated instances. | **Very** expensive and only in a few regions. |

For this course we default to **Amazon Linux 2** because:

- the SSM agent and AWS CLI are pre-installed;
- AWS publishes security patches through `yum`;
- the `t3.micro` instance is free-tier eligible for 12 months;
- the boto3 + moto test scaffolding is simpler to mock.

### When you'd reach for a Marketplace AMI

Three common cases:

1. **Pre-hardened OS images** (e.g. CIS-hardened Linux). Saves you
   the work of running STIG yourself.
2. **Software bundles** (e.g. nginx Plus, Datadog Agent, MongoDB
   Atlas local-mode). The publisher keeps the AMI updated; you pay
   per hour.
3. **GPU / ML stacks** (e.g. Deep Learning AMIs with CUDA +
   PyTorch + Jupyter). For one-off experiments this is faster
   than building the stack yourself.

Always read the Marketplace product page: the price is per instance
hour, and it stacks on top of the EC2 instance price.

### When you'd reach for a custom AMI

Two common cases:

1. **Golden image** — your team bakes the OS, agents, monitoring
   agent, and a hardening baseline into one AMI, and every new
   instance is launched from that. We'll cover this in section 5.
2. **Cross-region migration** — you build an AMI in `us-east-1`,
   copy it to `eu-west-1`, and launch from the copy. Faster than
   re-installing everything from scratch.

### Architecture choice: x86_64 vs arm64 (Graviton)

Modern instance types come in two CPU families. The Graviton family
(AWS-designed ARM processors) is **roughly 20% cheaper per vCPU**
than the comparable x86_64 instance. For most Linux workloads the
code just works, but you need:

- an arm64 AMI (most Quick Start AMIs ship both);
- arm64-native binaries for any native code (Go, Rust, C extensions
  in Python);
- arm64-native Docker base images.

If you don't have an arm64 AMI handy, an x86_64 instance is the safe
choice. Section 3 of this course uses x86_64 throughout.

### Finding the latest AMI id

The console hides a complication: **AMI ids are region-specific**.
The `ami-0abcdef…` you see in the console for `us-east-1` is
**different from** the id for `eu-west-1`. In real automation you
typically resolve the latest id at launch time with something
like:

```bash
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
  --output text
```

For this course's `launch_instance.py` we pass `--ami-id` as a
command-line argument so the script doesn't bake in a region-specific
id.

## Quiz prep

- Name two Quick Start AMIs available in the AWS console. (Amazon
  Linux 2, Ubuntu Server LTS, Windows Server, macOS, Red Hat
  Enterprise Linux.)
- What is the cost difference between a Quick Start AMI and a
  Marketplace AMI? (Quick Start is free; Marketplace adds a per-hour
  software charge on top of the instance cost.)
- Are AMI ids global or region-specific? (Region-specific.)
- What's the main reason to pick a custom AMI over a Quick Start
  AMI? (Your team has pre-baked OS, agents, and hardening into it
  — "golden image".)

## Further reading

- AWS docs: *Amazon Machine Images (AMI)* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html>
- AWS docs: *AWS Marketplace* — <https://aws.amazon.com/marketplace>
- AWS docs: *Find a Linux AMI* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/finding-an-ami.html>
