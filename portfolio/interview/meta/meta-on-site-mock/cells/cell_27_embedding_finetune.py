"""
Cell 27: Embedding Fine-Tuning — when, how, and the eval gate

The interview question:
'When would you fine-tune an embedding model instead of using
 off-the-shelf? Walk me through the process.'

L6 answer structure:
- Off-the-shelf (ada-002, text-embedding-3) covers 80% of cases
- Fine-tune when: domain jargon, retrieval is poor, cost matters
- 3-step process: data prep, fine-tune, eval gate
- Cost: $5-50k for one fine-tune, 2-4 weeks engineer time
- Eval gate: must beat baseline on Recall@8 by >= 5pp
"""
import numpy as np
import time
import random
from collections import defaultdict

# ════════════════════════════════════════════════════════════════
# WHEN TO FINE-TUNE: the L6 decision matrix
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("WHEN TO FINE-TUNE: the L6 decision matrix")
print("=" * 70)
print("""
Off-the-shelf works for 80% of cases. Fine-tune ONLY when:

  ✓ Domain jargon: 'CCPA §1798.105' vs 'data deletion' (legal)
  ✓ Acronyms: 'P95 latency' vs 'p95' vs 'latency percentile'
  ✓ Code: function names, error codes ('HTTP 503' not 'server busy')
  ✓ Cost: fine-tune once, run cheap forever
  ✓ Recall@8 < 0.7 with off-the-shelf (the bar)

DON'T fine-tune when:
  ✗ Off-the-shelf Recall@8 > 0.85
  ✗ You don't have a gold set yet (build one first)
  ✗ Domain is broad (general Q&A, not specialized)
  ✗ You can't measure the improvement (no eval harness)

The cardinal sin: fine-tune on synthetic data from an LLM.
  Result: model learns LLM's biases, not real user behavior.
  The L6 always uses REAL USER QUERIES from logs.
""")

# ════════════════════════════════════════════════════════════════
# SIMULATION: off-the-shelf vs fine-tuned on domain
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SIMULATION: off-the-shelf vs fine-tuned (legal domain)")
print("=" * 70)

# Simulate 2 embedding models
class EmbeddingModel:
    def __init__(self, name, domain_alignment):
        self.name = name
        self.domain_alignment = domain_alignment  # 0-1, how well it knows domain
    def embed(self, text):
        # Simulate: model with low domain_alignment is noisy on jargon
        np.random.seed(hash(text) % 10000)
        base = np.random.randn(64)
        # Add domain-specific signal proportional to alignment
        if 'gdpr' in text.lower() or 'ccpa' in text.lower() or '§' in text:
            base += self.domain_alignment * 5 * np.random.randn(64)
        return base / np.linalg.norm(base)

# Simulate 1000 legal docs
np.random.seed(42)
legal_docs = []
for i in range(1000):
    if i % 3 == 0:
        text = f"GDPR Article 17 grants data subjects the right to erasure"
    elif i % 3 == 1:
        text = f"CCPA §1798.105 requires deletion upon verifiable consumer request"
    else:
        text = f"Under privacy law, personal data must be erased on request"
    legal_docs.append(text)

# Simulate 100 user queries (mix of jargon and natural)
queries = [
    "right to be forgotten",  # paraphrase, not jargon
    "GDPR Article 17",         # exact jargon
    "CCPA deletion request",   # mixed
    "delete my data",          # natural
] * 25

# Simulate ground truth: which docs are relevant to which query
def ground_relevant(q):
    """For simulation: 'GDPR Article 17' query -> docs with that text."""
    q_lower = q.lower()
    if 'gdpr article 17' in q_lower:
        return set(range(0, 1000, 3))  # every 3rd doc
    elif 'ccpa' in q_lower:
        return set(range(1, 1000, 3))
    elif 'right to be forgotten' in q_lower:
        return set(range(0, 1000, 3))  # matches GDPR docs
    else:
        return set(range(2, 1000, 3))  # matches general privacy

# Compute Recall@10 for both models
def recall_at_k(model, queries, docs, k=10):
    # Embed all docs
    doc_embs = np.array([model.embed(d) for d in docs])
    recalls = []
    for q in queries:
        q_emb = model.embed(q)
        sims = doc_embs @ q_emb
        top_k = set(np.argsort(-sims)[:k])
        relevant = ground_relevant(q)
        if not relevant: continue
        recalls.append(len(top_k & relevant) / min(k, len(relevant)))
    return np.mean(recalls) if recalls else 0

print("\nRecall@10 on 100 legal queries:")
off_shelf = EmbeddingModel("text-embedding-3 (off-the-shelf)", domain_alignment=0.3)
fine_tuned = EmbeddingModel("fine-tuned (domain_alignment=0.9)", domain_alignment=0.9)

r_off = recall_at_k(off_shelf, queries, legal_docs, k=10)
r_ft = recall_at_k(fine_tuned, queries, legal_docs, k=10)
print(f"  Off-the-shelf:  Recall@10 = {r_off:.3f}")
print(f"  Fine-tuned:     Recall@10 = {r_ft:.3f}")
print(f"  Improvement:    +{(r_ft - r_off)*100:.1f} pp")

