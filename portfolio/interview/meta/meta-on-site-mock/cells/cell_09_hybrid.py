"""
Cell 9: Hybrid Search (BM25 + vector) with Reciprocal Rank Fusion (RRF)

What this proves for the L6 interview:
- Vector search misses exact matches (employee IDs, product SKUs)
- BM25 catches keyword matches but misses semantic similarity
- Reciprocal Rank Fusion (RRF) combines both with no weight tuning
- RRF formula: score(d) = sum(1 / (k + rank(d)))
"""
import sqlite3
import sqlite_vec
import numpy as np
import re
from collections import defaultdict
import time

conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

# ─── Setup: documents with mixed keyword + semantic content ────────
conn.executescript("""
    CREATE TABLE docs (
        doc_id  TEXT PRIMARY KEY,
        title   TEXT,
        body    TEXT
    );
    CREATE VIRTUAL TABLE docs_vec USING vec0(embedding float[64], doc_id text);
""")

np.random.seed(42)
DIM = 64

# Documents: some have unique IDs (BM25 wins), some are semantically similar (vector wins)
docs = [
    ("doc_001", "Employee ID Policy",       "Each employee receives a unique identifier in the format EMP-12345. This ID is used for HR systems."),
    ("doc_002", "Vacation Policy",          "Full-time employees receive 20 days of paid time off per calendar year, accrued monthly."),
    ("doc_003", "Remote Work Guidelines",   "Staff may work from home up to 3 days per week with manager approval. Coordinate via Slack."),
    ("doc_004", "Office Locations",         "Meta has offices in Menlo Park, New York, London, and Singapore. Visit meta.com/locations for details."),
    ("doc_005", "401k Match Policy",        "The company matches 100% of employee 401k contributions up to 5% of salary, vested over 4 years."),
    ("doc_006", "Onboarding Process",       "New hires attend a week-long orientation covering benefits, systems, and team introductions."),
    ("doc_007", "Performance Review Cycle", "Reviews happen bi-annually in March and September. Managers use the 9-box grid framework."),
    ("doc_008", "Expense Reimbursement",    "Submit expenses within 30 days via the Concur portal. Receipts required for amounts over $25."),
    ("doc_009", "Employee Resource Groups", "ERGs like Women in Tech and Black@Meta foster community. Membership is voluntary and confidential."),
    ("doc_010", "Promotion Criteria",       "Promotion requires sustained impact, demonstrated leadership, and manager sponsorship. Reviewed by calibration committee."),
]

# Build a vocabulary index for BM25
def tokenize(text):
    return re.findall(r'\w+', text.lower())

# Compute IDF (Inverse Document Frequency) for BM25
N_DOCS = len(docs)
df = defaultdict(int)  # document frequency
doc_tokens = {}
for doc_id, title, body in docs:
    tokens = set(tokenize(title + " " + body))
    doc_tokens[doc_id] = tokenize(title + " " + body)
    for t in tokens:
        df[t] += 1

idf = {t: np.log((N_DOCS - df[t] + 0.5) / (df[t] + 0.5) + 1) for t in df}

# Build embeddings (fake but deterministic, related to title keywords)
def doc_embedding(title, body):
    """Embedding = normalized hash of title words + body words, scaled by IDF."""
    tokens = tokenize(title + " " + body)
    vec = np.zeros(DIM)
    for t in tokens:
        h = hash(t) % DIM
        vec[h] += idf.get(t, 1.0)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

doc_vecs = {doc_id: doc_embedding(title, body) for doc_id, title, body in docs}

# Insert into DB
for doc_id, title, body in docs:
    conn.execute("INSERT INTO docs VALUES (?, ?, ?)", (doc_id, title, body))
    conn.execute("INSERT INTO docs_vec(rowid, embedding, doc_id) VALUES (?, ?, ?)",
                 (hash(doc_id) & 0x7FFFFFFF, sqlite_vec.serialize_float32(doc_vecs[doc_id].tolist()), doc_id))
conn.commit()
print(f"Inserted {len(docs)} documents with embeddings\n")

# ─── BM25 implementation ───────────────────────────────────────────
def bm25_score(query, doc_id, k1=1.5, b=0.75):
    """Standard BM25 scoring."""
    query_tokens = tokenize(query)
    doc_len = len(doc_tokens[doc_id])
    avg_dl = sum(len(toks) for toks in doc_tokens.values()) / N_DOCS
    score = 0.0
    for qt in query_tokens:
        if qt not in idf:
            continue
        tf = doc_tokens[doc_id].count(qt)
        if tf == 0:
            continue
        score += idf[qt] * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_dl))
    return score

def bm25_search(query, top_k=5):
    scores = [(doc_id, bm25_score(query, doc_id)) for doc_id, _, _ in docs]
    scores.sort(key=lambda x: -x[1])
    return scores[:top_k]

