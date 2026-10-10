---
id: L85
title: Amazon FSx for Windows File Server 101
section: 15
duration: "10:00"
prereqs:
  - L82-L84
---

# L85 — Amazon FSx for Windows File Server 101

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 15
> **Duration:** 10:00
> **Prereqs:** L82–L84

## What you will learn

By the end of this lecture you will be able to:

1. describe what FSx for Windows File Server is, the workloads it
   fits, and the workloads it does not fit;
2. pick the right **storage capacity**, **throughput capacity**,
   **deployment mode** (Single-AZ vs Multi-AZ), and **backup
   retention** for a given workload;
3. explain how FSx exposes CloudWatch metrics and how to query
   `FreeStorageCapacity` to drive a monitor or alarm;
4. describe the **FCI (File Server Cluster Instance)** concept and
   how FSx implements it as a Multi-AZ deployment with
   synchronous replication;
5. call `fsx.describe_file_systems` and `fsx.update_file_system`
   from a Lambda function to grow a file system programmatically.

## Key terms

- **FSx for Windows File Server** — fully managed Windows file
  server with SMB, NTFS, and AD integration.
- **Storage capacity** — the *total* provisioned size of the file
  system, in GiB. Range: 32 GiB – 65 536 GiB.
- **Throughput capacity** — the *baseline* disk throughput, in
  MB/s, provisioned independently of storage capacity. Tiers:
  8, 16, 32, 64, 128, 256, 512, 1024, 2048 MB/s.
- **Burst credits** — a throughput "buffer" for short spikes
  above the baseline. Earned when usage is below baseline; spent
  when usage exceeds it.
- **Single-AZ** — one file server in one AZ. Lower cost; an AZ
  issue means a brief outage.
- **Multi-AZ** — a **preferred** file server in one AZ and a
  **standby** file server in another AZ, with synchronous
  replication. The "FCI cluster" deployment.
- **FCI (File Server Cluster Instance)** — the multi-node Windows
  file-server cluster pattern this section targets. In FSx this
  *is* a Multi-AZ deployment; AWS does not expose individual
  cluster nodes.
- **SMB** — Server Message Block, the file-sharing protocol. FSx
  supports SMB 2.x and 3.x; you can opt in to SMB 3.0 multichannel
  for higher single-client throughput.
- **NTFS** — New Technology File System, the Windows file-system
  format. FSx supports NTFS ACLs end-to-end, including on
  on-premises clients connected over a trust.
- **DFS** — Distributed File System, the Windows namespace
  service. Optional in FSx; you can host a DFS namespace on a
  Windows EC2 instance that points at the FSx share.
- **Storage tier** — `Standard` (HDD-backed, cheaper) or
  `High-Performance` (SSD-backed, faster). Storage tier is part
  of the file system's CloudWatch dimensions.
- **`StorageCapacity`** — the control-plane field returned by
  `fsx.describe_file_systems`. Always in GiB. This is what the
  monitor Lambda compares to the threshold.
- **`FreeStorageCapacity`** — the CloudWatch metric on
  `AWS/FSx`. The number of bytes of *free* space currently
  available. Drives the CloudWatch alarm.

## What FSx for Windows is

FSx for Windows File Server is a fully managed file server that
exposes SMB shares to Windows, macOS (with SMB 3), and Linux
clients. AWS runs the file servers for you, manages replication
(in Multi-AZ mode), patches Windows, takes daily backups, and
integrates with AWS Managed Microsoft AD for authentication and
NTFS ACLs.

The simplest mental model: *"a Windows file server in the cloud,
minus the licence and the patching."* The price-per-GB includes
the underlying disk, the Windows licence, and the FSx control
plane.

### What it is *not*

- It is **not** NFS or Linux-POSIX. For NFS, use FSx for Lustre
  or FSx for ONTAP (the latter is dual-protocol).
- It is **not** an object store. For S3-style flat-namespace
  storage of unstructured files, use S3. (FSx is hierarchical:
  files in directories, with NTFS ACLs, exactly like a file server.)
- It is **not** a database. For SQL Server on a managed file
  system, the SQL Server workbooks are a different conversation.

## The three knobs you have to set

When you create an FSx for Windows file system you pick three
values, and they are independent of each other:

### 1. Storage capacity (`StorageCapacity`)

The total provisioned size in GiB. Range: 32 – 65 536 GiB. Pricing
is roughly $0.13/GB-month for SSD (this looks like the
2026 list price — verify in the FSx pricing page before quoting).

You can change the storage capacity *up* (grow) at any time
without downtime. You cannot shrink it. The minimum grow step is
**10 GiB**. The handler in L86 enforces both of these rules.

A sizing rule of thumb: peak file system utilisation should stay
below 80 % of `StorageCapacity`. If you regularly cross 80 %, you
should either grow the file system or move cold data to S3 +
Glacier.

