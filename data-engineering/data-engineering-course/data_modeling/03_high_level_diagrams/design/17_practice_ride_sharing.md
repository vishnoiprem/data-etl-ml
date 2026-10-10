# Lesson 17 — Practice: Ride-Sharing Platform

> **What you'll learn:** the multi-fact ride-sharing star, with
> the trip-cancellation split and surge as a measure. By the end
> of this lesson you'll be able to draw the schema in under 10
> minutes.

---

## Why this lesson

Ride-sharing is the prompt you get at Uber, Lyft, Grab,
and any company that operates a two-sided marketplace
(drivers and riders). The schema looks like e-commerce
on the surface — there's a fact table, there are
dimensions — but the trick is that *two* events matter
(completed trips and cancellations), and the trickier
trick is that **surge is a measure, not a dimension.**
Most mid-level candidates draw one fact and try to fit
both events into it; that breaks the grain rule. Most
also make `dim_surge` a tiny dim of buckets
(`1.0`, `1.2`, `1.5`), which loses the fact that surge
is continuous. This lesson teaches the two-fact split
and the "continuous measure" decision, both of which
show up in every ride-sharing interview.

---

## The prompt

> "Design a data warehouse for a ride-sharing service so the
> analytics team can measure driver utilization, rider demand,
> and pricing effectiveness."

This is the second canonical question. The expected schema has
*two* fact tables (`fact_trips` and `fact_cancellations`) at
different grains, and the GPS stream is a third fact at an
even finer grain.

---

## The star schema

```
                ┌──────────────┐
                │ dim_drivers  │
                │ (SCD 2)      │
                └──────┬───────┘
                       │ driver_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ dim_date │◄───┤  fact_trips  ├───►│ dim_riders   │
└──────────┘    │              │    └──────────────┘
                │ measures:    │
                │  distance_km │    ┌──────────────┐
                │  duration_min│◄───┤ dim_cities   │
                │  surge_      │    │ (SCD 2)      │
                │   multiplier │    └──────────────┘
                │  fare        │
                │  tip         │    ┌──────────────┐
                │  total_rev   │◄───┤ dim_time_of_ │
                └──────┬───────┘    │   day        │
                       │            └──────────────┘
                       │
                       │            ┌──────────────┐
                       └───────────►│fact_         │
                                    │cancellations │
                                    └──────────────┘
```

The schema has **two fact tables** at different grains. That's
the non-obvious part. Most mid-level candidates draw a single
`fact_trips` and try to fit cancellations into it; that
breaks the grain rule.

---

## Why two fact tables

The grains are different:

- `fact_trips` — one row per **completed trip**.
- `fact_cancellations` — one row per **cancellation**.

A cancellation is *not* a completed trip. It's a different
event with different measures (minutes_to_cancel, who
canceled). Trying to fit both into one fact table requires a
nullable measure column (`fare IS NULL for cancellations`)
and breaks the grain rule (the row means different things
depending on which columns are populated).

The right move is two fact tables, each at its own grain.
They can share dimensions (`dim_drivers`, `dim_riders`,
`dim_date`) but they have different rows.

---

## Why surge is a measure, not a dimension

A common candidate trap: make `dim_surge` a dimension with
levels like `1.0`, `1.2`, `1.5`, `2.0`. The interviewer
pushes back: surge is *continuous* (it can be 1.37), not
discrete. So it goes on the fact as a measure.

The trade-off: if 95% of trips have a surge of 1.0 and the
analyst wants to filter "trips with surge > 1.5," the
filter is on a measure. That's fine. The measure is indexed
in the partition key if needed.

---

## The measures on `fact_trips`

| Measure | Type | Notes |
|---|---|---|
| `distance_km` | REAL | The actual distance. |
| `duration_min` | REAL | Start to end. |
| `surge_multiplier` | REAL | 1.0 = no surge. |
| `fare` | REAL | Base + distance + time. |
| `tip` | REAL | Optional. |
| `total_revenue` | REAL | fare + tip. |

All measures are at the trip grain. `surge_multiplier` is
the *only* non-additive measure — you can average it but
not sum it. The other measures are all additive.

---

## The measures on `fact_cancellations`

| Measure | Type | Notes |
|---|---|---|
| `minutes_to_cancel` | REAL | Time from request to cancel. |
| `canceled_by` | TEXT | rider / driver / platform. |

`canceled_by` is a *categorical* measure, not a numeric one.
It goes on the fact as a low-cardinality column or as a tiny
dim (`dim_cancel_reason`). The interview rule of thumb: if
the cardinality is < 50 and the column is filter-only, leave
it on the fact. If you need to attach attributes (e.g.,
"cancel_reason_name" or "is_chargeable"), make it a dim.

---

## The dimensions

### `dim_drivers` (SCD Type 2)

Drivers change vehicle, city, and rating over time. SCD 2.

### `dim_riders` (SCD Type 1)

