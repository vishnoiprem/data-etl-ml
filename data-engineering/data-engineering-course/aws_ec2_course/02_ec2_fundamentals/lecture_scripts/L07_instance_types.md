# L07 — EC2 Instance Types (families, sizes, use cases)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 02
> **Duration target:** 12:00
> **Lecture ID:** L07

## Status

Authored.

## Prereqs

- L04 (VMs and hypervisors).
- L05 (EC2 is IaaS — you choose the size).
- L06 (regions and AZs).

## Key terms

- **Instance type** — a fixed combination of vCPU count, memory,
  storage, and network performance that you rent by the hour or
  second. The `t3.micro` you launch at 09:00 is a different
  physical configuration from the `c5.xlarge` your teammate
  launches at 09:01.
- **Instance family** — a group of instance types optimized for a
  particular ratio of resources. Five families matter in this
  course: **general purpose** (M, T), **compute optimized** (C),
  **memory optimized** (R, X), **storage optimized** (I, D), and
  **accelerated computing** (P, G, F, Inf).
- **Generation** — a major hardware revision. `c5` is the 5th
  generation of the C family; `c6i` is the 6th generation (Intel);
  `c7g` is the 7th generation (AWS Graviton, ARM-based). Newer
  generations are typically faster and cheaper per unit of work
  than older ones.
- **Size** — within a family and generation, a small/medium/large
  ladder: `nano`, `micro`, `small`, `medium`, `large`, `xlarge`,
  `2xlarge`, `4xlarge`, ... `24xlarge` (or further, depending on
  the family). Each step up roughly doubles the vCPUs and memory.
- **vCPU** — a virtual CPU. On most EC2 instances, one vCPU equals
  one hardware thread (so a 4-vCPU instance is consuming 4
  hyperthreads of the underlying physical core).
- **EBS-optimized** — the default on most modern instance types.
  Means the network path between the instance and its EBS volume
  is dedicated and does not compete with general network traffic.
- **ENA (Elastic Network Adapter)** — the high-performance
  network interface used by most modern instance types. Supports
  up to 100 Gbps on the largest sizes.

## Lecture

EC2 is not one product — it is roughly 600 products, each a
slightly different combination of CPU, memory, storage, and
network. AWS calls each combination an **instance type**, and the
catalog of instance types is organized into **families** and
**generations** and **sizes**. Once you can read the catalog like
a table, picking the right instance for a workload becomes
mechanical.

The naming convention is the first thing to memorize. An instance
type is a string like `c5.xlarge`. Three parts:

- **Family letter(s)** — the first 1–2 characters identify the
  family. `c` = compute optimized, `m` = general purpose, `r` =
  memory optimized, `t` = burstable general purpose, `i` = storage
  optimized (HDD-backed), `d` = storage optimized (dense), `p` =
  accelerated (GPU, training), `g` = accelerated (GPU, graphics),
  `f` = accelerated (FPGA, increasingly rare), `inf` = AWS
  Inferentia (ML inference), `x` = memory optimized (extreme
  memory).
- **Generation number** — a single digit right after the family
  letter. `c5` is the 5th generation of the C family, `c6i` is
  the 6th (Intel), `c7g` is the 7th (Graviton3, ARM-based). Newer
  generations are almost always better than older ones at the
  same price.
- **Size** — after the dot. `nano`, `micro`, `small`, `medium`,
  `large`, `xlarge`, `2xlarge`, `4xlarge`, `8xlarge`,
  `12xlarge`, `16xlarge`, `24xlarge`, `32xlarge`, `48xlarge`,
  and a few exotic sizes for the largest types. Each step up
  roughly doubles the vCPUs and the memory and increases the
  network bandwidth.

So `c5.xlarge` reads as: "compute-optimized, 5th generation,
xlarge size" — which means 4 vCPUs and 8 GiB of RAM. The `c5.24xlarge`
at the top of the same family is 96 vCPUs and 192 GiB of RAM.
Same family, same generation, twenty-four times the size.

The **five families that matter for this course** are:

