# 56. Grammarly (Anthropic-style AI team)

- **Role:** AI Engineer (LLM Features / Writing AI)
- **Tech stack:** Python, TypeScript, React, Kubernetes, Kafka, Postgres, Redis, OpenAI/Anthropic APIs, in-house transformer models, ONNX, Triton
- **Comp band:** $200K-$420K (mature startup, well-funded)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + ML/NLP | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML/NLP, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Grammarly?"
**Answer:** Three-bet: (1) Grammarly is a household name writing tool with 30M+ DAU, building AI features is product-validated, (2) the engineering culture balances research (in-house NLP) with production AI (LLM integration), (3) the mission (improve communication) is genuinely compelling.
**Tip:** Mention a specific Grammarly feature you use, and one you'd want to build.

### Q1.2: "Tell me about an NLP or LLM project you shipped"
**Answer:** Concrete numbers — DAU impact, latency, error rate, training methodology. Grammarly values shipped impact, not just research ideas.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a simple edit-distance corrector (Levenshtein)"
**Answer:**
```python
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]
```
**Tip:** Grammarly uses BK-trees for fast fuzzy spelling correction. Mention BK-tree + Bloom filter for very large vocabularies.

### Q2.2: NLP — "How would you build a tone/style classifier for Grammarly?"
**Answer:** Three options: (1) fine-tuned BERT/RoBERTa classifier on labeled (formal/casual/confident/etc.) data, (2) LLM-based zero-shot with chain-of-thought, (3) hybrid: LLM for label generation + small classifier for serving.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a token bucket rate limiter.
- **Q3.1.2:** Build a Trie for spelling suggestions.
- **Q3.1.3:** Implement a small autocomplete (suffix arrays or Tries).

### Round 3.2: System design
- **Q3.2.1:** "Design Grammarly's autocomplete architecture." Discuss: client-side debouncing, server-side language model (BERT or LLM), streaming responses, latency budget (200ms), privacy (on-device vs server).
- **Q3.2.2:** "Design a writing assistant that personalizes to your voice." Talk: embedding your past writing, few-shot prompting, RAG over your corpus, ongoing updates.

### Round 3.3: ML / NLP deep-dive
- **Q3.3.1:** "Walk through how you'd build a grammar error correction model." Discuss: seq2seq (T5/BART), data augmentation, eval (CoNLL-2014, BEA-2019), human review, hallucination prevention.
- **Q3.3.2:** "How would you A/B test an LLM-based writing feature?" Discuss: feature flags, randomization, primary metric (engagement, retention), guardrails (latency, error rate), qualitative review.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a feature you shipped that moved the needle."
- **Q3.4.2:** "Why writing AI? What excites you about this space?"

## Stage 4: Hiring committee
Grammarly's committee is product + engineering + research. They look for: NLP depth (you should know transformers + classical NLP), product engineering skills (you should be able to ship), and a writing-AI passion. Red flags: never having trained a transformer, weak on classical NLP, no product instincts.

## Stage 5: Offer
Base is at the high end ($200K-$300K+ for senior), equity is meaningful (private, growing). Negotiation: equity, sign-on, level.

## Tips for the Grammarly loop
1. **Brute-force NLP fundamentals** — tokenization, edit distance, language models, transformers.
2. **Have shipped LLM products** — autocomplete, summarization, rewriting, etc.
3. **Practice the "design a writing assistant" round** — almost always asked.
4. **Show taste in UX for AI features** — Grammarly is product-obsessed.
5. **Read the Grammarly engineering blog** — they publish about AI features.
6. **Be ready to compare in-house models vs LLM APIs** — this is their active debate.
7. **Have opinions on tone/style detection** — this is Grammarly's bread and butter.

## Real candidate report
> "Phone screen was edit-distance + an NLP design question. Onsite had 4 rounds including a tough ML round on grammar error correction (they wanted BERT vs T5 vs LLM tradeoffs in detail). Behavioral was a 'tell me about a feature you shipped' style question. Offer: $230K + 0.04% equity." — Levels.fyi, 2025

## Sources
- [Grammarly careers](https://www.grammarly.com/careers)
- [Grammarly engineering blog](https://www.grammarly.com/blog/engineering/)
- [Grammarly AI research](https://www.grammarly.com/research)
- [Grammarly Glassdoor](https://www.glassdoor.com/Interview/Grammarly-Interview-Questions-E395909.htm)
- [Levels.fyi Grammarly](https://www.levels.fyi/companies/grammarly)