### 2. Throughput capacity

The baseline disk throughput in MB/s. You pick from a list of
predefined tiers (8, 16, 32, 64, 128, 256, 512, 1024, 2048).
The relationship between storage capacity and throughput capacity
is **not** linear: the file system's *baseline* throughput is the
*tier* you pick, not a function of how many GiB you provisioned.

In addition to the baseline, FSx gives you **burst credits**. You
earn credits when your throughput is below baseline, and spend
them when it exceeds baseline. A typical pattern is a long quiet
period where you accrue credits, then a daily batch process that
spends them in a 30-minute spike. Burst headroom is generally
**3× the baseline** for SSD tier and **6×** for HDD tier, but the
exact formula is in the FSx user guide.

If your workload is **consistently** above baseline (e.g. a heavy
CAD workload that streams data all day), you need to *raise the
tier*, not rely on burst credits.

### 3. Deployment mode

- **Single-AZ 1.** Cheapest. One file server in one AZ. The
  underlying disk is replicated within the AZ, so you do not lose
  data on a single-disk failure, but if the AZ itself has an
  issue you are offline until the AZ recovers. Suitable for
  dev/test and non-critical workloads.
- **Single-AZ 2.** A newer single-AZ variant with a different
  replication factor. Same availability profile as Single-AZ 1.
- **Multi-AZ.** A **preferred** file server in one AZ and a
  **standby** file server in another AZ, with synchronous
  replication. AWS fails over automatically; SMB clients
  reconnect to the new preferred file server transparently.
  This is the **FCI cluster** deployment and is what section 15
  assumes.

The pricing difference between Single-AZ 1 and Multi-AZ is
roughly 2× on the storage and throughput rates. For production
workloads where the file system is on the critical path, the
extra cost is almost always worth it.

## How the FCI concept maps to FSx

In a traditional on-premises FCI cluster, two Windows file
servers share an underlying disk (a SAN LUN), coordinate via the
Windows Failover Clustering service, and present a single SMB
namespace to clients. The *Cluster Instance* is the abstraction
of "the file server", and individual nodes are interchangeable.

In FSx for Windows Multi-AZ, AWS runs the cluster for you. The
`FileSystemId` (`fs-0123456789abcdef0`) is the cluster; you do
not address individual file servers. The DNS name
`fs-0123456789abcdef0.corp.example.com` resolves to whichever
file server is currently the *preferred* node. AWS manages the
failover; SMB clients see a brief reconnect, not an outage.

For the **monitoring** system in section 15, none of this
matters beyond: there is one `FileSystemId` and one DNS name,
regardless of which AZ is currently serving. You `describe_file_systems`
once and get back the *cluster's* `StorageCapacity`.

## CloudWatch metrics for FSx

FSx publishes a rich set of metrics to CloudWatch under the
`AWS/FSx` namespace. The ones relevant to this section are:

| Metric | Meaning | Dimension |
|---|---|---|
| `FreeStorageCapacity` | Bytes of free space currently available. | `FileSystemId`, `StorageTier` |
| `StorageCapacityUtilization` | Percent of storage used. | `FileSystemId`, `StorageTier` |
| `DataReadBytes` / `DataWriteBytes` | Throughput, in bytes/min. | `FileSystemId`, `StorageTier` |
| `DataReadOperations` / `DataWriteOperations` | IOPS, in operations/min. | `FileSystemId`, `StorageTier` |
| `FileServerCapacityUtilization` | Percent of *throughput* capacity in use (baseline + burst). | `FileSystemId`, `StorageTier` |
| `ClientConnections` | Number of active SMB sessions. | `FileSystemId`, `StorageTier` |
| `TotalIOBytes` | Combined read + write throughput. | `FileSystemId`, `StorageTier` |

The first one — `FreeStorageCapacity` — is what the CloudWatch
alarm in L87 watches. The alarm transitions to `IN_ALARM` when
the metric is below `THRESHOLD_GB` GiB (converted to bytes in the
template).

### Why two notions of "capacity"?

A subtle thing: there are *three* notions of capacity in this
system and you need to keep them straight:

- `StorageCapacity` (control plane, GiB) — the file system's
  provisioned size. The monitor Lambda reads this from
  `fsx.describe_file_systems` and compares to `THRESHOLD_GB`.
- `FreeStorageCapacity` (metric, bytes) — the file system's
  *free* space right now. Drives the CloudWatch alarm.
- `ThresholdGb` (parameter, GiB) — the threshold the operator
  chose. Used by the alarm and by the Lambda.

In a healthy system `FreeStorageCapacity` (bytes) ≈
`StorageCapacity` (GiB × GiB-to-byte) — `UsedBytes`. When
`FreeStorageCapacity` drops below the threshold *and*
`StorageCapacity` is still well above the threshold, the file
system is being filled faster than expected. When `StorageCapacity`
itself is below the threshold, the file system has not been
grown recently and is dangerously close to its provisioned size.

