# 55. Notion AI

- **Role:** AI Engineer (Product AI / LLM Features)
- **Tech stack:** Python, TypeScript, React, Node, Postgres, Redis, Kafka, OpenAI/Anthropic APIs, embeddings, vector DBs, LangChain
- **Comp band:** $200K-$450K (Series A unicorn, very competitive)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + product sense | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, product AI, behavioral, founder | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Notion AI?"
**Answer:** Three-bet: (1) Notion is the most beloved productivity tool — building AI features inside it is a multi-million-user immediate wedge, (2) Notion AI's Q&A (RAG over your workspace) is a real product with real adoption, (3) the engineering culture is product-obsessed — every PM eng can ship.
**Tip:** Mention you're a Notion power user. Walk through a specific AI feature you use (Notion AI autocomplete, Q&A, translator, etc.).

### Q1.2: "Tell me about an LLM feature you shipped"
**Answer:** Concrete numbers — DAU impact, latency, error rate, eval methodology. Notion values product engineering impact, not just technical depth.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a simple summarization throttler (don't exceed N requests/sec)"
**Answer:**
```python
import time
class Throttler:
    def __init__(self, rps):
        self.interval = 1.0 / rps
        self.last = 0
    def wait(self):
        now = time.time()
        elapsed = now - self.last
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last = time.time()
```
**Tip:** Notion AI uses rate limiting + token budgeting for LLM calls. Discuss sliding window vs token bucket, jitter, backpressure.

### Q2.2: Product AI — "How would you build Notion AI's workspace Q&A feature?"
**Answer:** Three pillars: (1) **indexing** — every page converted to chunks + embeddings, stored in a vector DB, (2) **query** — user question → embedding → retrieve top-k pages → re-rank → synthesize with LLM, (3) **citation** — show the source pages inline so users can trust the answer.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding window chunker.
- **Q3.1.2:** Build a small rate limiter / token bucket.
- **Q3.1.3:** Implement a basic autocomplete (Tries or BK-trees).

### Round 3.2: System design
- **Q3.2.1:** "Design Notion AI's autocomplete feature." Talk: client-side debouncing, server-side ranking model, inline streaming, latency budget (200ms), A/B testing framework.
- **Q3.2.2:** "Design a multi-tenant LLM feature platform." Discuss: per-tenant usage tracking, rate limits, cost attribution, model fallback, observability.

### Round 3.3: Product AI deep-dive
- **Q3.3.1:** "How would you measure the quality of Notion AI's autocomplete?" Discuss: perplexity, BLEU vs reference, user acceptance rate, task completion rate, qualitative review.
- **Q3.3.2:** "How would you ship a new AI feature to 1M users safely?" Discuss: feature flags, gradual rollout, monitoring, fallback to non-AI, kill switches.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a feature you shipped that users loved."
- **Q3.4.2:** "Tell me about a feature that didn't work and what you learned."

### Round 3.5: Founder (Ivan Zhao does these)
- **Q3.5.1:** "What product would you build if money didn't matter?"
- **Q3.5.2:** "Where do you see Notion in 5 years?"

## Stage 4: Hiring committee
Notion's committee is product + engineering mixed. They look for: product sense (you should be able to talk about UX tradeoffs), technical depth (real LLM feature experience), and founder fit. Red flags: never having shipped to users, weak on product thinking, no genuine Notion usage.

## Stage 5: Offer
Base is at the high end ($200K-$300K+ for senior), equity is meaningful (private, high valuation). Negotiation: equity, sign-on, level (Notion uses E3-E7 with E5 ~ senior).

## Tips for the Notion AI loop
1. **Be a Notion power user** — show you understand the product.
2. **Build something with Notion AI's API** — they have one.
3. **Practice product AI patterns** — autocomplete, RAG Q&A, summarization, action items.
4. **Have shipped product features** — Notion wants builders, not just model tuners.
5. **Be ready for a founder round** — Ivan Zhao is technical and asks deep product questions.
6. **Brute-force LLM feature engineering** — rate limiting, token budgeting, A/B testing, eval.
7. **Read Notion's blog and engineering posts** — they publish about AI features.

## Real candidate report
> "Phone screen was autocomplete + rate limiter coding. Onsite had 4 rounds including a product AI round where I had to design a new AI feature end-to-end and walk through UX tradeoffs. The founder round with Ivan was intense — he really pushed on product vision. Offer: $260K + 0.04% equity." — Levels.fyi, 2025

## Sources
- [Notion careers](https://www.notion.so/careers)
- [Notion engineering blog](https://www.notion.so/blog/category/engineering)
- [Notion AI docs](https://www.notion.so/help/category/notion-ai)
- [Notion Glassdoor](https://www.glassdoor.com/Interview/Notion-Interview-Questions-E1751948.htm)
- [Levels.fyi Notion](https://www.levels.fyi/companies/notion)
