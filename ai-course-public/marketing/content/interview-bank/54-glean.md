# 54. Glean

- **Role:** AI Engineer / Software Engineer (Enterprise Search)
- **Tech stack:** Python, Go, TypeScript, React, Kubernetes, Postgres, Elasticsearch, vector DBs, LLM APIs, embeddings, OAuth/SAML/SCIM connectors
- **Comp band:** $200K-$420K (late-stage, well-funded, $4B+ valuation)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + system design | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML/search, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Glean?"
**Answer:** Three-bet: (1) Glean is the leader in enterprise AI search — they built the data ingest + permission system that's hard to replicate, (2) the engineering culture is ex-Google (Arvind Jain, founder, ex-Google Search), (3) the LLM + search integration (Glean Assistant) is best-in-class for enterprise.
**Tip:** Mention you've used Glean at a previous job — or, more likely, that you've used Slack AI / Microsoft Copilot and can articulate why Glean is better.

### Q1.2: "Tell me about a search or ML system you built"
**Answer:** Walk through a concrete project that involved: heterogeneous data sources, ranking, retrieval, or LLM integration. Glean cares about enterprise + AI.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement BM25 from scratch"
**Answer:**
```python
import math
from collections import Counter, defaultdict
class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = []
        self.doc_lens = []
        self.df = defaultdict(int)
        self.avgdl = 0
    def fit(self, docs):
        self.docs = [d.split() for d in docs]
        self.doc_lens = [len(d) for d in self.docs]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens)
        for d in self.docs:
            seen = set(d)
            for t in seen:
                self.df[t] += 1
    def score(self, query, doc_idx):
        score = 0
        for term in query.split():
            if term not in self.df: continue
            tf = self.docs[doc_idx].count(term)
            idf = math.log((len(self.docs) - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * self.doc_lens[doc_idx] / self.avgdl))
        return score
```
**Tip:** Glean combines BM25 + vector + LLM reranker. Mention Learning-to-Rank (LTR) as a power tool.

### Q2.2: Search — "How would you build an enterprise permission-aware search?"
**Answer:** Three pillars: (1) **identity graph** — connect users to docs via ACLs, groups, document sharing, (2) **inverted index with ACL tags** — every doc indexed with its accessible users, (3) **query-time ACL filter** — restrict results to docs the user can see.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a TF-IDF scorer.
- **Q3.1.2:** Build a top-k search function.
- **Q3.1.3:** Build a small LRU cache.

### Round 3.2: System design
- **Q3.2.1:** "Design Glean's enterprise connector system." Discuss: 100+ SaaS connectors (Slack, Notion, Confluence, Gmail, Drive), incremental sync, change detection, schema normalization, ACL extraction.
- **Q3.2.2:** "Design an enterprise search backend at Google scale." Talk: indexer (Logstash-style), ranker (BM25 + LTR + vector + LLM reranker), serving layer, UI customization, observability.

### Round 3.3: Search / ML deep-dive
- **Q3.3.1:** "How do you combine BM25, vector, and LLM reranking in a search pipeline?" Discuss: first-stage (BM25 + vector for recall), second-stage (cross-encoder or LLM for precision), cost/latency tradeoffs.
- **Q3.3.2:** "How do you build a permission-aware RAG system?" Talk: ACL extraction at ingest, document metadata, query-time filtering, audit logs, governance.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a complex production system you owned."
- **Q3.4.2:** "Why enterprise? Why AI for enterprise?"

## Stage 4: Hiring committee
Glean is structured — ex-Google leadership, big-tech-style loop review. They look for: deep systems experience, search/ranking familiarity, and an enterprise mindset (security, permissions, scale). Red flags: never having built a search system, weak on ML, no enterprise experience.

## Stage 5: Offer
Base is at big-tech level ($200K-$300K+ for senior), equity is meaningful (private, well-funded, late-stage). Negotiation: title, sign-on, equity refreshers.

## Tips for the Glean loop
1. **Brute-force search fundamentals** — BM25, TF-IDF, vector search, LTR, cross-encoders.
2. **Read about enterprise search** — Coveo, Sinequa, Elastic, Algolia. Glean competes with all of them.
3. **Have an enterprise project to discuss** — even a side project with permissions/auth.
4. **Practice the "design an enterprise connector" round** — almost always asked.
5. **Be ready to discuss RAG + permissions** — this is Glean's moat.
6. **Show taste in scaling** — Glean has large enterprise customers with billions of docs.
7. **Read the Glean engineering blog** — they post about enterprise AI architecture.

## Real candidate report
> "Phone screen was BM25 coding + a system design for an enterprise search backend. Onsite had 4 rounds including a Google-style system design where I had to design the full stack from connector to ranking to LLM reranker. Offer was $260K base + 0.05% equity, 5 day turnaround." — Levels.fyi, 2025

## Sources
- [Glean careers](https://www.glean.com/careers)
- [Glean engineering blog](https://www.glean.com/blog)
- [Glean docs](https://docs.glean.com)
- [Glean Glassdoor](https://www.glassdoor.com/Interview/Glean-Interview-Questions-E3509300.htm)
- [Levels.fyi Glean](https://www.levels.fyi/companies/glean)
