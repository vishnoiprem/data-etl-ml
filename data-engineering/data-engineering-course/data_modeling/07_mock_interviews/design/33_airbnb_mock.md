# Lesson 33 — Design a Data Warehouse Schema for Airbnb

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the *search-event grain* trap
> and the *geo-hierarchy dimension*.

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## Why this lesson

Airbnb is a *two-sided marketplace* with one of the
highest-volume event streams in consumer tech: every
search a guest runs, every map pan, every listing
view, every message between host and guest is an
event. The interviewer is testing whether you can
resist the temptation to model *listings* (the
obvious, low-volume subject) instead of *search
behavior* (the actual analytical subject). A strong
candidate walks in knowing that search-to-booking
conversion lives in a *funnel* fact, not in a single
listing row, and that the geo hierarchy (country →
state → city → neighborhood) is its own dimension
because every query filters on it.

---

## The prompt

> Design a data warehouse for Airbnb. 200M listings,
> 5B search events, 100M bookings, 50M reviews,
> hosts and guests. Analytics needs: host LTV,
> demand forecasting, search-to-booking conversion,
> review sentiment, listing performance.

---

## Step 1: Requirements gathering

Five clarifying questions:

1. **What is a "search event"?** A user types
   "Paris" in the search box, sees 200 results, and
   clicks on listing #1. Is that *one* search event
   or *three* (one for the search, one for each
   result impression, one for the click)? I assume
   one *search* row plus N *impressions* and a
   separate *click* — three fact tables.
2. **What is a "booking"?** A confirmed reservation
   with a check-in date and check-out date, or any
   "book" click (including cancellations)? I assume
   the confirmed, non-cancelled booking, with
   cancellations tracked separately.
3. **Host LTV** — over what window? LTV is
   lifetime *value*, which requires defining a
   lifetime (cumulative bookings × payout over 5
   years?) and a value (gross booking value, net
   payout, or platform take rate?).
4. **Geo hierarchy** — country, state, city,
   neighborhood. Are neighborhoods owned by Airbnb
   (curated) or by the city (open data)? And do
   neighborhood boundaries change?
5. **Review sentiment** — text reviews with a 1-to-5
   rating? Or a separate NLP-derived sentiment score
   computed at ETL time? The latter is a measure on
   the fact, not a separate dim.

---

## Step 2: High-level architecture

Four fact tables:

```mermaid
fact_search_events  (grain: 1 row per search)
   ├── search_key         (PK)
   ├── guest_key          → dim_guest
   ├── search_date_key    → dim_date
   ├── search_time_key    → dim_time
   ├── origin_location_key → dim_location
   ├── destination_location_key → dim_location
   ├── checkin_date_key   → dim_date
   ├── checkout_date_key  → dim_date
   ├── num_guests         (INT)
   ├── num_results        (INT)
   ├── filters_json       (TEXT, degenerate)
   └── search_ts          (TIMESTAMP)

fact_search_impressions (grain: 1 row per listing shown)
   ├── impression_key     (PK)
   ├── search_key         → fact_search_events
   ├── listing_key        → dim_listing
   ├── position           (INT, 1..N)
   ├── price_shown_cents  (BIGINT)
   └── was_clicked        (BOOLEAN)

fact_bookings  (grain: 1 row per booking)
   ├── booking_key        (PK)
   ├── listing_key        → dim_listing
   ├── guest_key          → dim_guest
   ├── host_key           → dim_host
   ├── book_date_key      → dim_date
   ├── checkin_date_key   → dim_date
   ├── checkout_date_key  → dim_date
   ├── cancel_date_key    → dim_date (NULL if active)
   ├── nights             (INT)
   ├── guests             (INT)
   ├── nightly_price_cents (BIGINT)
   ├── cleaning_fee_cents (BIGINT)
   ├── total_payout_cents (BIGINT, to host)
   ├── platform_fee_cents (BIGINT, Airbnb take)
   └── currency_code      (TEXT, degenerate)

fact_reviews  (grain: 1 row per review)
   ├── review_key         (PK)
   ├── booking_key        → fact_bookings
   ├── listing_key        → dim_listing
   ├── guest_key          → dim_guest
   ├── review_date_key    → dim_date
   ├── rating_overall     (INT, 1-5)
   ├── rating_cleanliness (INT, 1-5)
   ├── rating_accuracy    (INT, 1-5)
   ├── rating_communication (INT, 1-5)
   ├── rating_location    (INT, 1-5)
   ├── rating_checkin     (INT, 1-5)
   ├── rating_value       (INT, 1-5)
   └── sentiment_score    (REAL, NLP-derived)
```

