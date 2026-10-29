# Lesson 1 — The AI Engineering Interview Question Bank

> **Type:** Article + Worked Example · Module 18
> The 100 questions every AI engineer gets asked, organized by module, with the model answer, the trap, and what the interviewer is actually testing.

---

## How to use this lesson

Each question has:
- **The question** (verbatim or paraphrased — these appear in real interviews)
- **What the interviewer is testing** (the skill behind the question)
- **The model answer** (what a senior engineer says)
- **The trap** (the wrong answer that 70% of candidates give)
- **Follow-ups** (what they ask next)

This is a reference, not a script. Read it once. Re-read it the night before each interview.

---

## Module 1 — ML Foundations

### Q1: "Explain bias-variance tradeoff."

**Testing:** Core ML intuition.

**Trap:** "Bias is when the model is wrong, variance is when it overfits." (Circular, useless.)

**Model answer:** Bias is the error from a model that's too simple to capture the signal (underfit → high training error AND high test error). Variance is the error from a model that's too sensitive to the training data (overfit → low training error, high test error). The total error = bias² + variance + irreducible noise. As you increase model capacity, bias drops and variance rises. The sweet spot is where the sum is minimized.

**Follow-up:** "How does regularization affect the tradeoff?" (L2/L1 raise bias, lower variance.)

### Q2: "What's the difference between L1 and L2 regularization?"

**Testing:** Practical knowledge of regularization.

**Model answer:** Both add a penalty to the loss to discourage large weights. L2 penalizes the sum of squared weights; L1 penalizes the sum of absolute values. L2 spreads the penalty across all weights (small effect on all); L1 drives many weights to exactly zero (feature selection). L2 is the default; L1 is used when you want a sparse model.

**Follow-up:** "Why does L1 produce sparsity but L2 doesn't?" (Subgradient of L1 is constant; gradient of L2 grows with weight magnitude.)

### Q3: "When would you use precision-recall AUC over ROC AUC?"

**Testing:** Choosing the right metric.

**Model answer:** ROC AUC plots TPR vs FPR. PR AUC plots precision vs recall. ROC AUC is misleading on heavily imbalanced data — a model that predicts "always negative" gets 0.5 ROC AUC but 0.0 PR AUC. Use PR AUC when the positive class is rare (< 10%) or when false positives are much more costly than false negatives.

**Follow-up:** "How do you pick the threshold?" (Depends on the business cost of FP vs FN.)

### Q4: "Walk me through gradient descent."

**Testing:** Optimization fundamentals.

**Model answer:** Iterative algorithm to minimize a loss function. At each step, compute the gradient of the loss w.r.t. the parameters, then take a small step in the opposite direction. Three variants: batch (uses all data per step — slow, stable), stochastic (one example per step — fast, noisy), mini-batch (32-512 examples — best of both). Learning rate is the most important hyperparameter.

**Follow-up:** "What if the loss surface has saddle points?" (SGD escapes them naturally because of the noise; Adam normalizes per-parameter, which can hurt.)

### Q5: "Explain cross-entropy loss."

**Testing:** Loss functions for classification.

**Model answer:** For binary classification with predicted probability p and true label y ∈ {0,1}: L = -[y log p + (1-y) log(1-p)]. For multi-class: L = -Σ y_i log p_i (where y is one-hot). It's the negative log-likelihood under a Bernoulli/Categorical distribution. Minimizing cross-entropy is equivalent to maximizing likelihood.

