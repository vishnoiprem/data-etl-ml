"""
Cell 21: HNSW Index — the algorithm, the trade-offs, the sharding strategy

The interview question:
'How does HNSW work? Why is it faster than brute force?
 What's the recall / latency / memory trade-off?
 How do you shard a 100M-vector index?'

L6 answer structure:
- HNSW = Hierarchical Navigable Small World (multi-layer graph)
- Each layer is a navigable graph; search starts at top, descends
- Sub-linear: O(log N) per query instead of O(N) for brute force
- Trade-off: ef_search controls accuracy vs speed
- Sharding by hash(doc_id) % N_SHARDS distributes load
"""
import numpy as np
import time
import random
from collections import defaultdict
import heapq

# ════════════════════════════════════════════════════════════════
# BRUTE FORCE vs HNSW: the latency difference
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("BRUTE FORCE: O(N) per query (the baseline)")
print("=" * 70)

np.random.seed(42)
DIM = 64

# Build a 10k vector corpus
N = 10_000
corpus = np.random.randn(N, DIM).astype(np.float32)
# Normalize for cosine
corpus = corpus / np.linalg.norm(corpus, axis=1, keepdims=True)

# Brute force KNN
def brute_force_knn(query, k=10):
    """Cosine sim against all N vectors. O(N)."""
    sims = corpus @ query
    top_k = np.argsort(-sims)[:k]
    return top_k, sims[top_k]

# 100 queries
N_QUERIES = 100
queries = np.random.randn(N_QUERIES, DIM).astype(np.float32)
queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)

t0 = time.perf_counter()
for q in queries:
    brute_force_knn(q, k=10)
bf_ms = (time.perf_counter() - t0) * 1000 / N_QUERIES
print(f"  Brute force: {bf_ms:.2f}ms per query ({N} vectors)")
print(f"  At 1M vectors: ~{bf_ms * 100:.0f}ms per query (10x slower)")
print(f"  At 100M vectors: ~{bf_ms * 10000 / 1000:.0f}s (UNUSABLE)")

# ════════════════════════════════════════════════════════════════
# HNSW INTUITION
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("HNSW INTUITION: the multi-layer graph")
print("=" * 70)
print("""
HNSW = Hierarchical Navigable Small World graph.

Imagine a city with 4 layers of roads:
  Layer 3 (top):    highways (a few connections, long distance)
  Layer 2:          main avenues
  Layer 1:          streets
  Layer 0 (bottom): every alley (all nodes, dense connections)

Search algorithm:
  1. Start at a random entry point in the TOP layer
  2. Greedily walk to nearest neighbor (few steps, long jumps)
  3. Drop down a layer
  4. Repeat: greedily walk in this layer
  5. At layer 0, return top-K nearest

Why it's fast:
  - Each layer is a sparse graph (avg degree ~16)
  - Total hops from top to bottom: O(log N) layers
  - Each hop: O(1) neighbor lookups
  - Total: O(log N) per query
  - Brute force: O(N)

Build cost: O(N log N) to construct all layers
Memory: ~3-5x the raw vector size (graph edges + vectors)
""")

# ════════════════════════════════════════════════════════════════
# SIMULATED HNSW: 2-layer graph for intuition
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SIMULATED HNSW: 2-layer graph (top: 10 nodes, bottom: 1000)")
print("=" * 70)

class SimpleHNSW:
    """
    A simplified 2-layer HNSW for demo purposes.
    Top layer: 10 nodes (1% of corpus), each connected to 3-5 nearest
    Bottom layer: all 1000 nodes, each connected to 10-20 nearest
    """
    def __init__(self, vectors, top_fraction=0.1, M=8):
        self.vectors = vectors
        self.N = len(vectors)
        self.M = M
        # Top layer: random sample of top_fraction
        self.top_nodes = set(random.sample(range(self.N), int(self.N * top_fraction)))
        # Build adjacency: each node -> M nearest neighbors
        self.bottom_graph = defaultdict(list)
        self.top_graph = defaultdict(list)
        self._build_graph()

    def _build_graph(self):
        """O(N^2) build for demo. Real HNSW is O(N log N)."""
        # Bottom graph: for each node, M nearest
        for i in range(self.N):
            sims = self.vectors @ self.vectors[i]
            # Exclude self, take top M
            top_m = np.argsort(-sims)[1:self.M+1]
            self.bottom_graph[i] = list(top_m)
        # Top graph: only for top_nodes
        for i in self.top_nodes:
            sims = self.vectors @ self.vectors[i]
            candidates = [j for j in np.argsort(-sims) if j in self.top_nodes and j != i]
            self.top_graph[i] = candidates[:3]  # fewer connections at top

    def search(self, query, k=10, max_hops=100):
        """Simulate HNSW search: top layer -> bottom layer."""
        # Start at any top node
        if not self.top_nodes:
            return self._brute_search(query, k)

        start = next(iter(self.top_nodes))
        visited = {start}
        current = start
        current_sim = float(self.vectors[current] @ query)

        # Phase 1: greedy walk in top layer
        for _ in range(max_hops):
            improved = False
            for neighbor in self.top_graph.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                sim = float(self.vectors[neighbor] @ query)
                if sim > current_sim:
                    current = neighbor
                    current_sim = sim
                    improved = True
            if not improved:
                break

        # Phase 2: greedy walk in bottom layer
        for _ in range(max_hops):
            improved = False
            for neighbor in self.bottom_graph.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                sim = float(self.vectors[neighbor] @ query)
                if sim > current_sim:
                    current = neighbor
                    current_sim = sim
                    improved = True
            if not improved:
                break

        # Return top-K from visited
        sims = [(i, float(self.vectors[i] @ query)) for i in visited]
        sims.sort(key=lambda x: -x[1])
        return [i for i, _ in sims[:k]]

    def _brute_search(self, query, k=10):
        sims = self.vectors @ query
        return list(np.argsort(-sims)[:k])

