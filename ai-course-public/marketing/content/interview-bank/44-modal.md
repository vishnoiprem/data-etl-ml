# 44. Modal

- **Role:** Software Engineer (Serverless Compute / ML Infrastructure)
- **Tech stack:** Python, Rust, Go, containerd, gVisor, Kubernetes, S3, custom container runtime, FastAPI, React
- **Comp band:** $220K-$420K (small team, high talent density)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation + comp | 1 week | ~50% advance |
| 2. **Take-home or technical phone** | 90 min, code-heavy | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Systems design, coding, ML, founder | 1 day | ~30% advance |
| 4. **Hiring committee** | Small team, tight review | 1 week | ~70% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Modal?"
**Answer:** Three-bet: (1) Modal's container startup time (sub-second) is genuinely best-in-class — they've invested in custom container runtime, (2) the dev experience (`@modal.enter`, `modal run`, `modal deploy`) is the best in serverless, (3) the team is ex-Google infrastructure, ex-Stripe infra, and the bar is high.
**Tip:** Modal values engineers who can talk cold-start optimization at the kernel level. Mention your favorite infra war story.

### Q1.2: "Tell me about a system you built from scratch"
**Answer:** Frame it as: a system that solved a real pain, with clear technical choices, with measured impact. Modal's founders (Erik Bernhardsson, Akshat Bubna) both shipped at scale (Spotify, Google).

## Stage 2: Technical phone screen

### Q2.1: Coding: "Implement a function memoizer with TTL"
**Answer:**
```python
import time
def memoize(ttl_seconds):
    cache = {}
    def decorator(fn):
        def wrapper(*args):
            now = time.time()
            if args in cache and now - cache[args][1] < ttl_seconds:
                return cache[args][0]
            result = fn(*args)
            cache[args] = (result, now)
            return result
        return wrapper
    return decorator
```
**Tip:** Modal memoizes container start state aggressively. Talk about warm pool, snapshot/restore, copy-on-write FS.

### Q2.2: Systems: "How would you build a serverless function platform with sub-second cold starts?"
**Answer:** Four pillars: (1) pre-warmed container pool, (2) snapshot/restore (CRIU, gVisor), (3) lazy import, (4) pre-pulled base images (overlayfs dedup). Modal uses all four.
**Tip:** Mention Firecracker, microVMs vs containers, and the latency/memory tradeoff.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a simple async job queue with worker pool.
- **Q3.1.2:** Build a basic rate limiter (token bucket or sliding window).
- **Q3.1.3:** Implement a retry decorator with exponential backoff and jitter.

### Round 3.2: System design
- **Q3.2.1:** "Design Modal's container runtime." Talk: control plane (Go), worker plane (Rust), image layer cache (S3 + content-addressed), snapshot/restore, GPU passthrough, multi-tenant isolation.
- **Q3.2.2:** "Design a multi-tenant GPU scheduler with spot instances." Discuss preemption handling, queue prioritization, MIG slicing, fair-share across teams.

### Round 3.3: ML / Infra deep-dive
- **Q3.3.1:** "How would you build a fast LLM inference server on Modal?" Talk: vLLM + continuous batching, prefix caching, dynamic batching, request coalescing, KV cache memory management.
- **Q3.3.2:** "Walk through how Modal deploys a model from `modal deploy`." Discuss image build, function registration, scheduling, autoscale, observability.

### Round 3.4: Founder/behavioral
- **Q3.4.1:** "Tell me about a time you optimized something 10x. How did you measure it?"
- **Q3.4.2:** "Why infra? What draws you to this kind of work?"
- **Q3.4.3:** "A customer is using 10x the resources they expected. How do you investigate?" (Modal cares a lot about cost-aware design.)

## Stage 4: Hiring committee
Modal is small (~50 people) and tight. The committee is usually the founders + 2 senior engs. They look for: systems depth, willingness to be on-call for what you build, and a strong "builder" instinct. Red flags: hand-wavy answers on cold starts, no curiosity about the runtime internals.

## Stage 5: Offer
Modal pays top-of-market for senior engineers: $250K-$400K base, meaningful equity (private, well-funded). Equity is the leverage. They also offer unusual perks (4-day workweek tested, generous compute credits). Negotiation: equity is the main lever.

## Tips for the Modal loop
1. **Read Erik Bernhardsson's blog and the Modal engineering blog** — they're public about internals.
2. **Practice cold-start optimization talk** — snapshot/restore, container pooling, lazy import.
3. **Show fluency in Rust or Go** — Modal's worker plane is Rust, control plane is Go.
4. **Have an opinion on serverless vs always-on for ML** — Modal believes serverless wins.
5. **Build something on Modal before the interview** — `modal run` a real job, then talk about it.
6. **Be ready for a founder round** — Erik or Akshat do them themselves.
7. **Show taste in systems design** — Modal is opinionated (their motto is "infrastructure should be invisible").

## Real candidate report
> "Phone screen was an hour of systems design — designing Modal's container runtime from scratch. Onsite was 4 rounds in one day: coding (2 mediums), system design (cold start optimization), ML (vLLM serving), founder (Erik asked about my favorite infra paper). 5 day offer, base $260K + 0.04%." — Levels.fyi anonymous, 2025

## Sources
- [Modal careers](https://modal.com/careers)
- [Modal engineering blog](https://modal.com/blog)
- [Erik Bernhardsson's blog](https://erikbern.com)
- [Modal Glassdoor](https://www.glassdoor.com/Interview/Modal-Interview-Questions-E4605400.htm)
- [Levels.fyi Modal](https://www.levels.fyi/companies/modal-labs)
