# Lesson 1.2: How LLMs Actually Work

> **The mental model you need before you ship anything to production.**
> 30-45 min. Concept-heavy. Code: tokenize text and watch the model split it.

## 🎯 Architect Level

- [ ] 🟢 **Junior (1-2 yrs)** — implement and run
- [ ] 🟡 **Mid (3-5 yrs)** — extend with monitoring
- [ ] 🟠 **Senior (6-10 yrs)** — add multi-tenancy
- [ ] 🔴 **Staff (10+ yrs)** — design the SLA, capacity model, incident playbook

> *Picking the right level is a one-time decision per lab. Pick the highest level you can honestly complete. Move up next time.*

---

## 🧠 Concept (5 min)

A Large Language Model is **two things stacked**:

1. **A tokenizer** — chops text into integer IDs the model understands. The same string "ChatGPT" might be 1 token, 2 tokens, or 3 depending on the model. Tokens ≠ words, ≠ characters.
2. **A transformer** — a giant stack of matrix multiplications + attention that, given the previous tokens, predicts the probability distribution over the next token. That's it. There is no "thinking." There is no "memory" beyond the context window.

This single design choice — **predict the next token** — is what makes modern LLMs both magical and brittle. Magical because next-token prediction, scaled to billions of parameters trained on most of the public internet, produces reasoning. Brittle because:
- The model has no ground truth. It can **hallucinate** with total confidence.
- The model has no memory. Every conversation must re-supply the full history.
- The model has no tools. To act, you must give it function calls.

For an architect, the operational consequences are:
- **Token costs scale linearly with context.** A 100K-token prompt costs 100× a 1K-token prompt.
- **Latency scales with output length**, not input (output is sequential; input is parallel).
- **Hallucination is a property, not a bug.** You need RAG, evals, or constraints to make it reliable.

Three mental models you must internalize:
- **Context window = RAM.** When it's full, older context falls out (or you summarize, or you RAG).
- **Temperature = dice roll.** 0 = greedy, 1 = creative. 0.7 is a sane default.
- **System prompt = configuration, not instruction.** It sets the persona, not the task.

---

## 🛠️ Build It (45 min)

### Spec

Build a small Python program that:
1. Loads a tokenizer (use `tiktoken`, the same tokenizer OpenAI uses)
2. Tokenizes 5 different strings of varying length
3. Prints the token IDs, the count, and the visual tokens (with spaces between)
4. Visualizes the tokenization with a colored ASCII bar (each `#` is one token)
5. Compares token counts between two different model encodings (e.g., `cl100k_base` vs `p50k_base`)

### Acceptance Criteria

**Functional:**
- [ ] The program runs without errors using only `tiktoken` (no OpenAI API key needed)
- [ ] Tokenizes at least 5 strings: a sentence, a code snippet, a URL, a number, a non-English string
- [ ] Shows both the token IDs and the human-readable tokens
- [ ] Renders an ASCII bar showing relative token counts
- [ ] Compares at least 2 different encodings

**Quality:**
- [ ] All functions have docstrings
- [ ] Code is readable in <5 minutes
- [ ] No magic numbers — use named constants

**Observability (Mid+):**
- [ ] Print the byte-pair encoding rule for at least one example
- [ ] Log the total tokens processed
- [ ] For Senior+: estimate cost at current OpenAI pricing

### Starter Code

Open `lesson-1-2-how-llms-work.py` in the same folder. It has a `TODO` per step.

### Solution

The same `.py` file has the complete solution after the `# === SOLUTION ===` divider. Run the file; the starter section runs first and demonstrates the concept, then the solution section shows a production-grade version.

---

## 🏛️ Architect Notes

### Trade-offs

| Choice | Pros | Cons | Pick when |
|---|---|---|---|
| `tiktoken` (OpenAI tokenizer) | Same as GPT-4, accurate cost estimates | Locked to OpenAI's encoding | You're using OpenAI models |
| `transformers` AutoTokenizer | Works with any HF model (Llama, Mistral) | Different IDs than OpenAI → cost surprises | You're mixing model families |
| Character-level | Trivial, no dependencies | 4-10× more tokens than BPE → costs explode | Never (just for toy demos) |
| SentencePiece (BPE/Unigram) | Open-source friendly | Each model has its own | Open-source models (Llama, Mistral) |

