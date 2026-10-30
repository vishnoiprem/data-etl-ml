# Query Carpool Ride Metrics

## 1. Simple way to think
- A ride-sharing "carpool" product matches multiple riders going in the same direction into one car.
- Common metrics: daily completed pooled rides, average seat utilization (% of seats filled), average detour minutes, on-time pickup rate.
- The schema typically has: `rides(ride_id, request_ts, status, total_seats, booked_seats, ...)`, `ride_events(ride_id, event_type, event_ts)`, `users`, `cities`.
- Mental model: filter to `status = 'completed'`, group by day, compute aggregations.

## 2. Interview write-up (how to solve it)

```sql
-- 1) Daily completed pooled rides
SELECT DATE(completed_ts) AS day,
       COUNT(*)            AS completed_rides
FROM rides
WHERE status = 'completed'
  AND is_carpool = TRUE
GROUP BY 1
ORDER BY 1;

-- 2) Average seats utilization
SELECT DATE(completed_ts)                AS day,
       AVG(booked_seats::float / total_seats) AS avg_seat_utilization
FROM rides
WHERE status = 'completed'
  AND is_carpool = TRUE
  AND total_seats > 0
GROUP BY 1
ORDER BY 1;

-- 3) Riders served per day (a single ride can have multiple riders)
SELECT DATE(r.completed_ts) AS day,
       COUNT(DISTINCT rr.rider_id) AS daily_riders
FROM rides r
JOIN ride_riders rr ON rr.ride_id = r.ride_id
WHERE r.status = 'completed' AND r.is_carpool
GROUP BY 1
ORDER BY 1;
```

## 3. Best optimized solution
Single pass with conditional aggregation, indexed by `(status, is_carpool, completed_ts)`.

```sql
SELECT DATE(completed_ts)                   AS day,
       COUNT(*)                             AS completed_rides,
       COUNT(DISTINCT ride_id)              AS unique_rides,
       AVG(booked_seats::float / NULLIF(total_seats, 0))
                                            AS avg_seat_utilization,
       SUM(booked_seats)                    AS total_seats_filled
FROM rides
WHERE status     = 'completed'
  AND is_carpool = TRUE
  AND completed_ts >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(completed_ts)
ORDER BY 1;
```

Add a covering index:
```sql
CREATE INDEX idx_rides_carpool_completed
  ON rides (completed_ts)
  INCLUDE  (booked_seats, total_seats, is_carpool, status);
```

### Why it's optimal
- One scan of a filtered partition (90-day window).
- `NULLIF` guards against divide-by-zero.
- Index covers the WHERE clause and the SELECT list, so the query is index-only.
- `SUM(booked_seats)` is a bonus metric that piggybacks on the same scan.

### Common mistakes & interviewer tips
- Forgetting `NULLIF` for utilization — division by zero on rides with `total_seats = 0` (e.g., canceled before assignment).
- Counting "rides" as "riders" — a carpool ride may carry 3 riders; the metric depends on the question.
- Tip: always state the time zone used for `DATE()`. "Daily" means different things in UTC vs. local.