# ─── Vector search ─────────────────────────────────────────────────
def vector_search(query, top_k=5):
    qvec = doc_embedding(query, query)  # re-use same embedding function
    qvec_norm = np.linalg.norm(qvec)
    if qvec_norm > 0:
        qvec = qvec / qvec_norm
    qser = sqlite_vec.serialize_float32(qvec.tolist())
    results = conn.execute("""
        SELECT doc_id, distance FROM docs_vec
        WHERE embedding MATCH ? ORDER BY distance LIMIT ?
    """, (qser, top_k)).fetchall()
    return [(doc_id, 1 - dist) for doc_id, dist in results]  # convert distance to similarity

# ─── Reciprocal Rank Fusion ─────────────────────────────────────────
def reciprocal_rank_fusion(rankings, k=60):
    """
    RRF: score(d) = sum(1 / (k + rank(d)))
    k=60 is the standard from the original paper.
    """
    rrf_scores = defaultdict(float)
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            rrf_scores[doc_id] += 1.0 / (k + rank)
    return sorted(rrf_scores.items(), key=lambda x: -x[1])

# ─── Test queries ───────────────────────────────────────────────────
test_queries = [
    ("What is EMP-12345?",          "Exact ID match - BM25 should win"),
    ("How many vacation days?",     "Keyword match - BM25 strong"),
    ("Tell me about time off",      "Semantic - vector should help"),
    ("401k retirement plan",        "Mixed - both should contribute"),
]

print("=" * 70)
print("HYBRID SEARCH: BM25 + VECTOR + RRF")
print("=" * 70)

for query, expected in test_queries:
    print(f"\n>>> Query: '{query}'  ({expected})")
    print("-" * 70)

    bm25_results = bm25_search(query, top_k=5)
    vector_results = vector_search(query, top_k=5)
    hybrid_results = reciprocal_rank_fusion([bm25_results, vector_results], k=60)

    print(f"  BM25 Top 3:    ", end="")
    for doc_id, score in bm25_results[:3]:
        title = next(t for d, t, _ in docs if d == doc_id)
        print(f"{doc_id}({score:.2f})", end=" ")
    print()

    print(f"  Vector Top 3:  ", end="")
    for doc_id, sim in vector_results[:3]:
        title = next(t for d, t, _ in docs if d == doc_id)
        print(f"{doc_id}({sim:.2f})", end=" ")
    print()

    print(f"  Hybrid (RRF):  ", end="")
    for doc_id, rrf in hybrid_results[:3]:
        print(f"{doc_id}({rrf:.4f})", end=" ")
    print()

# ─── Benchmark: which is faster? ────────────────────────────────────
print("\n" + "=" * 70)
print("LATENCY COMPARISON: BM25 vs Vector vs Hybrid")
print("=" * 70)

query = "vacation policy employee benefits"
N_TRIALS = 100

# Warm up
bm25_search(query); vector_search(query)

t0 = time.perf_counter()
for _ in range(N_TRIALS):
    bm25_search(query)
bm25_ms = (time.perf_counter() - t0) * 1000 / N_TRIALS

t0 = time.perf_counter()
for _ in range(N_TRIALS):
    vector_search(query)
vec_ms = (time.perf_counter() - t0) * 1000 / N_TRIALS

t0 = time.perf_counter()
for _ in range(N_TRIALS):
    bm25_results = bm25_search(query)
    vector_results = vector_search(query)
    reciprocal_rank_fusion([bm25_results, vector_results])
hyb_ms = (time.perf_counter() - t0) * 1000 / N_TRIALS

print(f"\nAvg latency per query ({N_TRIALS} trials):")
print(f"  BM25 only:    {bm25_ms:.2f}ms")
print(f"  Vector only:  {vec_ms:.2f}ms")
print(f"  Hybrid (RRF): {hyb_ms:.2f}ms  (BM25 + vector + fusion)")

# ─── L6 talking point ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'why hybrid, not just vector?')")
print("=" * 70)
print("""
Q: "Why hybrid search? Doesn't vector search cover everything?"

A: "No. Vector search has two failure modes:

1. EXACT MATCH: User asks 'What is my employee ID EMP-9847?' - the embedding
   of 'EMP-9847' is essentially random. Vector search returns semantically
   related docs (any doc with 'employee ID') but not the right one.
   BM25 nails it because it does exact token match.

2. ACRONYM / SKU: 'P-40', 'iPhone 15', 'API v3.2' - same problem.
   Real users type IDs and SKUs, not natural language.

BM25 covers exact match, vector covers semantics. Reciprocal Rank Fusion
combines them with no weight tuning - just rank position. k=60 in the
formula is from the original paper (Cormack et al. 2009).

In prod: hybrid adds ~1ms to p95 latency (parallel queries + RRF).
That's the price for 20-30% recall improvement on real user queries.

Architecture: BM25 in OpenSearch/Elasticsearch + Vector in Qdrant.
RRF runs in the serving path. Cache RRF results in Redis for hot queries.
""")
