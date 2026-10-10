---
title: L50 — Lambda Limits — Memory
author: Prem Vishnoi <prem.vishnoi@example.com>
section: 11
duration: 4:22
---

# L50 — Lambda Limits — Memory

> Memory is the only knob you turn on a Lambda function. Behind it
> sit proportional CPU, network bandwidth, and ephemeral disk size.
> Picking the right memory setting is the cheapest performance
> optimization you can make.

## Prereqs

- L48 (concurrency).

## Key terms

- **Memory** — RAM available to your function, 128 MB – 10,240 MB
  (10 GB) in 1-MB increments.
- **vCPU** — proportional allocation. 1,769 MB ≈ 0.5 vCPU; 10,240
  MB ≈ 6 vCPU. Lambda *never* exposes this number directly.
- **Ephemeral disk** — `/tmp` scratch space, 512 MB – 10,240 MB,
  scaling with memory.
- **`/tmp`** — the *only* writable filesystem at runtime.

## 1. The memory ↔ CPU ↔ disk ↔ network relationship

Lambda does not let you set CPU directly. Memory is the surrogate:

| Memory (MB) | Approx. vCPU | Network (Gbps) | `/tmp` (MB) |
|---|---|---|---|
| 128 | 0.04 | ~0.07 | 512 |
| 512 | 0.16 | ~0.25 | 512 |
| 1,769 | 0.5 | ~0.85 | 1,512 |
| 3,008 | 1.0 | ~1.5 | 2,752 |
| 5,120 | 1.6 | ~2.5 | 4,864 |
| 10,240 | 6.0 | ~5.0 | 10,240 |

> The relationship is *linear*. Doubling memory roughly doubles
> CPU, disk ceiling, and network. There is no separate CPU-bound
> limit to optimize against.

## 2. Why more memory can be *cheaper*

This is counterintuitive, but real:

1. More memory ↔ more CPU ↔ faster execution.
2. Lambda's billing model is **GB-seconds**: `(memory_mb / 1024) *
   duration_s`.
3. If your function is CPU-bound (e.g. JSON parsing, image resize), a
   2× memory bump can cut duration by more than 2× — net cheaper bill
   and faster response.

The "find the right memory" exercise is:

```bash
# Use AWS Lambda Power Tuning (open-source)
git clone https://github.com/alexcasalboni/aws-lambda-power-tuning
cd aws-lambda-power-tuning
./pwt.sh --lambdaPowerValues 128,512,1024,2048,3008 \
         --resourceId my-function --region us-east-1
```

It runs each memory size against your real payload, plots
cost/performance, and prints a recommendation.

## 3. Hard limits

| Resource | Limit |
|---|---|
| Memory | 128 MB – 10,240 MB |
| Disk (`/tmp`) | 512 MB – 10,240 MB |
| Timeout | 1 s – 900 s (15 minutes) |
| Payload (sync invoke) | 6 MB request / 6 MB response |
| Payload (async) | 256 KB |
| Environment variables | 4 KB total |
| Layers | 5 layers, 250 MB unzipped total |
| Deployment package (zipped) | 50 MB direct / 250 MB with layers |
| Container image | up to 10 GB |

## 4. boto3 — change memory at runtime

```python
import boto3
lam = boto3.client("lambda", region_name="us-east-1")
lam.update_function_configuration(
    FunctionName="my-worker",
    MemorySize=2048,                      # MB
)
```

You can also use `publish_version` after to make the new memory
"stick" as a version (L57).

## 5. Pitfalls

- **`/tmp` is per-instance, ephemeral.** Two invocations on the same
  warm instance see each other's leftover files if you do not clean
  up. Don't `os.chdir("/tmp")` and forget where you are.
- **Memory pressure crashes are silent.** OOM is shown in CloudWatch
  as a `Runtime.ExitCode 137` — easy to mistake for an unhandled
  exception. Always log memory spikes:

```python
import psutil, os
def handler(event, context):
    p = psutil.Process(os.getpid())
    print(f"mem_before={p.memory_info().rss/1024/1024:.1f}MB")
    ...
```

## Lecture summary

- Memory is the master knob: it controls CPU, disk, and network.
- The range is 128 MB – 10,240 MB.
- More memory often *lowers* cost for CPU-bound work — use the
  Power Tuning tool to find the sweet spot.

## Hands-on (≈ 3 minutes)

```bash
# Power-tune a function across 6 memory sizes
python 11_lambda_advanced_concepts/code/power_tune.py \
    --function my-worker --values 128,512,1024,2048,3008,4096
```

## Quiz prep

- What is the minimum and maximum memory you can set?
- Why might doubling memory *reduce* cost?
- What's the maximum size of `/tmp`?

## Further reading

- AWS — [Lambda configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html)
- alexcasalboni — [aws-lambda-power-tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
