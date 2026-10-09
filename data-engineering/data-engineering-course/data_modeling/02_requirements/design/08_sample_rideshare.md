# Lesson 08 — Sample Business Requirements: Ride-Sharing

> **What you'll learn:** a worked end-to-end discovery session for
> the canonical "design a data warehouse for a ride-sharing
> service" prompt. You'll see the candidate navigate the
> trip-event complexity and commit to a grain that handles
> late-arriving GPS pings.

---

## The prompt

> Interviewer: "Design a data warehouse for a ride-sharing
> service so the analytics team can measure driver utilization,
> rider demand, and pricing effectiveness."

This is the second of the six canonical questions. It shows up at
Uber, Lyft, and any mobility / logistics company. The expected
schema has a `fact_trips` table at the trip grain, joined to
`dim_drivers`, `dim_riders`, `dim_cities`, and `dim_date`, with a
separate `fact_trip_events` for the high-cardinality GPS stream.

---

## The discovery (5 minutes)

> Candidate: "Before I draw, can I ask a few discovery questions?
> Ride-sharing has some specific gotchas — late events, surge
> pricing, multi-stop trips — and I want to make sure I model
> them right."

1. **What's the grain of the headline metric — one row per
   ride request, per accepted trip, per completed trip, or per
   driver-day? These give very different numbers.**
2. **How do we handle trip events that arrive late — e.g., a GPS
   ping that comes in 30 seconds after the trip ended? Is the
   event-time the source of truth, or the arrival-time?**
3. **How is 'driver utilization' defined — by minutes online,
   by minutes on a trip, or by ratio of busy-time to online-time?
   These produce different dashboards.**
4. **Is the analytics team the only consumer, or do we also need
   to support surge-pricing models, fraud detection, and ops
   dashboards for live ops?**
5. **How do we treat canceled trips — canceled by rider, by
   driver, or by the platform (e.g., unmatched after 5 min)?**
6. **How is surge pricing represented — a separate fact table,
   a dimension, or a measure on the trip fact?**
7. **Are there multi-city or multi-country considerations — does
   each city have its own pricing rules, or is it a single
   global rate card?**

---

## The interviewer's answers (compressed)

> Interviewer: Grain is one row per completed trip. Driver
> utilization = (minutes on trip) / (minutes online). Surge is
> a measure on the trip fact. Cancellations are separate fact
> tables. Multi-city, with city-level rate cards.

---

## The requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — Ride-Sharing

## Consumers
- **Analytics** — driver & rider dashboards
- **Data Science** — surge pricing models, fraud detection
- **Ops** — live operations, supply/demand heatmaps

## Use cases
1. Driver utilization by city by hour
2. Rider demand by city by day-of-week
3. Surge multiplier distribution by city
4. Cancellation rate by rider vs driver
5. Trip-level revenue (net of surge, refunds, tips)

## Source systems
| name | system | volume | freshness |
| --- | --- | --- | --- |
| trips | Kafka events | 10M/day | real-time |
| drivers | PostgreSQL | 100k rows | real-time |
| riders | PostgreSQL | 50M rows | real-time |
| surge_rules | PostgreSQL | 1k rules | hourly |
| gps_pings | Kafka events | 1B/day | real-time |

## Fact tables
- **fact_trips** — grain: one row per completed trip
  - measures: trip_distance_km, trip_duration_min, surge_multiplier,
    fare, tip, total_revenue
  - dimensions: dim_drivers, dim_riders, dim_cities, dim_date,
    dim_time_of_day
- **fact_trip_events** — grain: one row per trip event (start, end,
  waypoint, GPS ping)
  - measures: event_latency_ms
  - dimensions: dim_trips, dim_event_types
- **fact_cancellations** — grain: one row per cancellation
  - measures: minutes_to_cancel
  - dimensions: dim_trips, dim_drivers, dim_riders, dim_cancellation_reason

## Non-functional
- **Volume:** 10M trips/day, 1B GPS pings/day
- **Freshness:** real-time for trips, hourly for aggregates
- **Retention:** 2 years trips, 90 days raw GPS
```

---

## The grain commitment (1 minute)

> Candidate: "OK — to make sure I have this right: the primary
> fact table is `fact_trips` at the grain of **one row per
> completed trip**, with `fare`, `tip`, and `total_revenue` as
> the measures. `dim_cities` is SCD Type 2 (cities change rate
> cards over time). The high-cardinality GPS stream is *not* in
> `fact_trips` — it's a separate `fact_trip_events` table at the
> event grain. Cancellations are a third fact table, with its
> own grain. Does that match what you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Primary grain:** one row per completed trip.
2. **Surge:** measure on the fact, not a separate dimension.
3. **GPS events:** separate fact table, not denormalized into
   `fact_trips`.
4. **Cancellations:** separate fact table.
5. **City SCD:** Type 2.

These are the five decisions that will drive the star schema in
Lesson 17.

---

## What the candidate did right

- Asked the **grain** question first — the most leveraged question
  in any modeling round.
- Asked about **late-arriving events** — a domain-specific gotcha
  for ride-sharing.
- Asked about **surge pricing** as a *modeling* question (fact
  measure vs dim vs separate fact), not just as a metric
  definition.
- Asked about **cancellation** as a *separate entity* — a common
  omission in mid-level answers.
- Made the GPS stream a separate fact — the right call for
  cardinality reasons.

---

## What the candidate did *not* do

- Did not ask about **fraud signals** (fake rides, GPS spoofing) —
  could be a follow-up.
- Did not ask about **payment systems** (which currency, which
  processor).
- Did not ask about **regulatory** (e.g., NYC TLC reporting).

These are the depth-dive material — the interviewer will likely
drive into one of them.

---

## Try it

Re-do this exercise on a different marketplace: Airbnb, Turo,
DoorDash, Instacart. Time yourself: 5 minutes for discovery, 3
minutes for the doc, 1 minute for the grain commitment. Total:
under 10 minutes. The trick on marketplaces is the **two-sided
grain** (rider + driver) and the **time-windowing** (request,
accept, arrive, complete). Make sure you commit to a grain that
handles both.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
