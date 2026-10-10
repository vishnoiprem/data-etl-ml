# 4. xAI

- **Role:** AI Engineer
- **Tech stack:** Python, PyTorch, JAX, CUDA, Triton, Rust (Grok serving)
- **Comp band:** $200K-$1M+ (L2-L6, cash-heavy)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, mission fit, speed orientation | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + ML fundamentals, fast loop | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds, 1-2 days)** | Coding → ML system design → Grok infra → "speed" round → behavioral | 1-2 days | ~30% advance |
| 4. **Team match + offer** | Fast turnaround; comp negotiation real | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an AI engineer with 5 years in large-scale training — most recently at [X] where I shipped a distributed training pipeline for a 70B model on 1024 H100s. Relevant: a Rust inference server that hit 10K req/s. I'm targeting xAI because the Grok real-time reasoning bet is the most ambitious training-systems bet in 2026.
**Tip:** xAI values speed + mission alignment; signal both.

### Q1.2: "Why xAI?"
**Answer:** I want to work on Grok because the real-time reasoning + X-data integration is a bet no one else can make. The 1 thing I'd test: whether a 1T model with RLHF on real-time X data beats a 1T model trained on a 6-month-old snapshot on truthfulness. I disagree with the closed-model thesis — Grok should be open-weights.
**Tip:** Specific bet + specific test + Grok-specific disagreement.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement a sliding-window attention with KV cache reuse"
**Answer:**
```python
def sliding_window_attn(Q, K_cache, V_cache, window=512):
    # K_cache, V_cache: (seq_so_far, d)
    # Q: (1, d)  for one new token
    k_recent = K_cache[-window:]
    v_recent = V_cache[-window:]
    scores = Q @ k_recent.T / (Q.shape[-1] ** 0.5)
    weights = np.exp(scores - scores.max())
    weights /= weights.sum()
    return weights @ v_recent
```
xAI grades speed and memory: the window size is the memory/compute trade-off; 512 is the Mistral-canonical pick.
**Tip:** Name the window size, name the memory trade-off.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Top-K elements in a stream, O(n log K)"
**Answer:** Min-heap of size K. For each new element, push and pop if size > K. Final heap = top K. Trade-off: heap is O(n log K); quickselect is O(n) average but O(n²) worst case.

### Q3.1.2: "Implement a sharded key-value store with consistent hashing"
**Answer:** Hash both keys and nodes to a 32-bit ring; key lives on the next clockwise node. Replicas: store on the next N nodes. Rebalance: virtual nodes (e.g., 256 per physical node) for even distribution.
**Tip:** xAI's serving stack is consistent-hashing heavy; name the replica count.

### Round 3.2: ML system design (60 min)

### Q3.2.1: "Design Grok's real-time inference serving platform"
**Answer:** Three layers: (1) request router (model selection, batching), (2) inference engine (vLLM/TensorRT-LLM with continuous batching), (3) KV cache pool (paged, cross-request sharing for the same prompt prefix). Real-time: stream responses via SSE. Trade-off: throughput vs. TTFT.
**Tip:** Name paged attention, name the TTFT budget.

### Q3.2.2: "Design a training data pipeline for real-time X data"
**Answer:** Kafka for ingest → Spark Structured Streaming for cleaning → Delta Lake for the gold layer. Real-time: 1-min freshness SLA. Eval: per-topic accuracy + truthfulness rubric. The bet: real-time data + RLHF closes the truthfulness gap.
**Tip:** xAI's differentiator is the real-time data; lean into it.

### Round 3.3: Grok infra (60 min)

### Q3.3.1: "Walk through training a 1T model on 100K H100s"
**Answer:** 3D parallelism: TP=8 (NVLink node), PP=16, DP=800. ZeRO-3 for optimizer state sharding. Activation checkpointing every 4 layers. The bet: NVLink + InfiniBand fabric + custom collective library. Failure mode: a single GPU failure during a 30-day run; the answer is async checkpointing + restart from last-good.

### Round 3.4: "Speed" round (45 min)

### Q3.4.1: "How would you ship Grok-3 in 6 months?"
**Answer:** 3 streams in parallel: (1) data pipeline + RLHF infra, (2) training run with a 70B reference + 1T target, (3) serving infra on Memphis. Cut: red-team (defer to v2), multi-region (ship US-only first). The xAI culture rewards speed: bias to ship, fix in production.
**Tip:** Specific cuts, specific timeline, xAI "bias to ship" culture.

## Stage 4: Hiring committee

The committee weighs speed + technical depth + mission fit. They look for: (1) evidence of shipping at speed, (2) "what would you cut" answers that match the xAI culture, (3) real-time + scale fluency. Turnaround is fast (1-2 weeks).

## Stage 5: Offer

xAI comp is more cash-heavy than RSU-heavy. The play: anchor with a competing offer (OpenAI, Anthropic). Sign-on is real. 4-year vest, 1-year cliff. xAI negotiates; the band is wide.

## Tips for the xAI loop

- **Speed is the cultural signal.** "What would you cut" matters more than polish.
- **Real-time + scale is the differentiator.** X data + Grok reasoning + 100K H100s.
- **Rust is in the stack.** Cog (open-source) is Rust; signal fluency.
- **Mission fit matters.** "Truth-seeking AI" is the bet; defend it.
- **Bias to ship.** In production-fix loops, not pre-launch perfection.
- **NVLink + InfiniBand is the fabric.** Name the bandwidths, name the topology.
- **1-2 week turnaround.** The whole loop is fast.

## Real candidate report

> *"xAI moves fast — I had a recruiter screen on Monday, a phone screen on Wednesday, and an onsite the following week. The 'speed' round is real: they ask you to scope a 6-month project and they want specifics, not a Gantt chart. 'What would you cut' is the question, not 'how would you do it perfectly.'"*
> — Glassdoor candidate report, paraphrased from 2026 loop reports

## Sources

- [xAI — News & Updates](https://x.ai/news)
- [xAI Wikipedia](https://en.wikipedia.org/wiki/SpaceXAI)
- [xAI Grok Console](https://console.x.ai/)
- [Forbes — How France's Mistral Built a $14B AI Empire (Apr 2026)](https://www.forbes.com/sites/iainmartin/2026/04/16/how-frances-mistral-built-a-14-billion-ai-empire-by-not-being-american/)
- [Levels.fyi — xAI compensation](https://www.levels.fyi)