# Lesson 32 — Mock Interview: Ride-Sharing Schema

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the use of *role-playing
> dimensions* and *conformed dimensions*.

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

> Design a data warehouse for a ride-sharing service
> (think Uber / Lyft). We want to report on ride
> volume, driver utilization, surge pricing, and
> revenue. The OLTP source is a microservices backend
> with separate services for riders, drivers, trips,
> and payments.

---

## The transcript

**Interviewer:** Design a data warehouse for a
ride-sharing service.

**Candidate:** OK. Before I draw, let me clarify the
scope. "Ride-sharing" could mean bikes, scooters, or
cars. I'm assuming cars, but let me confirm.

**Interviewer:** Cars. Single city for now, but the
model should scale to multi-city.

**Candidate:** Good. Three clarifying questions:

1. **What defines a "ride"?** A ride starts when a
   rider is matched to a driver and ends when the
   driver marks the trip complete. Is that the
   grain?

2. **What do you mean by "surge pricing"?** A
   multiplier on the base fare, applied at request
   time, that decays as more drivers accept. Is that
   what we're reporting on?

3. **"Driver utilization" — % of time online +
   accepting rides? Or % of miles driven with a
   rider?**

**Interviewer:** Yes to all three.

**Candidate:** Good. One more: the OLTP is
microservices. So rider, driver, trip, and payment
are separate systems. The warehouse joins them on
`rider_id` and `driver_id` and `trip_id`. I want to
make sure I model the joins correctly.

**Interviewer:** Right. Go.

**Candidate:** OK, here's my design.

The central fact is `fact_trips` at the grain of
*one row per trip*. A trip has a clear start and end,
one rider, one driver, one vehicle, one city. The
measures are:

- `fare_amount` — base fare
- `surge_multiplier` — non-additive
- `total_amount` — fare × surge + fees
- `tip_amount`
- `distance_miles`
- `duration_seconds`
- `driver_payout` — what the driver earns

The dimensions:

- `dim_rider` — SCD 2. Riders sign up, churn, and
  re-sign-up. We want to know what the rider's
  home city was when they took the trip.
  Attributes: rider_id (natural key), name, signup_date,
  home_city, rating, payment_method_type.
- `dim_driver` — SCD 2. Drivers have a vehicle, a
  rating, a city, and they go on/off the platform.
  We want historical attribution: which driver
  was matched to which trip at the time of the trip.
  Attributes: driver_id, name, vehicle_make,
  vehicle_model, vehicle_year, rating, city, status.
