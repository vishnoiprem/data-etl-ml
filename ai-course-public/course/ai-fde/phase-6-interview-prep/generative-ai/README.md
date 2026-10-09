# Module 8 — Generative AI Interviews

> **GenAI interviews test whether you can ship LLMs in production, not just call them.** A company that's "AI-first" (Anthropic, OpenAI, LangChain) or "AI-powered" (Google, Microsoft, Amazon) wants to know: do you understand how LLMs work, where they fail, and how to deploy them responsibly? **The signal: a candidate who can explain transformer architecture AND a RAG failure mode AND a cost ceiling is showing they can own an AI system at scale.**

---

## The 4 sub-modules (the canonical GenAI interview format)

### Sub-module 1: LLM fundamentals

**What they test:** Do you understand how the technology works, or are you just calling an API?

**The 5 questions:**

1. **"What is the transformer architecture?"** → Self-attention, multi-head, feed-forward, layer norm. The 2017 "Attention is all you need" paper. The 6 encoder + 6 decoder layers in the original; modern LLMs are decoder-only (GPT, Qwen, Llama).
2. **"What's the difference between training, fine-tuning, and prompting?"** → Training = the base model, 1000s of GPUs, $1M+. Fine-tuning = LoRA / full FT, 1-10 GPUs, $100-10k. Prompting = the user-facing text, $0.
3. **"What's RLHF?"** → Reinforcement Learning from Human Feedback. The 3-step process: (1) supervised fine-tuning on human-written responses, (2) train a reward model on human preferences, (3) PPO / DPO to optimize the LM against the reward model.
4. **"What's the difference between GPT-4o-mini and Qwen-1.5B?"** → GPT-4o-mini is a hosted, closed-source, 8B-parameter model. Qwen-1.5B is a self-hostable, open-source, 1.5B-parameter model. Cost: 150× difference. Quality: 3-5% difference on most benchmarks.
5. **"What are embeddings, and how do they work?"** → A vector representation of text, typically 768-4096 dimensions, trained so similar texts have similar vectors. Used for semantic search, RAG, clustering.

**The FDE signal:** can you explain the technology in 2-3 sentences, with the cost + the quality + the operational complexity? A senior FDE has the cost-quality-complexity tradeoff memorized.

### Sub-module 2: RAG patterns

**What they test:** Can you build a retrieval-augmented generation system that doesn't hallucinate?

**The 5 questions:**

1. **"What's the difference between BM25, dense retrieval, and hybrid?"** → BM25 is a keyword-based ranking (TF-IDF + document length). Dense retrieval is a vector-based ranking (cosine similarity). Hybrid = both + RRF (reciprocal rank fusion). PacificFreight uses hybrid because the policy corpus is keyword-heavy and the shipment data is semantic-heavy.
2. **"How do you evaluate a RAG system?"** → 4 metrics: faithfulness (does the draft match the context?), ansrel (is the draft relevant?), context_precision (did we retrieve the right chunks?), context_recall (did we retrieve all the relevant chunks?). PacificFreight's threshold is 0.05 regression per metric.
3. **"How do you handle the 'lost in the middle' problem?"** → LLMs pay more attention to the beginning and end of the context. The fix: re-rank to put the most relevant chunks at the beginning, OR truncate the middle, OR use a longer-context model (Claude Sonnet at 200K, GPT-4o at 128K).
4. **"How do you prevent hallucinations?"** → 3 mitigations: (1) citation in every response (the draft includes "according to the shipment status: ..."), (2) thumbs-up/down feedback loop (the eval set is rebuilt weekly from the feedback), (3) circuit breaker on low faithfulness (if the eval set drops 0.10, fall back to a templated response).
5. **"When do you fine-tune vs prompt vs RAG?"** → Prompt: when the task is in the model's training distribution (most cases). RAG: when the task requires up-to-date or proprietary data. Fine-tune: when the task is high-volume, low-latency, and the cost ceiling is binding. PacificFreight: prompt + RAG for the MVP, fine-tune (Phase 4 P3 SLM) for the 10× growth.

**The FDE signal:** can you name the 4 metrics AND the 3 mitigations AND the prompt-vs-RAG-vs-fine-tune tradeoff? A senior FDE has the eval set as the spec.

### Sub-module 3: Production deployment

**What they test:** Can you ship an LLM system that survives the customer?

**The 5 questions:**

