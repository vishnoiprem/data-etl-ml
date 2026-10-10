# L11 — Choosing an Instance Type

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 03
> **Duration target:** 10:00
> **Lecture ID:** L11

## Status

Authored.

## Prereqs

- L07 (EC2 Instance Types) — instance families, sizes, use cases.
- L09 (the wizard) — Step 3 is "Instance Type".

## Key terms

- **Instance family** — the first letter of the instance type
  encodes the family (`t`, `m`, `c`, `r`, `x`, `p`, `g`, `i`, `d`,
  `h`). Each family optimizes for a different axis (burstable,
  general, compute, memory, memory-optimized, etc.).
- **Instance size** — after the family letter, the rest of the
  name encodes size: `nano < micro < small < medium < large <
  xlarge < 2xlarge < 4xlarge < ... < metal`.
- **vCPU** — the number of virtual CPUs the instance gets. Roughly
  one vCPU per physical core, but burstable types (T family) earn
  CPU credits when idle and spend them when busy.
- **Right-sizing** — choosing the cheapest instance type that meets
  your workload's CPU, memory, network, and storage needs.
- **EBS-optimized** — by default, instance types attach EBS
  volumes with no throughput guarantee. Enabling "EBS-optimized"
  (free for most modern types) gives you a dedicated bandwidth
  budget between the instance and its EBS volumes.
- **ENA / EFA** — Enhanced Networking (ENA) is the standard
  10–100 Gbps networking stack on most modern types. EFA (Elastic
  Fabric Adapter) adds OS-bypass for HPC and tightly-coupled ML.

## Lecture

Step 3 of the wizard asks you to pick the **hardware shape** of your
instance. The shape is encoded in the type string: a family letter,
a generation number, and a size suffix. For example `t3.micro` is
the **T** family, **3rd generation**, **micro** size.

### The instance type matrix

The instance catalog is huge, but the **families you'll meet 90% of
the time** are these:

| Family | Optimized for | Example | When to pick it |
|---|---|---|---|
| `t3` / `t4g` | Burstable general purpose | `t3.micro` | Free tier, dev/test, low-traffic web servers. The default starting point. |
| `m5` / `m6i` / `m6g` | General purpose | `m5.large` | Balanced CPU + memory. The safe default for most production workloads. |
| `c5` / `c6i` / `c6g` | Compute-optimized | `c5.xlarge` | CPU-bound workloads: batch processing, gaming servers, scientific modeling. |
| `r5` / `r6i` / `r6g` | Memory-optimized | `r5.2xlarge` | Memory-bound workloads: in-memory caches (Redis/Memcached), large heaps, in-memory analytics. |
| `x1` / `x2` | Memory-optimized (very large) | `x2idn.16xlarge` | SAP HANA, real-time analytics on huge data sets. |
| `p4` / `p5` | GPU (training) | `p4d.24xlarge` | Distributed deep-learning training. |
| `g4` / `g5` | GPU (inference + graphics) | `g5.xlarge` | Real-time inference, remote graphics, video transcoding. |
| `i3` / `i4i` | Storage-optimized (local NVMe) | `i3.large` | High IOPS at low latency: databases, search. |
| `d` (Dense) | Storage-dense HDD | `d2.xlarge` | Hadoop, log processing, large sequential reads/writes. |
| `h` (High Perf) | HPC | `hpc6id.32xlarge` | Tightly-coupled HPC, weather simulation. |

The pattern: the family letter tells you the **shape** of the
hardware. The generation number (3, 4, 5, 6, …) tells you roughly
how new the silicon is — newer generations are usually faster per
dollar. The size tells you the **scale** (1, 2, 4, 8, 16, 24
vCPUs).

### The right-sizing mindset

"Right-sizing" means: **don't pick the biggest type you can afford;
pick the cheapest type that meets your workload.**

A useful 4-step loop:

1. **Start small.** Default to `t3.micro` for dev/test, `m5.large`
   for production. The boto3 `ModifyInstanceAttribute` API lets you
   resize later, but only within the same family / architecture.
2. **Measure.** Use CloudWatch's `CPUUtilization` and memory
   metrics. (You'll need the CloudWatch agent for memory on Linux.)
3. **Pick the family that matches the bottleneck.** CPU-bound →
   C family. Memory-bound → R family. Bursty traffic → T family.
4. **Move up a size in the same family** if you need more capacity
   without changing the family. Move to a new family only if the
   **shape** of the workload has changed.

### What "burstable" actually means

T-family instances earn **CPU credits** when they're below baseline
utilization and spend them when they burst above baseline. A
`t3.micro` earns credits indefinitely and can spend them in short
spikes. If you run flat-out at 100% CPU, the credit balance empties
and the instance is throttled back to 20% of one vCPU — at which
point you should move to an M-family instance.

### vCPUs, memory, and network

Each instance type has a published spec sheet:

```text
t3.micro
  vCPU: 2
  Memory: 1 GiB
  Network: Up to 5 Gbps
  EBS-optimized:  (free for t3)
  Baseline CPU: 20%
  CPU credits earned / hour: 6
  CPU credit balance: 144
```

The AWS console shows this card as you click through instance
sizes. The boto3 equivalent is
`ec2.describe_instance_types(InstanceTypes=["t3.micro"])`.

### Naming conventions: when you see `c6i.large`

`c` — compute-optimized family.
`6` — sixth generation.
`i` — Intel Xeon CPU variant.
`large` — size.

Other suffixes you'll see: `a` (AMD), `g` (Graviton / ARM), `n`
(networking-optimized), `d` (with local NVMe), `e` (extra memory
or extra storage variant).

### Common mistakes

1. **Picking the largest type on day one** "just in case". You'll
   pay for capacity you don't use. Right-size at the start and
   resize as you measure.
2. **Picking a T-family for steady-state high-CPU** workloads. The
   CPU credit system throttles you. Move to M or C family.
3. **Mixing instance families in an Auto Scaling group.** Always
   pick one family / size per ASG; mixing leads to uneven
   utilization and confusing CloudWatch metrics.

### What this course uses

For the boto3 demo in L18 we default to `t3.micro` because:

- it's free-tier eligible;
- the boto3 + moto tests don't care about the type's resources;
- the user can override it with `--instance-type` for any other
  type.

## Quiz prep

- What does the **first letter** of an instance type tell you?
  (The family — e.g. `t` for burstable, `m` for general, `c` for
  compute, `r` for memory.)
- What does it mean for an instance to be "burstable"? (It earns
  CPU credits when idle and spends them when busy, allowing short
  spikes above baseline.)
- What's the typical default instance type for new AWS accounts?
  (`t3.micro` or `t2.micro`, free-tier eligible.)
- Name one reason to pick a C-family instance over an M-family
  instance. (CPU-bound workload — you need more compute per dollar
  and less memory.)

## Further reading

- AWS docs: *Instance types* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html>
- AWS docs: *Burstable performance instances* — <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html>
- AWS Instance Type finder (internal link) — <https://aws.amazon.com/ec2/instance-explorer/>
