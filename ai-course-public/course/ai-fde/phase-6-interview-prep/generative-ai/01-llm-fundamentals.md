# GenAI Sub-Lesson 1 — LLM Fundamentals (the canonical FDE GenAI primer)

> **LLM fundamentals is the canonical FDE GenAI primer.** 100% of FDE loops at AI companies (Anthropic, OpenAI, Sierra, LangChain, Meta, Google, Microsoft) test LLM fundamentals — at the level of "explain attention in 60 seconds," "where do LLMs fail?", "what's the difference between pre-training and fine-tuning?" The FDE signal: a candidate who can explain **transformer architecture + attention + pre-training vs fine-tuning + RLHF + the failure modes (hallucination, jailbreak, drift)** — in plain English — is signaling they can own a GenAI system.

---

## Why LLM fundamentals is the FDE signal

The 4 things the interviewer is testing:

1. **Can you explain attention in 60 seconds?** The candidate who can describe **query / key / value + scaled dot-product + multi-head + causal masking** without naming a single equation is signaling they understand the architecture.
2. **Can you name the pre-training vs fine-tuning distinction?** The candidate who can say "pre-training is the broad corpus; fine-tuning is the narrow task" — and then name the failure modes of each — is signaling they understand the lifecycle.
3. **Can you explain RLHF without hand-waving?** The candidate who can describe **reward model + PPO + the RLHF pipeline + the safety implications** is signaling they can ship a model that's actually aligned.
4. **Can you name the failure modes?** The candidate who can name **hallucination + jailbreak + drift + bias + sycophancy + reasoning failures** — and explain a mitigation for each — is signaling they operate a GenAI system.

**The FDE pattern:** explain the architecture + explain the lifecycle + name the failure modes + name the mitigations. The depth of the answer matches the depth of the FDE role: deeper for AI Lab roles, shallower for forward-deployed roles.

---

## The 4 sections of the canonical LLM-fundamentals answer

### Section 1: Architecture (60 seconds)

**The transformer, in 4 sentences:**

- **Tokens in, tokens out.** The model reads a sequence of tokens (subword units) and predicts the next token, one at a time.
- **Attention is the central operation.** Each token looks at every other token in the sequence and decides "how much should I weight this token when computing my representation?" This is the **query / key / value** mechanism: the query asks "what am I looking for?", the key says "what do I offer?", and the value is the actual content. Scaled dot-product attention computes a weighted sum of the values, where the weights are softmax(query · key / sqrt(d_k)).
- **Multi-head attention** runs this in parallel with different learned projections, so the model can attend to different "kinds" of relationships (syntactic, semantic, positional) at once.
- **The decoder is causal** (in GPT-style models): token at position t can only attend to positions ≤ t, not future positions. This is what makes generation work — you can't see the answer before you generate it.

**The 3 things to add for depth:**

1. **Positional encodings.** Transformers have no inherent notion of token order; positional encodings (sinusoidal in the original paper, learned or RoPE in modern models) inject order.
2. **Feed-forward layers.** After attention, each position goes through a 2-layer MLP (typically with a 4× expansion). This is where the "knowledge" lives — attention is the routing, MLP is the storage.
3. **Residual connections + layer norm.** Each sublayer has a residual connection and a layer norm, so gradients can flow through 100+ layers without exploding or vanishing.

**The 2-minute deep-dive add-on (if the interviewer asks):**

- **Pre-norm vs post-norm.** Modern LLMs use **pre-norm** (LayerNorm before attention/MLP, not after) because it trains more stably.
- **KV cache.** During generation, we cache the K and V matrices for past tokens so we don't recompute them — this is what makes streaming generation fast.
- **Speculative decoding.** A small "draft" model proposes tokens; the large model verifies them in parallel. 2-3× faster generation with no quality loss.

---

### Section 2: Lifecycle (60 seconds)

**The 4 stages of an LLM's life:**

