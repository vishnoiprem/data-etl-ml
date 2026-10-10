# 46. Lambda Labs (Lambda)

- **Role:** ML Infrastructure Engineer / Cloud Engineer / SRE
- **Tech stack:** Python, Go, Kubernetes, Slurm, CUDA, NCCL, InfiniBand, Onyx, RDMA, Ansible, Terraform, Prometheus, Grafana
- **Comp band:** $200K-$400K (well-funded, hyperscaler-style infra)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + infra | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, infra, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Tell me about your experience with large-scale GPU clusters"
**Answer:** Lead with concrete numbers: number of GPUs, interconnects (NVLink/IB), training framework, failure modes you handled. Lambda is building hyperscaler-grade GPU infra — they want operators, not just users.
**Tip:** Mention specific tooling: Slurm, K8s, NVIDIA DCGM, NCCL debugging, etc.

### Q1.2: "Why Lambda?"
**Answer:** Three-bet: (1) Lambda Cloud's reserved-instance model is the cheapest in the market for serious training (H100, H200, B200), (2) Lambda's engineering culture is hyperscaler-style (Stephan Qin, ex-Datadog, ex-AWS), (3) the LLM training products (Lambda Chat, vector DB) are an underrated growth bet.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Build a job scheduler for a GPU cluster"
**Answer:**
```python
import heapq
class ClusterScheduler:
    def __init__(self, total_gpus):
        self.total = total_gpus
        self.free = total_gpus
        self.queue = []
        self.id = 0
    def submit(self, job, gpus, priority=0):
        heapq.heappush(self.queue, (-priority, self.id, gpus, job))
        self.id += 1
    def tick(self):
        scheduled = []
        new_queue = []
        for prio, id, gpus, job in self.queue:
            if gpus <= self.free:
                self.free -= gpus
                scheduled.append(job)
            else:
                new_queue.append((prio, id, gpus, job))
        self.queue = new_queue
        return scheduled
```
**Tip:** Discuss bin-packing, multi-tenant fairness, queue priorities, and preemption.

### Q2.2: Systems — "How do you monitor GPU health in a 1000-GPU cluster?"
**Answer:** Three layers: (1) **hardware** — IPMI, BMC, NVLink/IB counters, DCGM exporter, (2) **software** — NCCL debug logs, training job metrics (loss, grad norm, throughput), (3) **alerting** — anomaly detection on utilization/temp/power, PagerDuty escalation.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a circuit breaker (very common in cloud infra).
- **Q3.1.2:** Build a simple LRU/LFU cache.
- **Q3.1.3:** Write a K-way merge (relevant to log aggregators).

### Round 3.2: System design
- **Q3.2.1:** "Design Lambda's GPU cloud control plane." Discuss: API gateway, scheduler (gang scheduling, topology-aware placement), provisioning, billing, observability.
- **Q3.2.2:** "Design a multi-tenant LLM training cluster." Talk: reservation system, preemption, queue priorities, RDMA/IB fabric, NVLink domains, NCCL topology, automatic failure recovery.

### Round 3.3: Infra / ML deep-dive
- **Q3.3.1:** "Walk me through how you'd debug a 1000-GPU training run that's 5x slower than expected." Talk: NCCL all-reduce bottlenecks, IB congestion, GPU thermal throttling, straggler nodes, dataloader stalls.
- **Q3.3.2:** "How would you set up a Slurm + K8s hybrid cluster for ML?" Discuss: when to use which, gang scheduling, K8s-on-Slurm, NFS/Lustre/WekaFS for shared storage.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a production incident you owned. What was the timeline?"
- **Q3.4.2:** "Why infra? What keeps you up at night about a GPU cluster?"

## Stage 4: Hiring committee
Lambda is bigger and more structured than RunPod. The committee is more like a big-tech loop review. They look for: deep infra experience (especially distributed systems + GPU), coding fluency, and operator mindset. Red flags: never having used a real cluster, weak on networking.

## Stage 5: Offer
Base is competitive ($200K-$300K for senior eng), equity is moderate (private, well-funded). Negotiation: title, sign-on, and equity refreshers.

## Tips for the Lambda loop
1. **Brute-force GPU networking knowledge** — IB, RDMA, NCCL, NVLink, RoCE.
2. **Practice the Slurm + K8s question** — Lambda uses both.
3. **Know DCGM, Prometheus, Grafana, Loki** — their observability stack.
4. **Have opinions on training infra**: FSDP vs DDP vs DeepSpeed, NVLink vs IB, etc.
5. **Read the Lambda blog and engineering posts** — they publish architecture deep dives.
6. **Be ready for a "design the control plane" round** — it's almost always asked.
7. **Show you've actually used Lambda Cloud or a competitor** (RunPod, CoreWeave, Vast).

## Real candidate report
> "Two phone screens — one coding (K-way merge + LRU), one systems (design a Slurm cluster for 1000 GPUs). Onsite was 4 rounds. The system design round was the toughest — they wanted me to design the full hyperscaler control plane in 45 minutes. Offer: $250K base, $50K sign-on, equity." — Levels.fyi, 2025

## Sources
- [Lambda careers](https://lambda.ai/careers)
- [Lambda engineering blog](https://lambda.ai/blog)
- [Lambda Cloud docs](https://docs.lambda.ai)
- [Lambda Glassdoor](https://www.glassdoor.com/Interview/Lambda-Labs-Interview-Questions-E2721130.htm)
- [Levels.fyi Lambda](https://www.levels.fyi/companies/lambda-labs)
