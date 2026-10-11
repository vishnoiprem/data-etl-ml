# 23. Google (Cloud AI / Vertex AI)

- **Role:** ML Engineer / Applied Scientist on Vertex AI, Gemini Cloud, or Cloud Customer Engineering
- **Tech stack:** Python, JAX, TensorFlow, TPU, Vertex AI (custom training, Vector Search, Pipelines, Model Garden), BigQuery, Dataflow, Go
- **Comp band:** $250K-$900K (L4-L6); L7+ crosses $1.2M+; RSUs vest 4-year with no cliff
- **Cumulative pass rate:** ~2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Team match, comp, basic fit | 1 week | ~50% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML/system design | 1-2 weeks | ~35% advance |
| 3. **Onsite (4-5 rounds)** | Coding, system design, ML, Googliness | 1-2 days | ~30% advance |
| 4. **Hiring committee (LSC)** | Cross-Googler committee, calibration | 2-3 weeks | ~60% advance |
| 5. **Offer** | Comp negotiation, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Google Cloud for ML?"
**Answer:** Three specific reasons. First, Vertex AI is the only hyperscaler platform that lets me bring my own JAX/TPU training and serve from the same place. Second, Gemini Cloud API is the most-used frontier model API in production, so the feedback loop is the tightest. Third, I've used BigQuery + Vertex at [previous job] and want to build the platform I wished I had.
**Tip:** Be specific to Vertex/Gemini — not generic Google. Reference a product doc or blog post.

### Q1.2: "Tell me about your most impactful ML project"
**Answer:** Pick a project with clear, *quantified* impact. Use the format: "The business problem was X. I built Y. The metric moved by Z. The infra cost was W."
**Tip:** Google interviewers want quantified impact at scale. "10% of users" beats "all users" if it's the right 10%.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "Serialize/deserialize a binary tree with next pointer"
**Answer:** BFS with a queue, using `#` as null marker. Or encode length-prefixed.
```python
def serialize(root):
    if not root: return ""
    q = [root]; out = []
    while q:
        n = q.pop(0)
        out.append(str(n.val) if n else "#")
        if n: q.extend([n.left, n.right])
    return ",".join(out)
```
**Tip:** Edge cases first: empty tree, single node, skewed tree.

### Q2.2: ML system design — "Design an embeddings service for 100M docs"
**Answer:** (1) Ingestion via Pub/Sub → Dataflow; (2) Embedding model (Gecko/PaLM-based) → batch or streaming; (3) Vector DB — Vertex AI Vector Search (ScaNN) with sharding; (4) Hybrid retrieval (BM25 + dense), re-rank with cross-encoder; (5) Updates via shadow index swap; (6) Latency budget 50ms p99.
**Tip:** Mention ScaNN/Vector Search by name. Cost is graded.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Word Ladder"
**Answer:** BFS from `beginWord`, expand one letter at a time, check if the result is in `wordList`. O(M·N·26) where M is word length, N is `wordList` size.

### Q3.1.2: "Find median from data stream"
**Answer:** Two heaps: a max-heap for the lower half, a min-heap for the upper half. Balance: sizes differ by at most 1. Median = top of larger heap, or average of the two tops. O(log N) per add.

### Round 3.2: System design (60 min)

### Q3.2.1: "Design Vertex AI Pipelines"
**Answer:** DAG runner (Kubeflow Pipelines under the hood), artifact store (Metadata Service for lineage), experiment tracking (Vertex Experiments), caching (per-step cache keyed by input hash), retry (exponential backoff with idempotency), parameterization (templated YAML). Cost: per-step compute, idle cost during retries. Trade-off: per-step isolation vs. shared cluster.
**Tip:** Name the DAG runner, the metadata service, the caching layer.

### Q3.2.2: "Design a multi-tenant model serving system"
**Answer:** Shared vs dedicated endpoints (shared = cheaper, noisier; dedicated = guaranteed QPS). Autoscaling on QPS (target-tracking with a 30s window). LoRA adapter hot-swap (per-tenant adapter, paged in on first request). Rate limiting per tenant (token bucket). Cold start mitigation: pre-warm top-10 tenants.
**Tip:** Multi-tenancy is the Vertex differentiator from open-source.

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "How would you build an evaluation pipeline for a fine-tuned Gemini variant?"
**Answer:** Four layers: (1) held-out human-rated set (1K queries, calibrated weekly), (2) LLM-judge with calibration (compare against human ratings, discard if correlation < 0.7), (3) domain-specific rubrics (factual, safety, helpfulness), (4) canary traffic (1% of production). Anti-contamination: ensure eval set isn't in the training data via near-duplicate search.
**Tip:** Anti-contamination is the Gemini-specific trap.