Riders' country can change, but we don't usually need
historical attribution. SCD 1 — overwrite. The
`signup_date` is a snapshot, kept on the dim as an
attribute, not as an SCD field.

### `dim_cities` (SCD Type 2)

Cities change rate cards (per-km rate, per-min rate) over
time. SCD 2.

### `dim_date` (conformed)

Same dim as Lesson 16, plus a `day_of_week` for the
"weekday vs weekend" question.

### `dim_time_of_day` (junk-ish dim)

Hour + minute + part_of_day. The "part_of_day" is a
*derived* column (morning / midday / evening / night) that
the analyst uses for "demand by part of day" queries. It's
essentially a junk dim, except it has structure — see
Lesson 23.

---

## The trip-event fact (omitted but mentioned)

The prompt hints at "late-arriving GPS pings." The model
handles this with a third fact:

- `fact_trip_events` — one row per trip event (start,
  waypoint, end, GPS ping). Grain: one event per row.

This is *not* a denormalized column on `fact_trips` because
there can be hundreds of events per trip. The right move
is a separate fact at the event grain.

In `code/star_schemas.py`, this is not built (we have 5
schemas, not 6), but the design lesson is the same: when
the cardinality is too high for the parent fact, make a
child fact.

---

## Tradeoffs to call out

1. **Why two fact tables?** "Cancellation is a different
   event with a different grain. Putting both in one fact
   would require nullable measures and break the grain rule."
2. **Why surge as a measure?** "Surge is continuous, not
   discrete. It's filterable, but the value 1.37 is as
   valid as 1.5."
3. **Why is `dim_cities` SCD 2?** "City rate cards change
   over time. We need historical attribution for accurate
   revenue reporting."
4. **Why is `dim_riders` SCD 1, not SCD 2?** "Rider
   attributes don't usually need historical attribution.
   We can change the model if the data science team
   disagrees."
5. **Why not denormalize GPS into `fact_trips`?** "There
   are too many GPS pings per trip. A separate
   `fact_trip_events` at the event grain is the right
   shape."

---

## The DDL — running it

The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_rideshare_schema(q)`. Run the demo:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

Output (truncated):

```
[rideshare]  tables: ['dim_drivers', 'dim_riders', 'dim_cities',
                     'dim_date', 'dim_time_of_day',
                     'fact_trips', 'fact_cancellations']
   fact_trips sample row: {
     'trip_key': 1, 'trip_id': 5001, 'driver_key': 1,
     'rider_key': 1, 'city_key': 1, 'date_key': 20240301,
     'start_time_key': 800, 'end_time_key': 830,
     'distance_km': 5.2, 'duration_min': 25, 'surge_multiplier': 1.5,
     'fare': 18.5, 'tip': 3.0, 'total_revenue': 21.5
   }
```

---

## Sample queries

### Driver utilization by city by hour

```sql
SELECT
    c.city_name,
    tod.part_of_day,
    SUM(t.duration_min) AS busy_minutes
FROM fact_trips t
JOIN dim_cities c ON t.city_key = c.city_key
JOIN dim_time_of_day tod ON t.start_time_key = tod.time_key
GROUP BY c.city_name, tod.part_of_day
ORDER BY c.city_name, tod.part_of_day;
```

### Cancellation rate by rider

```sql
SELECT
    r.rider_id,
    COUNT(c.cancel_key) AS cancels,
    -- needs to be divided by rider's trip count; CTE omitted
    COUNT(c.cancel_key) * 1.0 / NULLIF(COUNT(DISTINCT t.trip_key), 0) AS rate
FROM dim_riders r
LEFT JOIN fact_cancellations c ON r.rider_key = c.rider_key
LEFT JOIN fact_trips t ON r.rider_key = t.rider_key
GROUP BY r.rider_id
ORDER BY rate DESC;
```

---

## Try it

Open
[`code/star_schemas.py`](../code/star_schemas.py) and read
`build_rideshare_schema`. Then:

1. State the grain of each fact table out loud.
2. List the measures on each fact.
3. List the dimensions and their SCD types.
4. Explain why surge is a measure and not a dimension.

Time yourself: 5 minutes. Then run the test:

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

The 24 tests cover all 5 schemas. If you have time, also
add a 6th schema for the GPS event stream and write
3 tests for it.

---

## In the interview, you would say...

> "Ride-sharing is two facts, not one — `fact_trips` at
> the completed-trip grain and `fact_cancellations` at
> the cancellation grain. Combining them requires
> nullable measures and breaks the grain rule. Surge is
> a measure on `fact_trips`, not a `dim_surge` of
> buckets, because surge is continuous (1.37 is as valid
> as 1.5). Drivers and cities are SCD 2 (vehicle, city
> rate card change over time); riders are SCD 1. The
> GPS ping stream is a third fact at the event grain,
> not denormalized onto `fact_trips` because there are
> hundreds of pings per trip."

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
