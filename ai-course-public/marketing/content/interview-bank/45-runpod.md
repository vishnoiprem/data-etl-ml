# 45. RunPod

- **Role:** ML Infrastructure Engineer / Cloud GPU Engineer
- **Tech stack:** Python, Go, TypeScript, Kubernetes, Docker, CUDA, NVIDIA drivers, Triton, vLLM, S3, K8s operators, Terraform
- **Comp band:** $170K-$340K (smaller than Lambda/CoreWeave, growing fast)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + infra | 1-2 weeks | ~40% advance |
| 3. **Onsite (3-4 rounds)** | Coding, system design, ML infra, founder | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1 week | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Tell me about your GPU/ML infra experience"
**Answer:** Highlight hands-on experience with K8s + GPU scheduling, CUDA kernels, or model serving. Even better: mention you've actually debugged a hung CUDA job, or set up a multi-GPU training run.
**Tip:** RunPod is a GPU cloud — they want people who've used GPUs in anger, not just abstracted them.

### Q1.2: "Why RunPod over Lambda or CoreWeave?"
**Answer:** Three-bet: (1) RunPod's developer experience is better (faster pod spin-up, simpler pricing), (2) Serverless endpoints are a real differentiator (Lambda/CoreWeave are more raw IaaS), (3) community / marketplace traction is strong on the consumer side (Stable Diffusion, ComfyUI).

## Stage 2: Technical phone screen

### Q2.1: Coding — "Write a GPU job queue with priority scheduling"
**Answer:**
```python
import heapq
class GPUQueue:
    def __init__(self):
        self.q = []
        self.counter = 0
    def submit(self, job, priority=0, gpus_needed=1):
        heapq.heappush(self.q, (-priority, self.counter, gpus_needed, job))
        self.counter += 1
    def schedule(self, available_gpus):
        scheduled = []
        deferred = []
        while self.q:
            prio, _, gpus, job = self.q[0]
            if gpus <= available_gpus:
                heapq.heappop(self.q)
                scheduled.append(job)
                available_gpus -= gpus
            else:
                break
        return scheduled
```
**Tip:** Talk about bin-packing, fragmentation, MIG vs full GPU, and preemption.

### Q2.2: Infra — "How do you isolate noisy-neighbor GPUs in a multi-tenant cloud?"
**Answer:** Three layers: (1) **hardware**: MIG slicing for H100/A100, (2) **kernel**: NVIDIA MPS for older GPUs, time-slicing via K8s device plugin, (3) **policy**: per-tenant cgroups, network bandwidth limits, IO throttling.

## Stage 3: Onsite (3-4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement an LRU cache.
- **Q3.1.2:** Build a simple HTTP rate limiter (sliding window).
- **Q3.1.3:** Parse a Terraform-like HCL config (RunPod uses K8s + custom CRDs).

### Round 3.2: System design
- **Q3.2.1:** "Design RunPod's pod scheduling system." Discuss: capacity (mix of on-demand + spot), placement (latency-aware bin-packing), preemption, image cache, network volume mounts.
- **Q3.2.2:** "Design a serverless GPU inference endpoint product." Talk: model registry, cold start (pre-warmed pool), warm pool sizing, request routing, autoscaling, observability.

### Round 3.3: ML / GPU deep-dive
- **Q3.3.1:** "How do you set up a multi-node, multi-GPU training run?" Talk: NCCL, RDMA/InfiniBand, rendezvous, distributed init, gradient bucketing, FSDP/ZeRO.
- **Q3.3.2:** "How would you benchmark and optimize an LLM inference server?" Discuss: vLLM, continuous batching, KV cache, prefix caching, quantization (INT8, INT4, FP8), speculative decoding.

### Round 3.4: Founder/behavioral
- **Q3.4.1:** "Tell me about a time you had to learn a new infra tech fast (e.g., CUDA). How did you ramp?"
- **Q3.4.2:** "Why GPU cloud? What excites you about it?"
- **Q3.4.3:** "A customer complains about GPU availability. Walk me through your investigation." (RunPod is obsessed with capacity.)

## Stage 4: Hiring committee
Smaller team (~150 people), tight review. They look for: K8s + GPU depth, ability to debug at the kernel level, customer empathy (RunPod has a strong community/DX focus). Red flags: not knowing what MIG is, or never having used a K8s GPU operator.

## Stage 5: Offer
Base is competitive for the size; equity is moderate (RunPod is private, growing). They sometimes offer GPU compute credits as a perk. Negotiation: sign-on + equity.

## Tips for the RunPod loop
1. **Know K8s GPU operators** (NVIDIA device plugin, GPU Operator, k8s-device-plugin) — they come up.
2. **Practice CUDA basics** — you don't need to write kernels, but know streams, memory hierarchy, NCCL.
3. **Be ready to discuss vLLM and inference optimization** — RunPod's serverless endpoints use vLLM.
4. **Show you've used RunPod or a competitor** — set up a pod, train a model, deploy an endpoint.
5. **Read the RunPod blog and docs** — they're public about their architecture.
6. **Have a strong opinion on cost vs latency** for GPU workloads.
7. **Be ready for a founder round** — RunPod's founders are technical and care about culture.

## Real candidate report
> "Phone screen was K8s + GPU scheduling design. Onsite had a CUDA optimization question (memory coalescing, occupancy) that I barely passed. The founder round was the toughest — they really grill you on why GPU cloud, what you know about the market. Offer: $200K + equity, 5 days." — Reddit r/MachineLearning, 2025

## Sources
- [RunPod careers](https://www.runpod.io/careers)
- [RunPod docs](https://docs.runpod.io)
- [RunPod engineering blog](https://www.runpod.io/blog)
- [RunPod Glassdoor](https://www.glassdoor.com/Interview/RunPod-Interview-Questions-E5078000.htm)
- [Levels.fyi RunPod](https://www.levels.fyi/companies/runpod)
