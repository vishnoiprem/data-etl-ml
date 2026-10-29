"""
Cell 22: Eval Metrics — Recall@K, nDCG, MRR, LLM-as-judge

The interview question:
'How do you measure RAG quality offline? Walk me through Recall@K,
 nDCG, MRR. When do you use each? Why is LLM-as-judge useful?'

L6 answer structure:
- Recall@K: 'is the right answer in the top K?' — coarse
- MRR: 'where is the FIRST right answer ranked?' — for Q&A with one gold
- nDCG: 'how good is the RANKING, position-weighted?' — for ordered relevance
- LLM-as-judge: 'does the answer look right?' — for open-ended
- The L6 picks Recall@8 for retrieval, nDCG@10 for ranking, LLM-as-judge for generation
"""
import math
import random
from collections import defaultdict
import numpy as np

# ════════════════════════════════════════════════════════════════
# DEMO 1: Recall@K
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("RECALL@K: 'is the right answer in the top K?'")
print("=" * 70)
print("""
Use case: retrieval quality, when you have N relevant docs and want
to know 'did we surface at least one in the top K?'

  Recall@K = |relevant ∩ retrieved_top_K| / |relevant|

For RAG: K=8, because the LLM context is 8 chunks.
If Recall@8 = 0.85, then 15% of queries are missing the gold doc.
""")

def recall_at_k(retrieved, relevant, k):
    """retrieved: list of doc_ids (ranked). relevant: set of doc_ids."""
    top_k = set(retrieved[:k])
    if not relevant:
        return 0.0
    return len(top_k & relevant) / len(relevant)

# Example
retrieved = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10']
relevant = {'d3', 'd7', 'd12'}  # 3 relevant docs
print(f"\nRetrieved (top 10): {retrieved}")
print(f"Relevant: {relevant}")
for k in [1, 3, 5, 8, 10]:
    r = recall_at_k(retrieved, relevant, k)
    print(f"  Recall@{k}: {r:.2f}")

# ════════════════════════════════════════════════════════════════
# DEMO 2: MRR (Mean Reciprocal Rank)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MRR: 'where is the FIRST right answer ranked?'")
print("=" * 70)
print("""
Use case: Q&A with ONE gold answer. 'How soon did we surface it?'

  RR = 1 / rank_of_first_relevant
  MRR = mean over queries

  First relevant at rank 1: RR = 1.0
  First relevant at rank 2: RR = 0.5
  First relevant at rank 5: RR = 0.2
  No relevant in top K: RR = 0.0
""")

def mrr(retrieved, relevant):
    """Reciprocal rank of first relevant doc."""
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant:
            return 1.0 / i
    return 0.0

queries = [
    (['d1', 'd2', 'd3'], {'d1'}),  # RR=1.0
    (['d5', 'd1', 'd2'], {'d1'}),  # RR=0.5
    (['d5', 'd6', 'd1'], {'d1'}),  # RR=0.33
    (['d5', 'd6', 'd7'], {'d1'}),  # RR=0.0 (not in top K)
]
mrr_scores = []
for ret, rel in queries:
    rr = mrr(ret, rel)
    mrr_scores.append(rr)
    print(f"  Retrieved {ret}, relevant {rel}: RR = {rr:.2f}")
print(f"  MRR = {sum(mrr_scores)/len(mrr_scores):.3f}")

# ════════════════════════════════════════════════════════════════
# DEMO 3: nDCG (Normalized Discounted Cumulative Gain)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("nDCG: 'how good is the RANKING, position-weighted?'")
print("=" * 70)
print("""
Use case: ranking quality with graded relevance (0, 1, 2, 3).
Position matters: rank 1 wrong is worse than rank 8 wrong.

  DCG = SUM (2^rel_i - 1) / log2(i + 1)  (for i=1 to K)
  nDCG = DCG / IDCG  (IDCG = DCG of perfect ranking)

Relevance grades:
  0 = not relevant
  1 = marginally relevant
  2 = relevant
  3 = highly relevant (the gold)
""")

