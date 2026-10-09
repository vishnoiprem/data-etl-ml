# 26 — Retry, Backoff, and Dead Letter Queues

> **Lesson 26 of 30 — Performance & Fault Tolerance**

The reliability toolkit. Every pipeline eventually hits a
flaky upstream, a temporary network blip, or a poison
message. The patterns in this lesson are how you survive
them.

---

## 1. The retry pattern

A retry is the simplest reliability mechanism: if the call
fails, try again. The naive version:

```python
def fetch():
    for _ in range(3):
        try:
            return requests.get(url)
        except Exception:
            continue
    raise
```

The problem: if 1000 workers all retry at the same time, the
upstream sees a thundering herd. The mitigation: *backoff*.

---

## 2. Exponential backoff

Exponential backoff means each retry waits longer than the
previous:

```
Attempt 1: try immediately
Attempt 2: wait 1 second
Attempt 3: wait 2 seconds
Attempt 4: wait 4 seconds
Attempt 5: wait 8 seconds
```

The pattern:

```python
import time

def fetch_with_backoff(max_attempts=5, base=1.0):
    for attempt in range(max_attempts):
        try:
            return requests.get(url)
        except Exception:
            if attempt == max_attempts - 1:
                raise
            time.sleep(base * (2 ** attempt))
```

The senior move: "I'd use exponential backoff with a base of
1 second and a max of 5 attempts. That gives a worst-case
wait of 16 seconds before the pipeline gives up."

---

## 3. Jitter

A problem with pure exponential backoff: if 1000 workers
all fail at the same time, they all retry at the same
times. The result: a synchronized stampede.

The fix: add *jitter*, a random component to the wait time:

```python
import random

def fetch_with_jitter(max_attempts=5, base=1.0):
    for attempt in range(max_attempts):
        try:
            return requests.get(url)
        except Exception:
            if attempt == max_attempts - 1:
                raise
            wait = base * (2 ** attempt)
            wait *= 0.5 + random.random()  # 50%-150% of the wait
            time.sleep(wait)
```

The senior move: "I'd always add jitter. The pure exponential
backoff pattern is a thundering-herd waiting to happen."

---

## 4. The retry budget

A *retry budget* is the maximum fraction of requests that
can be retries. If the budget is 10%, then 10% of requests
can be retries; the rest must succeed on the first try.

The pattern:

```python
class RetryBudget:
    def __init__(self, max_retry_rate=0.1):
        self.max_retry_rate = max_retry_rate
        self.attempts = 0
        self.retries = 0

    def allow_retry(self) -> bool:
        self.retries += 1
        return (self.retries / max(self.attempts, 1)) <= self.max_retry_rate
```

The senior move: "I'd use a retry budget to prevent the
pipeline from amplifying upstream failures. If the upstream
is down, the budget is exhausted and the pipeline fails
loudly instead of retrying forever."

---

## 5. The idempotency requirement

Every retried operation must be *idempotent* — running it
twice has the same effect as running it once. The patterns
were covered in Lesson 23: idempotency keys, staging tables,
`MERGE INTO` on a primary key.

The senior move: "I'd never add a retry without first
verifying the operation is idempotent. A non-idempotent
retry is a duplicate-data generator."

---

## 6. The dead letter queue (DLQ)

A DLQ is a holding pen for messages that *can't* be
processed. The pattern:

```
Producer → Main topic → Consumer
                              ↓ (fails N times)
                              DLQ topic
                              ↓
                            Human review
```

The consumer tries N times. If all fail, the message goes
to a DLQ topic. A human (or a separate cleanup job) reviews
the DLQ.

The senior move: "I'd use a DLQ for any consumer. The main
pipeline doesn't stop on a poison message; the message
goes to the DLQ for human review."

---

## 7. The DLQ patterns

| Pattern | When to use |
|---|---|
| **Same broker, separate topic** | Default. Simple, immediate. |
| **Same broker, separate partition** | Less common. |
| **External system (S3, database)** | When the DLQ is long-term. |

The senior move: "I'd use a separate topic on the same
broker. The DLQ has its own retention (e.g. 30 days) and
its own monitoring."

---

## 8. The alerting

Every retry and every DLQ entry should be a metric. The
minimum:

- `retry.count` per task
- `dlq.count` per task
- `retry.exhausted.count` per task (retries that gave up)

The senior move: "I'd alert when `retry.exhausted.count` is
non-zero. A retry that gives up is a real failure, not a
transient blip."

---

## 9. The code: `code/retry.py`

The course provides a retry decorator:

```python
from data_pipeline_design.06_performance.code.retry import retry

@retry(max_attempts=3, backoff=1.0, jitter=True)
def flaky_call():
    ...
```

The test in `tests/test_perf.py` exercises the 2x-then-succeeds
and always-fails cases.

---

## 10. The interview answer

> "Every retried operation must be idempotent. I'd use
> exponential backoff with jitter, a max of 5 attempts,
> and a retry budget of 10%. A dead letter queue catches
> poison messages that fail all retries; the main pipeline
> doesn't stop. I'd alert on `retry.exhausted.count` and
> `dlq.count`. The deep dive would be the idempotency story
> — staging tables for batch, dedup keys for streams."

That single paragraph covers: idempotency, backoff with
jitter, retry budget, DLQ, alerting, deep-dive choice.
Senior answer in 30 seconds.

---

## Try it

Look at the most recent retry you've added to a pipeline.
Is there backoff? Is there jitter? Is there a retry budget?
Is the operation idempotent? Is there a DLQ for poison
messages? If any is "no," the retry is either amplifying
load or producing duplicates.
