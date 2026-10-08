# Architecture

See [`README.md`](./README.md) for the full architecture diagram, the
three-retrieval-strategy comparison, and the "two-hop" example that motivates
graph RAG.

## ADRs (Architecture Decision Records)

### ADR-001 — Use NetworkX + SQLite as the local graph store (not Neo4j / Neptune)

**Context.** The project needs a real graph store so subgraph extraction and
neighbour-walk retrieval are honest — not a stub. Production targets are
**Amazon Neptune** (managed, Gremlin/SPARQL) and **Neo4j** (Cypher).

**Decision.** Use a `networkx.DiGraph` in memory, mirrored to SQLite
(`data/graph.sqlite`) for persistence. The class boundary is
`src/graph_store.py::GraphStore` with the same `add_node` / `add_edge` /
`neighbors` / `subgraph` methods a Neptune or Neo4j backend would expose.

**Why.**
- Zero new infra. `pip install -r requirements.txt` and you have a working
  graph. The demo runs on a laptop with no Docker, no cloud account, no JVM.
- The ABC is the seam: swapping in `NeptuneGraphStore` later is one file.
- Performance is fine up to ~100k nodes / 1M edges — well past what a demo
  corpus needs, and the failure mode (slow subgraph extraction) is obvious.

**Trade-offs.**
- No ACID transactions across nodes. For demo this is fine; production
  Neptune would give them.
- No graph-visualisation UI. Production would add **Graph Explorer** or
  **Neo4j Bloom**.
- The Gremlin/Cypher query surface is replaced by Python method calls.

### ADR-002 — Real LLM by default, mock fallback

**Context.** The repo's `06-regulated-industry/` and `08-llmops-platform/`
make the same call: a real LLM when a key is present, a deterministic
mock otherwise. We mirror that.

**Decision.** `LLM_MODE=auto` (default) → real if `ANTHROPIC_API_KEY` is
set, else mock. The mock returns canned answers + canned graph triples
for the AcmeCorp sample corpus, so the demo is reproducible offline.

### ADR-003 — Reciprocal Rank Fusion for hybrid retrieval (not score-fusion)

**Context.** Combining vector similarity, BM25, and graph walks into one
ranking is the central design choice. Three common options:

1. **Score fusion** — normalise each score to [0,1], take a weighted sum.
   Breaks when distributions differ (cosine similarities are 0.2–0.8; BM25
   can be 0–50).
2. **Cross-encoder reranking** — feed all candidates to a reranker. Best
   quality, but a second LLM call per query. Out of scope for the demo.
3. **Reciprocal Rank Fusion (RRF)** — `score(d) = Σ 1 / (k + rank_d(strategy))`.
   Rank-based, no normalisation needed, well-studied (Cormack et al., 2009).

**Decision.** RRF with `k=60` (the original paper's default). Each strategy
contributes its top-K, ranks are summed.

### ADR-004 — Triple extraction is a separate LLM call, not a free-text parse

**Context.** The LLM-extracted triples `(entity, type, relation, entity)`
are how the graph is built. Two options:
1. Free-form completion, regex-parse.
2. JSON-schema-constrained response, validate, retry on parse failure.

**Decision.** JSON-schema-constrained. `MockLLM.extract_json` returns
canned JSON; `AnthropicLLM.extract_json` uses Anthropic's tool-use
guaranteed-JSON mode (via the `tool_choice` parameter), with regex
fallback for resilience.
