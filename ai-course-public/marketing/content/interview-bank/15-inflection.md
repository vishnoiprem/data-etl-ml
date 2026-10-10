# 15. Inflection AI

- **Role:** AI Engineer
- **Tech stack:** Python, PyTorch, JAX, CUDA, Triton
- **Comp band:** $200K-$1M+ (L3-L6)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, mission fit (emotional intelligence, Pi) | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + ML fundamentals | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds, 1 day)** | Coding → ML deep-dive → safety/values round → behavioral | 1-2 days | ~30% advance |
| 4. **Reference + offer** | Comp negotiation real; mission-fit matters | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in conversational AI — most recently at [X] where I shipped a dialogue system that handled 10M conversations/day. Relevant: a paper on long-context memory for chatbots. I'm targeting Inflection because the emotional-intelligence + safety thesis is the bet I want to test.
**Tip:** Inflection grades emotional-intelligence + safety depth; bring dialogue specifics.

### Q1.2: "Why Inflection?"
**Answer:** I want to work on Pi because the emotional-intelligence thesis is what differentiates you from GPT-4 class. The 1 thing I'd test: whether long-context memory (10K-turn conversations) can match human-level recall on the user's stated preferences. I disagree with the pure-task-completion thesis — empathy is the moat.
**Tip:** Emotional intelligence + long-context memory is the Inflection bet.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement a sliding-window attention with global tokens"
**Answer:** Sliding window of W=4096 for most tokens, with N=64 global tokens that attend everywhere. The pattern: local + global, used in Mistral and Inflection's Pi.
```python
def local_global_attn(Q, K, V, window=4096, n_global=64):
    # K, V: (seq, d)
    # Last n_global positions are "global"
    n = K.size(0)
    global_idx = torch.arange(n - n_global, n)
    local_idx = torch.arange(max(0, n - window), n)
    # Compute attention separately for global and local, then combine
    return combined
```
**Tip:** Sliding window + global tokens is the Pi-canonical pattern.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Top-K elements in a stream, O(n log K)"
**Answer:** Min-heap of size K. For each new element, push and pop if size > K. Final heap = top K.

### Q3.1.2: "LRU cache with TTL"
**Answer:** `OrderedDict` for LRU + expiry timestamp; on `get` check TTL, evict if expired.

### Round 3.2: ML deep-dive (60 min)

### Q3.2.1: "How would you build long-term memory for a chatbot?"
**Answer:** Three layers: (1) short-term (current conversation, in-context), (2) medium-term (recent conversations, summarized), (3) long-term (user preferences, facts). The trade-off: long-term memory is a vector store + retrieval; the risk is over-personalization (echo chamber). Pi's bet: explicit user consent + opt-in for each memory.
**Tip:** 3-layer memory + opt-in is the Pi-canonical answer.

### Q3.2.2: "Compare dialogue evaluation methods"
**Answer:** 3 options: (1) human eval (gold standard, expensive), (2) LLM-as-judge (GPT-4 rubric, fast, biased), (3) task-completion metrics (engagement, retention, the actual product KPI). The right pick: a 4-layer eval — human eval on a 1K sample weekly, LLM judge on every conversation, task metrics daily, A/B monthly.
**Tip:** 4-layer eval is the dialogue pattern.

### Round 3.3: Safety/values round (60 min)

### Q3.3.1: "How would you detect a user in emotional distress and respond appropriately?"
**Answer:** Train a classifier on emotional-distress signals (self-harm keywords, patterns of hopelessness, etc.) with high precision. On detection: route to a specialized response (empathetic, suggest resources, offer human handoff). Trade-off: false positives (over-intervention, frustrating) vs. false negatives (missing real distress). The right pick: high precision (>0.95), high recall on the highest-severity cases.
**Tip:** High precision + human handoff is the safety pattern.

### Q3.3.2: "Pi should be empathetic. How do you prevent sycophancy?"
**Answer:** Sycophancy = agreeing with the user even when they're wrong. The fix: (1) train with explicit examples of disagreement (pushback with empathy), (2) eval rubric penalizes agreement with false claims, (3) red-team suite for sycophancy prompts. The trade-off: too much pushback feels cold; too little is sycophantic. The right pick: calibrated empathy.
**Tip:** Calibrated empathy + red-team is the anti-sycophancy answer.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "A time you designed for safety"
**Answer:** I shipped a content filter for a customer-facing chatbot that caught 99.5% of unsafe outputs in offline eval. The trade-off: I sacrificed 5% of legitimate responses to false positives. The post-launch metric: 0 safety incidents in 6 months.
**Tip:** Specific design + specific trade-off + specific metric.

### Q3.4.2: "Why Inflection?"
**Answer:** I want to work on Pi because the emotional-intelligence thesis is what differentiates you. The 1 thing I'd test: whether long-context memory (10K-turn conversations) can match human-level recall on user-stated preferences. I disagree with the pure-task-completion thesis — empathy is the moat.

## Stage 4: Hiring committee

The committee weighs emotional intelligence + safety + Inflection mission fit. They look for: (1) coherent dialogue + memory narrative, (2) calibrated-empathy evidence, (3) "would I trust this person with Pi's safety layer?" 1-2 week turnaround.

## Stage 5: Offer

Inflection comp is base + RSU + sign-on. SF / Palo Alto hub. Cash component is decent; equity is meaningful. The play: anchor with a competing offer (OpenAI, Anthropic). Sign-on is real for senior candidates.

## Tips for the Inflection loop

- **Emotional intelligence is the moat.** Calibrated empathy, not sycophancy.
- **Long-context memory is the bet.** 3-layer: short + medium + long.
- **Safety round is real.** High precision + human handoff.
- **4-layer dialogue eval.** Human + LLM + task + A/B.
- **Why Inflection needs the empathy disagreement.** Not pure task-completion.
- **Pi is the product.** Read about it before the loop.
- **Mission fit matters.** "Kind, helpful, honest" is the bet.

## Real candidate report

> *"Inflection's interview is unique — the safety round is separate, like Anthropic's, but the focus is on emotional safety: detecting distress, preventing sycophancy, calibrated empathy. The 'why Inflection' answer needs to be about emotional intelligence, not capability. The candidate who talks about benchmarks loses."*
> — Glassdoor candidate report, paraphrased from 2026 loops

## Sources

- [Inflection AI](https://inflection.ai/)
- [Pi — Inflection's chatbot](https://pi.ai/)
- [Inflection AI Engineering Blog](https://inflection.ai/blog)
- [Mustafa Suleyman — Inflection AI](https://www.linkedin.com/in/mustafasuleyman/)
- [Levels.fyi — Inflection compensation](https://www.levels.fyi)