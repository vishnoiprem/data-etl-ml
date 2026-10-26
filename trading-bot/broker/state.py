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
    PRIMARY KEY (ticker, ts),
    CHECK (action IN ('BUY', 'WATCH'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker      TEXT NOT NULL,
    signal_ts   TEXT NOT NULL,
    verdict     TEXT NOT NULL,  -- 'BUY' / 'SKIP' / 'MANUAL_SELL'
    notional    REAL,           -- dollar amount, only for BUY
    shares      INTEGER,        -- only for BUY
    reason      TEXT,
    decided_at  TEXT NOT NULL,
    FOREIGN KEY (ticker, signal_ts) REFERENCES signals (ticker, ts),
    CHECK (verdict IN ('BUY', 'SKIP', 'MANUAL_SELL'))
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
    FOREIGN KEY (decision_id) REFERENCES decisions (id),
    CHECK (side IN ('BUY', 'SELL')),
    CHECK (shares > 0),
    CHECK (fill_price > 0),
    CHECK (notional > 0)
);

CREATE INDEX IF NOT EXISTS idx_trades_ticker
    ON trades (ticker);
CREATE INDEX IF NOT EXISTS idx_trades_decision
    ON trades (decision_id);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker       TEXT NOT NULL,
    kind         TEXT NOT NULL,  -- 'price_above' / 'price_below' / 'pct_change' / 'ma_cross'
    threshold    REAL NOT NULL,
    note         TEXT,           -- free-form, e.g. "buy the dip"
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL,
    triggered_at TEXT,           -- set when fired; non-null = done
    last_price   REAL,           -- last price seen when checked
    CHECK (kind IN ('price_above', 'price_below', 'pct_change', 'ma_cross')),
    CHECK (active IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (active) WHERE active = 1;
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


@dataclass
class Alert:
    id: int
    ticker: str
    kind: str           # 'price_above' | 'price_below' | 'pct_change' | 'ma_cross'
    threshold: float
    note: Optional[str]
    active: bool
    created_at: str
    triggered_at: Optional[str]
    last_price: Optional[float]


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

        Returns {ticker: {shares, avg_cost, total_cost}}.
        avg_cost is the average COST BASIS of remaining BUY shares — sells
        reduce the share count but never reduce the cost basis. Selling 50
        of 100 shares bought at $50 leaves avg_cost = $50 (not $30, which
        is what you'd get if you subtracted sell proceeds).
        """
        with self.cursor() as cur:
            cur.execute(
                """SELECT ticker,
                          SUM(CASE WHEN side='BUY' THEN shares ELSE -shares END) AS net,
                          SUM(CASE WHEN side='BUY' THEN notional ELSE 0 END) AS buy_cost
                   FROM trades
                   GROUP BY ticker
                   HAVING net > 0"""
            )
            out: dict[str, dict] = {}
            for ticker, net, buy_cost in cur.fetchall():
                net_i = int(net)
                out[ticker] = {
                    "shares": net_i,
                    "total_cost": float(buy_cost),
                    "avg_cost": float(buy_cost) / net_i if net_i else 0.0,
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

    # ---- alerts ----------------------------------------------------------
    def add_alert(self, ticker: str, kind: str, threshold: float,
                  note: Optional[str] = None) -> Alert:
        """Create an active alert. Returns the new Alert row.

        Valid kinds: 'price_above', 'price_below', 'pct_change', 'ma_cross'.
        Threshold is interpreted per-kind:
          - price_above / price_below: a price level
          - pct_change: an absolute percent (e.g. 5.0 = 5%)
          - ma_cross: 50 or 200 (the MA to watch)
        """
        now = datetime.utcnow().isoformat()
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO alerts
                   (ticker, kind, threshold, note, active, created_at)
                   VALUES (?, ?, ?, ?, 1, ?)""",
                (ticker.upper(), kind, float(threshold), note, now),
            )
            new_id = cur.lastrowid
        return self.get_alert(new_id)  # type: ignore[return-value]

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        with self.cursor() as cur:
            cur.execute(
                """SELECT id, ticker, kind, threshold, note, active,
                          created_at, triggered_at, last_price
                   FROM alerts WHERE id=?""",
                (alert_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return Alert(
                id=row[0], ticker=row[1], kind=row[2], threshold=row[3],
                note=row[4], active=bool(row[5]), created_at=row[6],
                triggered_at=row[7], last_price=row[8],
            )

    def list_alerts(self, only_active: bool = True) -> list[Alert]:
        sql = """SELECT id, ticker, kind, threshold, note, active,
                        created_at, triggered_at, last_price
                 FROM alerts"""
        if only_active:
            sql += " WHERE active = 1"
        sql += " ORDER BY id DESC"
        with self.cursor() as cur:
            cur.execute(sql)
            return [Alert(
                id=r[0], ticker=r[1], kind=r[2], threshold=r[3],
                note=r[4], active=bool(r[5]), created_at=r[6],
                triggered_at=r[7], last_price=r[8],
            ) for r in cur.fetchall()]

    def deactivate_alert(self, alert_id: int) -> bool:
        """Mark an alert as triggered (active=0, triggered_at=now)."""
        now = datetime.utcnow().isoformat()
        with self.cursor() as cur:
            cur.execute(
                """UPDATE alerts SET active=0, triggered_at=?
                   WHERE id=? AND active=1""",
                (now, alert_id),
            )
            return cur.rowcount == 1

    def update_alert_price(self, alert_id: int, last_price: float) -> None:
        """Update the last_price for an alert (so we can show it in the UI)."""
        with self.cursor() as cur:
            cur.execute(
                "UPDATE alerts SET last_price=? WHERE id=?",
                (float(last_price), alert_id),
            )

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