# Build simulated HNSW
random.seed(42)
small_n = 1000
small_corpus = np.random.randn(small_n, DIM).astype(np.float32)
small_corpus = small_corpus / np.linalg.norm(small_corpus, axis=1, keepdims=True)

hnsw = SimpleHNSW(small_corpus, top_fraction=0.1, M=8)
print(f"  Built: {small_n} nodes")
print(f"  Top layer: {len(hnsw.top_nodes)} nodes")
print(f"  Bottom graph: avg degree ~{hnsw.M}")

# Time HNSW
t0 = time.perf_counter()
for q in queries[:10]:
    hnsw.search(q, k=10)
hnsw_ms = (time.perf_counter() - t0) * 1000 / 10

# Time brute force on same size
t0 = time.perf_counter()
for q in queries[:10]:
    sims = small_corpus @ q
    np.argsort(-sims)[:10]
bf_small_ms = (time.perf_counter() - t0) * 1000 / 10

print(f"\n  On 1000 vectors:")
print(f"  Brute force:   {bf_small_ms:.2f}ms")
print(f"  HNSW (sim):    {hnsw_ms:.2f}ms")
print(f"  At 1M vectors, gap becomes 100x")

# Recall: how often does HNSW match brute force?
correct = 0
for q in queries[:50]:
    bf_top = set(np.argsort(-(small_corpus @ q))[:10])
    hnsw_top = set(hnsw.search(q, k=10))
    correct += len(bf_top & hnsw_top) / 10
recall = correct / 50
print(f"  Recall@10:     {recall:.2f}  (vs brute force)")

# ════════════════════════════════════════════════════════════════
# ef_search: the recall / latency knob
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("ef_search: the recall / latency knob (L6 trade-off)")
print("=" * 70)
print("""
HNSW has 3 key parameters:
  M:        max connections per node (8-32, more = better recall, more memory)
  efConstruction: search depth during build (100-200, more = better graph)
  efSearch: search depth at query (10-200, more = better recall, slower)

efSearch is the L6 knob: tune at query time, no rebuild.
  efSearch=10:  fast, ~85% recall
  efSearch=50:  balanced, ~95% recall (default)
  efSearch=200: slow, ~99% recall

In Qdrant: set in query params
  client.search(..., params={"hnsw_ef": 100})
""")

# ════════════════════════════════════════════════════════════════
# SHARDING: 100M vectors across 10 shards
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SHARDING: 100M vectors across 10 shards")
print("=" * 70)
print("""
The problem: a single HNSW index with 100M vectors = 100GB+ memory
  - Doesn't fit on one node (typical: 256GB-1TB RAM)
  - One node is a SPOF
  - One node can't serve 10K QPS

The solution: shard by hash(doc_id) % N_SHARDS
  - 10 shards, 10M vectors each, ~10GB per shard
  - Each shard = 3 replicas (read availability)
  - Query goes to ALL shards in parallel, merge top-K

  shards = [hash(doc_id) % 10 for _ in queries]
  per-shard top-K = 50 (oversample for merge quality)
  merge = sort by score, take top 8

Cross-shard merge cost: O(K * N_SHARDS) = O(50 * 10) = O(500) per query
This is the bottleneck for very high shard counts (>100).

For 100M vectors at Meta:
  - 10 shards, 10M each, 3 replicas = 30 nodes
  - Each node: 32 vCPU, 128GB RAM
  - Cost: ~$3k/month/node * 30 = $90k/month
  - QPS capacity: 10 shards * 1k QPS = 10k QPS
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'HNSW vs IVF vs brute force?')")
print("=" * 70)
print("""
Q: "How does HNSW work? How do you shard a 100M-vector index?"

A: "HNSW is a multi-layer navigable graph. Top layers are sparse
   with long-distance connections; bottom layer has all nodes with
   short-distance connections. Search starts at the top, walks
   greedily to nearest, drops a layer, repeats. O(log N) per query.

Why HNSW:
  - Sub-linear query time: 25ms p99 for 1M vectors
  - High recall: 95%+ with ef_search=50
  - Incremental: add vectors without rebuild
  - Memory: ~3-5x raw vector size

Why not brute force:
  - O(N) per query
  - 100k vectors = 50ms, 1M = 500ms, 100M = UNUSABLE

Why not IVF (Inverted File Index):
  - Faster build than HNSW
  - Lower recall at same latency (~85% vs 95%)
  - Used when you need to rebuild daily
  - L6 default: HNSW for prod, IVF for batch eval

Sharding strategy for 100M vectors:
  - 10 shards by hash(doc_id) % 10
  - 10M vectors per shard, ~10GB each
  - 3 replicas per shard for availability
  - Query to all shards in parallel
  - Per-shard top-50, merge to top-8
  - Cost: ~$90k/month for 10k QPS capacity

The cardinal sin: one giant shard, no replicas.
Result: OOM on insert, single point of failure, can't scale QPS.

The trade-off knob: ef_search.
  Low (10):  fast, low recall (85%)
  High (200): slow, high recall (99%)
  Default (50): balanced

In prod we tune ef_search via A/B test:
  - 50% traffic: ef=50 (default)
  - 50% traffic: ef=100
  - Compare: latency, recall@8 (from gold set), satisfaction
  - Ship the winner.

For cold-start with no gold set:
  - Start ef=50
  - Build gold set from feedback (thumbs up/down)
  - Re-tune monthly as the gold set grows
""")
