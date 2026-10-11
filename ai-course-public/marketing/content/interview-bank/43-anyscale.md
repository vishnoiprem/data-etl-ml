# 43. Anyscale (Ray)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual (e.g., a Ray distributed graph with actor nodes, task arrows, and the Anyscale purple color). Color: Anyscale purple (#7C3AED). Headline: "Anyscale / AI Distributed Systems Engineer / 2026".

> **TL;DR:** Anyscale builds the productized Ray; the loop is recruiter → 90-min systems phone → 4-round onsite (with a Ray committer in the room) → committee → offer, and the signature round is "design Ray's autoscaler." The winning candidate has read the Ray paper, knows lineage reconstruction cold, and has shipped something on Ray or vLLM in public.

```
Recruiter (50%) → Phone (35%) → Onsite (30%) → Committee (60%) → Offer
```

- **Role:** Distributed Systems Engineer / ML Infrastructure Engineer
- **Tech stack:** Python, C++, Go, Ray, Kubernetes, gRPC, Pluggable Transport, KubeRay, PyTorch, vLLM, MLflow, Postgres, Redis
- **Comp band:** $220K-$450K total comp (E4-E6: SWE/ML Infra) | RSUs/equity 4-year vest
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min, focused on distributed systems background | 1 week | ~50% advance |
| 2. **Technical phone screen** | 90 min coding + systems | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Distributed systems design, coding, ML, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Cross-functional panel | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Tell me about a distributed system you built"
**Answer:** Lead with a system that handled real scale (10K+ QPS, TB-scale data, or 100+ node cluster). Explain the failure modes you'd seen and the design choices you'd make differently now.
**Tip:** Anyscale is built by the creators of Ray. They want people who think in actors, tasks, and object stores, not just REST.

### Q1.2: "Why Anyscale?"
**Answer:** Three-part: (1) Ray is the de facto standard for distributed Python ML, (2) Anyscale is the productized version (serverless Ray, observability, cost optimization), (3) the LLM serving story (Anyscale Endpoints / vLLM) is a real moat.

## Stage 2: Technical phone screen

### Q2.1: Coding: "Implement a task scheduler with priorities and retries"
**Answer:**
```python
import heapq, threading, time
class Scheduler:
    def __init__(self):
        self.q = []
        self.id = 0
        self.lock = threading.Lock()
    def submit(self, fn, priority=0, retries=0):
        with self.lock:
            heapq.heappush(self.q, (-priority, self.id, retries, fn))
            self.id += 1
    def run(self):
        while self.q:
            _, _, retries, fn = heapq.heappop(self.q)
            try: fn()
            except Exception as e:
                if retries > 0:
                    self.submit(fn, retries=retries-1)
```
**Tip:** Ray's task system does exactly this + lineage reconstruction. Mention Plasma object store, GCS, and worker pools.

### Q2.2: Systems: "How does Ray achieve fault tolerance?"
**Answer:** Three pillars: (1) **lineage reconstruction** — tasks re-execute if their object dependency is lost, (2) **actor restart** — actors restart with checkpoint/restore, (3) **placement group scheduling** — resources reserved for fault domains.
**Tip:** Discuss the tradeoff: eager re-execution (Ray's default) vs eager but expensive checkpointing (Spark).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement an in-memory key-value store with TTL and LRU eviction (very Ray-like).
- **Q3.1.2:** Build a basic MapReduce: `map(fn, items)` and `reduce(fn, mapped)` over a distributed cluster.
- **Q3.1.3:** Write a Ray actor that maintains state and supports concurrent calls with futures.

### Round 3.2: System design (distributed systems heavy)
- **Q3.2.1:** "Design Ray's autoscaler." Discuss: head node vs worker nodes, idle node termination, bin-packing, heterogeneous hardware (GPU + CPU), spot/preemptible handling.
- **Q3.2.2:** "Design a multi-tenant LLM serving platform on Ray + vLLM." Discuss: request routing, continuous batching, prefix caching, paged attention, fairness across tenants, GPU sharing (MIG/MPS).

### Round 3.3: ML deep-dive
- **Q3.3.1:** "How would you train a 70B model across 256 GPUs?" Discuss: tensor parallelism, pipeline parallelism, ZeRO/FSDP, mixed precision, gradient accumulation, async checkpointing.
- **Q3.3.2:** "Walk through how you'd debug a Ray job that hangs." Head node logs, `ray status`, dashboard, object store spilling, `ray memory`.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a time you owned a system end-to-end in production."
- **Q3.4.2:** "Describe a technical disagreement you had and how it resolved."
- **Q3.4.3:** "Why open-source ML infra?" (Anyscale is committed to Ray OSS; this matters culturally.)

## Stage 4: Hiring committee
The committee is technical and tends to be ex-Ray maintainers, ex-databricks, ex-Anyscale. They look for: deep systems knowledge (you should know the difference between task backpressure, actor concurrency, and object store spilling), the ability to write production C++ and Python, and a strong opinion on what makes Ray special. A public OSS contribution — even a small PR to Ray or vLLM — is the single biggest signal you can send, because the committee has seen every type of "I read the paper" candidate.

## Stage 5: Offer
Anyscale pays near-big-tech for senior engineers ($300K+ all-in for E5). Equity is meaningful (private, strong valuation). Negotiation lever: title (E5 vs E6) and equity grants.

## Tips for the Anyscale loop
1. **Read the Ray paper and design docs.** Anyscale engineers expect you to know lineage reconstruction.
2. **Practice the Anyscale / vLLM / Ray Serve stack** — these are their three product lines.
3. **Brute-force distributed systems fundamentals**: consensus (Raft), placement groups, bin-packing, autoscaling.
4. **Code in Python and C++** — Ray is mostly C++ core + Python API.
5. **Be opinionated about actor vs task model** — ask thoughtful questions.
6. **Have a public OSS contribution** to a related project (Ray, vLLM, DeepSpeed) — huge positive signal.
7. **Practice the "design autoscaler" round** — it's almost always asked.

## Real candidate report
> "Phone screen asked me to implement a distributed task queue with retries. Onsite was intense: 4 rounds including one where the interviewer (a Ray committer) asked me to design Ray's autoscaler. I had to walk through idle node termination and preemption. Got the offer 5 days later, $310K all-in." — Levels.fyi, 2025

## Sources
- [Anyscale careers](https://www.anyscale.com/careers)
- [Ray documentation](https://docs.ray.io)
- [Anyscale engineering blog](https://www.anyscale.com/blog)
- [Anyscale Glassdoor](https://www.glassdoor.com/Interview/Anyscale-Interview-Questions-E3257849.htm)
- [Levels.fyi Anyscale](https://www.levels.fyi/companies/anyscale)

---

## The 1 thing to remember

Read the Ray paper and have an OSS PR (or a substantive local fork) before the onsite — the Anyscale committee is staffed by Ray maintainers, and the candidate who can talk lineage reconstruction, placement groups, and actor restart without Googling wins.
