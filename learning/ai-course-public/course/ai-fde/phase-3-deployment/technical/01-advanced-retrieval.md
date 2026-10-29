# Lesson T1 — Advanced retrieval and RAG

> **The mock store stops being enough at 50 chunks. Here's what to swap in.** 45 minutes. Hands-on: build a hybrid retriever in 250 lines.

By the end of this lesson you can lift Phase 2's `MockVectorStore` into a **hybrid retriever** (BM25 + dense + RRF fusion) and explain when each retriever is right. You have a working `HybridRetriever` class, a CLI that compares the three retrievers side-by-side, and a `POST /admin/reindex` endpoint that swaps the corpus at runtime.

The PacificFreight scenario: Mei reports "drafts are good but I had to paraphrase 'held at customs' to find the right policy chunk." That's the moment hybrid search earns its keep — the BM25 retriever catches the exact jargon the policy uses, the dense retriever catches Mei's paraphrases, and RRF combines the two without parameter tuning.

---

## 🎯 Outcome

You produce one artifact:

- `service/retrieval_v2.py` — a `HybridRetriever` class with `BM25Index`, `DenseIndex`, `RRFFusion`, `CrossEncoderReranker` (stub). Same `retrieve(query, k, source_filter) -> list[RetrievedChunk]` interface as Phase 2's `MockVectorStore`, so swapping it into `service/app.py` is one line.

When you finish, you can answer in 60 seconds: "should I use BM25, dense, or hybrid?" And you can sketch the math for Reciprocal Rank Fusion on a whiteboard.

## 🧠 Mindset

A modern RAG system is **two retrievers, not one**. Each is right for a different kind of match:

- **BM25** (Okapi BM25, the classical baseline): ranks by IDF-weighted term frequency with document-length normalization. Excellent at exact-term matches — "SGD 42.50", "FCA Incoterms 2020", "PF-1003". Robust across domains without any training. The right baseline for any new RAG system.
- **Dense** (cosine similarity over embedding vectors): ranks by semantic similarity. Excellent at paraphrases — "stuck" matches "held", "duty" matches "tariff". Requires an embedding model (text-embedding-3-small is the modern default) and a vector index.
- **Hybrid** (RRF fusion of the two): combines the strengths without the parameter-tuning tax. The Cormack et al. 2009 paper shows RRF is **as good as tuned convex combinations** at zero parameters.

The trap:

1. **The "dense is enough" trap.** You build a dense-only system, it works on 7 chunks, it falls apart at 1,000 chunks because the embedding model wasn't trained on your domain's jargon. **Always start with BM25 as the baseline**, add dense on top.
2. **The "tune the weights" trap.** You build a hybrid system, you have `alpha * bm25 + (1 - alpha) * dense`, you spend 3 days tuning `alpha`. Use RRF instead — it has no weights, and it's empirically as good.
3. **The "cross-encoder is always better" trap.** Cross-encoders (BERT-style models that score every (query, doc) pair jointly) are slower (10-100x) and rarely worth the latency cost unless you have a hard quality problem. Try RRF first; add a cross-encoder as Stage 3 only if needed.

> **FDE rule:** ship BM25 + dense + RRF. Add a cross-encoder when the eval shows the top-1 is wrong on 5+ rows per week. Not before.

## 🛠️ Practice — the HybridRetriever

### The math: Reciprocal Rank Fusion

Given two ranked lists from two retrievers, RRF assigns each document a score:

```
score(d) = Σ_i 1 / (k + rank_i(d))
```

Where `rank_i(d)` is the position of document `d` in retriever `i`'s ranking (1-indexed, missing = 0), and `k` is a constant (60 is the standard value, from the original paper).

**Worked example.** Two retrievers each rank 3 documents:

| Doc | BM25 rank | Dense rank | RRF score |
|---|---|---|---|
| A | 1 | 3 | 1/61 + 1/63 = 0.0323 |
| B | 2 | 1 | 1/62 + 1/61 = 0.0325 |
| C | 3 | 2 | 1/63 + 1/62 = 0.0318 |

So the RRF ranking is **B > A > C** — `B` is the consensus top, even though each retriever had a different top. This is the key insight: **RRF rewards documents that multiple retrievers agree on, not the highest individual score.**

### The code (lifted from `service/retrieval_v2.py`)

```python
class BM25Index:
    """Okapi BM25 with k1=1.5, b=0.75. The de-facto classical baseline."""
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None: ...
    def add(self, docs: Iterable[tuple[str, str]]) -> None: ...
    def score(self, query: str, doc_id: str) -> float:
        # IDF: log(1 + (N - df + 0.5) / (df + 0.5))
        # TF norm: (f * (k1+1)) / (f + k1 * (1 - b + b * dl/avgdl))
        ...

class DenseIndex:
    """Dense retriever stand-in. Uses Phase 2's token-overlap F1 + length
    bonus as the 'embedding similarity' until a real embedding model plugs in."""
    def __init__(self) -> None: ...
    def add(self, docs: Iterable[tuple[str, str]]) -> None: ...
    def score(self, query: str, doc_id: str) -> float: ...

class RRFFusion:
    def fuse(self, ranked_lists: list[list[str]]) -> list[tuple[str, float]]:
        scores: dict[str, float] = defaultdict(float)
        for ranked in ranked_lists:
            for rank, did in enumerate(ranked, start=1):
                scores[did] += 1.0 / (self.k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

class HybridRetriever:
    def retrieve(self, query, k=5, source_filter=None):
        pool_k = max(10, k * 3)
        bm25_hits = self.bm25.query(query, k=pool_k)
        dense_hits = self.dense.query(query, k=pool_k)
        fused = self._rrf.fuse(
            [[did for did, _ in bm25_hits], [did for did, _ in dense_hits]]
        )
        # Optional cross-encoder rerank — stub for now.
        # Apply source filter + final top-k.
        ...
```