- `dim_city` — SCD 1 (cities don't change). name,
  state, country, region, timezone.
- `dim_date` — conformed. Role-played for
  `request_time_key`, `pickup_time_key`, and
  `dropoff_time_key` on the trip fact.
- `dim_time` — separate from date. Granularity at
  the minute. Role-played the same way: request,
  pickup, dropoff. We need this for the
  hour-of-day analysis.
- `dim_payment_method` — small dim. credit_card,
  apple_pay, google_pay, cash.
- `dim_promotion` — small dim. promo_code,
  discount_pct. Could be a junk dim, but
  promotion has enough attributes to warrant its own
  table.
- `dim_surge_zone` — geographic zone for surge
  pricing. The zone is a polygon in the city, and
  each zone has a current surge multiplier. I'd
  model this as a slowly-changing fact, not a dim,
  because the multiplier is changing constantly and
  we want to attribute the trip to the multiplier at
  request time.

**Interviewer:** Walk me through the role-playing date
dim.

**Candidate:** A single trip has three dates: when it
was requested, when the rider was picked up, and when
the driver dropped them off. All three are foreign
keys on the fact:

```sql
FOREIGN KEY (request_date_key)  REFERENCES dim_date(date_key),
FOREIGN KEY (pickup_date_key)   REFERENCES dim_date(date_key),
FOREIGN KEY (dropoff_date_key)  REFERENCES dim_date(date_key)
```

Same for time:

```sql
FOREIGN KEY (request_time_key)  REFERENCES dim_time(time_key),
FOREIGN KEY (pickup_time_key)   REFERENCES dim_time(time_key),
FOREIGN KEY (dropoff_time_key)  REFERENCES dim_time(time_key)
```

The dim is the same physical table; the role-playing
is at the FK level. The analyst knows that
`request_date_key` is the date the rider opened the
app, and `pickup_date_key` is the date they got in
the car. Same `dim_date`, different roles.

**Interviewer:** Why a separate dim_time, not just
include hour in dim_date?

**Candidate:** Because `dim_date` is one row per
calendar day (3650 rows for 10 years). `dim_time` is
one row per minute of the day (1440 rows). If I
include `time_of_day` in `dim_date`, every fact row
joins to a 3650-row dim, which is fine — but the
analyst can never filter by "rides between 5pm and
7pm" without exploding the date key. With a separate
`dim_time`, the query is
`WHERE pickup_time_key BETWEEN 1020 AND 1140` (1020
= 17:00, 1140 = 19:00). And `dim_time` has
attributes the date dim doesn't: hour, minute, hour
bucket (morning / afternoon / evening / night),
rush_hour_flag.

**Interviewer:** Why SCD 2 on drivers?

**Candidate:** Because the driver-vehicle-city
combination changes over time. A driver might switch
cars, change cities, go inactive, come back, change
rating. The trip fact has the `driver_key` for the
SCD 2 row that was current at trip time. If we used
SCD 1, an analyst asking "what was the average
rating of drivers for trips in Q1" would get *today's*
ratings, not Q1's. SCD 2 fixes that.

**Interviewer:** What about the surge pricing? Walk
me through how the fact attributes a trip to the
surge multiplier at request time.

**Candidate:** Two options. The first is a slowly
changing dim on `dim_surge_zone` with a
`surge_multiplier` column, SCD 2 by zone. The fact
joins to the version of the zone that was current at
request time.

The second is a separate fact: `fact_surge_observations`,
one row per (zone, minute), with `surge_multiplier`.
The trip fact joins to the observation at request
time.

I'd pick the second — surge changes too often for
SCD 2 to be efficient (every minute!), and the fact
of "the surge was 1.5x in zone X at minute Y" is
itself a fact, not a dim attribute. So:

```sql
CREATE TABLE fact_surge_observations (
  surge_key       INTEGER PRIMARY KEY,
  zone_key        INTEGER NOT NULL,
  observation_ts  TIMESTAMP NOT NULL,
  surge_multiplier REAL NOT NULL
);
```

The trip fact has `request_surge_key` (FK to
`fact_surge_observations`) for the surge that was
in effect when the trip was requested.

**Interviewer:** Why a separate fact for surge? Why
not a column on `dim_surge_zone`?

**Candidate:** Because `dim_surge_zone` is a dim
with one row per zone (a small, slow-changing
master-data table — Manhattan, Brooklyn, etc.). The
surge multiplier is a *measurement* that changes
every minute, not a property of the zone. Mixing
the two in one table is an error: the dim is
"master data" with one row per zone, and the fact
is "events" with many rows per zone.

**Interviewer:** What's the grain of the revenue
report?

**Candidate:** Daily revenue by city. The query is:

```sql
SELECT d.date_key, c.city_name,
       SUM(f.total_amount) AS revenue,
       COUNT(*) AS trips
FROM fact_trips f
JOIN dim_date d ON f.dropoff_date_key = d.date_key
JOIN dim_city c ON f.city_key = c.city_key
WHERE d.date_key BETWEEN 20240101 AND 20240131
GROUP BY d.date_key, c.city_name;
```

`dropoff_date_key` because we attribute revenue to
the day the trip ended, not the day it started. (A
trip that starts at 11:50pm and ends at 12:10am
attributes to the new day.)

**Interviewer:** What if a driver disputes the
fare and the total_amount is updated post-hoc?

**Candidate:** Good question. If the trip fact is
updated, the historical aggregation changes. We
have two options:

1. **SCD 1 on the trip fact** — overwrite the
   `total_amount` and accept that historical
   aggregations may shift. The audit trail is the
   payments service.
2. **Append-only fact with correction rows** — the
   original trip row has a `total_amount`, the
   correction has a negative `total_amount` (or a
   `correction_flag`).

For a ride-sharing system, I'd pick option 2 because
finance reporting needs to be reproducible. The
audit trail is the sum of all rows for a given
`trip_id`.

**Interviewer:** What about the OLTP-to-warehouse
mapping? The OLTP is microservices.

**Candidate:** Each microservice publishes a CDC
stream. The warehouse has separate staging tables
per service:

- `stg_riders` — from the rider service.
- `stg_drivers` — from the driver service.
- `stg_trips` — from the trip service.
- `stg_payments` — from the payment service.

The dimension loaders read from staging, apply SCD 2
logic, and write to the conformed dim tables. The
fact loader joins the staging tables on
`rider_id`, `driver_id`, `trip_id` and writes to
`fact_trips`. The dim keys are assigned by the
warehouse (surrogate), not the OLTP (natural).

**Interviewer:** Tradeoffs?

**Candidate:** Three:

1. **One row per trip vs per leg.** A "trip" with
   multiple stops (rider picks up a friend) is one
   trip or many? I assumed one trip with multiple
   stops, with `stops` as an array column. If a
   stop is its own billable event, the grain is
   finer — one row per leg.
2. **SCD 2 on the driver.** Required for historical
   attribution, but doubles the dim size and the
   join cost. Worth it.
3. **Separate `dim_time` vs hour on `dim_date`.**
   Adds a dim, but enables hour-of-day analysis. The
   alternative (one row per minute in `dim_date`) is
   52M rows, which is silly.

**Interviewer:** Last question — how do you model
the payment side? A rider might pay with a stored
card, but the actual charge is split between the
driver, the platform, and the tax authority.

**Candidate:** That's a separate fact:
`fact_payments`, at the grain of *one row per
payment leg*. A $30 trip with a $5 tip might have
three legs: $25 to the driver, $5 tip to the driver,
$0 to the platform (negative margin for promo), $2
to the tax authority. The legs are append-only,
audit-trail-friendly, and finance reports on them
directly. They join back to the trip on
`trip_id`.

**Interviewer:** That's time.

---

## Rubric scoring (4 buckets)

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about ride definition, surge, utilization. |
| **Picks a grain** | 5/5 | One row per trip, defended. |
| **Makes and defends tradeoffs** | 5/5 | Date vs time dim, SCD 2, separate surge fact. |
| **Talks while drawing** | 5/5 | Narrated every FK, every dim choice. |

---

## Take-aways

- **Role-playing dimensions** — three FKs to `dim_date`
  on the same fact, for request / pickup / dropoff.
- **Surge pricing as a fact, not a dim attribute** —
  because it changes too fast for SCD 2 to be efficient.
- **Payments as a separate fact with append-only
  correction rows** — for finance reproducibility.
- **CDC streams from microservices** — staging tables
  per service, with surrogate keys assigned in the
  warehouse.

---

## Try it

Set a 30-minute timer. Re-state the problem, draw the
star, name the dimensions, write the DAU query and the
revenue query. Then read the solution above.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
