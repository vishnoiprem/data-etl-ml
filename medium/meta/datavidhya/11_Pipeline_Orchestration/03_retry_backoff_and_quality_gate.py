"""
Problem 03: Retries with exponential backoff, and a quality gate that fails loudly.

Meta flavor: "The upstream API is flaky and the job keeps failing. Fix it."

How to Think:
- RETRY ONLY WHAT IS RETRYABLE. A 503 or a timeout is transient — retry it.
  A 400, a schema mismatch, or a missing column is deterministic; retrying it
  just burns 3 attempts and delays the alert. Classify the error first. This
  distinction is what interviewers are actually probing.
- EXPONENTIAL BACKOFF, not fixed delay: 1s, 2s, 4s. Fixed retries against a
  service that is already overloaded make the outage worse — you become part of
  the incident.
- Add JITTER in production so a fleet of workers does not retry in lockstep
  (the thundering herd). Omitted here only so the test is deterministic.
- CAP the attempts and then FAIL. Infinite retries turn a page-worthy outage
  into a silently stuck pipeline, which is strictly worse.
- The QUALITY GATE must be able to fail the run. Publishing an empty or
  half-written partition is worse than publishing nothing, because downstream
  consumers cannot tell it is wrong.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark


class TransientError(Exception):
    """Retryable: timeout, 5xx, throttling."""


class PermanentError(Exception):
    """NOT retryable: bad request, schema mismatch, auth failure."""


def with_retries(fn, max_attempts=4, base_delay=1.0):
    """
    Retry `fn` on TransientError with exponential backoff. Returns
    (result, attempts, delays). Delays are computed, not slept, so the test is
    fast and deterministic — real code would sleep(d) with jitter.
    """
    delays = []
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(attempt), attempt, delays
        except PermanentError:
            raise                                    # fail fast, do not retry
        except TransientError:
            if attempt == max_attempts:
                raise
            delays.append(base_delay * (2 ** (attempt - 1)))
    raise AssertionError("unreachable")


# --- Transient failures: succeeds on the 3rd attempt ----------------------
def flaky(attempt):
    if attempt < 3:
        raise TransientError(f"503 on attempt {attempt}")
    return "ok"

result, attempts, delays = with_retries(flaky)
assert result == "ok" and attempts == 3, (result, attempts)
assert delays == [1.0, 2.0], delays
print(f"[PASS] transient: succeeded on attempt {attempts}, backoff {delays}")

# --- Permanent failure: must NOT be retried -------------------------------
calls = {"n": 0}


def bad_schema(attempt):
    calls["n"] += 1
    raise PermanentError("column 'gross_amount' missing")

try:
    with_retries(bad_schema)
    raise AssertionError("should have raised")
except PermanentError:
    pass
assert calls["n"] == 1, f"retried a permanent error {calls['n']} times"
print("[PASS] permanent error failed fast after 1 attempt (no wasted retries)")

# --- Exhausted retries must raise, not hang -------------------------------
def always_down(attempt):
    raise TransientError("upstream down")

try:
    with_retries(always_down, max_attempts=3)
    raise AssertionError("should have raised")
except TransientError:
    print("[PASS] exhausted retries raised instead of retrying forever")


# --- Quality gate ---------------------------------------------------------
def quality_gate(date):
    """Fail the run rather than publish a bad partition."""
    n = spark.sql(f"SELECT COUNT(*) c FROM orders WHERE order_date = '{date}'") \
             .collect()[0]["c"]
    if n == 0:
        raise ValueError(f"partition {date} is empty - refusing to publish")
    return n

assert quality_gate("2026-01-01") == 2
print("[PASS] quality gate passed a good partition (2 rows)")

try:
    quality_gate("2026-02-30")        # no such data
    raise AssertionError("gate should have failed")
except ValueError as e:
    print(f"[PASS] quality gate blocked an empty partition: {e}")