Dimensions:

- `dim_listing` — SCD 2. listing_id, host_key, title,
  property_type, room_type, accommodates, bedrooms,
  bathrooms, base_price_cents, cleaning_fee_cents,
  min_nights, max_nights, instant_bookable, is_active.
- `dim_host` — SCD 2. host_id, name, signup_date,
  country, response_rate, response_time_hours,
  is_superhost, total_listings.
- `dim_guest` — SCD 1 (or 2 if segment matters).
  guest_id, name, signup_date, country, language,
  total_bookings.
- `dim_location` — *one dim with a hierarchy*.
  location_key, country, state, city, neighborhood,
  lat, lon, geo_hash, parent_location_key. See §3.3
  for why one dim with hierarchy beats four.
- `dim_date` — conformed. role-played for book /
  checkin / checkout / cancel.
- `dim_time` — minute grain, for search event
  time-of-day analysis.

---

## Step 3: The 3 hardest parts

### 3.1 Search-event grain

This is the *defining* modeling choice. A "search" is
not a single event — it is a *funnel*:

```
search (1 row)
  ├── impression of listing A
  ├── impression of listing B
  ├── impression of listing C
  └── click on listing B → booking
```

If you model "one row per search", you lose the
impressions and the click. If you model "one row per
impression", you lose the search context (filters,
guest count, destination). The right answer is
**three** fact tables:

1. `fact_search_events` — one row per search. Holds
   the search-level context (filters, num_guests,
   checkin, checkout, destination). The `search_key`
   is the parent.
2. `fact_search_impressions` — one row per listing
   *shown* in the search results. Joins back to
   `fact_search_events` on `search_key`. Holds
   `position`, `price_shown_cents`, `was_clicked`.
3. `fact_bookings` — one row per confirmed booking.
   Joins back to `fact_search_events` on the
   originating search, if known (via a
   `referrer_search_key` column).

The conversion rate is then a *join* between these
three facts. The query for "search-to-booking
conversion for searches originating in Paris":

```sql
SELECT
  100.0 * COUNT(DISTINCT b.booking_key) /
         COUNT(DISTINCT s.search_key) AS conversion_pct
FROM fact_search_events s
JOIN dim_location l ON s.destination_location_key = l.location_key
LEFT JOIN fact_bookings b
  ON b.referrer_search_key = s.search_key
WHERE l.city = 'Paris'
  AND s.search_date_key BETWEEN 20240101 AND 20240131;
```

### 3.2 Host LTV calculation

"Host LTV" is a *derived* measure, not a stored
column. The definition: cumulative platform fees
paid by a host, over their lifetime on the platform,
discounted to net present value.

The calculation requires:

1. **Cumulative bookings per host** — running sum of
   `platform_fee_cents` over `fact_bookings` joined
   to `dim_host`, partitioned by `host_key` and
   ordered by `book_date_key`.
2. **Survival curve** — what fraction of hosts are
   still active after 1, 2, 3 years? Computed from
   `dim_host` (active = `last_booking_date > now -
   365d`) and the host's `signup_date`.
3. **Discount rate** — typically 10% per year for
   consumer-marketplace LTV.

The query is *not* a real-time warehouse query. It
is a batch job that runs monthly and writes the
result to `agg_host_ltv_monthly`, grain = one row
per (host, month), with `cumulative_payout_cents`,
`cumulative_bookings`, and `ltv_24m_estimate_cents`
(24-month forward LTV using the survival curve).

