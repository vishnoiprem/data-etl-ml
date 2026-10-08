-- ─────────────────────────────────────────────────────────────────────────────
-- 16-graph-rag — ClickHouse schema
-- Runs on first boot of the clickhouse container (mounted at /docker-entrypoint-initdb.d/)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS graph_rag;

-- ─────────────────────────────────────────────────────────────────────────────
-- eval_results — one row per (question, strategy)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS graph_rag.eval_results
(
    -- identifiers
    question        String,
    kind            LowCardinality(String),  -- 'single-hop' | 'two-hop' | 'adversarial'
    strategy        LowCardinality(String),  -- 'vector' | 'bm25' | 'graph' | 'hybrid'

    -- expected
    expected_doc_ids    Array(String),
    expected_keywords   Array(String),

    -- observed
    cited_doc_ids       Array(String),
    cited_chunk_ids     Array(String),
    answer_excerpt      String,

    -- metrics (all in [0, 1])
    citation_precision  Float32,
    keyword_hit_rate    Float32,
    refused             UInt8,   -- 0 or 1, avoids boolean quirks in CH

    -- provenance
    llm_mode            LowCardinality(String),  -- 'mock' | 'real'
    created_at          DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (kind, strategy, created_at)
PARTITION BY toYYYYMM(created_at);


-- ─────────────────────────────────────────────────────────────────────────────
-- query_log — every question asked via the API
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS graph_rag.query_log
(
    request_id      UUID DEFAULT generateUUIDv4(),
    question        String,
    strategy        LowCardinality(String),
    cited_doc_ids   Array(String),
    cited_chunk_ids Array(String),
    graph_seeds     Array(String),
    latency_ms      UInt32,
    refused         UInt8,
    llm_mode        LowCardinality(String),
    created_at      DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY created_at
PARTITION BY toYYYYMM(created_at);


-- ─────────────────────────────────────────────────────────────────────────────
-- graph_snapshot — materialised view of the knowledge graph for the UI
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS graph_rag.graph_snapshot
(
    head        String,
    head_type   LowCardinality(String),
    rel         LowCardinality(String),
    tail        String,
    tail_type   LowCardinality(String),
    created_at  DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(created_at)
ORDER BY (head, rel, tail);
