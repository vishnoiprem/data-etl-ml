# 12. Replicate

- **Role:** ML Engineer
- **Tech stack:** Python, Cog (open-source), Docker, FastAPI, Rust, CUDA
- **Comp band:** $200K-$500K (L3-L6, small team)
- **Cumulative pass rate:** ~4-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, open-source + small-team fit | 1 week | ~60% advance |
| 2. **Take-home / pairing session** | Build a small Cog model | 1-2 weeks | ~50% advance |
| 3. **Onsite (3-4 rounds, 1 day)** | Coding → Cog / Docker system design → ML deployment → behavioral | 1-2 days | ~40% advance |
| 4. **Reference + offer** | Comp negotiation real | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in model deployment — most recently at [X] where I shipped a Cog-based serving platform for 100+ models. Relevant: my open-source Cog PR that added [specific feature]. I'm targeting Replicate because the model-as-a-service thesis is the bet I want to be closest to.
**Tip:** Replicate is small + open-source; signal both.

### Q1.2: "Why Replicate?"
**Answer:** I want to work on the Cog + Replicate platform because the model-as-a-service thesis is what enables every independent ML developer. The 1 thing I'd test: whether we can hit <500ms cold start for a 7B model with the Cog container pattern. I disagree with the always-on-GPU pricing — push for scale-to-zero.
**Tip:** Small team + open-source + scale-to-zero is the Replicate bet.

## Stage 2: Take-home / pairing session

### Q2.1: "Build a Cog model that runs Stable Diffusion XL and exposes it via HTTP"
**Answer:** Write `predict.py` with a `Predictor` class and a `predict(prompt, ...)` method. Add a `cog.yaml` with the image + GPU + Python deps. Build with `cog build -t sdxl`. Run with `cog run -p "a cat"`.
```python
# predict.py
from cog import BasePredictor, Input, Path
import torch
from diffusers import StableDiffusionXLPipeline
class Predictor(BasePredictor):
    def setup(self): self.pipe = StableDiffusionXLPipeline.from_pretrained("stability-ai/sdxl", torch_dtype=torch.float16).to("cuda")
    def predict(self, prompt: str = Input()) -> Path:
        img = self.pipe(prompt).images[0]; out = Path("/tmp/out.png"); img.save(out); return out
```
Replicate grades Cog fluency + Docker fundamentals.
**Tip:** Cog + Docker is the Replicate stack.

## Stage 3: Onsite (3-4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Build a small queue with retries and exponential backoff"
**Answer:**
```python
import time, queue, threading
class RetryQueue:
    def __init__(self, max_retries=5, base=1.0):
        self.q, self.max, self.base = queue.Queue(), max_retries, base
    def worker(self):
        while True:
            item = self.q.get()
            try: self.process(item); self.attempts = 0
            except Exception as e:
                item["attempts"] = item.get("attempts", 0) + 1
                if item["attempts"] < self.max:
                    time.sleep(self.base * (2 ** item["attempts"]) + random.random() * 0.1)
                    self.q.put(item)
            finally: self.q.task_done()
```
Trade-off: exponential backoff vs. constant retry; jitter avoids thundering-herd.
**Tip:** Backoff + jitter is the Replicate serving pattern.

### Q3.1.2: "Implement LRU cache with size-based budget (not count)"
**Answer:** Track current size; on `put`, evict until size ≤ budget. Use a heap or sorted list to track entries by access time. Trade-off: O(n) eviction vs. O(log n) with a heap.

### Round 3.2: Cog / Docker system design (60 min)

### Q3.2.1: "Design the Replicate model-serving platform"
**Answer:** Three layers: (1) API gateway (auth, rate limiting), (2) scheduler (queue requests, route to available GPU pools), (3) worker (Cog container, GPU-attached, scale-to-zero on idle). Cold start: 30s for a 7B model with Cog image caching. The trade-off: cold start vs. cost (scale-to-zero saves money but adds latency).
**Tip:** Scale-to-zero + cold start is the Replicate differentiator.

### Q3.2.2: "Design GPU pool autoscaling"
**Answer:** Track queue depth + GPU utilization. Scale up when queue depth > 5 per GPU; scale down when GPU utilization < 20% for 5 minutes. Cold start penalty: pre-warm popular models. Trade-off: pre-warming costs money but cuts p99 latency.
**Tip:** Queue-depth + GPU-utilization is the autoscaling signal.

### Round 3.3: ML deployment (60 min)

### Q3.3.1: "How would you optimize a Cog model's cold start?"
**Answer:** (1) Pre-build the Cog image and cache it on every node, (2) lazy-load model weights on first predict (not on container start), (3) use safetensors for memory-mapped loading, (4) keep the container warm for popular models. Trade-off: warm containers cost money but cut cold start from 30s to 5s.
**Tip:** Image caching + lazy weights is the canonical answer.

### Q3.3.2: "How would you handle a model that runs out of GPU memory?"
**Answer:** (1) Check the model + batch size, (2) enable FP16 or BF16, (3) enable xformers or FlashAttention, (4) enable CPU offload for the optimizer, (5) shard the model across multiple GPUs. Trade-off: complexity vs. memory savings.
**Tip:** Memory optimization ladder is the deployment answer.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "A time you fixed a production bug"
**Answer:** A model was OOMing at scale. I profiled: the Cog container wasn't releasing GPU memory between requests. Fix: explicitly call `torch.cuda.empty_cache()` after each predict. Latency dropped 40%.
**Tip:** Specific bug + specific fix + specific metric.

### Q3.4.2: "Why Replicate?"
**Answer:** I want to work on the platform because the model-as-a-service thesis is what enables every independent ML developer. The 1 thing I'd test: whether we can hit <500ms cold start for a 7B model with the Cog container pattern. I disagree with always-on-GPU pricing — push for scale-to-zero.

## Stage 4: Hiring committee

The committee weighs Cog / Docker depth + small-team fit + open-source contribution. They look for: (1) shipping instinct (Cog PR, model shipped), (2) infrastructure depth (autoscaling, cold start), (3) "would I trust this person with the platform?" 1-week turnaround.

## Stage 5: Offer

Replicate comp is base + RSU + sign-on. Cash component is decent; equity is meaningful (small team, pre-IPO). The play: anchor with a competing offer (if you have one). Sign-on is real for senior candidates.

## Tips for the Replicate loop

- **Cog + Docker is the stack.** Build a model before the loop.
- **Scale-to-zero is the bet.** Name the cold-start trade-off.
- **Queue depth + GPU utilization is the autoscaling signal.**
- **Image caching + lazy weights cut cold start.**
- **Memory optimization ladder.** FP16 → xformers → CPU offload → sharding.
- **Small team.** Mission fit matters more than credentials.
- **Open-source contribution counts.** Bring Cog PRs.

## Real candidate report

> *"Replicate's interview is unique — the take-home was a real Cog model. The onsite rounds felt like the platform engineers talking through their actual architecture. The candidate who treats it like a generic ML interview loses. Cog + Docker + cold start is the signal."*
> — Glassdoor candidate report, paraphrased from 2026 loops

## Sources

- [Replicate](https://replicate.com/)
- [Cog — open-source model container](https://github.com/replicate/cog)
- [Replicate Docs](https://replicate.com/docs)
- [Hacker News — Replicate threads](https://news.ycombinator.com/)
- [Levels.fyi — Replicate compensation](https://www.levels.fyi)