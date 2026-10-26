"""Eval report store: Postgres when configured, JSONL fallback for dev.

The previous `apex_eval.latest_eval()` returned the production targets
as hardcoded numbers — the endpoint was theater. This module reads the
last REAL harness run from either:
  1. `eval_reports` table in Postgres (if `APEX_POSTGRES_URL` is set)
  2. `eval/reports/eval_*.json` files on disk (default fallback)

The harness itself (`eval/harness.py`) is unchanged — it still writes
JSON to `eval/reports/eval_<ts>.json`. This module is the consumer.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from .apex_eval import EvalReport
from .settings import Settings

logger = logging.getLogger("apex.eval_store")


# Production targets — KEPT as a comparison baseline, not returned as data.
# The /eval endpoint reports these alongside a real report so the operator
# can see "we're at 0.86, target is 0.89" instead of being lied to.
PRODUCTION_TARGETS = {
    "recall_at_8": 0.89,
    "ndcg_at_8": 0.91,
    "p95_latency_ms": 420.0,
    "judge_groundedness": 4.0,
    "judge_hallucination": 2.0,
}


def _reports_dir() -> Path:
    """Path to the JSONL report directory used by the harness."""
    return Path(__file__).parent.parent.parent / "eval" / "reports"


def _latest_from_jsonl() -> EvalReport | None:
    """Read the most recent eval_*.json file. Return None if no reports exist."""
    reports_dir = _reports_dir()
    if not reports_dir.exists():
        return None
    files = sorted(reports_dir.glob("eval_*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    try:
        data = json.loads(files[-1].read_text())
    except Exception as exc:
        logger.warning("failed to read eval report %s: %s", files[-1], exc)
        return None
    return _dict_to_report(data)


def _latest_from_postgres(settings: Settings) -> EvalReport | None:
    """Read the most recent row from eval_reports. None if not configured.

    Lazy import: `psycopg` is not pinned in requirements.txt for this
    pass (A1 in the plan). When `APEX_POSTGRES_URL` is empty we never
    even import it.
    """
    if not settings.postgres_url:
        return None
    try:
        import psycopg  # type: ignore
    except ImportError:
        logger.warning("APEX_POSTGRES_URL set but psycopg not installed; falling back to JSONL")
        return None
    try:
        with psycopg.connect(settings.postgres_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS eval_reports (
                        ts TEXT PRIMARY KEY,
                        n_samples INT,
                        recall_at_8 DOUBLE PRECISION,
                        ndcg_at_8 DOUBLE PRECISION,
                        p50_latency_ms DOUBLE PRECISION,
                        p95_latency_ms DOUBLE PRECISION,
                        judge_groundedness DOUBLE PRECISION,
                        judge_hallucination DOUBLE PRECISION,
                        by_collection JSONB,
                        report JSONB
                    )
                """)
                cur.execute("""
                    SELECT ts, n_samples, recall_at_8, ndcg_at_8,
                           p50_latency_ms, p95_latency_ms,
                           judge_groundedness, judge_hallucination,
                           by_collection
                    FROM eval_reports
                    ORDER BY ts DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
        if not row:
            return None
        return EvalReport(
            timestamp=row[0],
            n_samples=row[1],
            recall_at_8=row[2],
            ndcg_at_8=row[3],
            p50_latency_ms=row[4],
            p95_latency_ms=row[5],
            judge_groundedness=row[6],
            judge_hallucination=row[7],
            by_collection=row[8] or {},
        )
    except Exception as exc:
        logger.warning("postgres eval read failed: %s", exc)
        return None


def _dict_to_report(d: dict[str, Any]) -> EvalReport:
    """Map a JSON report to our EvalReport dataclass.

    Two source shapes are supported:
    1. The flat shape written by `record_report` here:
       `{"timestamp":..., "recall_at_8":..., "ndcg_at_8":..., ...}`
    2. The nested shape written by the harness CLI (`eval.harness`):
       `{"timestamp":..., "metrics": {"recall_at_8":..., "ndcg_at_10":...}, ...}`

    We detect by checking for a top-level `metrics` key.
    """
    metrics = d.get("metrics", {}) if isinstance(d.get("metrics"), dict) else {}
    def _g(key: str, fallback: float = 0.0) -> float:
        # Prefer flat key, fall back to nested metrics, fall back to default.
        if key in d:
            return float(d[key])
        if key in metrics:
            return float(metrics[key])
        return fallback
    return EvalReport(
        timestamp=d.get("timestamp", ""),
        n_samples=int(d.get("n_samples", 0)),
        recall_at_8=_g("recall_at_8"),
        ndcg_at_8=_g("ndcg_at_8", _g("ndcg_at_10")),  # harness uses ndcg_at_10
        p50_latency_ms=_g("p50_latency_ms"),
        p95_latency_ms=_g("p95_latency_ms"),
        judge_groundedness=_g("judge_groundedness"),
        judge_hallucination=_g("judge_hallucination"),
        by_collection=d.get("by_collection", {}),
    )


def latest_report(settings: Settings) -> EvalReport | None:
    """Return the most recent eval report, or None if no reports exist.

    Tries Postgres first (if configured), then JSONL. Returns the first
    non-None result. Both can fail independently; we never raise.
    """
    pg = _latest_from_postgres(settings)
    if pg is not None:
        return pg
    return _latest_from_jsonl()


def record_report(settings: Settings, report: EvalReport) -> None:
    """Persist a report. Postgres if configured, else JSONL.

    The harness calls this after a run. We always write the JSONL form
    so a Postgres-configured prod still has the JSONL as a backup.
    """
    out_dir = _reports_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = report.timestamp.replace(":", "-").replace(".", "-")
    jsonl_path = out_dir / f"eval_{ts}.json"
    try:
        jsonl_path.write_text(json.dumps(report.to_dict(), indent=2))
    except Exception as exc:
        logger.warning("failed to write JSONL eval report: %s", exc)
    if not settings.postgres_url:
        return
    try:
        import psycopg  # type: ignore
        with psycopg.connect(settings.postgres_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS eval_reports (
                        ts TEXT PRIMARY KEY,
                        n_samples INT,
                        recall_at_8 DOUBLE PRECISION,
                        ndcg_at_8 DOUBLE PRECISION,
                        p50_latency_ms DOUBLE PRECISION,
                        p95_latency_ms DOUBLE PRECISION,
                        judge_groundedness DOUBLE PRECISION,
                        judge_hallucination DOUBLE PRECISION,
                        by_collection JSONB,
                        report JSONB
                    )
                """)
                cur.execute("""
                    INSERT INTO eval_reports
                        (ts, n_samples, recall_at_8, ndcg_at_8,
                         p50_latency_ms, p95_latency_ms,
                         judge_groundedness, judge_hallucination,
                         by_collection, report)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (ts) DO NOTHING
                """, (
                    report.timestamp, report.n_samples,
                    report.recall_at_8, report.ndcg_at_8,
                    report.p50_latency_ms, report.p95_latency_ms,
                    report.judge_groundedness, report.judge_hallucination,
                    json.dumps(report.by_collection),
                    json.dumps(report.to_dict()),
                ))
            conn.commit()
    except ImportError:
        logger.warning("APEX_POSTGRES_URL set but psycopg not installed; JSONL only")
    except Exception as exc:
        logger.warning("postgres eval write failed: %s", exc)
