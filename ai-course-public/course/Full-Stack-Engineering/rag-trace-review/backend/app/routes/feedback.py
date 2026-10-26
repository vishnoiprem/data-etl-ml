"""Feedback submission endpoint with idempotency."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from ..database import db_cursor
from ..models import FeedbackIn, FeedbackOut

log = logging.getLogger("feedback")
router = APIRouter(prefix="/traces", tags=["feedback"])


@router.put("/{trace_id}/feedback", response_model=FeedbackOut)
def submit_feedback(trace_id: str, body: FeedbackIn):
    now = datetime.now(timezone.utc).isoformat()
    with db_cursor(commit=True) as cur:
        # Single round-trip: only insert if the trace exists. If 0 rows changed,
        # the trace_id is unknown and we surface a 404.
        cur.execute(
            """
            INSERT INTO feedback(trace_id, rating, note, created_at)
            SELECT ?, ?, ?, ?
            WHERE EXISTS (SELECT 1 FROM traces WHERE trace_id = ?)
            ON CONFLICT(trace_id) DO UPDATE SET
                rating=excluded.rating,
                note=excluded.note,
                created_at=excluded.created_at
            """,
            (trace_id, body.rating, body.note, now, trace_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Trace not found: {trace_id}")
        cur.execute(
            "UPDATE traces SET feedback = ? WHERE trace_id = ?",
            (body.rating, trace_id),
        )
    log.info("feedback_submitted", extra={"trace_id": trace_id, "rating": body.rating})
    return FeedbackOut(trace_id=trace_id, rating=body.rating, note=body.note, created_at=now)
