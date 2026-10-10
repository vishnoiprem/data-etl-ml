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
**Answer:** "Three specific reasons. First, Vertex AI is the only hyperscaler platform that lets me bring my own JAX/TPU training and serve from the same place. Second, Gemini Cloud API is the most-used frontier model API in production, so the feedback loop is the tightest. Third, I've used BigQuery + Vertex at [previous job] and want to build the platform I wished I had."
**Tip:** Be specific to Vertex/Gemini — not generic Google. Reference a product doc or blog post.

### Q1.2: "Tell me about your most impactful ML project"
**Answer:** Pick a project with clear, *quantified* impact. Use the format: "The business problem was X. I built Y. The metric moved by Z. The infra cost was W."
**Tip:** Google interviewers want quantified impact at scale. "10% of users" beats "all users" if it's the right 10%.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding — "Serialize/deserialize a binary tree with next pointer"
**Answer:** BFS with a queue, using `-1` as null marker. Or encode length-prefixed.
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

### Round 3.1: Coding (60 min, 2 problems)
- **Q:** Word Ladder → BFS, O(M·N·26).
- **Q:** Find median from data stream → two heaps.
- (Optional 3rd): "Build a trie with insert/search/prefix."

### Round 3.2: System design (60 min)
- **Q: "Design Vertex AI Pipelines"** — DAG runner, artifact store (metadata service), experiment tracking, lineage, caching, retry, parameterization.
- **Q: "Design a multi-tenant model serving system"** — Shared vs dedicated endpoints, autoscaling on QPS, LoRA adapter hot-swap, rate limiting per tenant, cold start mitigation.

### Round 3.3: ML deep-dive (60 min)
- **Q: "How would you build an evaluation pipeline for a fine-tuned Gemini variant?"** — Held-out human-rated set, LLM-judge with calibration, domain-specific rubrics, regression tests, canary traffic.
- **Q: "Design the retrieval for Google's 'Search Generative Experience'"** — Query fan-out (multi-query), re-rank with cross-encoder, factuality guardrails, citations.

### Round 3.4: Googliness / behavioral (60 min)
- **Q:** "Tell me about a time you worked across teams on a shared infra project." (Collaboration)
- **Q:** "When have you changed your mind based on data?" (Intellectual humility)
- **Q:** "Describe a project where scope kept growing." (Prioritization)

### Round 3.5 (optional): Tech-lead "depth" round
Probing your specific ML subarea (e.g., RLHF, distributed training) at L5+ depth. Be ready to write a small training loop on the whiteboard.

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
> "Vertex AI loop was 5 rounds, 1 day. The system design was Vector Search + serving at 50K QPS — they pushed me on sharding and re-indexing strategy. The ML deep-dive was on Gemini eval — they wanted to know how I'd prevent eval set contamination. The Googliness round was unexpectedly hard; I told a 'I was wrong' story and got a 'strong hire' from the committee. 6 weeks total to offer." — r/MLQuestions, 2025-09

## Sources
- [Google Cloud Careers](https://cloud.google.com/careers)
- [Levels.fyi Google salaries](https://www.levels.fyi/companies/google/salaries)
- [Vertex AI docs](https://cloud.google.com/vertex-ai/docs)
- [Google Research blog](https://research.google/)
- [r/cscareerquestions Google interview](https://www.reddit.com/r/cscareerquestions/)
