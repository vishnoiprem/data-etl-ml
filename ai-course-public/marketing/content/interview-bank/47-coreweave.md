# 47. CoreWeave

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (e.g., a CoreWeave 25K-GPU cluster floorplan with rack rows, IB spines, and the CoreWeave blue/teal palette). Color: CoreWeave teal (#00D1B2 on near-black). Headline: "CoreWeave / AI Hyperscale GPU Engineer / 2026".

> **TL;DR:** CoreWeave runs one of the largest GPU clouds in the world (25K+ GPUs) and IPO'd in 2025; the loop is recruiter → 60-90 min systems phone → 4-5 round onsite (with a "build a hyperscaler control plane" round) → big-tech-style committee → offer, and the signature round is "deploy a 10K-GPU cluster from scratch." The winning candidate has read the S-1, masters the NVIDIA GPU operator, and can talk to OpenAI/Meta/NVIDIA-level customers as a peer.

```
Recruiter (50%) → Phone (35%) → Onsite (30%) → Committee (60%) → Offer
```

- **Role:** ML Infrastructure Engineer / Cloud SWE / SRE
- **Tech stack:** Kubernetes, Go, Python, NVIDIA GPU Operator, RDMA/InfiniBand, Arista switching, Terraform, Ansible, Prometheus, Grafana, Kafka, S3-compatible storage
- **Comp band:** $220K-$450K total comp (Senior SRE/ML Infra, staff+) | RSUs/equity 4-year vest (post-IPO)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + infra | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, infra, ML, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Cross-functional panel | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Tell me about your experience with hyperscale infrastructure"
**Answer:** CoreWeave runs one of the largest GPU clouds in the world (~25K+ GPUs). Highlight: distributed systems at scale, K8s at scale, networking (IB/RDMA), or production GPU clusters.
**Tip:** Even if you're from a non-infra background, frame projects where you built or operated something at scale.

### Q1.2: "Why CoreWeave?"
**Answer:** Three-bet: (1) CoreWeave is the most operationally mature GPU cloud (originally a crypto mining operator pivoted to AI — they understand hardware at a deep level), (2) they IPO'd in 2025 and are scaling fast, (3) their customers include the biggest AI labs (OpenAI, Meta, NVIDIA themselves).

## Stage 2: Technical phone screen

### Q2.1: Coding: "Build a job scheduler for a heterogeneous GPU cluster (mix of A100, H100, H200)"
**Answer:**
```python
import heapq
class HeteroScheduler:
    def __init__(self, gpus):
        # gpus: dict {gpu_type: count_free}
        self.gpus = gpus
        self.queue = []
        self.id = 0
    def submit(self, job, gpu_type, count):
        heapq.heappush(self.queue, (-job.priority, self.id, gpu_type, count, job))
        self.id += 1
    def tick(self):
        out = []
        remaining = []
        for prio, _, gtype, cnt, job in self.queue:
            if self.gpus.get(gtype, 0) >= cnt:
                self.gpus[gtype] -= cnt
                out.append(job)
            else:
                remaining.append((prio, _, gtype, cnt, job))
        self.queue = remaining
        return out
```
**Tip:** Discuss topology-aware placement (NVLink domains, IB fat-tree), bin-packing, and preemption.

### Q2.2: Infra: "How do you build a multi-tenant K8s cluster with GPU isolation?"
**Answer:** Three layers: (1) **hardware partitioning** — MIG, time-slicing, MPS, (2) **software isolation** — K8s namespaces, cgroups, network policies, (3) **policy** — quotas, priority classes, preemption. CoreWeave's K8s operator is the gold standard.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a rate limiter (token bucket).
- **Q3.1.2:** Build a small Raft-like consensus protocol (CoreWeave cares about consistency).
- **Q3.1.3:** Parse a YAML/Terraform config and validate it.

### Round 3.2: System design
- **Q3.2.1:** "Design CoreWeave's GPU cloud control plane." Talk: API gateway, scheduler (gang, topology-aware, bin-packing), observability, billing, multi-region.
- **Q3.2.2:** "Design a high-throughput, low-latency object store for ML workloads." Discuss: S3-compatible API, erasure coding, tiered storage, parallel uploads, RDMA transport for hot data.

### Round 3.3: Infra deep-dive
- **Q3.3.1:** "Walk through how you'd deploy a 10K-GPU cluster from scratch." Talk: physical layout (rack, power, cooling), network topology (fat-tree, IB), software stack (K8s, GPU operator, observability).
- **Q3.3.2:** "How do you handle a node failure during a 10K-GPU training run?" Discuss: failure detection, automatic restart, checkpointing, NCCL heartbeats, training resumption from checkpoint.

### Round 3.4: ML / GPU
- **Q3.4.1:** "How do you benchmark and optimize an LLM training run?" Talk: MFU, hardware FLOPs, dataloader, gradient accumulation, FSDP/ZeRO, FP8/INT8.
- **Q3.4.2:** "How would you set up an inference service for a 100B-param model on CoreWeave?" Discuss: vLLM, SGLang, prefix caching, continuous batching, KV cache memory.

### Round 3.5: Behavioral
- **Q3.5.1:** "Tell me about a time you owned a production outage. What did you do?"
- **Q3.5.2:** "Why CoreWeave over a hyperscaler?"

## Stage 4: Hiring committee
Structured like a public company now (post-IPO). The committee is more like big-tech. They look for: extreme infra depth, ability to operate at hyperscaler scale, and customer empathy (CoreWeave's customers are very technical — they need engineers who can talk shop). Post-IPO means committees are slower and more thorough, but the bar is also higher because comp is constrained by the public-company band.

## Stage 5: Offer
Base is at the high end ($250K-$350K for senior), equity is post-IPO (RSUs, 4-year vest), and CoreWeave offers significant sign-on to compete with hyperscalers. Negotiation: title and equity refreshers.

## Tips for the CoreWeave loop
1. **Master K8s + GPU operator** — CoreWeave's open-source K8s operator is the de facto standard.
2. **Brute-force networking** — IB, RDMA, RoCE, NVLink, fat-tree topology.
3. **Practice the "build a hyperscaler control plane" round** — almost always asked.
4. **Be ready to discuss training and inference workloads** in detail.
5. **Have a public OSS contribution or talk** — CoreWeave's team publishes.
6. **Show you've used CoreWeave or a competitor** — run a workload on it.
7. **Read CoreWeave's engineering blog and S-1** — the IPO filing is a goldmine.

## Real candidate report
> "Phone screen was a tough K8s + GPU scheduling design. Onsite had 5 rounds including a 'build a hyperscaler control plane' system design that took the full 60 minutes. The ML round asked me to optimize a 100B-param training run. Offer came in 6 days, $280K + 0.02% post-IPO RSU." — Levels.fyi, 2025

## Sources
- [CoreWeave careers](https://www.coreweave.com/careers)
- [CoreWeave engineering blog](https://www.coreweave.com/blog)
- [CoreWeave S-1 (IPO filing)](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001769628)
- [CoreWeave Glassdoor](https://www.glassdoor.com/Interview/CoreWeave-Interview-Questions-E3507800.htm)
- [Levels.fyi CoreWeave](https://www.levels.fyi/companies/coreweave)

---

## The 1 thing to remember

Read CoreWeave's S-1 filing and have an OSS PR to their K8s GPU operator before the onsite — the post-IPO committee filters for hyperscaler-grade depth, and the candidate who knows the operator internals beats the one who's just read the blog.
