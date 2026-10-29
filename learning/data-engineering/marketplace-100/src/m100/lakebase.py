"""
lakebase.py — Postgres-compatible Lakebase connection for state + ops log.

Lakebase is Databricks' Postgres-compatible lakehouse database,
GA Feb 2026. It exposes a standard Postgres wire protocol
on a per-workspace endpoint, so we connect with `psycopg` (v3)
just like any other Postgres.

What we store here:
  * `agent_log`  — one row per agent call. Lets us replay
                   or audit exactly what the LLM said.
  * `iterations` — a fast pointer to the current `iter_no`
                   for crash-recovery (Delta is the source
                   of truth, but a Postgres row gives us
                   sub-second reads on driver boot).
  * `skip_log`   — listings we deliberately skipped
                   (personalization required, schema-less
                   CSV with no rows, etc.) so we don't
                   keep trying them every iteration.

Fallback:
  If Lakebase is not provisioned (or not available in the
  region), we write to a Delta table in
  `<catalog>.agents.lakebase_fallback` with the same
  schema. Functionally equivalent for the driver, just
  slower for the dashboard.

Schema is created idempotently on first connect.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Schema (DDL applied on connect)
# ============================================================

DDL = """
CREATE TABLE IF NOT EXISTS agent_log (
    log_id         BIGSERIAL PRIMARY KEY,
    iter_no        INTEGER NOT NULL,
    listing_id     TEXT,
    prompt_tokens  INTEGER,
    completion_tokens INTEGER,
    latency_ms     INTEGER,
    quality_score  REAL,
    summary        TEXT,
    raw_response   JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS iterations (
    iter_no        INTEGER PRIMARY KEY,
    listing_id     TEXT,
    status         TEXT NOT NULL,    -- running | ok | skipped | failed
    quality_score  REAL,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS skip_log (
    listing_id     TEXT PRIMARY KEY,
    reason         TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS agent_log_iter_idx ON agent_log(iter_no);
CREATE INDEX IF NOT EXISTS agent_log_created_idx ON agent_log(created_at DESC);
CREATE INDEX IF NOT EXISTS iterations_status_idx ON iterations(status);

-- Bandit state (UCB1 over marketplace categories). One row per arm.
-- Persisted by bandit.py — read on driver boot, written after every
-- iteration.
CREATE TABLE IF NOT EXISTS bandit_state (
    name            TEXT PRIMARY KEY,
    pulls           BIGINT NOT NULL DEFAULT 0,
    sum_reward      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    last_pulled_at  TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# ============================================================
# Connection params
# ============================================================

def _conn_params() -> Optional[dict]:
    """Build Lakebase connection params from env.

    Required env (set by the DAB deploy when running in workspace):
      LAKEBASE_HOST     e.g. "instance-xxxxxx.database.cloud.databricks.com"
      LAKEBASE_PORT     default 5432
      LAKEBASE_DB       default "databricks_postgres"
      LAKEBASE_USER     workspace user or service principal
      LAKEBASE_PASSWORD PAT (Lakebase uses the same PAT as the workspace)

    Returns None if LAKEBASE_HOST is unset, which signals the
    fallback path.
    """
    host = os.getenv("LAKEBASE_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("LAKEBASE_PORT", "5432")),
        "dbname": os.getenv("LAKEBASE_DB", "databricks_postgres"),
        "user": os.getenv("LAKEBASE_USER", os.getenv("DATABRICKS_USER", "")),
        "password": os.getenv("LAKEBASE_PASSWORD", os.getenv("DATABRICKS_TOKEN", "")),
    }


# ============================================================
# Connection
# ============================================================

@contextmanager
def connect() -> Iterator[Optional["psycopg.Connection"]]:
    """Open a Lakebase connection. Yields None if Lakebase is unavailable.

    The driver treats None as "use the Delta fallback" and
    continues. The smoke test always uses the fallback.

    If `psycopg` is not installed, this also yields None —
    we don't want a missing optional dep to crash the driver.
    """
    try:
        import psycopg
    except ImportError:
        logger.info("psycopg not installed; using Delta fallback")
        yield None
        return
    params = _conn_params()
    if not params:
        logger.info("LAKEBASE_HOST unset; using Delta fallback")
        yield None
        return
    try:
        with psycopg.connect(**params, autocommit=False) as conn:
            with conn.cursor() as cur:
                # Idempotent DDL — safe to run on every connect.
                for stmt in DDL.strip().split(";\n"):
                    s = stmt.strip()
                    if s:
                        cur.execute(s)
            conn.commit()
            yield conn
    except Exception as e:
        logger.warning("Lakebase connect failed (%s); using Delta fallback", e)
        yield None


# ============================================================
# Helpers — typed on top of the connection
# ============================================================

def record_iteration_start(
    conn,
    iter_no: int,
    listing_id: str,
) -> None:
    """Mark an iteration as running."""
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO iterations (iter_no, listing_id, status)
            VALUES (%s, %s, 'running')
            ON CONFLICT (iter_no) DO UPDATE SET
                listing_id = EXCLUDED.listing_id,
                status = 'running',
                started_at = NOW()
        """, (iter_no, listing_id))


def record_iteration_end(
    conn,
    iter_no: int,
    *,
    status: str,
    quality_score: Optional[float] = None,
) -> None:
    """Mark an iteration complete (ok | skipped | failed)."""
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE iterations
            SET status = %s, quality_score = %s, finished_at = NOW()
            WHERE iter_no = %s
        """, (status, quality_score, iter_no))
    conn.commit()


def record_agent_call(
    conn,
    *,
    iter_no: int,
    listing_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    quality_score: Optional[float],
    summary: str,
    raw_response: dict,
) -> None:
    """Append a row to the agent log."""
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO agent_log
                (iter_no, listing_id, prompt_tokens, completion_tokens,
                 latency_ms, quality_score, summary, raw_response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """, (
            iter_no, listing_id, prompt_tokens, completion_tokens,
            latency_ms, quality_score, summary,
            json.dumps(raw_response),
        ))
    conn.commit()


def record_skip(
    conn,
    listing_id: str,
    reason: str,
) -> None:
    """Record a listing we deliberately skipped (so we don't retry)."""
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO skip_log (listing_id, reason)
            VALUES (%s, %s)
            ON CONFLICT (listing_id) DO UPDATE SET reason = EXCLUDED.reason
        """, (listing_id, reason))
    conn.commit()


def get_max_iteration(conn) -> int:
    """Read the highest iter_no we've recorded. Returns -1 if empty.

    The driver uses this for crash-recovery: on boot, resume
    from `max_iteration + 1` instead of 0.
    """
    if conn is None:
        return -1
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(iter_no), -1) AS n FROM iterations")
        return int(cur.fetchone()[0])


def is_skipped(conn, listing_id: str) -> bool:
    """True if we've already recorded a skip for this listing."""
    if conn is None:
        return False
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM skip_log WHERE listing_id = %s", (listing_id,))
        return cur.fetchone() is not None


# ============================================================
# Delta fallback — used when Lakebase is unavailable
# ============================================================

def fallback_ensure(spark, catalog: str = "marketplace_100") -> None:
    """Create the Delta fallback table if missing.

    Same schema as the Postgres tables, but flattened into
    one Delta table with a `kind` column to disambiguate.
    """
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.agents")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {catalog}.agents.lakebase_fallback (
            kind        STRING,  -- 'iter_start' | 'iter_end' | 'agent_call' | 'skip'
            iter_no     INT,
            listing_id  STRING,
            status      STRING,
            quality_score DOUBLE,
            prompt_tokens INT,
            completion_tokens INT,
            latency_ms  INT,
            summary     STRING,
            raw_json    STRING,
            created_at  TIMESTAMP
        )
    """)


def fallback_write(spark, rows: list[dict], catalog: str = "marketplace_100") -> None:
    """Append rows to the Delta fallback table.

    Rows is a list of dicts; missing keys become NULL.
    """
    if not rows:
        return
    fallback_ensure(spark, catalog)
    # Normalize: every row has the same keys
    keys = sorted({k for r in rows for k in r.keys()})
    normalized = [{k: r.get(k) for k in keys} for r in rows]
    df = spark.createDataFrame(normalized)
    df.write.mode("append").saveAsTable(f"{catalog}.agents.lakebase_fallback")
