"""
Problem 03: Retry policy with exponential backoff.

Meta flavor: Standard pattern for transient failures (network, throttle,
rate-limit). Show Airflow + Python implementations.

How to Think:
- Retries: 3-5 attempts.
- Delay = base * 2^attempt (with jitter).
- Cap at max_delay.
- Don't retry on permanent failures (4xx, schema errors).

How to Remember:
- "delay = min(base * 2^attempt, max_delay) * jitter."
- "Permanent vs transient: only retry the latter."

AI Use Cases:
- Auto-classify errors as transient vs permanent.
- Smart jitter based on upstream SLA.
- Failure prediction before retry.
"""
import random, time

def exponential_backoff(attempt, base=2.0, max_delay=60.0, jitter=True):
    """Standard full-jitter formula (AWS pattern)."""
    delay = min(base * (2 ** attempt), max_delay)
    if jitter:
        delay = random.uniform(0, delay)
    return delay

# Airflow equivalent
from airflow import DAG
from datetime import timedelta

RETRY_POLICY = {
    "retries":          5,
    "retry_delay":      timedelta(seconds=10),
    "retry_exponential_backoff": True,
    "max_retry_delay":  timedelta(minutes=5),
}

# Custom retry that knows what NOT to retry
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,            # programmer bug -> don't retry
    KeyError,
    SchemaMismatchError,   # permanent data error
)

def is_retryable(exc):
    return not isinstance(exc, NON_RETRYABLE_EXCEPTIONS)

# Pseudocode for an Airflow task with classification
def safe_call(**ctx):
    try:
        do_work()
    except Exception as e:
        if is_retryable(e):
            raise       # Airflow retries
        else:
            ctx["ti"].log.error(f"Non-retryable: {e}")
            send_to_dlq()
            raise AirflowFailException(e)
