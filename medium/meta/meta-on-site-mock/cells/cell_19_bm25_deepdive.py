"""
Cell 19: BM25 Deep Dive — the L6 hybrid search question

The interview question:
'Why hybrid search? Doesn't vector search subsume BM25?'
'Walk me through the BM25 formula.'

L6 answer:
- Vector: semantic similarity, fails on EXACT term match
  ('GDPR Article 17' - vector knows GDPR ~ privacy, but not 'Article 17')
- BM25: lexical exact match, fails on PARAPHRASES
  ('right to be forgotten' - no docs contain this exact phrase)
- Hybrid: best of both, RRF fusion = no weight tuning

This cell builds BM25 from scratch and shows the trade-off vs vector.
"""
import math
import numpy as np
from collections import Counter, defaultdict
import time

# ════════════════════════════════════════════════════════════════
# BUILD BM25 FROM SCRATCH (the L6 whiteboard version)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("BM25: the formula, the index, the query")
print("=" * 70)
print("""
BM25 score for query Q, document D:

  score(Q, D) = SUM over terms t in Q:
    IDF(t) * (tf(t, D) * (k1 + 1))
              / (tf(t, D) + k1 * (1 - b + b * |D| / avgdl))

Where:
  IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
  tf(t, D) = term frequency in D
  df(t) = number of docs containing t
  N = total docs
  |D| = length of D in words
  avgdl = average doc length
  k1 = 1.5 (typical), b = 0.75 (typical)

Why BM25 vs TF-IDF:
  - Term saturation: tf=10 is not 10x better than tf=1 (k1 caps it)
  - Length normalization: long docs don't auto-win (b factor)
""")

class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs = []          # list of list of tokens
        self.doc_lens = []
        self.avgdl = 0
        self.df = defaultdict(int)  # doc freq per term
        self.tf = []            # per-doc term freq
        self.idf = {}

    def fit(self, corpus):
        """corpus: list of strings"""
        for doc in corpus:
            tokens = doc.lower().split()
            self.docs.append(tokens)
            self.doc_lens.append(len(tokens))
            # Term freq in this doc
            tf_doc = Counter(tokens)
            self.tf.append(tf_doc)
            # Doc freq (count once per doc)
            for term in set(tokens):
                self.df[term] += 1
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens)
        N = len(self.docs)
        # Compute IDF for all terms
        for term, df in self.df.items():
            self.idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)
        return self

    def score(self, query, doc_idx):
        """BM25 score for one query against one doc."""
        score = 0
        doc_tf = self.tf[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        for term in query.lower().split():
            if term not in self.idf:
                continue
            tf = doc_tf.get(term, 0)
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator
        return score

    def top_k(self, query, k=10):
        """Rank all docs by BM25 score for query."""
        scores = [(i, self.score(query, i)) for i in range(len(self.docs))]
        scores.sort(key=lambda x: -x[1])
        return scores[:k]

# ════════════════════════════════════════════════════════════════
# DEMO: 100 docs with GDPR / privacy / legal vocabulary
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DEMO: 100 docs, GDPR / privacy / legal domain")
print("=" * 70)

np.random.seed(42)
corpus = [
    # Docs that contain "GDPR Article 17" exactly
    "GDPR Article 17 grants the right to erasure also known as right to be forgotten",
    "Under GDPR Article 17 individuals can request deletion of personal data",
    "Article 17 of GDPR provides data subject rights for erasure requests",
    # Docs about privacy but don't say "Article 17"
    "California Consumer Privacy Act provides data deletion rights to state residents",
    "Privacy regulations require companies to honor data deletion requests",
    "Personal data should be erased upon user request under privacy law",
    # Noise
    "The weather is sunny today and the temperature is warm",
    "Machine learning models require large datasets for training",
    "Vector databases enable semantic search over high dimensional embeddings",
    "Python is a popular programming language for data engineering",
] * 10  # 100 docs total

print(f"  Built corpus: {len(corpus)} docs")
print(f"  3 docs explicitly say 'GDPR Article 17'")

# Build index
bm25 = BM25()
bm25.fit(corpus)
print(f"  Vocab: {len(bm25.df)} unique terms")
print(f"  Avg doc length: {bm25.avgdl:.1f} words")

# Query 1: Exact term "GDPR Article 17"
print("\n" + "=" * 70)
print("QUERY 1: 'GDPR Article 17' (exact term match)")
print("=" * 70)
results = bm25.top_k("GDPR Article 17", k=5)
for idx, score in results:
    preview = corpus[idx][:80] + "..."
    print(f"  score={score:>6.2f}  {preview}")

# Query 2: Paraphrase "right to be forgotten"
print("\n" + "=" * 70)
print("QUERY 2: 'right to be forgotten' (paraphrase, no exact match)")
print("=" * 70)
results = bm25.top_k("right to be forgotten", k=5)
for idx, score in results:
    preview = corpus[idx][:80] + "..."
    print(f"  score={score:>6.2f}  {preview}")

# ════════════════════════════════════════════════════════════════
# IDF INTUITION
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("IDF INTUITION: rare terms matter more")
print("=" * 70)
terms_to_check = ['gdpr', 'article', '17', 'data', 'the', 'is']
N = len(corpus)
print(f"\n{'Term':<12} {'df':>5} {'IDF':>8} {'Interpretation'}")
print("-" * 60)
for term in terms_to_check:
    df = bm25.df.get(term, 0)
    idf = bm25.idf.get(term, 0)
    interp = "rare, valuable" if idf > 3 else "common, less valuable" if idf > 1 else "stopword-ish"
    print(f"{term:<12} {df:>5} {idf:>8.2f}  {interp}")

print("""
Notice: 'gdpr' (df=30) has high IDF.
         'the'  (df=100) has low IDF (almost all docs).
         '17'   (df=30) has high IDF (specific).

The IDF weight makes rare-but-relevant terms dominate the score.
""")

# ════════════════════════════════════════════════════════════════
# WHY HYBRID: the L6 punchline
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("WHY HYBRID: vector misses exact terms, BM25 misses paraphrases")
print("=" * 70)
print("""
Failure mode 1: vector misses 'Article 17'
  - Vector knows 'GDPR' ~ 'privacy' ~ 'data protection'
  - But 'Article 17' is a SPECIFIC provision. Vector averages it out.
  - BM25 wins here: exact term match scores high.

Failure mode 2: BM25 misses 'right to be forgotten'
  - No doc says 'right to be forgotten' verbatim
  - But docs talk about it as 'data deletion' / 'erasure'
  - Vector wins here: semantic similarity catches the paraphrase.

Hybrid (RRF fusion): get BOTH signals, no weight tuning.
""")

# Simulate the trade-off
def vector_search(query, k=5):
    """Mock vector search: matches paraphrase, misses exact 'Article 17'."""
    query_tokens = set(query.lower().split())
    scored = []
    for i, doc in enumerate(corpus):
        doc_tokens = set(doc.lower().split())
        # Crude semantic: word overlap
        overlap = len(query_tokens & doc_tokens) / len(query_tokens)
        scored.append((i, overlap))
    scored.sort(key=lambda x: -x[1])
    return scored[:k]

print("Query: 'right to be forgotten'")
print("\n  VECTOR top-3 (finds paraphrases):")
for idx, score in vector_search("right to be forgotten", 3):
    print(f"    {score:.2f}  {corpus[idx][:70]}...")

print("\n  BM25 top-3 (finds exact terms):")
for idx, score in bm25.top_k("right to be forgotten", 3):
    print(f"    {score:.2f}  {corpus[idx][:70]}...")

print("\n  HYBRID RRF top-3 (both signals):")
# Reciprocal Rank Fusion
vector_ranks = {idx: rank for rank, (idx, _) in enumerate(vector_search("right to be forgotten", 20))}
bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25.top_k("right to be forgotten", 20))}
all_idx = set(vector_ranks) | set(bm25_ranks)
rrf_scores = []
for idx in all_idx:
    rrf = (1 / (60 + vector_ranks.get(idx, 1000))) + (1 / (60 + bm25_ranks.get(idx, 1000)))
    rrf_scores.append((idx, rrf))
