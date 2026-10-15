# Day 20 — Mock Interview Day 3

## Exercise 1 — Feedback history endpoint
`GET /traces/{id}/feedback/history` returns all historical feedback entries (audit log).

## Exercise 2 — Streaming traces
Stream newly-created traces via SSE. Use a simple in-memory pubsub.

## Exercise 3 — Multi-tenancy
Add a `tenant_id` column and filter all queries by it.

## Exercise 4 — Slow query debug
A user reports `/traces?prompt_version=v1.0` is slow. Use `EXPLAIN QUERY PLAN`. Add an index on `(prompt_version, created_at DESC, trace_id DESC)` if needed.

## Exercise 5 — Design review
Critique our API: missing fields, wrong codes, inconsistent naming.

## Five Q&As
1. **What is a feature flag?** A runtime switch to enable/disable code paths.
2. **What is a canary release?** Rolling out to 1% of users.
3. **What is a circuit breaker?** Stop calling a failing service temporarily.
4. **What is an SLA?** Service Level Agreement — uptime, latency commitments.
5. **What is an SLO?** Service Level Objective — internal target.

## Coding assignment
Add a `?status=error` filter to the traces endpoint.

## Solution
```python
# In routes/traces.py
if status_filter:
    where.append("status = ?")
    params.append(status_filter)
```
- 0: doesn't compile
- 4: filters
- 6: returns 422 on invalid value
- 8: indexed
- 10: combined with date + prompt_version

**Time: 90 min**