# Write SQL for Car Rental Utilization by City

## 1. Simple way to think
- Tables: `user(user_id, ...)`, `location(loc_id, city, ...)`, `car(car_id, loc_id, ...)`, `rental(rental_id, car_id, user_id, start_ts, end_ts, ...)`.
- "Utilization" typically = `SUM(rental_duration) / SUM(available_time)` per car, then aggregated by city.
- Two readings: (a) % of time cars are rented, (b) % of fleet actively rented on average.
- The simpler answer: for each car, count hours/days rented in a period; divide by total hours in that period; average per city.

## 2. Interview write-up (how to solve it)

```sql
WITH rental_hours AS (
    SELECT r.car_id,
           SUM(EXTRACT(EPOCH FROM (COALESCE(r.end_ts, CURRENT_TIMESTAMP) - r.start_ts)) / 3600.0)
             AS hours_rented
    FROM rental r
    WHERE r.start_ts >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY r.car_id
),
period_hours AS (
    SELECT 30.0 * 24 AS hours
),
city_util AS (
    SELECT l.city,
           AVG(LEAST(rh.hours_rented, p.hours) / p.hours) AS avg_utilization
    FROM car c
    JOIN location l ON l.loc_id = c.loc_id
    LEFT JOIN rental_hours rh ON rh.car_id = c.car_id
    CROSS JOIN period_hours p
    GROUP BY l.city
)
SELECT city, avg_utilization
FROM city_util
ORDER BY avg_utilization DESC;
```

## 3. Best optimized solution

```sql
CREATE INDEX idx_rental_car_dates ON rental (car_id, start_ts, end_ts);
CREATE INDEX idx_car_loc ON car (loc_id, car_id);

WITH bounds AS (
    SELECT DATE_TRUNC('day', CURRENT_DATE - INTERVAL '30 days') AS start_day,
           DATE_TRUNC('day', CURRENT_DATE)                     AS end_day
),
rental_per_car AS (
    SELECT r.car_id,
           SUM(EXTRACT(EPOCH FROM (COALESCE(r.end_ts, CURRENT_TIMESTAMP) - r.start_ts))) AS secs
    FROM rental r, bounds b
    WHERE r.start_ts <  b.end_day
      AND COALESCE(r.end_ts, CURRENT_TIMESTAMP) > b.start_day
    GROUP BY r.car_id
),
window_secs AS (
    SELECT EXTRACT(EPOCH FROM (end_day - start_day)) AS s FROM bounds
)
SELECT l.city,
       AVG(LEAST(rpc.secs, w.s) / w.s) AS utilization
FROM car c
JOIN location l ON l.loc_id = c.loc_id
LEFT JOIN rental_per_car rpc ON rpc.car_id = c.car_id
CROSS JOIN window_secs w
GROUP BY l.city
ORDER BY utilization DESC;
```

### Why it's optimal
- Time-bounded scan of `rental` via the bounds CTE.
- Per-car aggregation precomputed once; city-level is a single GROUP BY.
- `COALESCE(end_ts, CURRENT_TIMESTAMP)` handles open rentals.
- `LEAST` caps utilization at 100% (a car can't be rented more than the window).

### Common mistakes & interviewer tips
- Counting rentals (count) instead of duration (time) — very different metrics.
- Not capping utilization above 100% (overlapping rentals or pre-period starts can push it over).
- Tip: clarify whether utilization is measured per car or as a fleet total. They give different denominators.