**Follow-up:** "Why not use MSE for classification?" (Gradient vanishes when predictions are very wrong; doesn't penalize confident wrong answers enough.)

---

## Module 2 — Deep Learning

### Q6: "Why do we need non-linear activation functions?"

**Trap:** "To add complexity." (Vague.)

**Model answer:** Without non-linearities, a stack of linear layers collapses into a single linear transformation (matrix multiplication is associative). So a 100-layer linear network is the same as a 1-layer linear network. Non-linearities (ReLU, GELU, sigmoid) break this collapse and let the network approximate arbitrary functions. Universal approximation theorem requires at least one non-linear layer.

**Follow-up:** "Why is ReLU preferred over sigmoid?" (Sigmoid saturates → vanishing gradient; ReLU has constant gradient for positive inputs.)

### Q7: "What happens if you initialize all weights to zero?"

**Model answer:** Every neuron in a layer computes the same output, gets the same gradient, and updates to the same value. The network can't break symmetry — all neurons stay identical forever. This is called the "symmetry problem." Fix: random initialization (He, Xavier, Kaiming).

### Q8: "Explain batch normalization."

**Model answer:** Normalize the activations of a layer to zero mean and unit variance, then scale and shift with learned parameters. Two benefits: (1) faster convergence because the loss surface is smoother, (2) mild regularization because each batch has different statistics. Drawbacks: behaves differently in train vs eval mode; not great for RNNs (layer norm is preferred there).

**Follow-up:** "What's the difference between BN, LN, InstanceNorm, GroupNorm?" (Different axes over which you compute mean/variance.)

### Q9: "What is the vanishing gradient problem and how do you fix it?"

**Model answer:** In deep networks, gradients are multiplied through the chain rule. If each layer's gradient magnitude is < 1, the product shrinks exponentially with depth — early layers get near-zero gradient and don't learn. Fixes: ReLU activation, residual connections, batch normalization, LSTM/GRU for RNNs, careful initialization.

### Q10: "Why do residual connections work?"

**Model answer:** ResNet's `y = F(x) + x` lets the gradient flow through the skip connection unchanged. Even if F's gradient is small, the gradient through the skip is 1, so the early layers always get a usable signal. This makes it practical to train 100+ layer networks.

**Follow-up:** "Is it the same as an LSTM's gating?" (Loosely — both create a path for gradient to bypass transformations.)

---

## Module 3 — Transformer Architecture

### Q11: "Explain self-attention."

**Model answer:** For each token, compute three vectors: Q (query), K (key), V (value). Attention = softmax(QK^T / √d_k) V. Each token's output is a weighted sum of all tokens' values, weighted by how relevant each is to this query. Multi-head attention runs this in parallel with different learned projections, then concatenates.

**Follow-up:** "Why scale by √d_k?" (Without it, dot products grow with dimension; softmax saturates; gradients vanish.)

### Q12: "What's the computational cost of self-attention?"

**Model answer:** O(n²d) for sequence length n, embedding dim d. The QK^T matrix is n×n. For n=2048, that's 4M entries — manageable. For n=100K, it's 10B — prohibitive. This is why long-context models need sparse attention, linear attention, or SSMs.

### Q13: "Why positional encodings?"

**Model answer:** Self-attention is permutation-invariant — it treats the input as a set, not a sequence. Without positional information, "the cat sat on the mat" and "the mat sat on the cat" look identical. Positional encodings add a token-position-dependent signal, either fixed (sinusoidal) or learned.

**Follow-up:** "Why sinusoidal?" (Allows extrapolation to longer sequences than seen in training; relative positions have a fixed linear transformation.)

### Q14: "What's the difference between encoder-only, decoder-only, and encoder-decoder models?"

**Model answer:** Encoder (BERT) — bidirectional attention, good for understanding/classification. Decoder (GPT) — causal (masked) attention, good for generation. Encoder-decoder (T5, original Transformer) — encoder reads input, decoder generates output; good for translation/summarization.

### Q15: "Explain Grouped Query Attention."

**Model answer:** Multi-head attention has separate K, V projections per head → lots of memory for KV cache. GQA shares K, V across groups of heads. MQA (Multi-Query) shares across all heads; GQA is the middle ground. Used in Llama-2 70B, Mistral, and most modern models. Cuts KV cache size 4-8× with minimal quality loss.

---

## Module 4 — How LLMs Generate Text

### Q16: "How does temperature affect generation?"

**Model answer:** Temperature scales the logits before softmax. T=0 picks the argmax (greedy, deterministic). T=1 samples from the original distribution. T>1 flattens the distribution (more random, more creative). T<1 sharpens it (more focused). T=0.7 is the typical "chat" default.

**Follow-up:** "When would you use T=0 vs T=0.7?" (T=0 for code/factual; T=0.7+ for creative writing.)

### Q17: "What is nucleus (top-p) sampling?"

**Model answer:** Sample from the smallest set of tokens whose cumulative probability ≥ p. E.g., top-p=0.9 keeps the 90% mass and renormalizes. Avoids sampling very low-probability tokens that would be off-topic. Often combined with temperature.

### Q18: "Explain beam search."

**Model answer:** Keep the top-k partial sequences at each step (k = beam width). At each step, expand each by one token, keep the top-k overall. Returns the highest-probability sequence (not necessarily the most natural). Used in machine translation; less used in modern LLM chat.

### Q19: "What's the difference between greedy decoding and beam search?"

**Model answer:** Greedy picks the single highest-prob token at each step. Beam search tracks k beams and picks the best overall sequence. Beam search is better in theory but often worse in practice for open-ended generation (it produces short, generic outputs).

---

## Module 5 — Modern LLM Architecture

### Q20: "Explain Mixture of Experts (MoE)."

**Model answer:** Replace the dense FFN layer with N "expert" FFNs and a router that picks the top-k for each token. Only k experts run per token → total FLOPs are a fraction of dense, but total parameters grow. E.g., Mixtral 8x7B has 47B total params but uses ~13B per token.

**Follow-up:** "What are the load-balancing challenges?" (If the router collapses to using only a few experts, you lose the capacity benefit; auxiliary loss terms force balance.)

### Q21: "What's the difference between RoPE and absolute positional embeddings?"

**Model answer:** Absolute embeddings add a learned vector to each token based on its position. RoPE (Rotary Position Embedding) rotates the Q and K vectors by an angle that depends on position. This makes attention scores depend on relative position directly — and allows length extrapolation by interpolating the rotation frequencies.

### Q22: "What is Flash Attention?"

**Model answer:** An algorithm to compute exact attention without materializing the full n×n attention matrix in HBM. Uses tiling and recomputation: load Q, K, V tiles into SRAM, compute partial softmax online, write the output. Memory drops from O(n²) to O(n). 2-4× speedup on A100/H100.

### Q23: "Why are SLMs (small language models) becoming more popular?"

**Model answer:** Three reasons: (1) inference cost is 10-100× lower, (2) they fit on a single GPU or even a phone, (3) for many tasks, the gap to a large model is < 5pp. The 2025 trend: domain-specific 7B models beating GPT-4 on their narrow task.

---

## Module 6 — Types of Language Models

### Q24: "When would you use an SLM vs a large proprietary model?"

**Model answer:** SLM when: (1) high-volume inference where cost matters, (2) low-latency requirement (< 100ms), (3) on-device / edge deployment, (4) data privacy requires self-hosting, (5) narrow task the SLM is fine-tuned for. Large proprietary when: (1) complex reasoning, (2) long-tail knowledge, (3) low volume, (4) no in-house ML team.

### Q25: "What is an embedding model and when would you fine-tune one?"

**Model answer:** An embedding model maps text to a dense vector such that semantically similar texts have high cosine similarity. Fine-tune when: (1) your domain has unusual vocabulary (legal, medical), (2) the base model doesn't capture the distinctions you care about, (3) you have 1K+ labeled pairs of (query, relevant_doc).

### Q26: "When would you use a code-specific model like Codex or Code Llama?"

**Model answer:** For code completion, bug fixing, code explanation, and PR review — they're pre-trained on huge code corpora and understand syntax natively. Not better at general reasoning. Don't use for non-code text generation.

---

## Module 7 — Training, Fine-Tuning, Alignment

### Q27: "What's the difference between pre-training, fine-tuning, and RLHF?"

**Model answer:** Pre-training: train from scratch on huge unlabeled corpus, next-token prediction objective. Fine-tuning: supervised training on labeled task data (SFT). RLHF: use human preferences to train a reward model, then optimize the policy with PPO or DPO. The order in modern training: pretrain → SFT → preference optimization.

### Q28: "Explain LoRA."

**Model answer:** Low-Rank Adaptation. Freeze the original weights W and learn a low-rank update: ΔW = A·B where A is d×r and B is r×k, with r << min(d,k). Total trainable params drop 100-1000×. At inference, merge ΔW back into W for zero added latency.

**Follow-up:** "What's QLoRA?" (LoRA + 4-bit quantized base model — fits 65B on a single 48GB GPU.)

### Q29: "What is DPO?"

**Model answer:** Direct Preference Optimization. Skip the reward model. Given (prompt, chosen, rejected) triples, train the model directly to make chosen more likely and rejected less likely. Simpler, more stable than RLHF; comparable quality.

### Q30: "How much data do you need to fine-tune an LLM?"

**Model answer:** For SFT on a narrow task: 1K-10K examples. For DPO: 1K-50K preference pairs. For continued pretraining on a new domain: 100M-1B tokens. For full pretraining from scratch: trillions of tokens.

---

## Module 8 — Prompt & Context Engineering

### Q31: "Explain chain-of-thought prompting."

**Model answer:** Instead of asking the model to answer directly, ask it to think step by step before giving the final answer. The reasoning trace lets the model "spend more compute" at inference. Improves math, logic, multi-step tasks by 20-40pp. Variants: zero-shot ("Let's think step by step"), few-shot (include worked examples), self-consistency (sample N times, majority vote).

### Q32: "What's the difference between prompt engineering and context engineering?"

**Model answer:** Prompt engineering = crafting the instruction. Context engineering = assembling everything the model sees: system prompt, retrieved docs, tool definitions, conversation history, few-shot examples. Context engineering is the broader, more important discipline.

### Q33: "How do you fit a 100-page document into the context window?"

**Trap:** "Just paste it." (Hits the context length limit.)

**Model answer:** Chunk the document, embed each chunk, retrieve top-k relevant chunks at query time (RAG). Alternatively, summarize each chunk with the model, embed the summaries. Don't blindly stuff the context — long contexts are slow AND the model loses focus in the middle ("lost in the middle" problem).

---

## Module 9 — Vector Search & RAG

### Q34: "Explain HNSW."

**Model answer:** Hierarchical Navigable Small World. A graph-based ANN index where each vector is a node connected to its neighbors. Multi-layer: top layer has few long-range edges, bottom layer has many short-range edges. Search starts at the top, greedily walks down to the bottom. O(log n) per query with > 95% recall.

**Follow-up:** "Compare HNSW vs IVF." (HNSW is faster at high recall; IVF uses less memory; production usually picks HNSW.)

### Q35: "How do you evaluate a RAG system?"

**Model answer:** Four axes: (1) retrieval quality — recall@k, MRR against a labeled set; (2) answer faithfulness — LLM-judge checks if the answer is supported by the retrieved context; (3) answer relevance — LLM-judge checks if the answer addresses the question; (4) end-to-end — human eval on a sample.

### Q36: "What's the chunking strategy?"

**Model answer:** Trade-off between context and specificity. Smaller chunks (200 tokens) → more precise retrieval but less context per chunk. Larger chunks (1000 tokens) → more context but noisier retrieval. Default: 500 tokens with 50-token overlap. For structured docs: respect section boundaries. For code: respect function/class boundaries.

### Q37: "What is hybrid search?"

**Model answer:** Combine BM25 (keyword) search with vector (semantic) search. Score = α · BM25 + (1-α) · vector. Hybrid wins when the query has rare terms (BM25) AND semantic intent (vector). Most production RAG uses hybrid.

---

## Module 10 — AI Agents

### Q38: "What is an AI agent?"

**Model answer:** An LLM plus a goal, tools it can call, memory of what it's done, and a loop that runs until the goal is reached. The loop is: think → act → observe → repeat. Agents handle multi-step tasks where the next step depends on the previous step's result.

### Q39: "When should you use an agent vs a chain?"

**Model answer:** Chain when the steps are known upfront and don't depend on intermediate results. Agent when the next step depends on what the model just learned. Rule of thumb: if you can draw the steps on a whiteboard, you don't need an agent.

### Q40: "What are the common failure modes of agents?"

**Model answer:** (1) Runaway loops — agent keeps calling tools past max_steps. (2) Hallucinated tool calls — invents a tool that doesn't exist. (3) Wrong arguments — passes malformed args. (4) Infinite retry — same tool, same bad args. (5) Skipped tools — knows it should use a tool but doesn't. (6) Stuck planning — keeps planning, never executes.

### Q41: "What's the ReAct pattern?"

**Model answer:** Reason + Act. The model emits a thought, then an action, then observes the result, then repeats. The interleaving forces the model to verbalize its reasoning, which improves both accuracy and debuggability.

---

## Module 11 — Harness Engineering

### Q42: "What's a harness?"

**Model answer:** Everything around the raw agent loop: input validation, tool retry, timeouts, observability, cost tracking, eval hooks, output filtering. Without the harness, the agent works in a notebook; with it, in production. Senior engineers spend 80% of their time on the harness, 20% on the agent.

### Q43: "Why use Pydantic for tool schemas?"

**Model answer:** The model hallucinates tool arguments. Pydantic validates every call before execution. If the model says `calculator(expression="import os")`, Pydantic raises. The contract is enforced.

### Q44: "How do you track cost per agent run?"

**Model answer:** Sum input_tokens × input_price + output_tokens × output_price across all LLM calls in the run. Persist per-run cost to a database. Alert on runs > some threshold (e.g., $0.50). Without this, you can't defend a model change.

---

## Module 12 — LLM Inference

### Q45: "What's TTFT vs TPOT?"

**Model answer:** TTFT (Time To First Token) — how fast the user sees the start of the response. Matters for chat UX. TPOT (Time Per Output Token) — how fast subsequent tokens arrive. Matters for streaming quality. Good baseline: TTFT < 200ms, TPOT < 50ms.

### Q46: "Explain KV cache."

**Model answer:** During decoding, we re-use the K and V projections from previous tokens instead of recomputing them. Memory grows linearly with sequence length × num_layers × num_heads × head_dim. For Llama-3-8B with 8K context, KV cache is ~2 GB per sequence. This is the biggest single win for inference (7× latency reduction).

### Q47: "What is continuous batching?"

**Model answer:** Traditional batching waits for the longest sequence in the batch to finish. Continuous batching inserts new sequences into the GPU as soon as one finishes. vLLM pioneered this with PagedAttention. 20-30× throughput improvement at high concurrency.

### Q48: "Explain speculative decoding."

**Model answer:** A small "draft" model proposes K tokens; the large model verifies all K in one forward pass. Accepted tokens get a ~2× speedup. Works because verification is cheap (one forward pass for K tokens) and most draft tokens are accepted.

### Q49: "When would you use INT4 quantization?"

**Model answer:** When you need the model to fit in less GPU memory (4× reduction), at the cost of small quality loss (~1-2pp). Production inference on cost-sensitive workloads.

---

## Module 13 — Evaluation

### Q50: "How do you evaluate an LLM app?"

**Model answer:** Three layers: deterministic (format, schema, regex — runs on 100% of data), LLM-as-judge (semantic quality — runs on all or sampled), human (gold standard — sample 1-5%). Measure LLM-judge correlation with humans; only trust judge scores with r > 0.7.

### Q51: "What's LLM-as-judge bias?"

**Model answer:** Three biases: (1) position bias — prefers the answer in position A. (2) verbosity bias — prefers longer answers. (3) self-preference — prefers its own style. Mitigations: randomize position, control length, use a different model as judge.

### Q52: "What's pairwise comparison?"

**Model answer:** "Which is better, A or B?" instead of "Rate A from 1-5." Pairwise is much more reliable because the model just picks, doesn't estimate. Used to compare prompt versions, model versions, fine-tuned vs base.

---

## Module 14 — Safety & Security

### Q53: "What is prompt injection?"

**Model answer:** Adversarial text in the prompt (or in retrieved data) that tries to hijack the model. Direct injection: attacker types it. Indirect injection: attacker plants it in data the model retrieves (e.g., a poisoned web page).

### Q54: "How do you defend against prompt injection?"

**Model answer:** Layered: (1) input filter for known patterns, (2) prompt isolation — wrap untrusted content in delimiters, (3) output validation — strip PII and banned tokens, (4) structured output — JSON schema prevents free-form text leakage, (5) tool allowlist + confirmation for sensitive actions. No single layer is enough.

### Q55: "What's the difference between prompt injection and a jailbreak?"

**Model answer:** Jailbreak targets the model's safety training ("DAN", roleplay). Prompt injection targets the application's behavior (data exfiltration, goal hijack). Different defenses: jailbreaks need better training data; injection needs app-level validation.

---

## Module 15 — Multimodal

### Q56: "Explain the Vision Transformer."

**Model answer:** Split image into 16×16 patches. Linearly project each patch to an embedding. Prepend a learnable [CLS] token. Add positional embeddings. Run through N Transformer encoder layers. The [CLS] token's final state goes to a classification head.

### Q57: "How does diffusion work?"

**Model answer:** Forward process: gradually add Gaussian noise to an image over T steps. Reverse process: train a model to predict the noise at each step. At inference, start from pure noise and iteratively denoise. The model is typically a U-Net.

### Q58: "What is classifier-free guidance?"

**Model answer:** Train one model that does both conditional (with text prompt) and unconditional generation. At inference, push the prediction away from unconditional and toward conditional: output = uncond + s · (cond - uncond). The scaling factor s controls how strongly to follow the prompt. Default s=7.5 in Stable Diffusion.

---

## Module 16 — Infrastructure

### Q59: "When do you self-host an LLM vs use an API?"

**Model answer:** Self-host when: (1) high volume (>10M tokens/day) — APIs become expensive, (2) data privacy required, (3) need a fine-tuned model that's hard to serve, (4) latency critical and you're near the model. API when: low volume, general purpose, no ML team, time-to-market matters.

### Q60: "What's the difference between vLLM, TGI, and TensorRT-LLM?"

**Model answer:** All are production inference servers. vLLM — PagedAttention + continuous batching, easy to use, Python. TGI (HuggingFace) — Rust, good multi-GPU support. TensorRT-LLM (NVIDIA) — fastest on NVIDIA hardware, requires more setup.

### Q61: "What is prefill-decode disaggregation?"

**Model answer:** Run prefill and decode on separate GPU pools. Prefill is compute-bound (batch many requests); decode is memory-bound (one token at a time, KV-heavy). Disaggregating lets each run on hardware optimized for its bottleneck. Used at scale by major serving systems.

---

## Module 17 — Frontier

### Q62: "What is JEPA?"

**Model answer:** Joint Embedding Predictive Architecture. Predict the embedding of future inputs, not the inputs themselves. Loss is in embedding space. Avoids the hallucination problem of generative models. Designed for video understanding, robotics, continuous-world reasoning.

### Q63: "What's the alternative to next-token prediction?"

**Model answer:** JEPA (predict embeddings), diffusion (iteratively denoise), flow matching (learn a continuous flow between distributions), SSMs (state-space models for long sequences). Each has different trade-offs.

---

## Module 18 — Interviewing

### Q64: "How do you debug a hallucinating RAG system?"

**Model answer:** Step by step: (1) is the right doc being retrieved? (top-k relevance score, manual inspection), (2) is the LLM citing the right doc? (citation check), (3) is the LLM fabricating beyond the docs? (faithfulness judge), (4) is the chunking losing context? (try larger chunks), (5) is the embedding model wrong for the domain? (fine-tune). Most issues are at steps 1 or 5.

### Q65: "How would you reduce LLM API cost by 10×?"

**Model answer:** Layered approach: (1) cache identical/similar prompts (Redis + semantic cache) → 30-50% savings. (2) Switch to a smaller model for simple queries (routing) → 3-5× savings on those. (3) Compress prompts — strip whitespace, shorten system prompt. (4) Reduce output length — set max_tokens, prompt for brevity. (5) Batch requests. (6) Self-host if volume is high enough.

### Q66: "Walk me through deploying an LLM app to production."

**Model answer:** Eval harness first (offline). Then: API endpoint with rate limiting, auth, request validation. Logging/observability (LangSmith or Langfuse). Cost tracking. Eval hook sampling 1% for human review. CI gate on eval set + cost. Canary deploy: 1% traffic → 10% → 100% with regression detection at each step. Rollback plan. Documentation.

### Q67: "How do you handle model deprecation?"

**Model answer:** Three-pronged: (1) abstraction — never call the model API directly; go through a wrapper that can swap models. (2) eval suite — run your eval on every candidate replacement before swapping. (3) migration window — keep both for 2 weeks, route 1% traffic to new model, compare.

---

## The "soft skills" questions

### Q68: "Tell me about a hard ML problem you solved."

**Testing:** Communication, depth, ownership.

**Model answer:** Use STAR. Situation: short context. Task: what was needed. Action: what YOU did (be specific about techniques, code, decisions). Result: quantified impact ($ saved, latency reduced, accuracy gained). 60 seconds max.

### Q69: "How do you stay current with AI?"

**Trap:** "I read papers on arXiv every day." (Unrealistic, performative.)

**Model answer:** A real answer — "I read the Papers With Hot Twitter Takes newsletter, follow specific researchers on X, and ship a small project every month to stay hands-on. I read 2-3 papers deeply per month, not 50 abstracts." Be specific.

### Q70: "What's your favorite recent AI paper and why?"

**Model answer:** Have ONE paper you can discuss in 5 minutes. Know: the problem, the method, the result, the limitation, and what you'd do differently. Good picks: Flash Attention (engineering), Constitutional AI (alignment), Self-Consistency (reasoning), any recent SOTA on a benchmark you care about.

---

## Worked Example — practice the bank

> **Goal:** Pick 10 questions at random, time yourself at 2 minutes each. Record your answers. Compare to the model answers. The first time you do this you'll discover huge gaps.

```python
import random, time

QUESTIONS = [q1, q2, ..., q70]   # the 70 questions above

random.shuffle(QUESTIONS)
for q in QUESTIONS[:10]:
    print(f"\nQ: {q['question']}")
    t0 = time.perf_counter()
    answer = input("Your answer: ")
    elapsed = time.perf_counter() - t0
    
    print(f"\nTime: {elapsed:.1f}s")
    print(f"Model answer: {q['model_answer']}")
    print(f"Trap: {q['trap']}")
    
    # Self-grade
    score = int(input("Did you mention the key idea? (0/1): "))
    q['my_score'] = score

# After 10 questions, compute overall readiness
total = sum(q.get('my_score', 0) for q in QUESTIONS[:10])
print(f"\nReadiness: {total}/10")
# 8+ : ready for senior interviews
# 5-7: solid mid-level, study gaps
# < 5: needs more review
```

---

## What this lesson teaches

1. **70 questions cover the curriculum.** Every question maps to a module.
2. **The trap is the test.** Most candidates give the trap answer. Avoid it.
3. **Concrete > abstract.** The model answer is concrete and quantified. Yours should be too.
4. **Practice out loud.** Reading answers ≠ giving answers. Time yourself.
5. **Follow-ups reveal depth.** If they ask a follow-up, they liked your first answer.

Read this and you have a cheat sheet for the senior AI engineering interview loop.

---

## What Comes Next

> Lesson 2 — **System Design for AI Apps** — the 5 most common system-design prompts (chatbot, RAG, agent, voice, multimodal), with the senior-engineer answer.
