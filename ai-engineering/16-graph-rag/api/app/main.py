"""FastAPI service for 16-graph-rag.

Endpoints:
    GET  /health
    GET  /strategies
    GET  /graph                       → full knowledge graph (nodes + edges)
    GET  /graph/stats                 → node/edge counts + type distribution
    POST /query                       → ask a question; log to query_log
    GET  /eval/summary                → strategy × kind table
    GET  /eval/rows?kind=&strategy=   → drill-down rows
    POST /ingest/eval                 → re-run eval and write to ClickHouse
    POST /ingest/graph                → snapshot current graph to ClickHouse
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

# Make /app/src importable inside the container
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import clickhouse_connect  # type: ignore
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

from src.config import PROJECT_ROOT, get_settings  # noqa: E402
from src.generation import Answer, Citation  # noqa: E402
from src.pipeline import STRATEGIES, GraphRAGPipeline  # noqa: E402

from api.app.auth import (  # noqa: E402
    COOKIE_NAME,
    User,
    clear_session_cookie,
    ensure_default_admin,
    find_user,
    get_current_user,
    issue_token,
    register_user,
    set_session_cookie,
    update_last_login,
    _verify_password,
)


# ─────────────────────────────────────────────────────────────────────────────
# ClickHouse client (lifespan-managed)
# ─────────────────────────────────────────────────────────────────────────────

class CHClient:
    def __init__(self) -> None:
        host = os.environ.get("CLICKHOUSE_HOST", "localhost")
        port = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
        database = os.environ.get("CLICKHOUSE_DB", "graph_rag")
        user = os.environ.get("CLICKHOUSE_USER", "default")
        password = os.environ.get("CLICKHOUSE_PASSWORD", "")
        self._client = clickhouse_connect.get_client(
            host=host, port=port, database=database,
            username=user, password=password,
        )

    def query_df(self, sql: str) -> list[dict[str, Any]]:
        result = self._client.query(sql)
        cols = result.column_names
        return [dict(zip(cols, row)) for row in result.result_rows]

    def insert_dicts(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self._client.insert(table=table, data=rows)


ch: CHClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ch
    logger.info("API startup — connecting to ClickHouse …")
    ch = CHClient()
    try:
        ensure_default_admin()
    except Exception as e:
        logger.warning(f"ensure_default_admin failed (non-fatal): {e}")
    logger.info("API ready.")
    yield
    logger.info("API shutdown.")


app = FastAPI(
    title="Graph RAG API",
    version="0.1.0",
    description="Backend for the 16-graph-rag dashboard.",
    lifespan=lifespan,
)

# CORS — wide open in dev. In prod, restrict to the web origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    strategy: Literal["vector", "bm25", "graph", "hybrid"] = "hybrid"


class QueryResponse(BaseModel):
    request_id: str
    question: str
    strategy: str
    answer: str
    citations: list[Citation]
    graph_seeds: list[str]
    graph_edges: list[tuple[str, str, str]]
    latency_ms: int
    refused: bool


class GraphNode(BaseModel):
    id: str
    type: str
    degree: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    rel: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class EvalSummaryRow(BaseModel):
    kind: str
    strategy: str
    n: int
    citation_precision: float
    keyword_hit: float
    refused: float


class EvalSummaryResponse(BaseModel):
    rows: list[EvalSummaryRow]


class EvalDetailRow(BaseModel):
    question: str
    kind: str
    strategy: str
    expected_doc_ids: list[str]
    cited_doc_ids: list[str]
    cited_chunk_ids: list[str]
    answer_excerpt: str
    citation_precision: float
    keyword_hit_rate: float
    refused: bool


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline (lazy)
# ─────────────────────────────────────────────────────────────────────────────

_pipeline: GraphRAGPipeline | None = None


def get_pipeline() -> GraphRAGPipeline:
    global _pipeline
    if _pipeline is None:
        logger.info("Loading pipeline …")
        _pipeline = GraphRAGPipeline()
        try:
            _pipeline.load()
        except FileNotFoundError:
            logger.warning("No persisted indices — building from sample_data/corpus …")
            _pipeline = GraphRAGPipeline()
            _pipeline.build(PROJECT_ROOT / "sample_data" / "corpus")
            _pipeline.load()
    return _pipeline


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/strategies")
def strategies() -> dict[str, list[str]]:
    return {"strategies": list(STRATEGIES)}


@app.get("/graph", response_model=GraphResponse)
def graph() -> GraphResponse:
    p = get_pipeline()
    g = p.graph
    nodes = [
        GraphNode(id=n, type=g._g.nodes[n].get("type", "Thing"), degree=g._g.degree(n))
        for n in g._g.nodes
    ]
    edges = [
        GraphEdge(source=u, target=v, rel=d.get("rel", k))
        for u, v, k, d in g._g.edges(keys=True, data=True)
    ]
    return GraphResponse(nodes=nodes, edges=edges)


@app.get("/graph/stats")
def graph_stats() -> dict[str, Any]:
    p = get_pipeline()
    g = p.graph._g  # noqa: SLF001
    type_dist: dict[str, int] = {}
    for _, data in g.nodes(data=True):
        t = data.get("type", "Thing")
        type_dist[t] = type_dist.get(t, 0) + 1
    rel_dist: dict[str, int] = {}
    for _, _, _, data in g.edges(keys=True, data=True):
        r = data.get("rel", "?")
        rel_dist[r] = rel_dist.get(r, 0) + 1
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "node_types": type_dist,
        "rel_types": rel_dist,
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    p = get_pipeline()
    t0 = time.perf_counter()
    result = p.retrieve(req.question, strategy=req.strategy)
    answer = p.generator.generate(result)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    request_id = str(uuid.uuid4())
    refused = "i don't" in answer.text.lower() or "i do not" in answer.text.lower()

    # Log to ClickHouse (best-effort; never fail the request because of logging)
    if ch is not None:
        try:
            ch.insert_dicts(
                "query_log",
                [
                    {
                        "request_id": request_id,
                        "question": req.question,
                        "strategy": req.strategy,
                        "cited_doc_ids": result.doc_ids(),
                        "cited_chunk_ids": result.chunk_ids(),
                        "graph_seeds": result.graph_seeds,
                        "latency_ms": latency_ms,
                        "refused": 1 if refused else 0,
                        "llm_mode": p.llm.name,
                    }
                ],
            )
        except Exception as e:
            logger.warning(f"query_log insert failed: {e}")

    return QueryResponse(
        request_id=request_id,
        question=req.question,
        strategy=req.strategy,
        answer=answer.text,
        citations=answer.citations,
        graph_seeds=result.graph_seeds,
        graph_edges=[(s, r, t) for s, r, t in result.graph_edges],
        latency_ms=latency_ms,
        refused=refused,
    )


@app.get("/eval/summary", response_model=EvalSummaryResponse)
def eval_summary() -> EvalSummaryResponse:
    if ch is None:
        raise HTTPException(503, "ClickHouse not connected")
    rows = ch.query_df(
        """
        SELECT
            kind,
            strategy,
            count() AS n,
            avg(citation_precision) AS citation_precision,
            avg(keyword_hit_rate)   AS keyword_hit,
            avg(refused)            AS refused
        FROM graph_rag.eval_results
        GROUP BY kind, strategy
        ORDER BY kind, strategy
        """
    )
    out: list[EvalSummaryRow] = []
    for r in rows:
        out.append(
            EvalSummaryRow(
                kind=r["kind"],
                strategy=r["strategy"],
                n=int(r["n"]),
                citation_precision=float(r["citation_precision"]),
                keyword_hit=float(r["keyword_hit"]),
                refused=float(r["refused"]),
            )
        )
    return EvalSummaryResponse(rows=out)


@app.get("/eval/rows", response_model=list[EvalDetailRow])
def eval_rows(
    kind: str | None = Query(None),
    strategy: str | None = Query(None),
    limit: int = Query(100, le=1000),
) -> list[EvalDetailRow]:
    if ch is None:
        raise HTTPException(503, "ClickHouse not connected")
    where = []
    params: dict[str, Any] = {}
    if kind:
        where.append("kind = {kind:String}")
        params["kind"] = kind
    if strategy:
        where.append("strategy = {strategy:String}")
        params["strategy"] = strategy
    where_clause = "WHERE " + " AND ".join(where) if where else ""
    sql = f"""
        SELECT
            question, kind, strategy,
            expected_doc_ids, cited_doc_ids, cited_chunk_ids,
            answer_excerpt, citation_precision, keyword_hit_rate, refused
        FROM graph_rag.eval_results
        {where_clause}
        ORDER BY created_at DESC
        LIMIT {limit}
    """
    raw = ch._client.query(sql, parameters=params)  # noqa: SLF001
    cols = raw.column_names
    out: list[EvalDetailRow] = []
    for row in raw.result_rows:
        d = dict(zip(cols, row))
        out.append(
            EvalDetailRow(
                question=d["question"],
                kind=d["kind"],
                strategy=d["strategy"],
                expected_doc_ids=list(d["expected_doc_ids"]),
                cited_doc_ids=list(d["cited_doc_ids"]),
                cited_chunk_ids=list(d["cited_chunk_ids"]),
                answer_excerpt=d["answer_excerpt"],
                citation_precision=float(d["citation_precision"]),
                keyword_hit_rate=float(d["keyword_hit_rate"]),
                refused=bool(d["refused"]),
            )
        )
    return out


@app.post("/ingest/eval")
def ingest_eval() -> dict[str, Any]:
    """Re-run the eval and write results to ClickHouse."""
    if ch is None:
        raise HTTPException(503, "ClickHouse not connected")
    p = get_pipeline()
    s = get_settings()
    files = [
        ("single-hop", s.sample_data_dir / "eval_golden.jsonl"),
        ("two-hop", s.sample_data_dir / "eval_twohop.jsonl"),
        ("adversarial", s.sample_data_dir / "eval_adversarial.jsonl"),
    ]
    total = 0
    for kind, path in files:
        if not path.exists():
            continue
        report = p.eval(path)
        rows = []
        for r in report.rows:
            rows.append(
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
        ch.insert_dicts("eval_results", rows)
        total += len(rows)
    return {"rows_inserted": total}


@app.post("/ingest/graph")
def ingest_graph() -> dict[str, Any]:
    """Snapshot the current in-memory graph into ClickHouse."""
    if ch is None:
        raise HTTPException(503, "ClickHouse not connected")
    p = get_pipeline()
    g = p.graph
    rows = []
    for u, v, k, d in g._g.edges(keys=True, data=True):  # noqa: SLF001
        rows.append(
            {
                "head": u,
                "head_type": g._g.nodes[u].get("type", "Thing"),  # noqa: SLF001
                "rel": d.get("rel", k),
                "tail": v,
                "tail_type": g._g.nodes[v].get("type", "Thing"),  # noqa: SLF001
                "created_at": datetime.utcnow(),
            }
        )
    # ReplacingMergeTree dedupes on (head, rel, tail) so re-running is safe
    ch.insert_dicts("graph_snapshot", rows)
    return {"rows_inserted": len(rows)}
