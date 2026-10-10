# 21. Netflix (ML / Recsys)

- **Role:** Machine Learning Engineer (Personalization / Recsys)
- **Tech stack:** Python, PyTorch, TensorFlow, Spark, Scala, Kafka, AWS (Netflix OSS: Metaflow, Iceberg, Maestro, Titus), Java
- **Comp band:** $300K-$900K (L4-L6); senior staff/principal crosses $1M+; equity is heavily RSU-weighted, top-of-market cash
- **Cumulative pass rate:** ~1-2%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Hiring manager intro, comp, motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 1 coding + 1 ML take-home style | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML deep-dive, behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Cross-functional panel review (the "panel") | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp conversation, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** "I'm a senior MLE with 6 years at [X] working on recsys — most recently I led the home-page ranking model that lifted engagement 9%. I shipped a two-tower retrieval model in PyTorch, and I care deeply about offline/online metric alignment. I want to come to Netflix because the culture of 'context not control' and the freedom to ship end-to-end matches how I work best."
**Tip:** Netflix recruiters value "freedom & responsibility" candor. Mention a model you owned end-to-end.

### Q1.2: "Why Netflix over [FAANG competitor]?"
**Answer:** "Three concrete reasons. First, your recsys stack is public and admired — Metaflow + the published research is what I've studied for two years. Second, the data volume per user is unmatched. Third, I want the talent density — I want peers who've published top-tier recsys work."
**Tip:** Reference a specific Netflix research blog post (e.g., "Artwork Personalization at Netflix").

## Stage 2: Technical phone screen (60 min)

### Q2.1: Coding — "Top-K frequent items in a stream"
**Answer:** Use a `Counter` with a min-heap of size K, or a `defaultdict(int)` + heapq.nlargest. O(N log K).
```python
import heapq
from collections import Counter
def top_k(stream, k):
    c = Counter(stream)
    return heapq.nlargest(k, c.keys(), key=c.get)
```
**Tip:** Discuss space complexity (Count-Min Sketch for memory-constrained).

### Q2.2: ML — "Design a movie recommendation model"
**Answer:** Walk through two-tower retrieval (user tower + item tower, dot product, trained with in-batch negatives), then a Lightweight ranking model (DLRM/DeepFM) using watch time as a label. Discuss embeddings, feature stores, position bias, exploration via bandits. Mention offline metrics (NDCG, MAP, hit rate) and online A/B.
**Tip:** Netflix specifically watches for awareness of *contextual bandits* and *causal* effects of recommendations.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q:** Implement LRU cache with O(1) get/put → ordered dict or doubly linked list + hashmap.
- **Q:** Serialize/deserialize a binary tree (BFS with sentinels).
- **Q:** Merge k sorted lists → heap with (val, list_idx, elem_idx).

### Round 3.2: System design
- **Q: "Design Netflix's homepage personalization"** — Members, rows, ranking, evidence (artwork, synopsis), exploration, diversity, A/B infra (AB测试), counterfactual logging.
- **Q: "Design a feature store serving 1B features/sec"** — Online (Redis/DynamoDB) + offline (Iceberg), point-in-time joins, freshness SLOs.

### Round 3.3: ML deep-dive
- **Q: "How would you build a cold-start model for new titles?"** — Content features (poster, synopsis embeddings from a multimodal model), collaborative via LLM-derived item embeddings, popularity priors, exploration boost.
- **Q: "Walk me through how you measure the causal impact of a ranking change."** — Interleaving, switchback experiments, cuped variance reduction, holdback.

### Round 3.4: Behavioral
- **Q:** "Tell me about a model that worked offline but failed online." Use STAR — e.g., forgetting position bias.
- **Q:** "Disagreement with a PM on a launch metric." Show trade-off articulation.
- **Q:** "Describe a time you pushed back on leadership." Netflix-specific: "context not control" means you must give judgment.

## Stage 4: Hiring committee
A cross-functional panel (3-5 senior engineers + 1 PM) reviews all interview packets and votes. Netflix has no managers in IC reviews for the most senior levels. They look for: (1) judgment at the level of the role, (2) high "talent density" — would you be peer to the best here, (3) demonstrated end-to-end ownership, (4) alignment with "freedom & responsibility." Deliberation produces a strong-hire / hire / no-hire / strong-no-hire.

## Stage 5: Offer
Cash is top-of-market, RSUs vest 4 years with 0% cliff common, sign-on common. Negotiation leverage is real — Netflix matches competing offers and the comp team has authority. Team match happens after offer acceptance (rare to fail team match at Netflix — they err on the side of hiring).

## Tips for the Netflix loop
- Read the Netflix Research and Tech Blog before your interview — reference specific posts.
- Demonstrate "context not control" by sharing *how* you make decisions, not just what.
- Show end-to-end ownership: data, model, serving, monitoring.
- Be ready for the take-home — Netflix is one of the few big-tech companies that uses a modeling quiz.
- Quantify offline→online gaps and how you debug them.
- Talk about exploration vs exploitation — bandits come up often.
- For senior roles, mention *judgement* explicitly — Netflix is "high performance, high freedom."

## Real candidate report
> "I had 5 rounds in 2 days. The take-home was a real recsys problem with a 4-hour cap. The system design was the homepage — they pushed me on the cold-start case for new titles. The behavioral round was 'free & responsible' flavored — I told a story about overruling a PM and they loved it. Offer came in 4 business days, top-of-band." — r/cscareerquestions, 2025-10

## Sources
- [Netflix Tech Blog](https://netflixtechblog.com/)
- [Levels.fyi Netflix salaries](https://www.levels.fyi/companies/netflix/salaries)
- [Interview101 Netflix MLE guide](https://www.interview101.com/interviews/netflix/machine-learning-engineer)
- [Netflix Research](https://research.netflix.com/)
- [r/cscareerquestions Netflix interview thread](https://www.reddit.com/r/cscareerquestions/)
