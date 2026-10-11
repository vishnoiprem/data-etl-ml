# 24. Meta (GenAI / Ads ML / FAIR)

- **Role:** ML Engineer or Research Engineer (GenAI, Ads ranking, Integrity, FAIR)
- **Tech stack:** Python, PyTorch (heavily), C++, CUDA, FBGEMM, TorchRec, FSDP, React/GraphQL for some roles
- **Comp band:** $300K-$1.2M (E3-E7); E7+ crosses $2M+; RSUs heavy, base high
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Loop intro, team match | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~30% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, ML deep-dive, behavior | 1-2 days | ~30% advance |
| 4. **Hiring committee (ML cross-functional)** | Senior ML panel vote | 2-3 weeks | ~50% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Meta for ML?"
**Answer:** I want to work on the largest ML systems in the world. PyTorch is the de facto standard and Meta invented it — the engineers who maintain it are the ones I want to learn from. I'm particularly excited about [Llama / Ads ranking / Integrity].
**Tip:** Be specific. Meta interviewers will know if you're a generic ML candidate.

### Q1.2: "Tell me about a model you took from research to production"
**Answer:** I built a retrieval-augmented QA system at [X]. Started as a research prototype, ran A/B against baseline, and after 3 months shipped to 20% of traffic. Final state: 12% absolute accuracy lift, 8ms p99 latency, and I mentored two junior engineers through the productionization.
**Tip:** "Move fast" energy is rewarded at Meta. Show iteration speed.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "K-th largest element in a stream"
**Answer:** Maintain a min-heap of size K. Push new elements; if size > K, pop.
```python
import heapq
class KthLargest:
    def __init__(self, k, nums):
        self.k = k; self.h = nums; heapq.heapify(self.h)
        while len(self.h) > k: heapq.heappop(self.h)
    def add(self, val):
        heapq.heappush(self.h, val)
        if len(self.h) > self.k: heapq.heappop(self.h)
        return self.h[0]
```
**Tip:** Meta coding is *fast* — they time you. Skip small talk, start coding.

### Q2.2: ML — "Design the ranking model for Instagram Reels"
**Answer:** Multi-stage: (1) candidate generation — two-tower from user history + content embeddings; (2) light ranker (DLRM/DeepFM with engagement, watch-time, share, save labels); (3) heavy ranker (transformer-based) with multi-task heads; (4) diversity/safety re-rank; (5) serving at 100ms with embedding cache. Discuss *negative feedback signals* (skip, hide) and exploration via counterfactual logging.
**Tip:** Meta ML questions are *very* applied. They want scale and engagement signal specifics.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (45-60 min)

### Q3.1.1: "Valid parentheses"
**Answer:** Stack; push on `(`, `[`, `{`; pop and check on closing. O(N).

### Q3.1.2: "Regular expression matching"
**Answer:** DP, O(M·N). `dp[i][j]` = does `s[:i]` match `p[:j]`. Handle `*` as zero or more of the preceding char.

### Round 3.2: System design (45-60 min)

### Q3.2.1: "Design a feature store for Ads"
**Answer:** Realtime (Kafka → Flink → in-memory store, <10ms p99) + batch (Spark → Iceberg, hourly refresh). Embedding versioning (v1, v2 stored side-by-side; reads pin to a version for replay). Point-in-time joins (key by event_time, fetch features as of event_time). Freshness SLA: 1 min for realtime, 1 hour for batch.
**Tip:** Embedding versioning + PIT is the Ads-ML differentiator.

### Q3.2.2: "Design an LLM serving infra for Llama at 1M QPS"
**Answer:** Continuous batching (vLLM/TGI) for throughput. Speculative decoding (draft model proposes tokens, target model verifies) for latency. Paged attention (KV cache in fixed-size pages, 16 tokens) for memory. Multi-LoRA (per-tenant adapter hot-swap). Prefix caching (system prompt + shared context cached across requests).
**Tip:** All four techniques together is the Meta serving stack.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "Walk me through the loss function for an Ads CTR model"
**Answer:** Three pieces: (1) calibration — negative down-sampling with a calibration layer (divide by sampling rate); (2) multi-task — shared bottom, separate heads for CTR and CVR with shared embeddings; (3) off-policy correction — inverse propensity weighting to handle position bias and selection bias from logged clicks. Loss: log-loss with weights, summed across tasks.
**Tip:** Calibration + multi-task + off-policy is the Ads CTR stack.