1. **General purpose (M, T).** Balanced CPU and memory, the
   default choice when you do not know what to pick. The **M
   family** (e.g., `m5.large`, `m6i.xlarge`) gives you a fixed
   baseline of CPU. The **T family** (e.g., `t3.micro`,
   `t4g.small`) is **burstable**: you get a small CPU baseline
   plus a CPU credit bank that fills up when you are idle and
   drains when you burst above the baseline. T instances are
   cheap and great for dev environments, low-traffic web servers,
   and any workload that is mostly idle with occasional spikes.
   They are a *bad* fit for sustained high-CPU work — you will
   run out of credits and the instance will throttle to the
   baseline.
2. **Compute optimized (C).** High vCPU-to-memory ratio. Good for
   CPU-bound workloads: batch processing, scientific modeling,
   game servers, video transcoding, and most importantly for
   this course, the front-end tier of a high-traffic web
   application. `c6i.large` is 2 vCPUs / 4 GiB; `c6i.24xlarge`
   is 96 vCPUs / 192 GiB.
3. **Memory optimized (R, X).** High memory-to-vCPU ratio. Good
   for in-memory databases (Redis, Memcached), real-time big-data
   analytics, and any workload that needs to hold a large
   working set in RAM. The R family (`r6i`, `r7g`) tops out
   around 1 TiB of RAM; the X family (`x2idn`, `x2iedn`) tops
   out around 4 TiB.
4. **Storage optimized (I, D).** High disk throughput and IOPS,
   with local NVMe SSD attached. Good for NoSQL databases
   (Cassandra, MongoDB), data warehousing, and log processing.
   The I family is balanced; the D family is *dense* (up to 48
   TB of local HDD per instance).
5. **Accelerated computing (P, G, Inf).** Hardware accelerators
   attached: GPUs (`p4d`, `g5`) for machine learning training
   and graphics, AWS Trainium (`trn1`) for ML training at
   scale, AWS Inferentia (`inf2`) for ML inference, FPGAs (`f1`,
   legacy). You will not launch these in this course, but you
   should know they exist for the day you need to train a model.

How do you pick? Three rules of thumb:

- **Start with T or M.** Default to `t3.medium` for small dev
  workloads and `m6i.large` or `m6i.xlarge` for production
  general-purpose workloads. Most apps are not CPU-bound or
  memory-bound; they are waiting on a database or a network
  call, and the difference between a C and an M does not
  matter.
- **Profile, then size up.** Launch a workload, watch CPU and
  memory utilization in CloudWatch, and resize based on what
  you see. Overprovisioning is fine for the first iteration;
  right-sizing is an optimization you do later.
- **Pick the newest generation you can.** `m6i` over `m5`,
  `c7g` over `c6i`, etc. — every generation is faster and
  cheaper per unit of work. The only reason to pick an older
  generation is that a specific instance size is not yet
  available in the new one, or you need an x86 architecture
  (Graviton/ARM is `g`-suffixed: `m6g`, `c7g`, `r7g`).

You can also mix families: a stateless web fleet on `c6i`,
caching layer on `r6i`, database on `r6i` or `x2idn`, ML
training on `p4d`. Each tier gets the family that matches its
bottleneck.

## Hands-on

Theory lecture, but do this:

1. In the EC2 console, go to **Instance Types** in the left
   nav. Filter by family (`General purpose`, `Compute
   optimized`, etc.) and skim the catalog. Notice the
   consistent shape: every family has the same size ladder,
   and you can read the vCPU/memory/network columns side by
   side.
2. In the EC2 launch wizard (you will not actually launch),
   pick `t3.micro` and then pick `c5.xlarge`. Look at the
   "Summary" panel on the right — the vCPU, memory, and
   network performance numbers update live.

In L11 we'll revisit this when we choose an instance type
for our first real launch.

## Quiz prep

- Decode `c5.xlarge`: what is the family, generation, and
  size? How many vCPUs and how much RAM does it have?
- What is the difference between the T family and the M
  family? When would T be a bad choice?
- List the five EC2 instance families and one workload each
  that is a good fit.
- Why is "pick the newest generation" almost always good
  advice?
- What is the difference between `c6i` and `c7g`? When would
  you pick one over the other?

## Further reading

- AWS: [Amazon EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- AWS: [Burstable Performance Instances](https://docs.aws.amazon.com/ec2/latest/instancelisting/instance-types.html#burstable)
- AWS: [AWS Graviton Processor](https://aws.amazon.com/ec2/graviton/)