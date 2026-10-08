"""Seed ClickHouse with eval results + graph snapshot.

Run after `make ingest` (or after the API has built its own pipeline):

    LLM_MODE=mock python3 scripts/seed_clickhouse.py
    # or via Docker:
    docker compose exec api python scripts/seed_clickhouse.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import clickhouse_connect  # type: ignore
from loguru import logger

from src.config import get_settings
from src.pipeline import GraphRAGPipeline


def main() -> None:
    host = os.environ.get("CLICKHOUSE_HOST", "localhost")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
    database = os.environ.get("CLICKHOUSE_DB", "graph_rag")

    logger.info(f"Connecting to ClickHouse at {host}:{port}/{database} …")
    client = clickhouse_connect.get_client(host=host, port=port, database=database)

    # Verify the schema is in place (init.sql should have created these)
    tables = client.query("SHOW TABLES FROM graph_rag").result_rows
    logger.info(f"Tables in graph_rag: {[t[0] for t in tables]}")

    # Build/load the pipeline
    s = get_settings()
    p = GraphRAGPipeline()
    if s.graph_path().exists():
        p.load()
    else:
        p.build(s.sample_data_dir / "corpus")

    # 1) Eval results
    logger.info("Running eval …")
    files = [
        ("single-hop", s.sample_data_dir / "eval_golden.jsonl"),
        ("two-hop", s.sample_data_dir / "eval_twohop.jsonl"),
        ("adversarial", s.sample_data_dir / "eval_adversarial.jsonl"),
    ]
    eval_rows: list[dict] = []
    for kind, path in files:
        if not path.exists():
            logger.warning(f"  missing {path}")
            continue
        report = p.eval(path)
        for r in report.rows:
            eval_rows.append(
                {
                    "question": r.question,
                    "kind": r.kind,
                    "strategy": r.strategy,
                    "expected_doc_ids": r.expected_doc_ids,
                    "expected_keywords": r.expected_keywords,
                    "cited_doc_ids": r.cited_doc_ids,
                    "cited_chunk_ids": r.cited_chunk_ids,
                    "answer_excerpt": r.answer_excerpt,
                    "citation_precision": r.citation_precision,
                    "keyword_hit_rate": r.keyword_hit_rate,
                    "refused": 1 if r.refused else 0,
                    "llm_mode": p.llm.name,
                    "created_at": datetime.utcnow(),
                }
            )
    if eval_rows:
        client.insert("eval_results", eval_rows)
        logger.info(f"Inserted {len(eval_rows)} eval rows.")

    # 2) Graph snapshot
    g = p.graph
    graph_rows: list[dict] = []
    for u, v, k, d in g._g.edges(keys=True, data=True):  # noqa: SLF001
        graph_rows.append(
            {
                "head": u,
                "head_type": g._g.nodes[u].get("type", "Thing"),  # noqa: SLF001
                "rel": d.get("rel", k),
                "tail": v,
                "tail_type": g._g.nodes[v].get("type", "Thing"),  # noqa: SLF001
                "created_at": datetime.utcnow(),
            }
        )
    if graph_rows:
        client.insert("graph_snapshot", graph_rows)
        logger.info(f"Inserted {len(graph_rows)} graph edges.")

    logger.success("Seed complete.")


if __name__ == "__main__":
    main()