def dcg(relevances, k):
    """Discounted Cumulative Gain."""
    dcg = 0
    for i, rel in enumerate(relevances[:k], 1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg

def ndcg(retrieved, graded_relevant, k):
    """graded_relevant: dict doc_id -> relevance grade (0-3)."""
    rels = [graded_relevant.get(d, 0) for d in retrieved[:k]]
    ideal_rels = sorted(graded_relevant.values(), reverse=True)[:k]
    # Pad to length k
    while len(ideal_rels) < k:
        ideal_rels.append(0)
    dcg_val = dcg(rels, k)
    idcg_val = dcg(ideal_rels, k)
    if idcg_val == 0:
        return 0.0
    return dcg_val / idcg_val

# Example
retrieved = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8']
graded = {'d3': 3, 'd5': 2, 'd1': 1}  # d3 is highly relevant, d5 relevant, d1 marginal

print(f"\nRetrieved: {retrieved}")
print(f"Graded:    {graded}")
for k in [3, 5, 8]:
    score = ndcg(retrieved, graded, k)
    print(f"  nDCG@{k}: {score:.3f}")

# Compare: bad ranking
retrieved_bad = ['d4', 'd1', 'd5', 'd2', 'd6', 'd7', 'd3', 'd8']
print(f"\nBad ranking: {retrieved_bad}")
for k in [3, 5, 8]:
    score = ndcg(retrieved_bad, graded, k)
    print(f"  nDCG@{k}: {score:.3f}  <- lower because d3 (most relevant) is at rank 7")

# ════════════════════════════════════════════════════════════════
# DEMO 4: LLM-as-judge
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("LLM-AS-JUDGE: 'does the answer look right?'")
print("=" * 70)
print("""
Use case: open-ended generation, no programmatic gold.

How it works:
  1. Sample 100 queries from traces
  2. For each, generate answer with current model
  3. Send to GPT-4 with prompt: 'Rate this answer 1-5 on accuracy,
     groundedness, completeness. Return JSON {score, reason}.'
  4. Aggregate: mean score, % below 3 (regression)
  5. Cost: 100 * $0.05 = $5 per eval run
""")

# Simulated
def llm_judge(answer, evidence_ids):
    """Simulated LLM judge. In prod: real GPT-4 call."""
    cited = sum(1 for eid in evidence_ids if eid in answer)
    if cited >= 3:
        return {"score": 5, "reason": "cites 3+ evidence chunks, accurate"}
    elif cited >= 1:
        return {"score": 3, "reason": "cites 1-2 evidence, partial"}
    else:
        return {"score": 1, "reason": "no evidence cited, possible hallucination"}

sample_answers = [
    ("Based on doc_42 and doc_17, the answer is X", ["doc_42", "doc_17"]),
    ("The answer is X.", []),  # no evidence
    ("According to doc_42, doc_17, doc_99, doc_123, the answer is Y",
     ["doc_42", "doc_17", "doc_99", "doc_123"]),
]
print(f"\n{'Answer snippet':<60} {'Score':>5}")
print("-" * 70)
total_score = 0
for answer, evidence in sample_answers:
    result = llm_judge(answer, evidence)
    total_score += result['score']
    print(f"{answer[:58]:<60} {result['score']:>5}")
print(f"\nMean judge score: {total_score/len(sample_answers):.1f}/5")

# ════════════════════════════════════════════════════════════════
# THE L6 METRIC SUITE
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("THE L6 METRIC SUITE: which metric, when, why")
print("=" * 70)
print("""
RETRIEVAL (the chunks you fetch):
  Recall@8    — 'is the gold in top 8?' (LLM context = 8 chunks)
  MRR         — 'how soon?' (for Q&A with one gold)
  nDCG@10     — 'is the ranking good?' (for graded relevance)

RANKING (the order of the chunks):
  nDCG@10     — the gold standard for ranking
  MAP         — mean of per-query average precision

GENERATION (the LLM answer):
  LLM-as-judge — 'is it accurate, grounded, complete?'
  BLEU/ROUGE   — for known gold answers (translation, summarization)
  Human eval   — small sample (50-100) for ground truth

ONLINE (in production):
  Satisfaction — thumbs up/down from users
  Hallucination rate — LLM-as-judge on sample of traces
  p95 latency  — SLO monitoring

THE L6 DASHBOARD (5 cards):
  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
  │ Recall@8     │ nDCG@10      │ LLM-judge    │ Satisfaction │ p95 latency  │
  │   0.85       │   0.78       │   4.2/5      │   81%        │   580ms      │
  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

  These 5 cover: retrieval, ranking, generation, satisfaction, latency.
  A regression in any ONE is a bug to investigate.
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you measure RAG quality?')")
print("=" * 70)
print("""
Q: "How do you measure RAG quality offline? Which metrics?"

A: "Five metrics, one per layer:

RETRIEVAL:
  - Recall@8 = 'gold doc in top 8'. The LLM sees 8 chunks; if gold
    isn't there, no metric downstream matters.
  - MRR for Q&A with single gold (faster first-relevant = better UX)

RANKING:
  - nDCG@10 with graded relevance (0/1/2/3). Position-weighted:
    a wrong doc at rank 1 hurts more than at rank 8.

GENERATION:
  - LLM-as-judge on 100 sample queries/week. GPT-4 rates the answer
    1-5 on accuracy, groundedness, completeness.
  - Cost: $5/week. Catches regressions that no offline metric sees.

SATISFACTION (online):
  - Thumbs up/down from real users. The only ground truth that matters.
  - Build gold set: feedback.corrected_answer WHERE rating=thumbs_down

LATENCY (SLO):
  - p95 < 1s. 99% of users won't wait longer.

The pipeline:
  Weekly job: sample 100 queries -> run current model -> compute all 5
  metrics -> push to dashboard -> alert on regression > 5%

The cardinal sin: ship a model change without checking the dashboard.
Every promotion needs a green dashboard for 24h before full rollout.

Follow-up: 'is LLM-as-judge reliable?'
  - Inter-rater agreement (judge vs human): ~85%
  - Bias: prefers longer answers, prefers GPT-style writing
  - Mitigation: rotate judges, blind eval, sample for human review
""")
