# Day 20 — Mock Interview Day 3
**Module 18** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Analogy for a 12-year-old:**
Today is the **third scrimmage**. You're getting good. Today: harder problems, less time, more critique.

---

## 2. Technical concepts (20 min)

Topics covered so far (Modules 14–17):
- Auth/security, testing, debugging/performance, packaging/deployment.

### Meta-skill: prioritization
If you can't finish in 30 minutes, deliver a *partial* solution that:
1. Compiles.
2. Has one happy-path test.
3. Is honest about what's missing.

---

## 3. Coding (30 min)

### Exercise 1 — Feedback history endpoint
`GET /traces/{id}/feedback/history` returns all historical feedback entries (audit log).

### Exercise 2 — Streaming traces
Stream newly-created traces via SSE. Use a simple in-memory pubsub.

### Exercise 3 — Multi-tenancy
Add a `tenant_id` column and filter all queries by it.

### Exercise 4 — Slow query debug
A user reports `/traces?prompt_version=v1.0` is slow.
Use `EXPLAIN QUERY PLAN`. Add an index on `(prompt_version, created_at DESC, trace_id DESC)` if needed.

### Exercise 5 — Design review
Critique our API: missing fields, wrong codes, inconsistent naming.

### Sample I/O
See above.

### Line-by-line
Discuss with a partner or write the explanation as comments.

---

## 4. Debugging & tests (20 min)

For each exercise, ask:
- What's the test that would catch a regression?
- What's the security implication?
- What's the migration plan for existing data?

For multi-tenancy, the migration is:
```sql
ALTER TABLE traces ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default';
CREATE INDEX idx_traces_tenant ON traces(tenant_id);
```

---

## 5. Mock interview practice (20 min)

**Q1 — "What is a feature flag?"**
> A runtime switch to enable/disable code paths.

**Q2 — "What is a canary release?"**
> Rolling out to 1% of users.

**Q3 — "What is a circuit breaker?"**
> Stop calling a failing service temporarily.

**Q4 — "What is an SLA?"**
> Service Level Agreement — uptime, latency commitments.

**Q5 — "What is an SLO?"**
> Service Level Objective — internal target.

---

## 6. Success criteria check
- [ ] I can scope a feature in 5 minutes.
- [ ] I can describe multi-tenancy tradeoffs.
- [ ] I can read a slow-query plan.
- [ ] I can critique my own API.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add a `?status=error` filter to the traces endpoint.**

### Rubric (0–10)
- 0: doesn't compile
- 4: filters
- 6: returns 422 on invalid value
- 8: indexed
- 10: combined with date + prompt_version

### Solution
```python
# In routes/traces.py
if status_filter:
    where.append("status = ?")
    params.append(status_filter)
```

**Time: 90 min**