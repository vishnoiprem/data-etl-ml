# Example: Business Requirements Gathering

## Why this lesson

This lesson is the *capstone* for Module 02. The previous seven lessons gave you a 5W+H framework, a 50+ question bank, and deep dives into metrics, query patterns, latency, volume, and retention. Now we put it all together. Below is a single end-to-end worked example — a full requirements-gathering session for one business (ride-sharing) — where you can see all the pieces working in concert. The candidate asks discovery questions, writes the requirements doc, and commits to a grain. By the end, you should be able to time-box the same exercise at under 15 minutes for any prompt.

---

## The prompt

> Interviewer: "Design a data warehouse for a ride-sharing
> service so the analytics team can measure driver utilization,
> rider demand, and pricing effectiveness."

The candidate runs the full playbook: recognize the core
problem, surface metrics, identify query patterns, pin latency,
estimate volume, define retention, write the doc, commit to a
grain.

---

## Step 1 — Recognize the core business problem (30 seconds)

The candidate pauses and identifies the core problem in one
sentence:

> "The core business problem here is **two-sided marketplace
> liquidity** — matching riders to drivers across cities and
> time windows, with dynamic pricing as the lever. The
> warehouse has to support driver-utilization, rider-demand,
> and pricing-effectiveness analysis across all three."

This sentence anchors everything that follows. The candidate has
already named the entities (riders, drivers, trips, cities,
prices) and the analytical lenses (utilization, demand,
pricing).

---

## Step 2 — Discovery questions (5 minutes)

> Candidate: "Before I draw, can I ask a few discovery
> questions? Ride-sharing has specific gotchas — late events,
> surge pricing, multi-stop trips — and I want to make sure I
> model them right."

### Metric questions (1 minute)

1. **What's the headline metric — completed trips, GMV, or
   driver utilization?** These are different numbers, and
   the schema follows the headline.
2. **How is 'driver utilization' defined — minutes online,
   minutes on a trip, or busy-time / online-time ratio?**
3. **How is 'rider demand' defined — ride requests,
   accepted requests, or completed rides?**
4. **How is 'pricing effectiveness' measured — gross fare,
   net of surge, or net of surge + refunds + tips?**

### Query-pattern questions (1 minute)

