"""
tests/test_cron_lock.py — verify cron_lock fail-CLOSED behavior.

When the DB can't be reached (network down, postgres stopped, bad
credentials, psycopg2 missing), the lock must yield False so callers
refuse to run the email phase. Yielding True would let two crons
double-send, which is the failure mode this lock was created to
prevent.
"""

import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import db.cron_lock as cron_lock  # noqa: E402

try:
    import psycopg2  # noqa: E402
    HAVE_PG = True
except ImportError:
    HAVE_PG = False
    psycopg2 = None  # type: ignore


def test_yields_false_when_psycopg2_missing(monkeypatch):
    """Without psycopg2, the lock must yield False (fail-CLOSED).

    Previously it yielded True, which let two concurrent cron
    runs both enter the email phase and double-send.
    """
    monkeypatch.setattr(cron_lock, "HAVE_PG", False)
    with cron_lock.cron_lock("autopilot") as got:
        assert got is False, (
            "cron_lock must fail-CLOSED when psycopg2 is unavailable"
        )


def test_yields_false_when_connect_times_out(monkeypatch):
    """If psycopg2.connect raises OperationalError (DB down / wrong
    creds / network unreachable), the lock must yield False."""
    if not HAVE_PG:
        return  # can't test what isn't installed

    def _raise_connect(*a, **k):
        raise psycopg2.OperationalError("connection refused")

    monkeypatch.setattr(cron_lock, "HAVE_PG", True)
    monkeypatch.setattr(psycopg2, "connect", _raise_connect)
    with cron_lock.cron_lock("autopilot") as got:
        assert got is False, (
            "cron_lock must fail-CLOSED on connect failure"
        )


def test_yields_true_on_successful_lock(monkeypatch):
    """Happy path: pg_try_advisory_lock returns true → context yields True."""
    if not HAVE_PG:
        return

    class _Cursor:
        def execute(self, *a, **k): pass
        def fetchone(self): return (True,)
        def close(self): pass
    class _Conn:
        def cursor(self): return _Cursor()
        def close(self): pass

    monkeypatch.setattr(cron_lock, "HAVE_PG", True)
    with mock.patch.object(psycopg2, "connect", return_value=_Conn()):
        with cron_lock.cron_lock("autopilot") as got:
            assert got is True
