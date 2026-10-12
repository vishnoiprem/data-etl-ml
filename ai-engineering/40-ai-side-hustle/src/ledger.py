"""
ledger.py — SQLite revenue ledger for all 3 streams.

Why a single ledger?  Because the dashboard needs to compare apples
to apples. Each stream records revenue with (stream, amount_usd,
units, date) and the dashboard groups by stream and date.

State per row:
  stream:      "seo" | "saas" | "product"
  amount_usd:  dollars earned
  units:       articles / paying_customers / sales
  source:      URL or product name (for drill-down)
  date:        ISO date (defaults to today UTC)
  note:        freeform (e.g. "Gumroad sale", "affiliate click")
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VALID_STREAMS = ("seo", "saas", "product")


class Ledger:
    """Thread-safe SQLite revenue ledger."""

    def __init__(self, db_path: str | Path = "ledger.db") -> None:
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
                CREATE TABLE IF NOT EXISTS revenue (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream       TEXT    NOT NULL,
                    amount_usd   REAL    NOT NULL,
                    units        INTEGER NOT NULL DEFAULT 1,
                    source       TEXT,
                    note         TEXT,
                    occurred_at  TEXT    NOT NULL,
                    recorded_at  TEXT    NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_rev_stream ON revenue(stream)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_rev_date ON revenue(occurred_at)")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def record(self, stream: str, amount_usd: float, units: int = 1,
               source: str | None = None, note: str | None = None,
               occurred_at: str | None = None) -> int:
        if stream not in VALID_STREAMS:
            raise ValueError(f"stream must be one of {VALID_STREAMS}, got {stream!r}")
        if amount_usd < 0:
            raise ValueError("amount_usd must be >= 0")
        if units < 0:
            raise ValueError("units must be >= 0")
        now = datetime.now(timezone.utc).isoformat()
        when = occurred_at or now
        with self._lock, self._conn() as c:
            cur = c.execute(
                """INSERT INTO revenue
                       (stream, amount_usd, units, source, note, occurred_at, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (stream, amount_usd, units, source, note, when, now),
            )
            return cur.lastrowid

    def record_many(self, rows: Iterable[dict]) -> list[int]:
        return [self.record(**r) for r in rows]

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def total(self, stream: str | None = None) -> float:
        sql = "SELECT COALESCE(SUM(amount_usd), 0) AS t FROM revenue"
        params: tuple = ()
        if stream:
            sql += " WHERE stream=?"
            params = (stream,)
        with self._conn() as c:
            return float(c.execute(sql, params).fetchone()["t"])

    def units_total(self, stream: str) -> int:
        with self._conn() as c:
            return int(c.execute(
                "SELECT COALESCE(SUM(units), 0) AS u FROM revenue WHERE stream=?",
                (stream,)).fetchone()["u"])

    def by_day(self, stream: str | None = None, days: int = 30) -> list[dict]:
        """Daily revenue series for the last `days` days, all streams if stream=None."""
        with self._conn() as c:
            if stream:
                rows = c.execute(
                    """SELECT substr(occurred_at, 1, 10) AS day,
                              SUM(amount_usd) AS usd,
                              SUM(units) AS units
                       FROM revenue
                       WHERE stream=? AND occurred_at >= datetime('now', ?)
                       GROUP BY day ORDER BY day""",
                    (stream, f"-{days} days")).fetchall()
            else:
                rows = c.execute(
                    """SELECT substr(occurred_at, 1, 10) AS day,
                              SUM(amount_usd) AS usd,
                              SUM(units) AS units
                       FROM revenue
                       WHERE occurred_at >= datetime('now', ?)
                       GROUP BY day ORDER BY day""",
                    (f"-{days} days",)).fetchall()
        return [dict(r) for r in rows]

    def by_stream(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT stream,
                          SUM(amount_usd) AS usd,
                          SUM(units) AS units,
                          COUNT(*) AS events
                   FROM revenue
                   GROUP BY stream
                   ORDER BY usd DESC""").fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        with self._conn() as c:
            row = c.execute(
                """SELECT
                       COALESCE(SUM(amount_usd), 0)                          AS total_usd,
                       COALESCE(SUM(CASE WHEN stream='seo'    THEN amount_usd END), 0) AS seo_usd,
                       COALESCE(SUM(CASE WHEN stream='saas'   THEN amount_usd END), 0) AS saas_usd,
                       COALESCE(SUM(CASE WHEN stream='product' THEN amount_usd END), 0) AS product_usd,
                       COUNT(*) AS events
                   FROM revenue""").fetchone()
        d = dict(row)
        d["best_stream"] = max(
            [("seo", d["seo_usd"]), ("saas", d["saas_usd"]),
             ("product", d["product_usd"])],
            key=lambda x: x[1],
        )[0] if d["events"] else None
        return d