The monitor Lambda reads `StorageCapacity` because we want to
*grow the file system*, and `update_file_system` takes a GiB
target. The CloudWatch alarm reads `FreeStorageCapacity` because
we want to *page ops on a metric*, and CloudWatch works in the
metric's native units.

## Programmatic access: boto3

The two FSx API calls we use in section 15:

```python
import boto3

fsx = boto3.client("fsx", region_name="us-east-1")

resp = fsx.describe_file_systems(FileSystemIds=["fs-0123456789abcdef0"])
fs = resp["FileSystems"][0]
current_gb = fs["StorageCapacity"]      # GiB, always
lifecycle = fs["Lifecycle"]             # AVAILABLE, CREATING, UPDATING, ...

fsx.update_file_system(
    FileSystemId="fs-0123456789abcdef0",
    StorageCapacity=200,                # new total GiB
)
```

Things to know:

- `describe_file_systems` is **idempotent** and side-effect-free.
  You can call it as often as you want; there is no rate limit
  worth caring about for a single file system.
- `update_file_system` is **asynchronous**. The response returns
  the new state immediately, but the actual grow can take minutes.
  During the grow the file system's `Lifecycle` is `UPDATING`.
- The **minimum grow step is 10 GiB**; the handler rounds up.
- You **cannot shrink** a file system via `update_file_system`.
  Only growth is supported through the API.
- You **can grow concurrently**: if you call `update_file_system`
  while the file system is `UPDATING`, the second call is queued
  and applied after the first. We guard against this with the
  cooldown.
- `update_file_system` also accepts `WindowsConfiguration` for
  changing things like the throughput capacity and the daily
  backup window; the section-15 handler does not use them.

## Sizing example for the section-15 use case

The plant's CAD workload has these observed characteristics:

- 1.5 TiB total data at go-live, growing ~30 GiB/day.
- A 4-hour nightly batch that writes ~30 GiB (so the daily grow).
- ~200 concurrent design-engineer sessions during the workday.

Choose:

- `StorageCapacity`: 2 TiB (2 048 GiB) at go-live. Provides ~12
  months of runway at 30 GiB/day before growth is required;
  comfortably above the 100 GiB `THRESHOLD_GB`.
- `ThroughputCapacity`: 128 MB/s baseline. The 4-hour nightly
  batch needs ~2.1 MB/s of *sustained* throughput, well within
  baseline; peak hourly reads by 200 designers are also well
  below baseline.
- Deployment mode: **Multi-AZ**, because the file system is on
  the production critical path.
- Backup retention: **2 weeks** of daily backups (the FSx
  default) — covers the user-error cases (accidentally deleted a
  folder) that backups are good for.

When the file system reaches the 80 % utilisation mark — ~1.6
TiB used — the monitor Lambda grows it by 20 % (50 % headroom
on the current used). Two such grows cover the next six months.
This is exactly the loop L86 implements.

## Hands-on preview

You do not need to provision FSx to read this lecture. Two things
you can do right now:

1. **Read the IAM policy** at `code/monitor_lambda/iam_policy.json`
   and notice the `fsx:DescribeFileSystems` and
   `fsx:UpdateFileSystem` actions, scoped to a single file
   system ARN.
2. **Run the test suite** to confirm the test for the
   below-threshold grow path passes:

   ```bash
   cd code/monitor_lambda
   pytest -v
   ```

The handler itself, which ties `StorageCapacity` to the grow
decision, is L86. The CloudWatch alarm and the wiring are L87.

## Quiz prep

You should now be able to answer:

- What is the relationship between `StorageCapacity`,
  `FreeStorageCapacity`, and `ThresholdGb`?
- Why is the **storage** tier priced separately from the
  **throughput** tier in FSx?
- What is the difference between Single-AZ 1, Single-AZ 2, and
  Multi-AZ deployments, and which is the "FCI cluster" mode?
- What is the minimum grow step on `update_file_system`, and why
  does the handler round up to it?
- Why does the monitor Lambda use the control-plane
  `StorageCapacity` rather than the CloudWatch
  `FreeStorageCapacity` metric for its grow decision?

## Further reading

- AWS docs: [What is Amazon FSx for Windows File Server?](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/what-is.html)
- AWS docs: [FSx for Windows performance](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/performance.html)
- AWS docs: [Monitoring FSx metrics in CloudWatch](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/monitoring-cloudwatch.html)
- AWS docs: [Updating an FSx for Windows file system](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/managing-file-systems.html)
- AWS docs: [Multi-AZ file systems](https://docs.aws.amazon.com/fsx/latest/WindowsGuide/high-availability-multi-az.html)
- AWS docs: [FSx for Windows pricing](https://aws.amazon.com/fsx/windows/pricing/)
- L86 — the monitor Lambda
- L87 — the wiring