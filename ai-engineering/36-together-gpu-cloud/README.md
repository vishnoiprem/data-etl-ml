# Together-style GPU cloud + inference autoscaler

Bare-metal GPU access plus a serverless inference layer on top, with a queue-depth-driven autoscaler that fills H100s to 80%+ utilization while keeping tail latency under 200ms. The two signals (queue depth + p99 latency) need to be combined — queue alone over-provisions, latency alone under-provisions.

## Shape

```
   Requests ──► queue ──► GPUs (pool)
                          │  observed: utilization, p99 latency
                          ▼
                       tick()
                          │
            ┌─────────────┴──────────────┐
            ▼                            ▼
       scale_up (queue high        scale_down (util low
        OR p99 > budget)            AND gpus > 1)
            │                            │
            └──────────┬─────────────────┘
                       ▼
                  next tick
```

## What I built

- `sched/autoscale.py` — `GPU` (active, in_flight, served, utilization) + `Request` + `GPUScheduler`.
- `tick()` simulates one round: complete N requests, record latencies, then decide scale_up / scale_down / noop.
- Scale-up triggers on either: `utilization > 0.9` OR `p99 > budget` AND `len(gpus) < max_gpus`.
- Scale-down triggers on: `utilization < 0.4` AND `len(gpus) > 1`.
- Smoke test: enqueue 200 requests (burst), tick 5 times with growing latency (forces scale-up), then tick 5 with low latency (forces scale-down).

## Real numbers

- Target utilization: 75-85% sweet spot. Below 60% is wasted spend; above 90% is queue risk.
- p99 latency budget: 200ms for chat, 500ms for batch, 50ms for inline (Copilot-style).
- Scale-up cooldown: 30-60s (don't churn GPUs on a transient burst).
- Scale-down cooldown: 5-15 minutes (avoid thrash on a quiet period that resumes).
- H100 80GB spot price: $2-4/hr. Cold-start cost: 60-90s to load a 70B model.

## What I learned the hard way

- **Cooldowns are non-optional.** Without them, a 5-second burst of 1000 requests scales you to 16 GPUs and then immediately scales back down — wasted provisioning.
- **Two signals beat one.** Queue alone is laggy (you only see the queue after requests pile up). Latency alone is reactive (p99 is high means users already suffered). Combine them.
- **Cold-start is the real cost.** A GPU that takes 90s to load a 70B model is not a "scale-up" — it's a "we missed the SLA." Pre-warm or use smaller models for the burst.
- **Per-tenant fairness beats raw utilization.** One tenant can dominate the queue and starve everyone else. A fair scheduler caps per-tenant in-flight + uses a deficit round-robin.

## When to use

- Multi-tenant inference serving (cost + SLA).
- Bursty workloads (chat, search, code completion).
- You have a model warm-pool strategy (so cold-start is acceptable).

## When NOT to use

- Single-tenant, steady-state load (just size the pool once).
- Latency budgets under 50ms (cold-start is too slow; need a pre-warmed pool).
- Models that take > 5 minutes to load (cold-start is unacceptable).

## Run

```bash
pip install -r requirements.txt
make smoke
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
