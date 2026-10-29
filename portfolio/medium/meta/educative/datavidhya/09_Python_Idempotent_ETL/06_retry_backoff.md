# Retry with exponential backoff for transient errors

## Problem
ETL jobs call external systems that fail in two ways: transient (rate limits,
gateway timeouts, network resets) and permanent (auth errors, validation
errors). Retrying a permanent error wastes quota and time; retrying a
transient error is mandatory. The retry policy must be bounded and not
interfere with the data-layer idempotency of the job.

## How to Think
1. Classify failures explicitly. Use distinct exception types.
2. Only retry `TransientError`. Surface `PermanentError` immediately.
3. Exponential backoff: `base * 2^attempt` plus full jitter to avoid thundering
   herd when many workers retry at the same instant.
4. Cap attempts (`max_attempts`) so a flapping dependency cannot stall the job.
5. When the underlying API supports it, send an idempotency token (e.g.
   Graph dedup hash) so retries do not create duplicates on the server side.

## How to Remember
- **Pattern**: "classify, then backoff bounded by attempt count"
- Idempotency = same input -> same output, regardless of run count.
- Backoff protects the upstream API; idempotency protects your downstream data.

## Code (Python)
```python
class TransientError(Exception): ...
class PermanentError(Exception): ...

def call_with_retry(fn, policy):
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except PermanentError:
            raise
        except TransientError as e:
            if attempt == policy.max_attempts - 1:
                raise
            time.sleep(policy.sleep_for(attempt))
```

## Common Mistakes
- Retrying on all exceptions -- turns auth bugs into runaway loops.
- Linear backoff -- synchronizes retries across workers and DOSes the upstream.
- No jitter -- many workers retry at the same instant.
- No cap on attempts -- a dead dependency ties up the job forever.

## AI Use Cases
- Calling Meta Marketing/Graph APIs during ETL with predictable throttling.
- Polling cloud object stores for newly written partition files.
- Hitting third-party conversion APIs in a Multi-Touch Attribution pipeline.
