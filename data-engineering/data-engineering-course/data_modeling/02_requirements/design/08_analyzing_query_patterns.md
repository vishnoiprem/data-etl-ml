# Analyzing Query Patterns

## Why this lesson

A data model that looks correct on paper can still fail in production if it doesn't match the *query patterns* the business will actually run. Will analysts run point-in-time lookups ("what did the customer look like when this event happened?") or only current-state lookups ("what's the customer's current country?")? Will they run cohort retention queries, funnel queries, or sessionization queries? Will they join across multiple fact tables, or only ever join to one? Each query pattern has a schema implication: SCD type, surrogate vs natural key, role-playing dims, fact table choice. This lesson uses a ride-sharing worked example to show you how to surface query patterns *before* you draw the schema, and how each pattern drives a specific modeling decision.

---

## The prompt

> Interviewer: "Design a data warehouse for a ride-sharing
> service so the analytics team can measure driver utilization,
> rider demand, and pricing effectiveness."

The candidate's first move: surface the query patterns the
business will run against the warehouse. Below is how a senior
candidate does that.

---

## The four query patterns every modeler must know

There are four query patterns that show up in 90% of warehouse
workloads. The senior candidate names them, asks the interviewer
which apply, and designs accordingly:

| Pattern | Description | Schema implication |
|---|---|---|
| **Point-in-time lookup** | "What was the customer/driver/product/price at the time of event X?" | SCD 2 dims with effective/expiry dates; temporal joins. |
| **Current-state lookup** | "What's the customer's current country / plan / status?" | SCD 1 dim, or SCD 2 with `is_current = 1` filter. |
| **Aggregation by time window** | "Sum of revenue by day / week / month." | Date dim with day/week/month keys; fact table at fine grain so it can be re-aggregated. |
| **Aggregation by entity** | "Sum of revenue by customer / driver / product." | Surrogate keys; many-to-one FK from fact to dim. |

For ride-sharing, all four apply. The candidate asks:

> "Are we doing **point-in-time analysis** — e.g., 'what was the
> surge multiplier in this city at the moment this trip was
> requested?' — or only current-state analysis?"

---

## Query discovery — the ride-sharing worked example

> Candidate: "Before I draw, can I ask a few discovery questions?
> Ride-sharing has specific query patterns — late events, surge
> pricing windows, multi-stop trips — and I want to make sure I
> model them right."

1. **Point-in-time vs current-state.**
   > "Do we need to reconstruct history — e.g., 'what city rate
   > card applied to this 2023 trip?' — or only query the current
   > state of the system?" This decides SCD type on `dim_cities`.
2. **High-cardinality stream queries.**
   > "Will analysts ever query the GPS ping stream directly — e.g.,
   > 'replay this driver's route for the last 30 minutes' — or is
   > the GPS stream a firehose we only aggregate?" This decides
   > whether `fact_trip_events` is a real fact table or a cold
   > log.
3. **Funnel queries.**
   > "Are we doing funnel analysis on the request → accept → arrive
   > → complete flow? E.g., 'what's the abandon rate at each
   > step?'" This decides whether cancellation is a separate
   > fact table or a flag on `fact_trips`.
4. **Cross-fact joins.**
   > "Do we ever need to join trips to support tickets, or trips
   > to payments, in a single query?" This decides which dims are
   > conformed across facts.
5. **Time-window aggregations.**
   > "What time windows do we aggregate by — 5-minute windows for
   > live ops, hourly for ops dashboards, daily for analytics?"
   > This decides the date dim's grain and the fact's event-time
   > column.
6. **Late-arriving data.**
   > "How do we handle trip events that arrive late — e.g., a GPS
   > ping that comes in 30 seconds after the trip ended? Is the
   > event-time the source of truth, or the arrival-time?" This
   > decides partitioning and recompute strategy.
7. **Cancellation as event.**
   > "How do we treat canceled trips — as a status on `fact_trips`,
   > or as a separate `fact_cancellations` table?" This decides
   > whether the analyst can run "cancellation rate by step" as
   > a simple funnel.

---

## How query patterns drive schema choice

| Query pattern | Modeling decision |
|---|---|
| Point-in-time lookups on drivers | `dim_drivers` is SCD 2 with `effective_date` / `expiry_date`. |
| Point-in-time lookups on city rate cards | `dim_cities` is SCD 2. |
| GPS stream queries | `fact_trip_events` is a real fact table at the event grain, with `event_latency_ms` as a measure. |
| Funnel analysis (request → accept → arrive → complete) | `fact_trips` carries a `trip_status` column; `fact_cancellations` is a separate fact at the cancellation grain. |
| Cross-fact joins (trips + support) | `dim_drivers` and `dim_riders` are conformed across facts. |
| 5-minute live-ops windows | `dim_time_of_day` at the 5-minute grain joins to `fact_trips`; event-time is the partition key. |
| Late-arriving events | Partition by event-time, not arrival-time; document the SLA. |

The interviewer pattern: a senior candidate names the *query
pattern* and then says the *schema decision* it implies. That's
two sentences that demonstrate both query literacy and modeling
fluency.

---

## The interviewer's answers (compressed)

> Interviewer: Yes, we do point-in-time lookups on city rate
> cards (SCD 2). The GPS stream is a firehose — we don't query
> it directly, but we do aggregate it for surge pricing. We do
> funnel analysis on the request → accept → complete flow.
> Cancelled trips are a separate fact. Late events: event-time
> is the source of truth, partition by event-time.

---

## The query-driven requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — Ride-Sharing

## Query patterns
- **Point-in-time** on city rate cards and driver attributes
- **Funnel** on request → accept → arrive → complete
- **5-minute live-ops** aggregations for surge pricing
- **Cross-fact** joins between trips and cancellations
- **Daily aggregations** for revenue dashboards

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
> the measures. `dim_cities` is SCD Type 2 because of the
> point-in-time rate-card lookups. The high-cardinality GPS
> stream is *not* in `fact_trips` — it's a separate
> `fact_trip_events` table at the event grain, supporting
> 5-minute live-ops windows. Cancellations are a third fact
> table, with its own grain, supporting the funnel analysis.
> Does that match what you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Primary grain:** one row per completed trip.
2. **Surge:** measure on the fact, not a separate dimension.
3. **GPS events:** separate fact table, not denormalized into
   `fact_trips`.
4. **Cancellations:** separate fact table (funnel support).
5. **City SCD:** Type 2 (point-in-time lookups).

These are the five decisions that will drive the star schema.

---

## What the candidate did right

- Surfaced **point-in-time** as a query pattern and made it
  drive the SCD decision on `dim_cities`.
- Recognized the **GPS stream** as a separate fact table for
  cardinality and query-pattern reasons.
- Made the **funnel** pattern drive a separate `fact_cancellations`
  table.
- Asked about **late-arriving events** — a domain-specific gotcha
  for ride-sharing.

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
DoorDash, Instacart. Time yourself: 5 minutes for query-pattern
discovery, 3 minutes for the doc, 1 minute for the grain
commitment. Total: under 10 minutes. The trick on marketplaces is
the **two-sided grain** (rider + driver) and the **time-windowing**
(request, accept, arrive, complete). Make sure you commit to a
grain that handles both.

---

## In the interview, you would say...

> "Before I draw, I'm going to ask which **query patterns** the
> business needs — point-in-time lookups, current-state lookups,
> time-window aggregations, funnel analysis, cross-fact joins.
> Each pattern implies a different schema choice: SCD type, fact
> table grain, conformed vs role-playing dims. Naming the pattern
> and the implication is the interview signal I'm going for."

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
