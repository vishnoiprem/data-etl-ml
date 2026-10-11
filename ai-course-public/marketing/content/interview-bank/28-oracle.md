# 28. Oracle (OCI AI / Generative AI Service)

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + signature visual. Color: company brand color as accent. Headline on image: "ORACLE / OCI AI / 2026".

> **TL;DR:** Oracle's loop is built for **sovereign cloud** and regulated industries — banks, governments, healthcare — where data never leaves the customer's perimeter. The signature stack is **23ai Vector Search** + **OCI Generative AI Service**, and the winning candidate has shipped on-prem or hybrid and can write Java under pressure.

```
Recruiter (55%) → Phone (45%) → Onsite (35%) → Tech Panel (60%) → Offer
```

- **Role:** ML Engineer / Applied Scientist (OCI AI Services, Generative AI, Vector Search)
- **Tech stack:** Python, PyTorch, TensorFlow, Java, OCI (Oracle Cloud), Kubernetes, CUDA, GraalVM
- **Comp band:** $200K-$600K total comp (IC3-IC5) | RSUs 4-year, 1-year cliff; senior crosses $750K+
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Org match (OCI/Generative AI), comp | 1 week | ~55% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML | 1-2 weeks | ~45% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~35% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

Oracle's loop looks like a standard big-tech interview, but the lens is always "will this work in a regulated customer's environment?" If you can't talk about compliance, on-prem, and audit, you'll get stuck on the first ML design question.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Oracle for AI?"
**Answer:** "OCI is the only hyperscaler with a sovereign-cloud story — government, defense, and regulated industries are a $100B+ market where Oracle wins. The Generative AI Service and Vector Search launched in 2024 are credible technical products. I want to build AI for customers who can't use OpenAI due to compliance."
**Tip:** Reference *sovereign cloud*, *OCI AI Services*, *23ai Vector Search* — not generic AI.

### Q1.2: "Describe a model you deployed for a regulated industry"
**Answer:** STAR with focus on *compliance, audit, and on-prem options*. Oracle sells to banks, governments, and healthcare — they value this.
**Tip:** Show you've shipped where data sovereignty matters.

## Stage 2: Technical phone screens (90 min)

Confirm the language upfront — Java is on the table, and interviewers won't switch mid-round. The ML round expects you to name 23ai Vector Search and Oracle's database heritage unprompted; if you don't, the interviewer will.

### Q2.1: Coding: "Reverse a linked list in groups of K"
**Answer:** Iterative with prev/curr/next pointers. O(N) time, O(1) space.
```python
def reverseKGroup(head, k):
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        kth = group_prev.next
        for _ in range(k):
            if not kth:
                return dummy.next
            kth = kth.next
        # reverse k nodes starting at group_prev.next
        prev, cur = None, group_prev.next
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # reconnect
        first = group_prev.next
        group_prev.next = prev
        first.next = cur
        group_prev = first
```
**Tip:** Linked list + tree problems are common. Confirm language upfront (Java vs Python).

### Q2.2: ML: "Design a vector search service for enterprise RAG"
**Answer:** (1) Embedding service — REST/gRPC, supports OpenAI/Cohere/Oracle models; (2) Vector index — HNSW or IVF, 23ai native vector index; (3) Metadata filtering with ACLs; (4) Hybrid retrieval (BM25 + dense); (5) Re-rank with cross-encoder; (6) Latency 50ms p99 for 10M vectors; (7) Multi-tenant isolation via schema or DB.
**Tip:** Reference *23ai Vector Search* and *Oracle Database* by name. Oracle is a database company first.

## Stage 3: Onsite (4 rounds)

The onsite is where Oracle checks for cloud-infra depth — vector search, multi-tenant serving, on-prem deployment. Java fluency gets tested in the coding round; SQL fluency gets tested in the system design. Both are real signals, not optional.

### Round 3.1: Coding (60 min, 2 questions)
- Q: Implement a thread-safe rate limiter (token bucket).
- Q: Valid Sudoku. Backtracking with row/col/box bitmasks.
- Optional 3rd: SQL with window functions, CTEs, recursive queries.

### Round 3.2: System design (60 min)
- Q: Design OCI Generative AI Service. Multi-tenant LLM serving, fine-tuning pipeline, RLHF, content safety filters, dedicated AI clusters (H100/A100), quota management, and billing.
- Q: Design a hybrid search service over enterprise documents. Oracle 23ai vector + text indexes, ACL filtering, freshness via incremental indexing, and OCI Object Storage ingestion.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you fine-tune a model for a bank's customer-service use case? On-prem fine-tuning (data sovereignty), guardrails for PII, eval with the bank's own data, RAG over policy docs, and audit logs.
- Q: How would you evaluate an enterprise RAG system? Faithfulness, relevance, citation accuracy, latency, cost-per-query, and customer-specific rubrics.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you worked with a regulated customer (healthcare, finance, gov).
- Q: A time you shipped on-prem. Critical for OCI.
- Q: Disagreement with a PM on scope.

## Stage 4: Hiring committee
A panel of senior engineers + product reviews. They look for: (1) ML bar for the level, (2) cloud-infra depth (Oracle is a database + cloud company), (3) enterprise readiness (compliance, multi-tenancy, on-prem), (4) Oracle values (Integrity, Collaboration, Innovation, Customer Focus). Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Oracle is competitive for cloud roles but typically below FAANG top-of-band. Negotiation is moderate. Team match after loop. Recent AI push has improved comp bands.

## Tips for the Oracle loop
- Reference *OCI*, *23ai*, *Generative AI Service*, *Vector Search* by name.
- For ML rounds, emphasize *enterprise constraints*: compliance, on-prem, multi-tenancy.
- For system design, the vector search + RAG platform is a hot question.
- Java is heavily used — be ready to write Java if asked (vs Python).
- SQL is important — Oracle is a database company. Window functions, CTEs, recursive queries.
- For behavioral, "Customer Focus" is real — Oracle is sales-driven.
- Show on-prem / hybrid cloud experience if you have it.

## Real candidate report
> "Loop for OCI Generative AI. 4 rounds, 1 day. Coding was 1 Java (rate limiter) and 1 Python (Sudoku). The system design was a multi-tenant vector search service over Oracle 23ai. ML deep-dive was fine-tuning for a bank. Behavioral was sales-driven and they asked about a time I partnered with field sales. Offer at IC4, ~$380K total, 5 weeks total." — Blind, 2025-09

## Sources
- [Oracle Careers](https://www.oracle.com/careers/)
- [Levels.fyi Oracle salaries](https://www.levels.fyi/companies/oracle/salaries)
- [Oracle AI Blog](https://blogs.oracle.com/ai-and-datascience/)
- [Oracle 23ai Vector Search docs](https://www.oracle.com/database/ai-vector-search/)
- [Glassdoor Oracle ML interviews](https://www.glassdoor.com/Interview/Oracle-Interview-Questions-E1737.htm)

---

## The 1 thing to remember

At Oracle, every answer should bend toward sovereignty — name 23ai Vector Search, the OCI Generative AI Service, and on-prem deployment, because "data never leaves the customer's perimeter" is the whole game.
