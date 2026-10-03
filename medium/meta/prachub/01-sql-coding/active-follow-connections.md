# Write SQL for Active Follow Connections

## 1. Simple way to think
- Table: `follow_events(requester_id, target_id, event, event_ts)` with `event IN ('request_follow','follow_success','follow_reject','unfollow')`.
- An "active follow" = requester currently follows target.
- Transitions:
  - `request_follow` → pending (not yet active)
  - `follow_success` → active
  - `follow_reject` → never active (request denied)
  - `unfollow` → no longer active
- For each (requester, target) pair, the latest event decides current state.
- A pair is "active" iff the most recent event for that pair is `follow_success`.

## 2. Interview write-up (how to solve it)

```sql
WITH latest AS (
    SELECT requester_id, target_id, event,
           ROW_NUMBER() OVER (PARTITION BY requester_id, target_id
                              ORDER BY event_ts DESC) AS rn
    FROM follow_events
)
SELECT requester_id, target_id
FROM latest
WHERE rn = 1
  AND event = 'follow_success';
```

This is the canonical "most-recent-event-wins" pattern.

## 3. Best optimized solution

```sql
CREATE INDEX idx_follow_events_pair_ts
  ON follow_events (requester_id, target_id, event_ts DESC);

WITH latest AS (
    SELECT DISTINCT ON (requester_id, target_id)
           requester_id, target_id, event
    FROM follow_events
    ORDER BY requester_id, target_id, event_ts DESC
)
SELECT requester_id, target_id
FROM latest
WHERE event = 'follow_success';
```

(Postgres-style `DISTINCT ON`; for MySQL/standard SQL, use the `ROW_NUMBER()` version.)

For a count of currently active follows per user:
```sql
WITH latest AS (
    SELECT requester_id, target_id, event,
           ROW_NUMBER() OVER (PARTITION BY requester_id, target_id
                              ORDER BY event_ts DESC) AS rn
    FROM follow_events
)
SELECT requester_id, COUNT(*) AS active_follows
FROM latest WHERE rn = 1 AND event = 'follow_success'
GROUP BY requester_id
ORDER BY active_follows DESC;
```

### Why it's optimal
- One scan of `follow_events`; the window function is single-pass.
- The descending composite index serves the `PARTITION BY ... ORDER BY event_ts DESC` directly — no sort.
- Output is small (only currently active pairs).

### Common mistakes & interviewer tips
- Forgetting that `follow_reject` is a terminal state — if rejected and then they sent a new request, the latest event matters, not the first.
- Including pending requests in "active."
- Tip: clarify the meaning of "active." A requester who's been accepted, then unfollowed, then re-accepted — depending on the latest event, status flips. State the rule.
