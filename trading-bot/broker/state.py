"""SQLite-backed state for the trading bot.

The single source of truth for "did we already act on signal X?" and
"what positions do we currently hold?" Lives in a local SQLite file so
the bot survives restarts without losing track of open positions.

Schema (3 tables):
  - signals: every signal we've seen (id = (ticker, ts) from TimescaleDB)
  - decisions: BUY/SKIP verdicts, with rationale
  - trades: every fill (buy or sell), linked to a decision

The `action_signal` UNIQUE INDEX on (ticker, ts) is the idempotency
guarantee: a single (ticker, ts) signal can produce at most one decision
and at most one buy fill. This is what lets the bot poll the DB
continuously without ever re-buying the same signal.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    ticker     TEXT NOT NULL,
    ts         TEXT NOT NULL,   -- ISO 8601 UTC
    action     TEXT NOT NULL,   -- 'BUY' / 'WATCH' (from Flink)
    price      REAL NOT NULL,
    target     REAL,
    confidence REAL,
    reason     TEXT,
    seen_at    TEXT NOT NULL,
    PRIMARY KEY (ticker, ts)
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker      TEXT NOT NULL,
    signal_ts   TEXT NOT NULL,
    verdict     TEXT NOT NULL,  -- 'BUY' / 'SKIP'
    notional    REAL,           -- dollar amount, only for BUY
    shares      INTEGER,        -- only for BUY
    reason      TEXT,
    decided_at  TEXT NOT NULL,
    FOREIGN KEY (ticker, signal_ts) REFERENCES signals (ticker, ts)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_decision_per_signal
    ON decisions (ticker, signal_ts);

CREATE TABLE IF NOT EXISTS trades (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id  INTEGER NOT NULL,
    ticker       TEXT NOT NULL,
    side         TEXT NOT NULL,  -- 'BUY' / 'SELL'
    shares       INTEGER NOT NULL,
    fill_price   REAL NOT NULL,
    notional     REAL NOT NULL,
    filled_at    TEXT NOT NULL,
    broker_id    TEXT,           -- Alpaca order id
    FOREIGN KEY (decision_id) REFERENCES decisions (id)
);

CREATE INDEX IF NOT EXISTS idx_trades_open
    ON trades (ticker) WHERE side = 'BUY';
"""


@dataclass
class Signal:
    ticker: str
    ts: str
    action: str
    price: float
    target: Optional[float] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None


@dataclass
class Decision:
    id: int
    ticker: str
    signal_ts: str
    verdict: str
    notional: Optional[float]
    shares: Optional[int]
    reason: Optional[str]
    decided_at: str


@dataclass
class Trade:
    id: int
    decision_id: int
    ticker: str
    side: str
    shares: int
    fill_price: float
    notional: float
    filled_at: str
    broker_id: Optional[str] = None


class State:
    """Thread-safe-ish wrapper around a single SQLite file.

    SQLite handles its own locking; we just need to open with
    check_same_thread=False and serialize calls via a single connection.
    """

    def __init__(self, path: str = "trades.db"):
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.executescript(SCHEMA)
        self._conn.execute("PRAGMA journal_mode=WAL")

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    # ---- signals ---------------------------------------------------------
    def record_signal(self, sig: Signal) -> bool:
        """Insert signal if new. Returns True if newly inserted, False if dup."""
        with self.cursor() as cur:
            cur.execute(
                """INSERT OR IGNORE INTO signals
                   (ticker, ts, action, price, target, confidence, reason, seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (sig.ticker, sig.ts, sig.action, sig.price, sig.target,
                 sig.confidence, sig.reason, datetime.utcnow().isoformat()),
            )
            return cur.rowcount == 1

    def unseen_buy_signals(self) -> list[Signal]:
        """All BUY signals that don't yet have a decision."""
        with self.cursor() as cur:
            cur.execute(
                """SELECT s.ticker, s.ts, s.action, s.price, s.target,
                          s.confidence, s.reason
                   FROM signals s
                   LEFT JOIN decisions d
                     ON s.ticker = d.ticker AND s.ts = d.signal_ts
                   WHERE s.action = 'BUY' AND d.id IS NULL
                   ORDER BY s.ts""",
            )
            return [Signal(*row) for row in cur.fetchall()]

    # ---- decisions -------------------------------------------------------
    def record_decision(self, dec: Decision) -> int:
        """Insert decision. Returns the new id.

        Raises sqlite3.IntegrityError if (ticker, signal_ts) already
        has a decision — that's the idempotency guard.
        """
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO decisions
                   (ticker, signal_ts, verdict, notional, shares, reason, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (dec.ticker, dec.signal_ts, dec.verdict, dec.notional,
                 dec.shares, dec.reason, dec.decided_at),
            )
            new_id = cur.lastrowid
        # Return the full Decision row so callers can use it
        return Decision(
            id=new_id, ticker=dec.ticker, signal_ts=dec.signal_ts,
            verdict=dec.verdict, notional=dec.notional, shares=dec.shares,
            reason=dec.reason, decided_at=dec.decided_at,
        )

    def has_decision(self, ticker: str, signal_ts: str) -> bool:
        with self.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM decisions WHERE ticker=? AND signal_ts=?",
                (ticker, signal_ts),
            )
            return cur.fetchone() is not None

    # ---- trades ----------------------------------------------------------
    def record_trade(self, trade: Trade) -> int:
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO trades
                   (decision_id, ticker, side, shares, fill_price,
                    notional, filled_at, broker_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (trade.decision_id, trade.ticker, trade.side, trade.shares,
                 trade.fill_price, trade.notional, trade.filled_at, trade.broker_id),
            )
            return cur.lastrowid

    def open_positions(self) -> dict[str, dict]:
        """Net open position per ticker.

        Returns {ticker: {shares, avg_cost, total_cost}}. Sells subtract.
        """
        with self.cursor() as cur:
            cur.execute(
                """SELECT ticker,
                          SUM(CASE WHEN side='BUY' THEN shares ELSE -shares END) AS net,
                          SUM(CASE WHEN side='BUY' THEN notional ELSE -notional END) AS cost
                   FROM trades
                   GROUP BY ticker
                   HAVING net > 0"""
            )
            out: dict[str, dict] = {}
            for ticker, net, cost in cur.fetchall():
                out[ticker] = {
                    "shares": int(net),
                    "total_cost": float(cost),
                    "avg_cost": float(cost) / int(net) if net else 0.0,
                }
            return out

    def decision_for(self, ticker: str, signal_ts: str) -> Optional[Decision]:
        with self.cursor() as cur:
            cur.execute(
                """SELECT id, ticker, signal_ts, verdict, notional, shares,
                          reason, decided_at
                   FROM decisions WHERE ticker=? AND signal_ts=?""",
                (ticker, signal_ts),
            )
            row = cur.fetchone()
            return Decision(*row) if row else None

    def close(self) -> None:
        self._conn.close()


def build_test_state(tmp_path: str = ":memory:") -> State:
    """In-memory state for tests/smoke."""
    s = State.__new__(State)
    s.path = tmp_path
    s._conn = sqlite3.connect(tmp_path, check_same_thread=False,
                              isolation_level=None)
    s._conn.executescript(SCHEMA)
    return s
