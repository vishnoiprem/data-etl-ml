"""Cursor-paginated trace listing + detail endpoints."""
import base64
import json
import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from ..database import db_cursor
from ..models import (
    TraceSummary,
    TraceDetail,
    RetrievedChunk,
    Citation,
    TracePage,
    PageMeta,
)

log = logging.getLogger("traces")
router = APIRouter(prefix="/traces", tags=["traces"])

PAGE_SIZE = int(os.environ.get("RAG_PAGE_SIZE", 50))
MAX_PAGE_SIZE = 200


def _encode_cursor(created_at: str, trace_id: str) -> str:
    raw = f"{created_at}|{trace_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, str]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at, trace_id = decoded.split("|", 1)
        return created_at, trace_id
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


@router.get("", response_model=TracePage)
def list_traces(
    day: Optional[str] = Query(None, description="YYYY-MM-DD"),
    prompt_version: Optional[str] = Query(None),
    min_latency: Optional[int] = Query(None, ge=0),
    max_latency: Optional[int] = Query(None, ge=0),
    cursor: Optional[str] = Query(None),
    limit: int = Query(PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    where: list[str] = []
    params: list = []

    if day:
        where.append("substr(created_at, 1, 10) = ?")
        params.append(day)
    if prompt_version:
        where.append("prompt_version = ?")
        params.append(prompt_version)
    if min_latency is not None:
        where.append("latency_ms >= ?")
        params.append(min_latency)
    if max_latency is not None:
        where.append("latency_ms <= ?")
        params.append(max_latency)
    if cursor:
        c_at, c_id = _decode_cursor(cursor)
        where.append("(created_at < ? OR (created_at = ? AND trace_id < ?))")
        params.extend([c_at, c_at, c_id])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT trace_id, created_at, prompt_version, user_query,
               token_usage, latency_ms, status, feedback
        FROM traces
        {where_sql}
        ORDER BY created_at DESC, trace_id DESC
        LIMIT ?
    """
    params.append(limit + 1)

    with db_cursor() as cur:
        rows = cur.execute(sql, params).fetchall()

    log.info("list_traces", extra={"day": day, "prompt_version": prompt_version, "rows": len(rows), "has_more": len(rows) > limit})
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [TraceSummary(**dict(r)) for r in rows]
    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = _encode_cursor(last["created_at"], last["trace_id"])
    return TracePage(items=items, meta=PageMeta(next_cursor=next_cursor, has_more=has_more))


@router.get("/{trace_id}", response_model=TraceDetail)
def get_trace(trace_id: str):
    with db_cursor() as cur:
        row = cur.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")
    d = dict(row)
    d["retrieved_chunks"] = [RetrievedChunk(**c) for c in json.loads(d["retrieved_chunks"])]
    d["citations"] = [Citation(**c) for c in json.loads(d["citations"])]
    return TraceDetail(**d)
