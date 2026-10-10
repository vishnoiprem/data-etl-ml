# 5. Mistral AI

- **Role:** AI Engineer
- **Tech stack:** Python, PyTorch, JAX, CUDA, Triton, vLLM, Rust
- **Comp band:** €150K-€500K+ (Paris, L3-L6)
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, mission fit (open-weights, EU sovereignty) | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + ML fundamentals, lean coding | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds, 1 day, Paris)** | Coding → ML theory → system design → behavioral | 1-2 days | ~30% advance |
| 4. **Reference checks + offer** | Fast; comp negotiation is real | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an AI engineer with 5 years in transformer efficiency — most recently at [X] where I shipped a MoE router that cut inference cost 3× on a 70B model. Relevant: a paper on sliding-window attention. I'm targeting Mistral because the open-weights + EU-sovereignty thesis is the bet I want to test.
**Tip:** Mistral values open-source + EU-sovereignty; signal both.

### Q1.2: "Why Mistral?"
**Answer:** I want to work on Mistral Large 4 because the open-weights + on-prem thesis is what differentiates you from OpenAI and Anthropic. The 1 thing I'd test: whether a fine-tuned Mistral 7B with a domain-specific MoE adapter can match GPT-4 class on a regulated-industry eval. I disagree with the closed-source pivot for Mistral Large — keep it open.
**Tip:** Specific Mistral bet + specific test + open-weights disagreement.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement rotary positional embedding (RoPE)"
**Answer:**
```python
import torch
def rotate_half(x):
    x1, x2 = x[..., :x.shape[-1]//2], x[..., x.shape[-1]//2:]
    return torch.cat((-x2, x1), dim=-1)
def apply_rope(x, cos, sin):
    return x * cos + rotate_half(x) * sin
# Precompute cos/sin at frequency theta_i = 1/(10000^(2i/d))
```
RoPE rotates each pair of features by a position-dependent angle, encoding relative position via the inner product.
**Tip:** RoPE is the Mistral-canonical architecture question.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Implement grouped-query attention (GQA) with KV cache reuse"
**Answer:** Multiple query heads share the same K/V head; cache size reduces by the GQA ratio (e.g., 4× for 8 query heads per 2 KV heads). On inference: cache shape = (n_kv_heads, seq, d); query shape = (n_heads, seq, d); broadcast K/V to query shape before attention.

### Q3.1.2: "Top-K routing in a Mixture-of-Experts layer"
**Answer:** Compute router logits W·x; pick top-K indices; softmax over the top-K; dispatch to the chosen experts; combine outputs weighted by the softmax. Trade-off: K=2 (standard) vs. K=1 (Switch Transformer, more efficient but higher variance).
**Tip:** Mistral Large 4 is MoE; K=2 is canonical.

### Round 3.2: ML theory (60 min)

### Q3.2.1: "Explain sliding-window attention and its memory/compute trade-off"
**Answer:** Each token attends only to the previous W tokens. Compute: O(n·W) per layer vs. O(n²) for full attention. Memory: O(W) per token for the KV cache. The trade-off: long-range dependencies are lost unless paired with global attention layers (Mixtral pattern). Mistral 7B used W=4096 with periodic global layers.

### Q3.2.2: "Compare open-weights vs. closed-weights for enterprise deployment"
**Answer:** 3 dimensions: (1) data privacy (open-weights = on-prem = no data leaves), (2) cost (open-weights = no per-token fee, just GPU), (3) customization (open-weights = fine-tunable, closed = prompting only). For regulated industries (healthcare, finance, EU gov): open-weights is the only viable path.
**Tip:** Sovereignty is the Mistral differentiator.

### Round 3.3: System design (60 min)

### Q3.3.1: "Design an on-prem LLM serving platform with Mistral 7B"
**Answer:** Three components: (1) inference engine (vLLM for batching, TensorRT-LLM for performance), (2) KV cache pool (paged, GPU memory budget), (3) request router (load balancing across replicas). Trade-off: throughput vs. TTFT. The sovereign angle: customer owns the GPUs and the data; Mistral provides the model + serving infra.
**Tip:** On-prem + sovereignty is the bet.

### Q3.3.2: "Design a fine-tuning pipeline for Mistral 7B on a customer dataset"
**Answer:** QLoRA: 4-bit base + LoRA adapters. Train on customer data; merge adapters for serving. The privacy story: data never leaves the customer environment. Eval: held-out customer eval + red-team + human review.
**Tip:** QLoRA is the Mistral-canonical fine-tune.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "Why open-weights?"
**Answer:** Open-weights is the only path to sovereign AI. If a hospital or a bank or a government can't run the model on their own hardware, they can't use it for sensitive data. The moat isn't the weights — it's the serving infra, the eval, the safety layer, the fine-tuning. We compete on those.
**Tip:** Sovereignty is the Mistral moat.

## Stage 4: Hiring committee

The committee weighs technical depth + open-source contribution + EU-sovereignty fit. They look for: (1) a coherent open-weights narrative, (2) transformer efficiency (RoPE, GQA, MoE, sliding-window) depth, (3) "would I want to ship this to a European bank?" 1-2 week turnaround.

## Stage 5: Offer

Mistral comp is base + RSU + sign-on. Cash component is high; the Paris cost of living is lower than SF. RSU vests 4 years, 1-year cliff. The play: anchor with a competing offer (if you have one from a US lab) — Mistral will match for senior candidates.

## Tips for the Mistral loop

- **Open-weights is the moat.** Sovereignty thesis is the differentiator.
- **Transformer efficiency is the test.** RoPE, GQA, MoE, sliding-window attention.
- **QLoRA for fine-tuning.** 4-bit base + LoRA adapters.
- **On-prem + sovereignty.** The customer owns GPUs and data.
- **EU-sovereignty is real.** GDPR + Digital Services Act + AI Act.
- **Paris-based.** Loop is on-site; travel reimbursed.
- **Mission fit matters.** "AI for everyone" is the bet; defend it.

## Real candidate report

> *"The Mistral interview is technically the deepest of the European labs. They asked me to derive rotary positional embeddings on a whiteboard, then to compare sliding-window vs. global attention for a long-context task. The 'why Mistral' answer needs to be specific: open-weights for sovereignty, not 'I like your models.'"*
> — Glassdoor candidate report, 2026

## Sources

- [Mistral AI](https://mistral.ai/)
- [Mistral Large 4 Docs](https://docs.mistral.ai/models/mistral-large-4-0)
- [Mistral AI Wikipedia](https://en.wikipedia.org/wiki/Mistral_AI)
- [Forbes — How France's Mistral Built a $14B AI Empire (Apr 2026)](https://www.forbes.com/sites/iainmartin/2026/04/16/how-frances-mistral-built-a-14-billion-ai-empire-by-not-being-american/)
- [Levels.fyi — Mistral compensation](https://www.levels.fyi)