# 62. Writer

- **Role:** AI Engineer (Enterprise LLM platform)
- **Tech stack:** Python, PyTorch, JAX, custom "Palmyra" model stack, FastAPI, Kubernetes, AWS
- **Comp band:** $200K-$450K base + equity (Series C, SF)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Background, comp, mission fit | 30 min | ~50% |
| 2. Technical phone screen | Coding + LLM fundamentals | 60 min | ~40% |
| 3. Onsite (4 rounds) | Coding, system design, ML deep-dive, behavioral | 4-5 hrs | ~25% |
| 4. Hiring committee | Cross-functional panel review | 1-2 wks | ~60% |
| 5. Offer | Comp negotiation | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Writer vs OpenAI/Anthropic?"
**Answer:** "I'm excited by the IP-removal guarantee for enterprise — Writer indemnifies outputs, which is the actual blocker for Fortune 500 deployment. I also want to work on graph-grounded RAG with Knowledge Graph, which Anthropic's API doesn't ship."
**Tip:** Show you understand the enterprise compliance gap that frontier labs don't serve.

### Q1.2: "What's your favorite Writer feature?"
**Answer:** "GraphRAG with the 'no hallucination' guardrail — you can constrain generation to a typed schema and reject any node not present in the enterprise graph. That's the pattern that finally makes AI reliable in regulated industries."
**Tip:** Use the docs — they've published benchmark pages for this.

## Stage 2: Technical phone screen

### Q2.1: LRU Cache.
**Answer:**
```python
class LRUCache:
    def __init__(self, c):
        self.cap, self.cache = c, collections.OrderedDict()
    def get(self, k):
        if k not in self.cache: return -1
        self.cache.move_to_end(k); return self.cache[k]
    def put(self, k, v):
        if k in self.cache: self.cache.move_to_end(k)
        self.cache[k] = v
        if len(self.cache) > self.cap: self.cache.popitem(last=False)
```
**Tip:** Standard; they want O(1) both ways.

### Q2.2: Implement constrained decoding for JSON output.
**Answer:** Build a finite-state machine from the JSON grammar, then at each decode step mask logits to only token IDs whose continuation is a valid prefix. Use `trie` over byte-pair tokens.
**Tip:** Writer's no-hallucination product literally does this; show you know the trick.

## Stage 3: Onsite

### Round 3.1: Coding
**Q:** Two-sum in a sorted array.
**Answer:** Two pointers O(n). Trivial — they use this to baseline.

### Round 3.2: System design
**Q:** Design a multi-tenant enterprise RAG service with role-based access.
**Answer:** Per-tenant vector store (Pinecone namespaces), ACL filter on retrieval, guardrail layer using Writer's own no-hallucination API, audit log to S3 with object lock, evaluator sampling 1% of generations for human review.

### Round 3.3: ML deep-dive
**Q:** Walk me through your training pipeline for a domain-adapted LLM.
**Answer:** Continued pretraining on 50B tokens of enterprise text → supervised fine-tune on 200K instruction examples → RLHF with critic trained on domain preferences → DPO ablation. Cite the Palmyra X 004 paper.

### Round 3.4: Behavioral
**Q:** Tell me about a disagreement with PM.
**Answer:** STAR: PM wanted to ship without evaluation; you pushed for a 2-week eval, found a 4% regression on Spanish, fixed it before launch.

## Stage 4: Hiring committee
Three staff+ engineers plus a PM. They look for: (1) ability to ship an enterprise product, (2) fluency in compliance terms (SOC2, HIPAA, EU AI Act), (3) thoughtful opinions on hallucination mitigation.

## Stage 5: Offer
Equity refreshers vest over 4 years; base is competitive but ~10% below frontier labs. They pay up for staff+.

## Tips for the Writer loop
- Read the Palmyra technical reports — they reference them.
- Know the difference between Writer and Anthropic's positioning cold.
- Practice grammar-constrained decoding.
- Be ready to defend every "no-hallucination" claim with a measurement.
- Show you've built in a regulated domain (fintech, health).
- They love candidates who've shipped RAG in production.

## Real candidate report
> "I had 4 rounds, two of which were system design for an enterprise AI platform. They asked how I'd handle PII in vector stores. Process took 3 weeks, offer came back above the band after I countered with a competing Anthropic offer." — Levels.fyi, Senior AI Engineer, 2025

## Sources
- [Writer careers](https://writer.com/careers)
- [Writer Palmyra X 004 report](https://writer.com/engineering)
- [Levels.fyi — Writer](https://www.levels.fyi/companies/writer)
- [Glassdoor — Writer interviews](https://www.glassdoor.com/Interview/Writer-Interview-Questions.htm)
- [Reddit r/MachineLearning — Writer](https://reddit.com/r/MachineLearning)
