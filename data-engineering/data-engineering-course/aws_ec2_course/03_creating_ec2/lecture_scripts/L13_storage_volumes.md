# L13 — Configuring Storage Volumes

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 03
> **Duration target:** 10:00
> **Lecture ID:** L13

## Status

Authored.

## Prereqs

- L09 (the wizard) — Step 6 is "Configure storage".

## Key terms

- **EBS** — Elastic Block Store. Network-attached block storage
  that persists independently of the instance lifecycle.
- **Root volume** — the EBS volume the AMI boots from. Created
  automatically from the AMI's snapshot. Defaults to 8 GB on
  Amazon Linux 2.
- **Additional volume** — a second (or third, or …) EBS volume
  attached to the instance. Mounted under `/mnt/data` (or
  wherever you tell the OS to mount it).
- **gp3** — General Purpose SSD, 3rd generation. The default for
  most workloads. Up to 16,000 IOPS and 1,000 MB/s baseline
  throughput per volume, independent of size.
- **io2 / io2 Block Express** — Provisioned IOPS SSD. For
  IOPS-bound databases (OLTP) where you need >16,000 IOPS or
  sub-millisecond latency. Up to 64,000 IOPS (io2) or 256,000
  IOPS (io2 Block Express) per volume.
- **st1** — Throughput-optimized HDD. Cheap per GB, great for
  big sequential scans (log processing, data warehousing).
- **sc1** — Cold HDD. Cheapest per GB, infrequent access. Don't
  use for a boot volume.
- **EBS encryption** — AES-256 at rest, transparent to the OS.
  Use the default `aws/ebs` KMS key or a customer-managed KMS key
  for compliance.
- **DeleteOnTermination** — when the instance is terminated, the
  volume is deleted. The root volume defaults to `True`; the
  default for additional volumes you attach at launch is also
  `True`, but you can flip it off if you want the data to survive
  the instance.

## Lecture

Step 6 of the wizard is "Configure storage". Every EC2 instance
needs at least one storage device: the **root volume** that the
AMI boots from. You can also attach **additional volumes** to hold
data that should survive a stopped/started instance or that
shouldn't sit on the root filesystem.

### Root volume vs additional volume

The root volume is created automatically from the AMI's snapshot.
You can resize it, change its type, and add encryption — but you
can't detach it without stopping the instance. The OS sees it as
`/dev/xvda` (Linux) or the C: drive (Windows).

An additional volume is one you attach explicitly. It can be any
EBS type, any size, and you mount it wherever you like (often
`/mnt/data` or `/var/lib/postgresql`). You can detach it from one
instance and attach it to another (with some caveats around
multi-attach and NVMe reservations).

### The EBS type matrix

The five EBS types you'll actually consider:

| Type | Category | Size range | Max IOPS/volume | Max throughput/volume | When to use it |
|---|---|---|---|---|---|
| **gp3** | SSD (general) | 1 GB – 16 TB | 16,000 | 1,000 MB/s | Default. Most workloads. Boot, app data, small DBs. |
| **io2** | SSD (IOPS-bound) | 4 GB – 16 TB | 64,000 | 1,000 MB/s | Production OLTP databases, latency-sensitive. |
| **io2 Block Express** | SSD (extreme IOPS) | 4 GB – 64 TB | 256,000 | 4,000 MB/s | The most demanding databases. Newer instance types only. |
| **st1** | HDD (throughput) | 125 GB – 16 TB | 500 | 500 MB/s | Big sequential scans: Kafka, log processing, data warehouses. |
| **sc1** | HDD (cold) | 125 GB – 16 TB | 250 | 250 MB/s | Cold data, infrequent access. Cheapest per GB. |

**Rule of thumb:** if you don't know, pick `gp3`. The 3,000 IOPS /
125 MB/s baseline is included in the price, and you only pay more
if you provision more.

### Provisioned IOPS vs baseline

Older `gp2` volumes tied IOPS to volume size (3 IOPS per GB,
capped at 16,000 IOPS at 5,334 GB). `gp3` decouples them: every
`gp3` volume gets 3,000 IOPS / 125 MB/s by default, and you
provision extra by paying for it.

For `io2` you provision both **size** and **IOPS** explicitly.
You'll pay per GB-month and per IOPS-month.

### Encryption

EBS encryption is **AES-256-XTS**, transparent to the OS, and
free (you only pay for the KMS key if you use a customer-managed
one). By default new volumes are encrypted with the
`aws/ebs` AWS-managed key. You can also:

- encrypt with a **customer-managed KMS key** (CMK) for compliance;
- set the **account default** so every new volume is encrypted;
- enforce encryption with an **IAM policy** that denies
  `ec2:CreateVolume` without the `Encrypted` flag.

This course's `launch_instance.py` does not pass an explicit
encryption flag — the account default applies.

### Snapshots (preview of section 5)

EBS **snapshots** are point-in-time copies of a volume, stored in
S3. They're how you back up a volume, how you copy a volume
across regions, and how you build a **custom AMI** (covered in
section 5).

A snapshot is **incremental after the first** — only the blocks
that have changed since the last snapshot are uploaded. The
**first** snapshot of a 100 GB volume is ~100 GB; subsequent
deltas might be only a few hundred MB.

### Block device mappings in boto3

The boto3 `BlockDeviceMappings` argument is a list. Each entry
says "device name → what to mount there". For the root volume
you typically pass:

```python
"BlockDeviceMappings": [
    {
        "DeviceName": "/dev/xvda",
        "Ebs": {
            "VolumeSize": 20,
            "VolumeType": "gp3",
            "DeleteOnTermination": True,
            "Encrypted": True,
        },
    }
]
```

The default `gp3` size in the course's launch script is whatever
the AMI ships with (8 GB on Amazon Linux 2). You can override by
passing your own `BlockDeviceMappings` argument.

### Common gotchas

1. **Volume size at launch != volume size later.** You can grow an
   EBS volume without stopping the instance (online resize) but
   you can't shrink it. If you need it smaller, snapshot, create
   a smaller volume, and swap.
2. **The "free tier" 30 GB is for gp2/gp3 only.** io1/io2 are not
   free-tier eligible.
3. **EBS volumes are AZ-scoped.** A volume created in
   `us-east-1a` cannot be attached to an instance in `us-east-1b`.
   For cross-AZ you'd snapshot → copy → new volume.
4. **DeleteOnTermination defaults vary.** The **root** volume
   defaults to `True`. **Additional** volumes attached at launch
   default to `True` (in newer API versions) but historically
   defaulted to `False` — always check.
5. **io2 Block Express requires specific instance types.** Not
   every instance type can attach one. Check the docs before
   provisioning.

## Quiz prep

- What's the difference between a root volume and an additional
  volume? (Root is created from the AMI snapshot, holds the OS;
  additional is a separate EBS volume you mount under your own
  path.)
- When would you pick `io2` over `gp3`? (When you need more than
  16,000 IOPS or sub-millisecond latency — typically a production
  OLTP database.)
- Are EBS volumes AZ-scoped or region-scoped? (AZ-scoped.)
- What happens to a volume when `DeleteOnTermination` is `True`
  and the instance is terminated? (The volume is deleted.)

## Further reading

- AWS docs: *Amazon EBS volume types* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html>
- AWS docs: *Make an Amazon EBS volume available for use on Linux* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html>
- AWS docs: *Encryption at rest* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html>