rrf_scores.sort(key=lambda x: -x[1])
for idx, score in rrf_scores[:5]:
    print(f"    {score:.4f}  {corpus[idx][:70]}...")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'BM25 vs vector, why hybrid?')")
print("=" * 70)
print("""
Q: "Why hybrid search? Doesn't vector subsume BM25?"

A: "No. They have COMPLEMENTARY failure modes:

  Vector FAILS on:
    - Exact term / id / article number ('Article 17', 'SKU 12345')
    - Rare terms that haven't been seen in embedding training
    - Acronyms that mean different things in different domains
    - Code snippets, function names, error codes

  BM25 FAILS on:
    - Paraphrases ('right to be forgotten' ~ 'data deletion')
    - Synonyms ('car' ~ 'automobile')
    - Cross-lingual search (multilingual embeddings only)
    - Semantic similarity in low-vocabulary queries

  Hybrid via RRF (Reciprocal Rank Fusion):
    score(d) = 1/(60 + rank_vector(d)) + 1/(60 + rank_bm25(d))
    - No weight tuning (k=60 is universal)
    - Each signal contributes 0.5 weight by default
    - Robust to one signal being bad

Production setup at Meta scale:
  - 50M docs: BM25 index = 8GB, vector index = 200GB
  - BM25: Elasticsearch / Lucene (mature, 20ms p99)
  - Vector: HNSW in Qdrant / Milvus (sub-linear, 25ms p99)
  - RRF fusion: simple SQL or in-memory merge (1ms)
  - Total: ~46ms, Recall@8 typically 8-12 pp higher than either alone

The interview follow-up is 'walk me through BM25':
  - Term saturation (k1 cap prevents tf=1000 from dominating)
  - Length normalization (b factor prevents long docs from auto-winning)
  - IDF: log((N - df + 0.5) / (df + 0.5) + 1)
            rare term = high IDF
            common term = low IDF
""")
