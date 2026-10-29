# Lesson 1 — Embeddings Demystified

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> What an embedding is, what it preserves, what it loses, and how to choose one.

---

## The 30-second take

An embedding is a **dense vector representation of some content** (text, image, audio, code) such that **semantically similar content maps to nearby vectors**. That's it. Everything else is engineering.

```
   "I love this product"        ──embed──►  [0.12, -0.34, 0.88, ...]  (1536 floats)
   "I adore this item"          ──embed──►  [0.11, -0.32, 0.85, ...]   (close ↑)
   "Refund policy question"     ──embed──►  [-0.45, 0.22, -0.13, ...]  (far ↓)
```

The dot product (or cosine) between two vectors is a measure of semantic similarity.

---

## What an embedding preserves

- **Topic similarity** — texts about similar subjects cluster.
- **Sentiment proximity** — positive reviews are closer to other positive reviews.
- **Lexical / syntactic patterns** — sentences with similar structure cluster.
- **Cross-lingual alignment** — multilingual models embed "hello" near "bonjour" near "hola".

## What an embedding loses

- **Exact word matching** — semantic ≠ lexical. "refund" and "money back" are close semantically but lexically different.
- **Numerical reasoning** — "I have 3 apples" vs "I have 30 apples" embed similarly.
- **Logical negation** — "I like this" vs "I don't like this" can embed close.
- **Order-dependence** — token order is reduced to a bag-of-thoughts.
- **Long-range dependencies** — beyond the model's context window.

**The fix for most of these is hybrid search** (Lesson 5) — combine embeddings with lexical retrieval.

---

## The math in one paragraph

Given a text `t`, an embedding model `f` produces a vector `v = f(t) ∈ ℝᵈ` where `d` is the embedding dimension (e.g. 768, 1024, 1536, 3072).

**Distance metrics:**
- **Cosine similarity** — angle between vectors. Most common. Range: [-1, 1]. Used when magnitude doesn't matter (text).
- **Dot product** — magnitude × cosine. Used when magnitude matters (e.g. normalised vectors where it equals cosine).
- **Euclidean (L2)** — straight-line distance. Used when absolute position matters.

For OpenAI / Cohere / most modern text embeddings, **use cosine** (or dot product on normalised vectors).

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

---

## The model landscape (2026)

| Model | Dim | Strengths | Notes |
|---|---|---|---|
| **OpenAI `text-embedding-3-small`** | 1536 | Cheap, fast, good general | Default for many |
| **OpenAI `text-embedding-3-large`** | 3072 | Best general accuracy | Higher cost |
| **Cohere `embed-v3`** | 1024 | Multilingual, hybrid search native | Good for enterprise search |
| **Voyage `voyage-3`** | 1024 | Strong on technical / code | Good for code search |
| **BGE-M3 / E5 / GTE** | 1024 | Open-source, run anywhere | Self-host |
| **Sentence-Transformers** | varies | Open-source, vast library | Self-host |
| **Google `text-embedding-004`** | 768 | Vertex AI integration | GCP-native |
| **Bedrock Titan Embeddings** | 1536 | AWS-native | Bedrock |

**Defaults to start with:** OpenAI `text-embedding-3-small` for prototyping, upgrade to `text-embedding-3-large` or Cohere `embed-v3` for production. Self-host (BGE-M3) only when data cannot leave your VPC.

---

## The "what dimension" decision

- **Higher dim** = more capacity, slower, more storage
- **Lower dim** = faster, cheaper, less expressive

For most retrieval tasks:
- 768–1024 is the sweet spot.
- 3072 is overkill unless you have evidence it helps on your eval set.

Many providers (OpenAI `text-embedding-3-*`) support **Matryoshka-style dimensionality reduction**: train at 3072, embed at 1536 or 256 at inference with minimal accuracy loss. Useful for storage-cost-sensitive deployments.

---

## Embeddings are not free

**Cost (text-embedding-3-small, 2026):** ~$0.02 per 1M tokens. At 1 M docs × 500 tokens each = 500 M tokens = $10. Cheap.

**Cost (text-embedding-3-large):** ~$0.13 per 1M tokens. ~$65 for the same corpus.

**Storage:** 1 M docs × 1536 floats × 4 bytes = 6 GB. Plus index overhead, 2–3× that.

**Latency:** ~50–200 ms per call batched. Batch where possible.

---

## The "embedding quality" eval

How do you know your embedding model is good for your task?

```
   1. Curate 50-200 query-document pairs relevant to your domain
   2. For each query, retrieve top-k using cosine similarity
   3. Compute:
      - recall@k: did the right doc appear in the top k?
      - MRR: how high did it rank?
      - NDCG: how good was the ordering?
   4. Compare models on the same eval set
```

This is the single most important eval to build. Without it, you're picking models by vibes.

---

## The "what to embed" decision

Not every field should be embedded. Common patterns:

| Field type | Embed? | Why |
|---|---|---|
| Free-text descriptions | ✅ yes | High semantic value |
| Title / headline | ✅ yes | Compact summary |
| Code | ⚠️ specialised model | Use Voyage or code-specific embedder |
| Structured metadata (status, country) | ❌ no | Use as filter, not as embedding |
| IDs | ❌ no | Use as filter / exact match |
| Numeric values | ❌ no | Use as filter or as feature |
| Long documents | ⚠️ chunk first | Embed chunks, not whole doc (Lesson 2 of Module 5) |
| Names of people | ⚠️ careful | PII / privacy concerns |

---

## The "metadata matters as much as the embedding"

```
   Embedding alone:           Embedding + metadata filter:
   ─────────────────          ────────────────────────────
   semantic match on          semantic match on content
   content only               AND filter on tenant_id,
                              AND date > X,
                              AND language = en,
                              AND doc_type != archived

   The metadata is what makes
   the search USEFUL.
```

A vector DB without metadata filtering is a free-text search engine without operators. Always design for both.

---

## What Comes Next

> Lesson 2 — **Vector DB Fundamentals** — what an ANN index actually does, how to choose one, and the tradeoffs between speed, recall, and memory.