1. **Pre-training.** Train a base model on a massive corpus (1-10T tokens) using next-token prediction. The base model is a "completion engine" — it can write, but it can't follow instructions. **Cost:** millions of GPU-hours. **Output:** a base model (Llama-3-base, GPT-3.5-base).
2. **Supervised fine-tuning (SFT).** Fine-tune the base model on a curated set of (instruction, response) pairs. The model learns to follow instructions, not just complete. **Cost:** thousands of GPU-hours. **Output:** an instruct model (Llama-3-Instruct, GPT-3.5-Turbo).
3. **RLHF / DPO.** Train a reward model on human preferences (which response is better?), then use RL (PPO) or DPO to optimize the SFT model against the reward model. The model learns to be helpful, harmless, and honest. **Cost:** thousands of GPU-hours. **Output:** a chat model (Claude, ChatGPT, Llama-3-Chat).
4. **Deployment.** Serve the chat model behind an API or via on-device inference. The model continues to learn from production signals (thumbs up/down, edit distance, retention).

**The 3 things to add for depth:**

1. **The data is the moat.** Pre-training data is the single biggest determinant of model quality. Scale + quality + diversity of the corpus.
2. **Fine-tuning is not a substitute for prompting.** Fine-tuning a small model on bad data is worse than prompting a large model with good context. Fine-tune for **style + format + domain terminology**; prompt for **reasoning + retrieval + tool use**.
3. **RLHF is what makes the model safe.** Without RLHF, the model is a base model — it can generate harmful content, leak training data, and be jailbroken trivially. RLHF is the safety layer.

---

### Section 3: Failure modes (60 seconds)

**The 6 failure modes every FDE should know:**

1. **Hallucination.** The model generates plausible-sounding but factually wrong text. **Mitigation:** retrieval-augmented generation (RAG) + citations + the eval-set-as-spec regression check.
2. **Jailbreak.** The user crafts a prompt that bypasses the safety alignment (e.g., "DAN" prompts, roleplay attacks, base64-encoded instructions). **Mitigation:** input-side classifiers + output-side classifiers + the safety eval set as the regression check.
3. **Drift.** The model's behavior changes over time — usually because the underlying model is upgraded (e.g., GPT-4 → GPT-4o) or because the prompt is changed. **Mitigation:** version pinning + the eval-set-as-spec regression check.
4. **Bias.** The model reproduces societal biases present in the training data (gender, race, age). **Mitigation:** bias eval set + diverse training data + RLHF with diverse raters.
5. **Sycophancy.** The model agrees with the user even when the user is wrong, because agreeing is rewarded in the preference data. **Mitigation:** Constitutional AI + anti-sycophancy prompts + the eval set.
6. **Reasoning failures.** The model makes mistakes on multi-step reasoning, math, or logic. **Mitigation:** chain-of-thought prompting + tool use (calculator, code interpreter) + the eval set.

**The pattern:** every failure mode has a **detection** (an eval metric) and a **mitigation** (a technique). The candidate who names the detection AND the mitigation is signaling they operate a GenAI system.

---

### Section 4: The cost + latency budget (60 seconds)

**The 4 numbers every FDE should know:**

- **Cost per million tokens:** GPT-4o is $5 input / $15 output. Claude Sonnet is $3 / $15. Llama-3-70B (self-hosted) is ~$0.50 / $0.50 (GPU cost amortized).
- **Tokens per second:** GPT-4o is ~100 tokens/sec. Claude Sonnet is ~80 tokens/sec. Llama-3-70B on an H100 is ~50 tokens/sec.
- **Time to first token (TTFT):** ~200-500ms for hosted models. ~100-200ms for self-hosted.
- **Context window:** GPT-4o is 128K tokens. Claude Sonnet is 200K. Llama-3 is 128K. The context window is the working memory.

**The 3 tradeoffs:**

1. **Larger model = better quality, higher cost.** GPT-4o beats GPT-4o-mini on benchmarks, but costs 30× more. Use the larger model for hard queries; use the smaller for routing.
2. **Longer context = more info, slower + more expensive.** 200K context costs more than 8K context. Trim the context to what the model needs.
3. **Self-hosted = lower per-token cost, higher ops cost.** Llama-3-70B is 10× cheaper per token but you pay for the GPUs, the ops, and the SLA.

