# Write Queries for Follows and Bookings

## 1. Simple way to think
- Two related temporal event logs: `follow_events` (already seen) and `bookings(booking_id, user_id, resource_id, start_ts, end_ts, status)`.
- The ask combines:
  - Bidirectional relational integrity (e.g., a follow must have a matching `follow_success` from the other side if "mutual" is required).
  - Efficient graph queries (who follows whom, who follows who-follows-X).
  - Interval queries (overlapping bookings, available slots).
- The unifying theme: temporal data + graph data, often stored in event-sourced form.

## 2. Interview write-up (how to solve it)

**Currently active follows (already covered)**
```sql
WITH latest AS (
    SELECT requester_id, target_id, event,
           ROW_NUMBER() OVER (PARTITION BY requester_id, target_id
                              ORDER BY event_ts DESC) AS rn
    FROM follow_events
)
SELECT requester_id, target_id
FROM latest WHERE rn = 1 AND event = 'follow_success';
```

**Mutual follows (A follows B AND B follows A)**
```sql
WITH active AS (
    SELECT requester_id, target_id
    FROM latest
    WHERE rn = 1 AND event = 'follow_success'
)
SELECT a.requester_id AS user_a, a.target_id AS user_b
FROM active a
JOIN active b ON b.requester_id = a.target_id AND b.target_id = a.requester_id
WHERE a.requester_id < a.target_id;     -- dedupe pairs
```

**Overlapping bookings for the same resource**
```sql
SELECT b1.booking_id, b2.booking_id, b1.resource_id
FROM bookings b1
JOIN bookings b2
  ON b1.resource_id = b2.resource_id
 AND b1.booking_id  < b2.booking_id
 AND b1.start_ts    < b2.end_ts
 AND b2.start_ts    < b1.end_ts
WHERE b1.status IN ('confirmed','pending')
  AND b2.status IN ('confirmed','pending');
```

**Available slots between bookings (per resource, on a given day)**
```sql
WITH day_bookings AS (
    SELECT resource_id, start_ts, end_ts
    FROM bookings
    WHERE start_ts::date = DATE '2025-03-15'
      AND status = 'confirmed'
)
SELECT resource_id, lag_end, start_ts AS next_start,
       start_ts - lag_end AS gap
FROM (
    SELECT resource_id, start_ts, end_ts,
           LAG(end_ts) OVER (PARTITION BY resource_id ORDER BY start_ts) AS lag_end
    FROM day_bookings
) t
WHERE lag_end IS NOT NULL;
```

## 3. Best optimized solution

**Use a `follows` materialized view + indexes for fast reads**
```sql
CREATE MATERIALIZED VIEW active_follows AS
WITH latest AS (
    SELECT requester_id, target_id, event,
           ROW_NUMBER() OVER (PARTITION BY requester_id, target_id
                              ORDER BY event_ts DESC) AS rn
    FROM follow_events
)
SELECT requester_id, target_id
FROM latest WHERE rn = 1 AND event = 'follow_success';

CREATE INDEX idx_active_follows_requester ON active_follows (requester_id);
CREATE INDEX idx_active_follows_target    ON active_follows (target_id);

-- Mutual follows become a single index intersection
SELECT a.requester_id, a.target_id
FROM active_follows a
JOIN active_follows b
  ON a.requester_id = b.target_id
 AND a.target_id    = b.requester_id
 AND a.requester_id < a.target_id;
```

**Bookings: use a range index + GiST/SP-GiST for overlap queries (Postgres)**
```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE INDEX idx_bookings_range ON bookings USING gist (resource_id, tsrange(start_ts, end_ts));

-- Overlap check becomes a single index probe
SELECT b1.booking_id, b2.booking_id
FROM bookings b1
JOIN bookings b2
  ON b1.resource_id = b2.resource_id
 AND b1.booking_id  < b2.booking_id
 AND tsrange(b1.start_ts, b1.end_ts) && tsrange(b2.start_ts, b2.end_ts)
WHERE b1.status = 'confirmed' AND b2.status = 'confirmed';
```

### Why it's optimal
- Materialized view serves frequent reads; the heavy `ROW_NUMBER` runs only on refresh.
- Composite indexes support both directions of the follow graph.
- GiST with `tsrange` uses an R-tree to answer overlap in O(log n) per probe.
- `LAG` window for "available slots" avoids self-join.

### Common mistakes & interviewer tips
- Forgetting the `a < b` (or `requester_id < target_id`) to avoid double-counting mutual pairs.
- Using `BETWEEN` for overlap — that misses the touching case (end == start). Use `start < other.end AND other.start < end`.
- Tip: when both event-log and interval queries are needed, recommend an event-sourced `follow_events` for the graph and a range index for bookings. They serve different access patterns optimally.