**Architect insight:** If you switch from GPT-4o to Claude mid-project, your token count for the same prompt can differ by 30%. Always pin the tokenizer in your cost model.

### Capacity Model

Tokenization is **CPU-bound, not network-bound**. Performance characteristics:

| Volume | Tokens/sec (single thread) | Latency p99 |
|---|---|---|
| 1 prompt | 50K tokens/sec | <1 ms |
| 100 concurrent prompts | 50K tokens/sec (CPU bound) | ~1 ms each |
| 10K prompts/min | Need pool of 4-8 cores | ~5 ms each |

**Rule of thumb:** Tokenization is so fast it never bottlenecks production. **If it does**, you're doing it wrong (loading the encoding 1000× instead of once).

**Where it DOES bite you:**
- Storing tokens in a database: 1M tokens ≈ 4 MB (each token = 4 bytes int32). Pre-tokenize at ingest, not at query.
- Embedding precomputation: tokenize first, then embed. Don't re-tokenize on every request.

### Cost Model (per 1M tokens, 2026)

| Model | Input | Output |
|---|---|---|
| GPT-4o | $5 | $15 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3.5 Sonnet | $3 | $15 |
| Claude 3.5 Haiku | $0.80 | $4 |
| Gemini Pro 1.5 | $1.25 | $5 |
| Llama 3 70B (self-hosted) | $0.10 (compute) | $0.10 |

**Token cost per request** for a typical RAG query (2K context, 500 output):

| Model | Per-request cost |
|---|---|
| GPT-4o-mini | $0.0006 |
| Claude 3.5 Haiku | $0.0036 |
| GPT-4o | $0.0175 |
| Claude 3.5 Sonnet | $0.0135 |

At 1M requests/day, the difference between GPT-4o and GPT-4o-mini is **$17,500/day**.

### When NOT to use this lab's content

**Don't pre-tokenize for multi-model systems if the models use different tokenizers.** You'll cache 2 sets of token IDs and waste memory. Instead, store the raw text and tokenize on demand.

**Don't optimize tokenization.** It's never the bottleneck. Optimize your prompt, your model choice, your caching, or your retry logic instead.

**Don't assume token count = cost.** Different models have different pricing for input vs output. A 2K input + 500 output prompt on GPT-4o is $0.0175; on Claude Haiku it's $0.0036 (5× cheaper) — but the same tokens.

### Production Checklist

- [ ] Tokenizer is loaded once at app startup, not per request
- [ ] Every LLM call logs `prompt_tokens`, `completion_tokens`, `total_tokens`
- [ ] Cost is computed at request time using the model's current pricing
- [ ] Long contexts (>10K tokens) are flagged in logs (cost risk)
- [ ] Per-user token budgets are enforced at the API layer
- [ ] If using RAG, context size is checked BEFORE the LLM call (don't embed 200K tokens by accident)
- [ ] Cost dashboards exist by model, user, and time window

---

## 🌙 Reflect (10 min)

Answer these in your own notes (or a comment at the bottom of the `.py` file):

1. **What did I build?**
   A tokenizer visualizer. What did you learn about how text becomes numbers?

2. **What was hard?**
   Was the ASCII bar chart? The encoding comparison? The cost math?

3. **What would I change at 10× scale?**
   If you had to tokenize 10M documents/day, what would you do differently? (Hint: pre-tokenize at ingest, not at query. Use multiprocessing. Cache the encodings.)

4. **What's tomorrow's lab?**
   Lesson 1.3: The Modern AI Stack. You'll compare 3 different LLM APIs on the same prompt and see the cost/quality/latency trade-offs.

---

## References

- [`tiktoken` GitHub](https://github.com/openai/tiktoken) — the tokenizer library
- [Hugging Face tokenizers summary](https://huggingface.co/docs/transformers/tokenizer_summary) — how BPE, WordPiece, Unigram differ
- [OpenAI tokenizer playground](https://platform.openai.com/tokenizer) — visualize tokenization in browser
- [Codebook § 1.1-1.5](../../workbooks/ai-engineer-codebook.md) — LLM API patterns
- [Codebook § 10.2](../../workbooks/ai-engineer-codebook.md#102-pricing-reference-per-1m-tokens-2026) — pricing reference table
- [Paired codebook exercises](../../workbooks/exercises/section-1-llm-apis-exercises.md) — extend what you learned here