# ════════════════════════════════════════════════════════════════
# THE 3-STEP PROCESS
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("THE 3-STEP FINE-TUNING PROCESS")
print("=" * 70)
print("""
STEP 1: DATA PREP (1-2 weeks)
  - Mine 10k+ (query, relevant_doc) pairs from logs
  - Filter: query has feedback, doc is gold-relevant
  - For each (query, doc_positive), sample 5-10 doc_negatives
  - Format: {"query": q, "positive": [d1], "negatives": [d2, d3, ...]}

STEP 2: FINE-TUNE (2-4 hours compute, $500-5k)
  - Start from base model (text-embedding-3)
  - Loss: contrastive (cosine sim positive high, negatives low)
  - Hyperparams: lr=1e-5, batch=64, epochs=3-5
  - Validate on held-out 10% of data

STEP 3: EVAL GATE (1-2 days)
  - Compute Recall@8, MRR, nDCG@10 on GOLD SET (separate from training)
  - Must beat baseline by >= 5pp on Recall@8
  - If not, iterate (more data, different hyperparams)
  - If yes, proceed to shadow dual-read A/B (cell 24)
""")

# ════════════════════════════════════════════════════════════════
# COST BREAKDOWN
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("COST: fine-tune vs stay off-the-shelf")
print("=" * 70)
print("""
Fine-tuning cost (one-time):
  - 10k training pairs, 3 epochs, batch 64
  - ~470 steps/epoch * 3 = 1410 steps
  - A100 GPU: ~30 min
  - Cost: ~$10-50 per run
  - Iterate 5-10 times: $50-500
  - Engineer time: 2-4 weeks = $20-40k (loaded)

Total: $20-50k for one fine-tune.

Operational cost saved (per year):
  - 1M queries/day * 365 = 365M queries/year
  - If fine-tuned model is 10% smaller (e.g., 1024 vs 1536 dim):
    - Storage: 1B vectors * 1024*4 bytes = 4TB vs 6TB (saves 2TB)
    - At $0.1/GB/month: $200/month savings = $2400/year
  - If fine-tuned model has +10pp Recall@8:
    - Better answers, more satisfaction, more usage
    - Hard to quantify, but $1M+ in LLM cost saved (fewer retries)

ROI: $20-50k upfront, $100k+/year savings = pays back in <6 months.
""")

# ════════════════════════════════════════════════════════════════
# THE L6 DASHBOARD for fine-tune rollout
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("THE ROLLOUT DASHBOARD: 5 must-track metrics")
print("=" * 70)
print("""
During shadow A/B, monitor:

  ┌──────────────────┬────────────┬────────────┐
  │ Metric           │ Baseline   │ Fine-tuned │ Action if FT < Baseline
  ├──────────────────┼────────────┼────────────┤
  │ Recall@8         │ 0.85       │ 0.91       │ Roll back
  │ p95 latency      │ 380ms      │ 420ms      │ Investigate (acceptable if +5%)
  │ Cost per 1M q    │ $50        │ $45        │ Better!
  │ Satisfaction     │ 81%        │ 85%        │ Better!
  │ Hallucination    │ 4%         │ 3%         │ Better!
  └──────────────────┴────────────┴────────────┘

The decision is multi-metric:
  - If Recall improves AND latency degrades <10%: ship it
  - If Recall improves AND latency degrades >10%: optimize (smaller model, smaller dim)
  - If Recall regresses: kill the rollout, post-mortem
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'when to fine-tune embeddings?')")
print("=" * 70)
print("""
Q: "When would you fine-tune an embedding model instead of using
    off-the-shelf? Walk me through the process."

A: "Fine-tune ONLY when off-the-shelf Recall@8 < 0.7. For 80% of
   cases, off-the-shelf (text-embedding-3, bge-large) is enough.

The trigger conditions:
  1. Domain jargon: 'CCPA §1798.105' is not the same as 'data deletion'
     in off-the-shelf embedding space
  2. Acronyms: 'P95 latency' vs 'p95' vs '95th percentile'
  3. Code: function names, error codes
  4. Cost: smaller fine-tuned model can match larger off-the-shelf

THE 3-STEP PROCESS (4-6 weeks engineer time):

STEP 1: DATA PREP (1-2 weeks)
  - Mine 10k+ (query, relevant_doc) pairs from user logs
  - Filter: query has thumbs_up, doc is in top-3 of retrieval
  - For each: sample 5-10 negatives (hard negatives from retrieval)
  - Format: {query, positive: [d1], negatives: [d2, ...]}

STEP 2: FINE-TUNE (2-4 hours compute)
  - Start from text-embedding-3 base
  - Loss: contrastive (cosine sim: positive high, negatives low)
  - Hyperparams: lr=1e-5, batch=64, epochs=3-5
  - Validate on held-out 10%

STEP 3: EVAL GATE (1-2 days)
  - Compute Recall@8, MRR, nDCG@10 on GOLD SET (separate from train)
  - Must beat baseline by >= 5pp on Recall@8
  - If yes: shadow dual-read A/B (cell 24 pattern)
  - If no: iterate (more data, different hyperparams)

THE CARDINAL SIN: fine-tune on synthetic data from an LLM.
  Result: model learns LLM's biases, not real user behavior.
  The L6 ALWAYS uses real user queries from logs.

Cost: $20-50k upfront, $100k+/year savings = pays back in 6 months.
""")
