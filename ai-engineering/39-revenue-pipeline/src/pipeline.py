"""
pipeline.py — SQLite-backed lead → opportunity → won/lost state machine.

States:
   new        — ingested but not yet qualified
   qualified  — scored ≥ 40, draft email written
   sent       — email sent (manually or via SMTP)
   replied    — got a reply (manually marked)
   won        — closed-won ($ recorded)
   lost       — closed-lost (reason recorded)

Why SQLite?  The consultant's data volume is small (100s of leads/year),
and a single file is easier to back up, query, and reason about than a
Postgres instance. The schema is portable: an `init_postgres.sql` could
mimic it 1:1.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from outreach import Email
from qualifier import Qualification
from signals import Lead


VALID_STATUSES = ("new", "qualified", "sent", "replied", "won", "lost")


class Pipeline:
    """Thread-safe SQLite pipeline store."""

    def __init__(self, db_path: str | Path = "pipeline.db") -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        self._init_schema()

    @contextmanager
    def _conn(self):
        c = sqlite3.connect(self._db_path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def _init_schema(self) -> None:
        with self._lock, self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint     TEXT    UNIQUE NOT NULL,
                    source          TEXT    NOT NULL,
                    company         TEXT    NOT NULL,
                    title           TEXT,
                    url             TEXT,
                    contact         TEXT,
                    text            TEXT,
                    tags            TEXT,
                    status          TEXT    NOT NULL DEFAULT 'new',
                    score           INTEGER DEFAULT 0,
                    deal_usd        INTEGER DEFAULT 0,
                    weighted_usd    INTEGER DEFAULT 0,
                    reasons         TEXT,
                    email_subject   TEXT,
                    email_body      TEXT,
                    won_usd         INTEGER,
                    lost_reason     TEXT,
                    first_seen_at   TEXT    NOT NULL,
                    last_touched_at TEXT    NOT NULL,
                    sent_at         TEXT,
                    replied_at      TEXT,
                    closed_at       TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_opp_status ON opportunities(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(score DESC)")

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------
    def upsert_lead(self, lead: Lead) -> int:
        """Insert a new opportunity or update the text/tags if seen before.

        Returns the opportunity id. Dedup is on `fingerprint` (source +
        company + normalized title).
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            cur = c.execute("SELECT id FROM opportunities WHERE fingerprint = ?",
                            (lead.fingerprint,))
            row = cur.fetchone()
            if row:
                # Already seen — just bump last_touched
                c.execute("""
                    UPDATE opportunities SET last_touched_at = ?
                    WHERE id = ?
                """, (now, row["id"]))
                return row["id"]
            cur = c.execute("""
                INSERT INTO opportunities
                    (fingerprint, source, company, title, url, contact, text,
                     tags, status, first_seen_at, last_touched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """, (lead.fingerprint, lead.source, lead.company, lead.title,
                  lead.url, lead.contact, lead.text,
                  json.dumps(lead.tags), now, now))
            return cur.lastrowid

    def upsert_many(self, leads: Iterable[Lead]) -> list[int]:
        return [self.upsert_lead(ld) for ld in leads]

    # ------------------------------------------------------------------
    # Qualify / outreach
    # ------------------------------------------------------------------
    def record_qualification(self, opp_id: int, q: Qualification, email: Email | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute("""
                UPDATE opportunities SET
                    status = CASE WHEN status='new' THEN 'qualified' ELSE status END,
                    score = ?, deal_usd = ?, weighted_usd = ?, reasons = ?,
                    email_subject = COALESCE(?, email_subject),
                    email_body    = COALESCE(?, email_body),
                    last_touched_at = ?
                WHERE id = ?
            """, (q.score, q.deal_usd, q.weighted_usd,
                  json.dumps(q.reasons),
                  email.subject if email else None,
                  email.body if email else None,
                  now, opp_id))

    def mark_sent(self, opp_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute("""
                UPDATE opportunities SET status='sent', sent_at=?, last_touched_at=?
                WHERE id = ?
            """, (now, now, opp_id))

    def mark_replied(self, opp_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute("""
                UPDATE opportunities SET status='replied', replied_at=?, last_touched_at=?
                WHERE id = ?
            """, (now, now, opp_id))

    def mark_won(self, opp_id: int, won_usd: int) -> None:
        if won_usd <= 0:
            raise ValueError("won_usd must be > 0")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute("""
                UPDATE opportunities SET status='won', won_usd=?, closed_at=?, last_touched_at=?
                WHERE id = ?
            """, (won_usd, now, now, opp_id))

    def mark_lost(self, opp_id: int, reason: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute("""
                UPDATE opportunities SET status='lost', lost_reason=?, closed_at=?, last_touched_at=?
                WHERE id = ?
            """, (reason, now, now, opp_id))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, opp_id: int) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM opportunities WHERE id=?", (opp_id,)).fetchone()
            return dict(row) if row else None

    def list_by_status(self, status: str, limit: int = 100) -> list[dict]:
        with self._conn() as c:
            rows = c.execute("""
                SELECT * FROM opportunities WHERE status=?
                ORDER BY score DESC, weighted_usd DESC
                LIMIT ?
            """, (status, limit)).fetchall()
            return [dict(r) for r in rows]

    def top_opportunities(self, min_score: int = 40, limit: int = 20) -> list[dict]:
        """Highest-priority opportunities that aren't closed yet."""
        with self._conn() as c:
            rows = c.execute("""
                SELECT * FROM opportunities
                WHERE status IN ('qualified', 'sent', 'replied') AND score >= ?
                ORDER BY weighted_usd DESC LIMIT ?
            """, (min_score, limit)).fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        with self._conn() as c:
            row = c.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status='new'       THEN 1 ELSE 0 END) AS new,
                    SUM(CASE WHEN status='qualified' THEN 1 ELSE 0 END) AS qualified,
                    SUM(CASE WHEN status='sent'      THEN 1 ELSE 0 END) AS sent,
                    SUM(CASE WHEN status='replied'   THEN 1 ELSE 0 END) AS replied,
                    SUM(CASE WHEN status='won'       THEN 1 ELSE 0 END) AS won,
                    SUM(CASE WHEN status='lost'      THEN 1 ELSE 0 END) AS lost,
                    COALESCE(SUM(CASE WHEN status='won' THEN won_usd ELSE 0 END), 0) AS won_usd,
                    COALESCE(SUM(CASE WHEN status IN ('qualified','sent','replied')
                                  THEN weighted_usd ELSE 0 END), 0) AS pipeline_usd
                FROM opportunities
            """).fetchone()
            return dict(row)