"""Poll the realtime-stock-pipeline TimescaleDB for new BUY signals.

The Flink pipeline writes rows to the `signals` table. We poll every
N seconds for rows that arrived since the last poll, hand them to the
SignalWatcher, and let it act.

We track our high-water mark (last seen signal ts) so we never re-poll
old signals and never miss a new one even across restarts.
"""
from __future__ import annotations
import time
import logging
import os
from typing import Optional
from datetime import datetime

import psycopg2

from broker.state import State, Signal
from bot.signal_watcher import SignalWatcher


log = logging.getLogger("poller")


SIGNAL_QUERY = """
SELECT ticker, ts, action, current_price, target_price, confidence, reasons
FROM signals
WHERE ts > %s AND action = 'BUY'
ORDER BY ts ASC
"""


class SignalPoller:
    def __init__(self, state: State, watcher: SignalWatcher,
                 dsn: Optional[str] = None,
                 poll_interval: float = 5.0):
        self.state = state
        self.watcher = watcher
        self.dsn = dsn or os.environ.get(
            "TIMESCALEDB_DSN",
            "host=localhost port=5432 dbname=stocks user=stocks password=stocks",
        )
        self.poll_interval = poll_interval
        self._last_ts: Optional[datetime] = None
        # Resume from the last decision we already processed
        with state.cursor() as cur:
            cur.execute("SELECT MAX(signal_ts) FROM decisions")
            row = cur.fetchone()
            if row and row[0]:
                self._last_ts = datetime.fromisoformat(row[0])

    def _fetch_new(self) -> list[Signal]:
        try:
            conn = psycopg2.connect(self.dsn)
        except Exception as e:
            log.warning("can't connect to TimescaleDB: %s", e)
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(SIGNAL_QUERY, (self._last_ts or "1970-01-01",))
                rows = cur.fetchall()
                sigs = [
                    Signal(
                        ticker=r[0],
                        ts=r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
                        action=r[2],
                        price=float(r[3]),
                        target=float(r[4]) if r[4] is not None else None,
                        confidence=float(r[5]) if r[5] is not None else None,
                        reason=r[6],
                    )
                    for r in rows
                ]
                if sigs:
                    self._last_ts = max(
                        datetime.fromisoformat(s.ts) for s in sigs
                    )
                return sigs
        finally:
            conn.close()

    def tick(self) -> int:
        """One polling cycle. Returns the number of signals processed."""
        sigs = self._fetch_new()
        if not sigs:
            return 0
        decisions = []
        for sig in sigs:
            d = self.watcher.process_signal(sig)
            if d:
                decisions.append(d)
        return len(decisions)

    def run_forever(self) -> None:
        log.info("polling TimescaleDB every %.1fs (high-water mark: %s)",
                 self.poll_interval, self._last_ts)
        while True:
            try:
                n = self.tick()
                if n:
                    log.info("processed %d new signals", n)
            except Exception:
                log.exception("polling cycle failed")
            time.sleep(self.poll_interval)