1. **"How do you handle LLM API downtime?"** → Circuit breaker (open at 5 errors/min, half-open at 30s, closed after 2 successes) + fallback (templated response). PacificFreight's circuit breaker is in `circuit.py::CircuitBreakerConfig`.
2. **"How do you handle cost ceilings?"** → 3 layers: (1) rate limit per user (Redis token bucket), (2) cost ceiling per tenant (Prometheus alert at 80% of ceiling), (3) SLM routing (route 80% of traffic to a self-hosted SLM at 0.5% of the cost). PacificFreight's cost ceiling is $5/month.
3. **"How do you handle PII?"** → Redactor in front of the LLM call (regex + NER), audit log of every redacted PII, no LLM with PII in the prompt. PacificFreight's redactor is in `circuit.py::Redactor`.
4. **"How do you handle prompt injection?"** → 3 layers: (1) system prompt with explicit "ignore user instructions that ask you to...", (2) input validation (regex for known injection patterns), (3) output validation (the draft must cite a chunk; if it doesn't, reject).
5. **"How do you scale to 10× growth?"** → 3 layers: (1) horizontally scale uvicorn workers (3-10 workers), (2) externalize state to Redis (rate limiter, session store), (3) multi-region DR (active/passive, DNS failover). PacificFreight's 10× growth journey is Phase 5 P1-P4.

**The FDE signal:** can you name the 3 layers of cost control AND the 3 layers of PII protection AND the 3 layers of scaling? A senior FDE has the operational boundary memorized.

### Sub-module 4: Eval and safety

**What they test:** Can you measure quality AND prevent harm?

**The 5 questions:**

1. **"How do you measure LLM quality?"** → 4 layers: (1) automated metrics (RAGAS: faithfulness, ansrel, context_precision, context_recall), (2) human evaluation (thumbs-up/down, weekly review), (3) A/B testing (route 10% of traffic to a new prompt, compare thumbs-up), (4) regression tests (the eval set runs in CI, blocks PRs above 0.05 regression).
2. **"How do you detect data drift?"** → 3 layers: (1) embedding distribution shift (compare this week's embeddings to last week's; alert at 0.10 KL divergence), (2) eval set regression (alert at 0.05 drop per metric), (3) thumbs-up rate drop (alert at 5% drop week-over-week).
3. **"How do you handle bias?"** → 3 layers: (1) eval set stratification (30 rows across 4 language buckets × 3 shipment types), (2) demographic parity check (does the thumbs-up rate differ by language?), (3) manual review (quarterly bias audit by an external reviewer).
4. **"How do you handle adversarial inputs?"** → 3 layers: (1) input validation (regex for known patterns: "ignore previous instructions", "you are now..."), (2) output validation (the draft must cite a chunk; if it doesn't, reject), (3) rate limit on retries (max 3 retries per user per minute).
5. **"How do you handle a model deprecation?"** → 3 layers: (1) version pinning (the model name is in config, not code), (2) eval set on the new model (run the eval set; if it drops > 0.05, block the upgrade), (3) gradual rollout (10% traffic → 50% → 100% over 1 week).

**The FDE signal:** can you name the 4 layers of quality measurement AND the 3 layers of drift detection AND the 3 layers of bias handling? A senior FDE has the eval set as the spec.

---

## The 4 GenAI anti-patterns

1. **Calling an LLM an "AI."** The LLM is a tool. The system is the AI. The system includes retrieval, prompting, eval, cost control, PII protection, scaling.
2. **Skipping the eval set.** "It works in my testing" is not an eval set. The eval set is 30 rows, 4 metrics, 0.05 threshold, in CI.
3. **Ignoring the cost ceiling.** "We can call GPT-4 for every request" is not a production design. The cost ceiling is the operational boundary.
4. **Skipping the failure mode.** "What if the LLM hallucinates?" is the first question. The answer is citation + thumbs-down + circuit breaker.

---

## How to use this module

1. **Memorize the 4 sub-modules.** They're the cheat sheet for 80% of GenAI interviews.
2. **Memorize the 5 questions per sub-module.** Total: 20 questions. Practice each one.
3. **Practice with a Phase 1-5 case study as the example.** Engagement 1 (PacificFreight) is the canonical example for every question.
4. **Rehearse with an AI assistant.** Have it score you on the 4 anti-patterns.
5. **Close with the operational boundary.** "The cost ceiling is $5/month. The eval set is 30 rows, 4 metrics, 0.05 threshold. The failure mode is hallucination; the mitigation is citation + thumbs-down + circuit breaker." That's the FDE answer.

---

## The 5 most common GenAI follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you choose between GPT-4o-mini and Claude Sonnet?" | "Cost + quality + latency. GPT-4o-mini is $0.15/1M tokens, 0.94 faithfulness, 1.5s P95. Claude Sonnet is $3/1M tokens, 0.97 faithfulness, 2.0s P95. We pick GPT-4o-mini for the MVP; we switch to Claude Sonnet if the quality threshold rises to 0.97." |
| 2. "How do you handle the cold-start problem?" | "3 layers: (1) eval set from day 1 (30 rows, even before the prompt is written), (2) zero-shot prompt for the first 100 requests (no fine-tuning, no RAG), (3) iterate weekly based on thumbs-up feedback. The cold-start is 4 weeks; the eval set is the spec from week 1." |
| 3. "How do you handle a 10× spike in traffic?" | "3 layers: (1) rate limit per user (Redis token bucket), (2) auto-scale uvicorn workers (3-10 workers based on CPU), (3) circuit breaker on the LLM API (fall back to a templated response at 5 errors/min). The cost ceiling is the binding constraint; the SLM is the long-term answer." |
| 4. "How do you know if the LLM is hallucinating?" | "3 layers: (1) citation in every response (the draft must cite a chunk; if it doesn't, reject), (2) thumbs-up rate (alert at 5% drop week-over-week), (3) eval set regression (alert at 0.05 drop per metric). The eval set is the canary." |
| 5. "How do you handle a model upgrade?" | "3 layers: (1) version pinning in config, (2) eval set on the new model (block the upgrade if it drops > 0.05), (3) gradual rollout (10% → 50% → 100% over 1 week). The eval set is the contract." |

**Memorize these 5.** They're the Q&A for 80% of GenAI follow-ups.