### Q3.3.2: "How would you improve Instagram's notification CTR model?"
**Answer:** Feature additions (recent session activity, predicted re-engagement probability). Label choice (24h engagement vs. 7d, by user segment). Position bias (only train on top-3 slots in the notification list). Holdout methodology (5% holdback for long-term measurement, separate from A/B).
**Tip:** Position bias + label choice + holdout is the canonical answer.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "A time you disagreed with your manager"
**Answer:** My manager wanted to ship a new ranker to 100% on day one. I argued for 1% canary → 10% → 50% → 100% over 2 weeks. The data I brought: prior 100% launches had 3× the rollback rate. They agreed; the canary caught a regression at 1% that would have cost $2M at 100%.
**Tip:** "Disagree directly" + data is the Meta meta-answer.

### Q3.4.2: "Ship something small vs. plan something big — when do you choose each?"
**Answer:** Ship small when: (1) the user problem is well-understood, (2) the metrics are measurable in <1 week, (3) the rollback cost is low. Plan big when: (1) the change is irreversible (model architecture), (2) the metric is delayed (long-term retention), (3) the coordination cost across teams is high.
**Tip:** "Ship fast" doesn't mean "always ship." Show judgment.

### Q3.4.3: "A time you had to unblock someone outside your team"
**Answer:** A team in a different org was blocked on our team's feature pipeline. I built a thin HTTP wrapper around our internal API in 2 days, wrote the docs, and shipped it to their Slack. They unblocked the same week. Cost: 2 days of my time; benefit: 3 weeks of cross-team velocity.
**Tip:** Specific unblock + specific metric.

### Round 3.5 (optional for senior): Coding in C++/PyTorch

For some roles, a round of writing actual PyTorch nn.Module code, or a C++ data-structure question. Confirm with recruiter.
**Tip:** Practice a custom nn.Module forward; know FSDP sharding.

## Stage 4: Hiring committee

Meta has a strong "calibration" culture. Senior ML panel reviews all signals. They look for: (1) technical bar, (2) impact at scale, (3) "Meta values" — Move Fast, Be Bold, Be Open, Focus on Long-Term, Build Awesome Things, Live in the Future, (4) team match. They err on the side of *no-hire* if signal is mixed. Loop is "debanded" — written feedback is locked.

## Stage 5: Offer

Cash + RSUs. Meta is one of the highest-paying employers in tech. Negotiation is real and aggressive — bring at least one competing offer, ideally FAANG-tier. Team match happens *after* the loop, sometimes after offer is verbally agreed.

## Tips for the Meta loop

- Move fast in the coding rounds. Talk while you code — Meta interviewers grade on signal density.
- For ML rounds, *draw the diagram* (retrieval, ranker, serving) and label with latencies.
- Reference specific Meta papers (TorchRec, FBGEMM, Llama, MAUVE).
- For behavioral, "disagree directly" stories score highly — don't be diplomatic.
- If applying to GenAI / Llama team, expect Python and PyTorch fluency, including distributed training (FSDP/ZeRO).
- For Ads ML, emphasize calibration, multi-task learning, and online metrics.
- Always quantify: 1B users, billions of impressions, p99 latency budgets.

## Real candidate report

> "Loop for GenAI (Llama team). 4 rounds in 1 day + 1 follow-up ML deep-dive. The system design was a Llama serving infra at 1M QPS — they wanted paged attention + continuous batching discussed in detail. The ML round was on RLHF — I had to whiteboard the DPO loss. Got E5 offer at ~$850K total. 5 weeks from screen to offer."
> — Blind, 2025-10

## Sources

- [Meta Careers](https://www.metacareers.com/)
- [Levels.fyi Meta salaries](https://www.levels.fyi/companies/meta/salaries)
- [PyTorch blog](https://pytorch.org/blog/)
- [Meta AI Research](https://ai.meta.com/research/)
- [r/MachineLearning Meta thread](https://www.reddit.com/r/MachineLearning/)
