# Mock 118 — FAANG Final Round

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Format

- 60 minutes, 1 problem, 1 senior interviewer (often an EM or director).
- The bar: clear, clean, communicates tradeoffs, recovers from mistakes gracefully.

## Problem — Design a Thread-Safe In-Memory Key-Value Store with TTL

Implement a class with `set(key, value, ttl_seconds)`, `get(key)`, and `delete(key)`. Values auto-expire. Thread-safe.

## Talking points

- "I'll keep `data: dict[key, (value, expires_at)]` protected by a lock."
- "Lazy expiry: check on `get`. Optional eager: a background sweeper — but that adds complexity. Lazy is fine for in-memory."
- "Trade-off vs. eager: lazy uses no background thread, but a stale key can sit in the dict until accessed."

## Grading rubric

- **Strong Hire**: O(1) ops, lazy expiry, explains tradeoff, writes tests, talks through concurrency.
- **Hire**: works, brief on tradeoffs.
- **Lean Hire**: works but no concurrency.
- **No Hire**: not thread-safe, doesn't think about expiry.