5. **Are we doing point-in-time lookups (e.g., "what was the
   city rate card when this trip was requested?") or only
   current-state lookups?**
6. **Are we doing funnel analysis on request → accept → arrive
   → complete?**
7. **Will analysts ever query the GPS ping stream directly,
   or only the aggregated surge / route views?**

### Latency questions (1 minute)

8. **What's the freshness tier — daily batch, hourly, or
   real-time?** For surge pricing, real-time matters; for
   finance, daily is fine.
9. **If we need 5-minute live-ops windows for surge, can the
   source CDC support it?**

### Volume questions (1 minute)

10. **Daily write volume — 10k trips/day, 1M, 10M?**
11. **Historical depth — 1 year, 3 years, forever?**
12. **Dim cardinality — 100k drivers, 1M, 10M?**
13. **Are there hot partitions — e.g., one mega-city, one
    mega-driver, 'today'?**

### Retention questions (1 minute)

14. **Regulatory retention — TLC reporting (NYC), GDPR for
    EU riders?**
15. **How long do we keep raw GPS pings — 30 days, 90 days?**
16. **Right-to-be-forgotten: tokenize at ingest, or delete
    on request?**

---

## Step 3 — The interviewer's answers (compressed)

> Interviewer: Headline metric is **completed trips** + **net
> revenue per trip**. Driver utilization = minutes on trip /
> minutes online. Demand = ride requests (we count requests,
> not just completions, so we can see unmet demand). Pricing
> effectiveness = gross fare net of surge. Grain is **one row
> per completed trip**. We do point-in-time lookups on city
> rate cards. Funnel: yes, request → accept → arrive →
> complete. GPS pings are aggregated, not queried directly.
> Latency: hourly batch for finance, 5-minute live-ops for
> surge pricing. Volume: 10M trips/day, 1B GPS pings/day.
> Historical: 2 years trips, 90 days raw GPS. TLC reporting
> required for NYC. GDPR for EU riders (tokenize PII).

---

## Step 4 — The requirements doc (3 minutes)

The candidate writes (or narrates):

```markdown
# Requirements — Ride-Sharing

## Headline metrics
- **Completed trips** per day, per city, per hour
- **Net revenue per trip** (gross fare net of surge, refunds,
  tips)
- **Driver utilization** = minutes on trip / minutes online
- **Rider demand** = ride requests (not just completions)
- **Pricing effectiveness** = gross fare net of surge

## Query patterns
- **Point-in-time** on city rate cards (SCD 2 needed)
- **Funnel** on request → accept → arrive → complete
- **5-minute live-ops** windows for surge pricing
- **Cross-fact** joins between trips and cancellations
- **Daily aggregations** for revenue dashboards

## Latency tier
- **Hourly batch** for finance and analytics
- **5-minute live-ops** for surge pricing (separate pipeline)
- **Real-time** for the GPS aggregation that drives surge

## Volume and scalability
- **Daily writes:** 10M trips, 1B GPS pings
- **Historical:** 2 years trips (7B rows), 90 days GPS
- **Dim cardinality:** 5M drivers, 100M riders, 500 cities
- **Growth rate:** 3x year-over-year
- **Hot partitions:** NYC and SF dominate writes (handled with
  city-key hash partitioning)

## Retention
- **Trip records:** 2 years hot, then cold archive
- **GPS pings:** 90 days, then aggregated
- **NYC TLC reporting:** immutable 7-year retention
- **GDPR (EU riders):** PII tokenized at ingest; deletion on
  request
- **WORM tier:** TLC reporting data, 7 years

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
- **fact_trips** — grain: *one row per completed trip*
  - measures: trip_distance_km, trip_duration_min, surge_multiplier,
    fare, tip, total_revenue
  - dimensions: dim_drivers, dim_riders, dim_cities, dim_date,
    dim_time_of_day
- **fact_trip_events** — grain: *one row per trip event (start,
  end, waypoint, GPS ping)*
  - measures: event_latency_ms
  - dimensions: dim_trips, dim_event_types
- **fact_cancellations** — grain: *one row per cancellation*
  - measures: minutes_to_cancel
  - dimensions: dim_trips, dim_drivers, dim_riders, dim_cancellation_reason
- **fact_ride_requests** — grain: *one row per ride request
  (including unmet demand)*
  - measures: minutes_to_match, surge_at_request
  - dimensions: dim_riders, dim_cities, dim_date, dim_time_of_day

## Non-functional
- **Volume:** 10M trips/day, 1B GPS pings/day
- **Freshness:** hourly for finance, 5-min for surge
- **Retention:** 2y trips hot + cold archive, 90d GPS, 7y TLC
- **Hot partitions:** NYC and SF (handled with hash
  partitioning by city)

## Assumptions / open questions
- "Driver utilization" is the ratio definition, per
  interviewer
- Cancellations are a separate fact for funnel support
- Surge is a measure on `fact_trips`, not a dim
- NYC TLC reporting is the only immutable retention requirement
- Multi-currency: single currency for v1 (deferred)
```

---

## Step 5 — The grain commitment (1 minute)

> Candidate: "OK — to make sure I have this right: the primary
> fact table is `fact_trips` at the grain of **one row per
> completed trip**, with `fare`, `tip`, and `total_revenue` as
> the measures. `dim_cities` is SCD Type 2 because we need
> point-in-time lookups on rate cards. The high-cardinality
> GPS stream is *not* in `fact_trips` — it's a separate
> `fact_trip_events` table at the event grain, supporting
> 5-minute live-ops windows. Cancellations are a third fact
> table, with its own grain, supporting the funnel. Unmet
> demand is a fourth fact table, `fact_ride_requests`, so we
> can see requests that never matched. The latency tier is
> **hourly batch** for finance with a separate **5-minute
> live-ops** pipeline for surge pricing. Does that match what
> you had in mind?"

The interviewer confirms. The candidate has committed to:

1. **Primary grain:** one row per completed trip.
2. **Surge:** measure on the fact, not a separate dimension.
3. **GPS events:** separate fact table.
4. **Cancellations:** separate fact table.
5. **Unmet demand:** separate fact table (`fact_ride_requests`).
6. **City SCD:** Type 2.
7. **Latency tier:** hourly + 5-minute live-ops (two pipelines).

These seven decisions will drive the star schema in Module 03.

---

## What the candidate did right

- **Recognized the core problem** in one sentence before asking
  any questions.
- Asked **metric, query-pattern, latency, volume, and retention
  questions** — covering all five non-functional buckets from
  this module.
- **Made a defensible assumption** about unmet demand (a
  separate fact table) and said it out loud.
- **Wrote a comprehensive requirements doc** with all the
  required sections, including retention.
- **Repeated the grain** back to the interviewer, with named
  measures and named SCD choices.
- **Distinguished** the two latency tiers (hourly for finance,
  5-minute for live-ops) and committed to two pipelines, not
  one.

---

## What the candidate did *not* do

- Did not ask about **fraud signals** (fake rides, GPS spoofing)
  — could be a follow-up depth-dive.
- Did not ask about **payment systems** (which currency, which
  processor).
- Did not ask about **regulatory** beyond TLC (e.g., California
  CPUC, EU data residency).
- Did not draw the star schema yet — that's Module 03.

---

## Timing the full exercise

A senior candidate completes the full exercise (recognition +
discovery + doc + commitment) in **12–15 minutes**:

- Recognition: 30 seconds
- Discovery: 5 minutes
- Doc: 3 minutes
- Commitment: 1 minute
- Buffer: 2–5 minutes for follow-ups

If you can hit 15 minutes for a prompt you've never seen, your
discovery-to-design handoff is at interview fluency.

---

## Try it

Pick any product you don't know well. Run the full playbook:
recognize the core problem, ask 5–8 discovery questions across
metric / query-pattern / latency / volume / retention, write
the doc, and commit to a grain. Time yourself: 15 minutes.

Do this three times on three different products. By the third,
the structure will be automatic.

---

## In the interview, you would say...

> "Here's the full playbook I'm going to run: I'll recognize
> the core business problem in one sentence, ask 5–8 discovery
> questions covering metrics, query patterns, latency, volume,
> and retention, write a 30-line requirements doc, and commit
> to a grain. The whole thing takes 12–15 minutes for a prompt
> I've never seen, and it earns the highest-weighted bucket on
> the rubric."

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
