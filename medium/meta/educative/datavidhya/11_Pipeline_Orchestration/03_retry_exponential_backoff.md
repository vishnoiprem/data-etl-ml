# Retry Policy: Exponential Backoff

## Problem
Design a retry policy for transient failures.

## How to Think
1. **Attempts** – 3-5 typical.
2. **Delay** – `base * 2^attempt`, capped at `max_delay`.
3. **Jitter** – full jitter (random uniform 0..delay) avoids thundering herd.
4. **Don't retry** permanent failures (4xx, schema errors).
5. **DLQ** non-retryable errors for human inspection.

## How to Remember
- **Formula**: `delay = min(base * 2^attempt, max_delay) * jitter`.
- **Only retry transient** (network, throttle, 5xx).

## Code (Python)
```python
import random

def exponential_backoff(attempt, base=2.0, max_delay=60.0, jitter=True):
    delay = min(base * (2 ** attempt), max_delay)
    if jitter:
        delay = random.uniform(0, delay)
    return delay
```

## Airflow Config
```python
default_args = {
    "retries":          5,
    "retry_delay":      timedelta(seconds=10),
    "retry_exponential_backoff": True,
    "max_retry_delay":  timedelta(minutes=5),
}
```

## Non-Retryable Classification
```python
NON_RETRYABLE_EXCEPTIONS = (ValueError, KeyError, SchemaMismatchError)

def is_retryable(exc):
    return not isinstance(exc, NON_RETRYABLE_EXCEPTIONS)
```

## Common Mistakes
- No jitter -> thundering herd on recovery.
- Retrying permanent errors -> wastes time.
- No max_delay -> unbounded retries during outages.

## AI Use Cases
- Auto-classify errors as transient vs permanent from logs.
- Smart jitter sized to upstream SLA.
- Failure prediction (skip retry if unlikely to succeed).