The interview question "how would you model host
LTV?" is testing whether you know it is a *batch
aggregate*, not a fact-table measure. Strong
candidates say: "I'd compute it offline, store the
result, and refresh monthly."

### 3.3 Geo-hierarchy dimension

A listing's location is *four* levels: country,
state, city, neighborhood. There are two design
choices:

- **Four separate dims** — `dim_country`, `dim_state`,
  `dim_city`, `dim_neighborhood`, each joined to the
  fact by FK.
- **One dim with hierarchy** — `dim_location` with
  `country`, `state`, `city`, `neighborhood` columns
  and a self-referencing `parent_location_key`.

The single dim wins. Reasons:

1. **The hierarchy is fixed at write time.** A
   neighborhood belongs to a city belongs to a state
   belongs to a country. There is no "what if the
   neighborhood changes country?" question.
2. **Analysts always want all four levels.** A
   report never asks "give me city revenue" without
   also showing the country. A single dim makes that
   one join.
3. **Renaming a city is one UPDATE.** With four
   dims, you'd have to update the city row *and* any
   parent-state relations.

```sql
CREATE TABLE dim_location (
  location_key         INTEGER PRIMARY KEY,
  country              TEXT NOT NULL,
  state                TEXT,
  city                 TEXT,
  neighborhood         TEXT,
  lat                  REAL,
  lon                  REAL,
  geo_hash             TEXT,
  parent_location_key  INTEGER REFERENCES dim_location(location_key)
);
```

A neighborhood row has `parent_location_key` pointing
to its city. The city has `parent_location_key`
pointing to its state. The state points to the
country (which has `parent_location_key` NULL).

The trade-off: a "roll-up" query (revenue by country)
still scans the full fact and joins to the full dim —
which is fine because the dim is small (~500K rows)
and the fact is already partitioned by date.

---

## Step 4: Common failure modes

1. **One row per search, no impressions.** The
   candidate forgets that "search" is a funnel.
   This loses the position-bias analysis
   (listings at position 1 get 80% of clicks) and
   the click-through rate by listing.
2. **Storing `rating` on `dim_listing`.** The
   listing's *current* rating is a denormalization
   that goes stale the moment a new review arrives.
   `rating` lives on `fact_reviews` and the
   "current" rating is a window function:
   `AVG(rating_overall) OVER (PARTITION BY
   listing_key ORDER BY review_date_key ROWS
   UNBOUNDED PRECEDING)`.
3. **Float for money.** Use `BIGINT` cents. Float
   accumulates rounding errors that show up in
   finance audits.
4. **No `referrer_search_key` on the booking.** A
   booking that came from a search is a *converted*
   search. Without the link, conversion analysis is
   impossible.
5. **Treating LTV as a real-time measure.** LTV is a
   batch aggregate. The interview answer is "I'd
   compute it offline and store the result."

---

## Step 5: Scoring against the rubric

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about search grain, booking definition, LTV window, geo hierarchy, sentiment. |
| **Picks a grain** | 5/5 | Three facts for the search funnel, plus bookings and reviews. Defended each. |
| **Makes and defends tradeoffs** | 5/5 | Search funnel as three facts, LTV as batch, single geo dim with hierarchy. |
| **Talks while drawing** | 5/5 | Narrated every dim, every FK, every measure. |

---

## In the interview, you would say...

> "The defining modeling choice is that *search* is
> a funnel, not an event. The right answer is three
> facts: `fact_search_events` (the search context),
> `fact_search_impressions` (one row per listing
> shown, with `position` and `was_clicked`), and
> `fact_bookings` (with a `referrer_search_key`
> back to the originating search). Conversion is a
> join between the three. Host LTV is a batch
> aggregate, not a stored measure — I'd compute it
> monthly and write to an `agg_host_ltv_monthly`
> rollup. Geo is a single dimension with a hierarchy
> column, not four separate dims, because the
> hierarchy is fixed and analysts always want all
> four levels at once."

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