---

## The 5 most common LLM-fundamentals questions

| Question | The FDE answer (60 sec) |
|---|---|
| 1. "Explain attention in 60 seconds." | "Each token asks 'what should I attend to?' via a query, compares to every other token's key, and takes a weighted sum of their values. Multi-head runs this in parallel for different relationship types. Causal masking prevents the model from seeing future tokens." |
| 2. "What's the difference between pre-training and fine-tuning?" | "Pre-training is on a massive corpus (1-10T tokens) with next-token prediction; the model learns language + world knowledge. Fine-tuning is on a small curated set of (instruction, response) pairs; the model learns to follow instructions. RLHF adds a safety + preference layer." |
| 3. "How do you prevent hallucination?" | "RAG with citations. Confidence-based routing. The eval-set-as-spec regression check. Force 'I don't know' as a valid response. Reduce temperature for high-stakes queries." |
| 4. "How do you prevent jailbreak?" | "Input-side classifier (Llama Guard, Prompt Guard). Output-side classifier. Constitutional AI principles in the system prompt. Red-team eval set. Rate limit on suspicious patterns." |
| 5. "Why is the cost so high?" | "Inference is dominated by the memory bandwidth of the GPU, not the FLOPS. A 70B model in FP16 needs 140GB of memory; one H100 has 80GB. So you need 2×H100 minimum, plus the KV cache. Per-token cost reflects GPU-amortized cost." |

---

## The 5 anti-patterns for LLM fundamentals

1. **Naming a single paper.** "Attention is all you need" is one paper in a 7-year arc. The candidate who only knows one paper is signaling they read the headline, not the field.
2. **Skipping the lifecycle.** Pre-training, SFT, RLHF, deployment — each stage has different failure modes. The candidate who only knows the architecture is signaling they can read a paper, not ship a model.
3. **Skipping the cost model.** The candidate who doesn't mention **per-token cost + GPU amortization + context window cost** is signaling they don't ship AI.
4. **Skipping the failure modes.** The candidate who doesn't name **hallucination + jailbreak + drift + bias + sycophancy + reasoning failures** is signaling they don't operate a GenAI system.
5. **Skipping the mitigations.** The candidate who names a failure mode but no mitigation is signaling they can identify problems, not fix them.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the difference between RLHF and DPO?" | "RLHF trains a reward model on human preferences, then uses PPO to optimize the SFT model against the reward model. DPO skips the reward model and directly optimizes the SFT model against the preference data using a closed-form objective. DPO is simpler + cheaper; RLHF is more flexible." |
| 2. "Why is inference so expensive compared to training?" | "Training is one-time; inference is per-query. A model that's trained once and queried 1B times has inference costs that dwarf training costs. This is why model serving is the largest line item in AI company financials." |
| 3. "How do you serve a 70B model on 1 GPU?" | "Quantization (INT4, INT8), paged attention (vLLM), speculative decoding, model parallelism (tensor parallel across 2-4 GPUs). You can serve a 70B model on 1×H100 with INT4 quantization at 30 tokens/sec." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The agent architecture built on LLM fundamentals |
| `../company-experiences/anthropic-fde-customer-simulation.md` | The Constitutional AI depth signal |
| `../company-experiences/meta-fde-ai-engineer.md` | The open-weight + on-device + safety story |

---

## The thesis

**LLM fundamentals is the canonical FDE GenAI primer.** The candidate who can explain **attention + lifecycle + failure modes + cost model** in 4 minutes — without naming a single equation — is signaling they can own a GenAI system.

**The 4-section answer (architecture, lifecycle, failure modes, cost) is the muscle memory.** The 5 questions are the practice bank. The 5 anti-patterns are the disqualifiers.

**General prep gets you past the resume screen. LLM fundamentals prep gets you past the GenAI depth round at Anthropic, OpenAI, Sierra AI, LangChain, Meta, Google, and Microsoft.**
