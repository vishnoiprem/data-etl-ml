"""
cron_lock.py — Cross-process lock for cron-scheduled jobs.

Uses Postgres advisory locks, so:
  - No file-based race conditions
  - Works across multiple machines
  - Auto-released on connection close (even on crash)
  - Zero dependencies beyond psycopg2

Usage:
    from db.cron_lock import cron_lock

    with cron_lock("autopilot") as got:
        if not got:
            print("Another autopilot is already running, exiting")
            return
        run_pipeline()
"""

import contextlib
import sys
import hashlib
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

try:
    import psycopg2
    import psycopg2.extras
    HAVE_PG = True
except ImportError:
    HAVE_PG = False


def _name_to_key(name: str) -> int:
    """Deterministic 32-bit int from a human-readable name."""
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return int(h, 16)


@contextlib.contextmanager
def cron_lock(name: str, _conn=None):
    """Try to acquire an exclusive Postgres advisory lock.

    Yields True if we got the lock, False if another process holds it.
    The lock auto-releases when the connection closes (even on crash).
    """
    if not HAVE_PG:
        # DB unavailable → fail-open with a warning
        yield True
        return

    key = _name_to_key(name)
    own_conn = _conn is None
    conn = _conn or psycopg2.connect(
        host=_env("AVILX_DB_HOST", "localhost"),
        port=int(_env("AVILX_DB_PORT", "5433")),
        dbname=_env("AVILX_DB_NAME", "avilx_leads"),
        user=_env("AVILX_DB_USER", "avilx"),
        password=_env("AVILX_DB_PASSWORD", "avilx"),
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_try_advisory_lock(%s)", (key,))
        got = cur.fetchone()[0]
        cur.close()
        try:
            yield bool(got)
        finally:
            if got:
                # Release explicitly; otherwise waits for conn close
                cur = conn.cursor()
                try:
                    cur.execute("SELECT pg_advisory_unlock(%s)", (key,))
                except Exception:
                    pass
                cur.close()
    finally:
        if own_conn:
            conn.close()


def _env(key: str, default: str) -> str:
    import os
    return os.getenv(key, default)
