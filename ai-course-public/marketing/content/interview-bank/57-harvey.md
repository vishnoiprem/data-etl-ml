# 57. Harvey (Legal AI)

- **Role:** AI Engineer (LLM Features / Domain-Specific AI)
- **Tech stack:** Python, TypeScript, React, Kubernetes, OpenAI/Anthropic APIs, fine-tuning (PEFT, LoRA), vLLM, vector DBs, Postgres, Redis
- **Comp band:** $200K-$450K (well-funded, $5B+ valuation, AI infra premium)
- **Cumulative pass rate:** ~2-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation + legal background | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + LLM/agent design | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, LLM/agent, legal domain, founder | 1-2 days | ~25% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Harvey?"
**Answer:** Three-bet: (1) Harvey is the breakout legal AI company — they won the AmLaw 100 (top law firms) early, and the moat is real (legal-domain fine-tuning + customer data), (2) the founders are ex-lawyers + ex-Stripe infra (Winston Weinberg + Gabe Pereyra), so the team is dual-domain, (3) the engineering culture is best-in-class AI infrastructure work.
**Tip:** Mention you've used Harvey (or Casetext, or CoCounsel) — Harvey cares about domain curiosity.

### Q1.2: "Tell me about a domain-specific AI app you built"
**Answer:** Walk through a project where you deeply understood the domain (could be legal, medical, financial, etc.) and built AI features for it. Harvey wants people who can partner with experts, not just build generic LLM wrappers.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a citation extractor (find legal citations in text)"
**Answer:**
```python
import re
def extract_citations(text):
    patterns = [
        r'\d+\s+U\.\s?S\.\s+\d+',  # US Reports
        r'\d+\s+F\.\s?\d?d?\s+\d+',  # Federal Reporter
        r'In re [A-Z][a-zA-Z ]+',  # In re cases
        r'[A-Z][a-zA-Z]+ v\. [A-Z][a-zA-Z]+',  # Case names
    ]
    cites = set()
    for p in patterns:
        cites.update(re.findall(p, text))
    return list(cites)
```
**Tip:** Real legal citation extraction is much messier (Bluebook formatting, parallel citations, signals like "see" / "see also" / "but cf."). Mention Eyecite / Westlaw / Lexis APIs.

### Q2.2: LLM — "How would you build a legal Q&A system that cites its sources?"
**Answer:** Three pillars: (1) **retrieval** over a corpus of case law + statutes + treatises (vector + BM25 + reranker), (2) **grounded generation** — prompt the LLM with retrieved docs and explicit "cite every claim" instruction, (3) **verification** — post-process to ensure every citation actually exists in the source.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding window chunker.
- **Q3.1.2:** Build a small LRU cache.
- **Q3.1.3:** Implement a simple agent loop (ReAct).

### Round 3.2: System design
- **Q3.2.1:** "Design a legal Q&A system with citations." Discuss: corpus (case law, statutes, regulations), retrieval pipeline (BM25 + vector + reranker), LLM prompting strategy, citation verification, hallucination prevention, audit logs.
- **Q3.2.2:** "Design a multi-tenant LLM platform for a law firm." Talk: per-firm data isolation, prompt versioning, model evaluation, billing, security.

### Round 3.3: LLM / agent deep-dive
- **Q3.3.1:** "How do you fine-tune a model for legal domain?" Discuss: data curation (lawyer-reviewed examples), PEFT/LoRA, RLHF with domain experts, evaluation (domain-specific benchmarks like LegalBench).
- **Q3.3.2:** "How do you build a legal agent that uses tools (Westlaw, Lexis, internal DMS)?" Talk: function calling, tool selection, error handling, retries, observability.

### Round 3.4: Legal domain (partner-style)
- **Q3.4.1:** "Walk me through how a senior associate would use Harvey in a real M&A deal. What features matter?"
- **Q3.4.2:** "How would you measure the quality of Harvey's legal outputs?" (This is a domain-specific eval question.)

### Round 3.5: Founder (Winston often does these)
- **Q3.5.1:** "Why legal? Why AI for lawyers?"
- **Q3.5.2:** "Tell me about a time you built something for a non-technical domain expert."

## Stage 4: Hiring committee
Harvey's committee is high-bar. They look for: (a) top 5% engineering chops, (b) domain curiosity (you should know the difference between civil law and common law, or between M&A and litigation), (c) humility + collaboration with lawyers. Red flags: arrogant about AI capabilities, never having worked with domain experts, weak on grounding/citations.

## Stage 5: Offer
Base is at the high end ($250K-$350K+), equity is meaningful (private, high valuation). Negotiation: equity, sign-on, level.

## Tips for the Harvey loop
1. **Learn legal fundamentals** — even just basic US legal system knowledge. Read a few Supreme Court opinions.
2. **Brute-force RAG + grounded generation** — this is Harvey's moat.
3. **Have a domain-specific AI project to discuss** — even a side project (e.g., RAG over SEC filings).
4. **Practice the "build a citation-aware Q&A system" round** — almost always asked.
5. **Be ready for a founder round** — Winston is technical and asks about legal domain.
6. **Read the Harvey blog** — they publish legal AI case studies.
7. **Have opinions on fine-tuning vs prompting** — Harvey does both.

## Real candidate report
> "Phone screen was coding (citation extractor) + legal Q&A design. Onsite had 4 rounds including a legal domain round where they asked me to walk through a real M&A use case. I had to know the difference between an LOI and a definitive agreement. Offer: $280K + 0.04% equity, 5 days." — Levels.fyi, 2025

## Sources
- [Harvey careers](https://www.harvey.ai/careers)
- [Harvey engineering blog](https://www.harvey.ai/blog)
- [Harvey case studies](https://www.harvey.ai/customers)
- [Harvey Glassdoor](https://www.glassdoor.com/Interview/Harvey-Interview-Questions-E3509500.htm)
- [Levels.fyi Harvey](https://www.levels.fyi/companies/harvey)
