# Google Data Engineer — Six-Round Question Breakdown with How to Answer

> Compiled from a candidate's six-round Google Bangalore DE interview account. Note: the account is secondhand (relayed from a contact), so treat the salary figures loosely — but the round structure and questions align closely with other first-hand reports, which is why they're reliable.
>
> Cross-cutting thread: **failure handling, idempotency, and partitioning** show up in nearly every technical answer. Mention them unprompted to signal seniority.
https://dev.to/gowthampotureddi/google-data-engineering-interview-questions-prep-guide-36c9
> 
> 
---

## ROUND 1 — Online Assessment (90 min): DSA + SQL + Python

### Q: DSA — medium problem on "error processing over sliding windows."
**How to answer:** This is a sliding-window pattern — maintain a window over a stream of log events and compute something (error rate, count) per window. Keep a deque or two pointers and a running aggregate; add the new element, evict ones outside the window, update the aggregate in O(1) per step so the whole pass is O(n).
> Say aloud: "Fixed-size window → deque; condition-based window → expand right, shrink left."

### Q: SQL — join two large tables, aggregate by category, filter using a window function.
**How to answer:** Structure as a CTE. Join → `GROUP BY category` → apply the window in an outer query and filter on it (you can't filter a window function in WHERE — use a subquery/CTE or QUALIFY).
```sql
WITH agg AS (
  SELECT category,
         SUM(x) AS total,
         RANK() OVER (ORDER BY SUM(x) DESC) AS rnk
  FROM a JOIN b USING (id)
  GROUP BY category
)
SELECT * FROM agg WHERE rnk <= 5;
```
Mention: join on indexed/clustered keys, filter early.

### Q: Python — write a function to detect data schema anomalies in logs.
**How to answer:** Define the expected schema (field names + types), then stream the logs and flag deviations.
```python
EXPECTED = {"user_id": int, "event": str, "ts": str}

def detect_anomalies(rows):
    bad = []
    for i, row in enumerate(rows):
        for field, typ in EXPECTED.items():
            if field not in row:
                bad.append((i, f"missing {field}"))
            elif not isinstance(row[field], typ):
                bad.append((i, f"{field} wrong type"))
    return bad
```
Talk about: missing fields, unexpected extra fields, type mismatches, and routing bad rows to a reject list with a reason — never silently drop.

**Round 1 tip:** practice LeetCode-medium for data engineering, plus HackerRank advanced SQL.

---

## ROUND 2 — Data Engineering Round: ETL + Big Data + SQL + Airflow

### Q: Design an ETL pipeline to ingest daily data from an external API into BigQuery.
**How to answer:** Walk the flow — scheduled trigger (Airflow/Composer) → call API with pagination + retry/backoff → land raw JSON in Cloud Storage (immutable, replayable) → transform/validate → load into a partitioned BigQuery table (partition by ingestion date). Mention idempotency: a rerun of the same day shouldn't duplicate — overwrite the date partition or MERGE.

### Q: How will you handle schema evolution in production?
**How to answer:** Land raw first so you never lose data; use BigQuery schema auto-detect / allow field addition for additive changes; for breaking changes, version the schema and parser, validate against an expected contract, and route nonconforming records to a quarantine table.
> Principle: additive changes flow through, breaking changes get caught and alerted, never silently corrupt downstream.

### Q: Difference between Airflow `@daily` vs externally / once triggered?
**How to answer:** `@daily` is a schedule — the DAG runs automatically each interval, with a data interval and catchup/backfill behavior. A once/externally triggered DAG runs only when something fires it (manual, API, or a sensor/event from upstream).
> Schedule-driven = predictable cadence with backfill; trigger-driven = event-driven, runs when data actually arrives.

### Q: Given a slow SQL query, optimize it.
**How to answer (checklist):** read the query plan first; filter early (predicate pushdown); ensure partition/cluster columns are used in WHERE; avoid `SELECT *`; replace correlated subqueries with joins or window functions; pre-aggregate if it's a repeated dashboard query; check for fan-out from a one-to-many join inflating rows.

**Round 2 tip:** be ready for whiteboard DAG design; show awareness of failure handling, retry logic, and partitioning.

---

## ROUND 3 — Coding Round (closest to a "Programming / Code Comprehension" round)

### Q: Multi-GB log file — find the top 10 users by event frequency. Memory-optimized, streaming required.
**How to answer:**
```python
import heapq
from collections import Counter

def top_10_users(path):
    counts = Counter()
    with open(path) as f:        # file object streams one line at a time
        for line in f:           # never loads the whole file into memory
            user = parse_user(line)
            if user:
                counts[user] += 1
    return heapq.nlargest(10, counts.items(), key=lambda kv: kv[1])
```
> Say: "I stream line by line, so memory is O(distinct users), not O(file size). Heap for top-10 avoids sorting everyone — O(n log 10). If distinct users don't fit in memory, I'd shard by hashing the user ID to multiple files (external/disk-based aggregation) and merge partial counts."

### Q: Follow-up — what if the streaming data type changes midway?
**How to answer:** Wrap parsing in try/except, route unparseable lines to a dead-letter count with the reason, version the parser so a format change is detected rather than silently miscounted, and emit a metric/alert when reject rate spikes.
> Grading point: graceful failure handling, not crashing.

**Round 3 tip:** practice generator functions and external-sort techniques.

---

## ROUND 4 — System Design (data-focused)

### Q: Design a real-time data pipeline for clickstream events.
**How to answer:** events → Pub/Sub or Kafka (buffer, absorbs spikes) → Dataflow/Spark streaming (parse, dedupe, enrich) → BigQuery partitioned + clustered, or a serving store. Clarify volume and freshness requirements before drawing.

### Q: How do you ensure fault tolerance?
**How to answer:** Durable queue with replay/offsets so no data is lost if a consumer dies; checkpointing in the stream processor; retries with backoff; dead-letter queue for poison messages; idempotent writes so replays don't duplicate.

### Q: Where would you add deduplication logic?
**How to answer:** Dedupe on a stable event_id as close to the sink as practical, because the queue gives at-least-once delivery. Options: windowed dedup in the stream processor (keep seen IDs for a time window), or MERGE / `QUALIFY ROW_NUMBER() = 1` on load into BigQuery.
> Trade-off: in-stream dedup is faster but needs state; load-time dedup is simpler but lets dupes travel further.

### Q: How would you store 1 billion rows efficiently?
**How to answer:** Columnar storage (BigQuery), partition by a time/date column to prune scans, cluster / z-order by the common filter columns, compress, and avoid row-by-row access patterns.
> Partition pruning is what keeps query cost flat as the table grows.

**Round 4 tip:** mention Pub/Sub or Kafka, Dataflow/Spark, BigQuery, z-ordering/partitioning.

---

## ROUND 5 — Behavioral / Googleyness (use STAR; show humility + growth mindset)

### Q: Tell me about a time you took full ownership of a failing project.
**How to answer:** Real example with STAR — situation (what was failing, the stakes), task (what you owned), action (concrete steps YOU drove: diagnosis, re-plan, communication), result (with a number), and the lesson.
> Ownership = you stepped up without being told to.

### Q: How do you handle conflict with a product manager?
**How to answer:** Seek to understand their goal first, bring data/evidence rather than opinion, find shared criteria, and commit fully once a decision is made even if it wasn't your first choice ("disagree and commit"). Empathy first, then solution.

### Q: What would you do if a deadline is missed because of your code?
**How to answer:** Own it immediately and transparently, communicate impact and a revised plan early (not at the deadline), fix the root cause, and add a safeguard (test/check/review step) so it can't recur.
> Humility + a concrete prevention step is what's scored.

---

## ROUND 6 — Hiring Manager (project deep-dive + cultural fit)

### Q: How did you build a data pipeline from scratch? (project deep-dive)
**How to answer:** Tell it end to end — problem, your design choices and *why* (the trade-offs you weighed), scale, and impact. Be ready for "why this component over that one" at every step.

### Q: How did you onboard junior data engineers?
**How to answer:** Show mentorship — documentation/runbooks you wrote, pairing, gradually scoped tasks, code review as teaching. Demonstrates emergent leadership.

### Q: What metrics define a successful data pipeline?
**How to answer:** Freshness/latency (is data on time), completeness/volume (expected row counts), accuracy/quality (null rates, schema conformance, reconciliation vs source), reliability (success rate, MTTR), and cost. Pick a few and explain why each matters.

### Q: Why Google / motivation to join? (final ~15 min, open-ended)
**How to answer:** Be specific and authentic — the scale of data problems, the impact, what you'll learn. Tie it to your trajectory. Avoid generic praise; name something concrete.

---

## KEY TECHNOLOGIES TO PRIORITIZE (from this account)
1. **SQL** — window functions + partitioning
2. **Python** — data structures + streaming
3. **Airflow** (orchestration)
4. **GCP** — Pub/Sub, BigQuery, Dataflow
- *Good to have:* Snowflake, dbt, Terraform, Git

## FINAL TIPS
- Brush up SQL optimization and real-world data pipeline challenges.
- Practice one DSA question every day.
- Understand system design **for data**, not just web apps.
- Be authentic in the behavioral round — they value culture fit.
- Learn GCP if you're coming from AWS or Azure.