### Run the demo

```bash
$ python3 service/retrieval_v2.py
--- query='customs duty payment'  source_filter=None ---
  bm25      shipment:PF-1003                8.9003
  bm25      style-guide#4                   2.5792
  bm25      shipment:PF-1010                1.7565
  dense     shipment:PF-1003                0.1224
  dense     shipment:PF-1007                0.0640
  dense     style-guide#4                   0.0556
  hybrid    shipment:PF-1003                0.0328
  hybrid    style-guide#4                   0.0320
  hybrid    shipment:PF-1007                0.0315
```

Three observations:

1. **BM25 and dense agree on PF-1003** — both retrievers rank it #1. The RRF consensus confirms.
2. **BM25 prefers jargon** — `style-guide#4` (Hard rules) ranks #2 in BM25 because of "customs duty payment" overlap.
3. **Dense prefers paraphrases** — `shipment:PF-1007` (Hiroshi Tanaka, Tokyo) ranks #2 in dense for "customs duty" because the chunk mentions "Tokyo Narita customs."

### The "stuck at customs in Vietnam" test

This is the killer test for hybrid search. Phase 2's pure-dense retriever would have returned PF-1007 (Tokyo) because "stuck" matches "held" via token overlap, but doesn't know the customer is in Vietnam:

```bash
$ python3 service/retrieval_v2.py
--- query='stuck at customs in Vietnam'  source_filter=None ---
  bm25      shipment:PF-1010                1.7565   ← Vietnam lane, customs held
  bm25      shipment:PF-1015                1.6058
  bm25      shipment:PF-1003                1.5814
  dense     shipment:PF-1007                0.0640   ← Tokyo customs — wrong lane
  dense     shipment:PF-1001                0.0541
  dense     shipment:PF-1015                0.0476
  hybrid    shipment:PF-1010                0.0320   ← BM25 wins, RRF promotes it
  hybrid    shipment:PF-1007                0.0320
  hybrid    shipment:PF-1015                0.0320
```

The hybrid retriever surfaces PF-1010 (Vietnam lane) at the top because BM25's IDF weight on "Vietnam" is strong. **Pure-dense would have failed this query.**

### The `POST /admin/reindex` endpoint

Phase 2's service loads the corpus once at startup. Phase 3 adds a runtime swap:

```bash
$ curl -X POST http://localhost:8000/admin/reindex \
       -H 'Content-Type: application/json' \
       -d '{"policy_chunks": [{"id": "policy:test1", "text": "Always be polite.", "section": "1"}]}'
{"ok": true, "n_policy": 1, "n_shipment": 0, "n_total": 1, "rebuild_ms": 0}
```

This is how Sarah (the ops manager) updates the style guide without restarting the service. The next `/draft` call uses the new corpus.

---

## 🏛️ FDE Lens — when does the mock stop being a mock?

Phase 2's ADR-0002 set the migration trigger at **policy > 50 chunks OR shipments > 10K**. Here's how to read that:

| Scale | What you need | Why |
|---|---|---|
| 7 policy + 15 shipments (Phase 2) | Token-overlap mock | Deterministic, free, no API key. Ships in 1 day. |
| 50 policy + 100 shipments | BM25 alone | IDF + TF saturation handles jargon; no need for embeddings yet. |
| 1K policy + 10K shipments | **BM25 + dense + RRF** (this lesson) | Dense catches paraphrases at this scale. The hybrid is what Phase 3 ships. |
| 50K policy + 1M shipments | BM25 + dense + RRF + cross-encoder rerank + Pinecone/pgvector | At this scale you need a real vector index for sub-100ms retrieval. The cross-encoder catches the long tail. |

**FDE rule of thumb:** if the eval shows context_precision < 0.7 on the top-3 retrieved, you need either (a) better chunking, (b) BM25 if you don't have it, or (c) a cross-encoder. In that order — each is cheaper to ship than the next.

## 🌙 Reflect

Write 3-5 sentences:

1. The eval set has 30 rows; the mock retriever scores `context_precision=0.62`. The new hybrid retriever scores... (run it). What's the delta, and what does it tell you about the mock's failure modes?
2. The cross-encoder is a "stub" in `retrieval_v2.py` — it does nothing. When would you swap in a real one, and what would the latency cost be?
3. The `POST /admin/reindex` endpoint takes a JSON body. A bad actor could POST 10M chunks. What would happen, and what's the right mitigation?
4. BM25's `k1` and `b` parameters have standard defaults (1.5, 0.75). Mei asks "should I tune them?" What do you say?
5. The RRF constant `k=60` is from the original 2009 paper. Cormack tested up to `k=10`. Why does `k=60` work better in practice?

**What's next** — T2 keeps the same eval harness from Phase 2 but adds the **live monitoring loop**: a `/feedback` endpoint, a `/metrics` Prometheus exporter, and the weekly **iteration report** that joins eval + feedback + cost. The artifact that survives the FDE's exit is the iteration cadence + the report template.