### Q3.3.2: "Design the retrieval for Google's 'Search Generative Experience'"
**Answer:** Query fan-out (multi-query via LLM) → multi-source retrieval (web, knowledge graph, vertical indexes) → re-rank with cross-encoder → factuality guardrails (cite-or-decline policy) → citation generation (in-line with source URL). Latency budget 1.5s p99. Eval: factuality rubric on 1K held-out queries weekly.
**Tip:** Multi-query + cite-or-decline is the SGE pattern.

### Round 3.4: Googliness / behavioral (60 min)

### Q3.4.1: "A time you worked across teams on a shared infra project"
**Answer:** Use STAR. Show how you navigated the team boundaries (Slack channels, weekly syncs, shared doc). The action: 2-3 specific coordination moves. Result: shipped on time, 1-2 teams adopted.
**Tip:** Cross-team collaboration is the Google meta-answer.

### Q3.4.2: "When have you changed your mind based on data?"
**Answer:** I believed that dense retrieval beats sparse for long-tail queries. Evidence from a 10K-query eval showed BM25 beat ColBERT on 18% of queries, mostly technical jargon. I changed the architecture to hybrid retrieval (BM25 + ColBERT with a learned combiner); long-tail metric improved 7%.
**Tip:** "I was wrong" + the data that proved it is the strongest Googliness answer.

### Q3.4.3: "A project where scope kept growing"
**Answer:** Use STAR. Show how you cut scope (named 3 specific cuts), what you kept, what shipped. The lesson: scope creep is a forcing function for prioritization.
**Tip:** Name what you cut, why, and what held.

### Round 3.5 (optional): Tech-lead "depth" round

Probing your specific ML subarea (e.g., RLHF, distributed training) at L5+ depth. Be ready to write a small training loop on the whiteboard.
**Tip:** Confirm the depth area with the recruiter; rehearse 2-3 whiteboard problems.

## Stage 4: Hiring committee (LSC — Level-Specific Calibration)

All interviewers submit "narratives" with calibration against the level. A separate committee of senior Googlers reviews, calibrated per level, and votes. They look for: (1) bar at level, (2) signal across multiple rounds (not just one strong round), (3) "Googliness" — collaboration + humility, (4) impact at scale. Hiring committee can "down-level" if they see L4 signal for an L5 req.

## Stage 5: Offer

Cash + RSUs + target bonus. Negotiation is real and Google typically matches competing base + a meaningful chunk of equity. The "team match" is a separate phase after loop pass — Google can sometimes not have a slot, which leads to a "you passed the bar but no seat" situation (rare at L5+, more common at L4).

## Tips for the Google Cloud loop

- Vertex AI / Gemini are different from Search/YouTube — show *Cloud-native* thinking (multi-tenancy, billing, quotas).
- Quantify scale: "petabytes", "billions of requests", "10K QPS" — not just "large."
- For Googliness rounds, demonstrate *intellectual humility* — Google is allergic to arrogance.
- Reference Google's published papers (Pathways, PaLM, Gemini technical reports) when relevant.
- Prepare for distributed-systems flavor: consensus, sharding, eventually-consistent vector indices.
- Always tie design decisions to *user/business* impact.
- For L6+: have a clear "tech leadership" story — leading without authority, mentoring, hiring bar.

## Real candidate report

> "Vertex AI loop was 5 rounds, 1 day. The system design was Vector Search + serving at 50K QPS — they pushed me on sharding and re-indexing strategy. The ML deep-dive was on Gemini eval — they wanted to know how I'd prevent eval set contamination. The Googliness round was unexpectedly hard; I told a 'I was wrong' story and got a 'strong hire' from the committee. 6 weeks total to offer."
> — r/MLQuestions, 2025-09

## Sources

- [Google Cloud Careers](https://cloud.google.com/careers)
- [Levels.fyi Google salaries](https://www.levels.fyi/companies/google/salaries)
- [Vertex AI docs](https://cloud.google.com/vertex-ai/docs)
- [Google Research blog](https://research.google/)
- [r/cscareerquestions Google interview](https://www.reddit.com/r/cscareerquestions/)
