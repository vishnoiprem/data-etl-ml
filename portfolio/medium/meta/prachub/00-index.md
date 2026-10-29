# Meta Data Engineer — PracHub Question Bank

All questions from [PracHub's Meta Data Engineer page](https://prachub.com/companies/meta/positions/data-engineer?sort=hot), covered in depth using a **3-format template** for every question:

1. **Simple way to think** — plain-English mental model, no jargon dump
2. **Interview write-up** — what you'd actually say/write in the round (SQL, Python, prose, ASCII diagrams)
3. **Best optimized solution** — production-grade version with tradeoffs and a "Why it's optimal" section

---

## How to use this guide

Each file is a real study reference (300-900 words). Read the **Simple way to think** first to lock in the intuition, then drill the **Interview write-up** until you can reproduce it cold, then study the **Optimized** section to understand what a senior+ answer adds.

Recommended order if you're early in prep: **`01` → `03` → `05` → `04`** (build coding fluency, then system design, then behavioral, then analytics — analytics is mostly content once the rest is solid).

| Folder | Questions | Best interview round |
|---|---|---|
| `01-sql-coding/` | 13 | Phone screen SQL + onsite coding (SQL-only or SQL-dominant) |
| `02-python-coding/` | 11 | Onsite Python coding (Python-dominant or Python-only) |
| `03-system-design/` | 6 | Onsite system design (45 min) |
| `04-analytics-experimentation/` | 6 | Onsite product analytics / metrics |
| `05-behavioral/` | 5 | Onsite behavioral & leadership |

**Total: 41 question files.**

---

## 01 — SQL (13)

SQL-only and SQL-dominant coding problems. Almost every Meta DE loop has at least one SQL phone screen.

| # | File | Topic |
|---|---|---|
| 1 | [values-owned-only-by-selected-user.md](./01-sql-coding/values-owned-only-by-selected-user.md) | Set difference / NOT EXISTS |
| 2 | [aggregate-netflix-metrics.md](./01-sql-coding/aggregate-netflix-metrics.md) | Daily aggregation + cumulative window |
| 3 | [validate-carpool-capacity.md](./01-sql-coding/validate-carpool-capacity.md) | LeetCode 1094 — sweep line |
| 4 | [query-carpool-ride-metrics.md](./01-sql-coding/query-carpool-ride-metrics.md) | Ride-share metrics SQL |
| 5 | [optimize-sql-minimize-scans.md](./01-sql-coding/optimize-sql-minimize-scans.md) | CTE elimination, scan reduction |
| 6 | [reservation-diff-largest-member.md](./01-sql-coding/reservation-diff-largest-member.md) | Self-join + MAX trick |
| 7 | [customer-max-consecutive-weeks.md](./01-sql-coding/customer-max-consecutive-weeks.md) | Gaps-and-islands (weeks) |
| 8 | [count-renewal-pct-unreturned-good.md](./01-sql-coding/count-renewal-pct-unreturned-good.md) | Conditional aggregation |
| 9 | [library-analytics-sql.md](./01-sql-coding/library-analytics-sql.md) | Library ops metrics |
| 10 | [car-rental-utilization-by-city.md](./01-sql-coding/car-rental-utilization-by-city.md) | Multi-join analytics |
| 11 | [four-algorithmic-library-problems.md](./01-sql-coding/four-algorithmic-library-problems.md) | Greedy + sorting combo |
| 12 | [active-follow-connections.md](./01-sql-coding/active-follow-connections.md) | Temporal event log state |
| 13 | [queries-follows-and-bookings.md](./01-sql-coding/queries-follows-and-bookings.md) | Temporal logs + graph + intervals |

### High-priority SQL subset to drill first
The questions most-solved by other candidates on PracHub:
- #3 validate-carpool-capacity (97 solved)
- #5 optimize-sql-minimize-scans — directly tests Meta's "scale" bias
- #9 library-analytics-sql (50 solved) — easy warm-up
- #10 car-rental-utilization-by-city (199 solved) — high-signal SQL
- #13 queries-follows-and-bookings (192 solved) — covers intervals + graph

---

## 02 — Python (11)

Python-dominant and Python-only coding problems. Almost every Meta DE loop has at least one Python round.

| # | File | Topic |
|---|---|---|
| 1 | [library-system-sql-python.md](./02-python-coding/library-system-sql-python.md) | Library domain — multi-table SQL + Python |
| 2 | [compute-capacities-after-closures.md](./02-python-coding/compute-capacities-after-closures.md) | Nested dict traversal |
| 3 | [top-3-content-per-category.md](./02-python-coding/top-3-content-per-category.md) | Top-k per group (heap) |
| 4 | [sql-python-data-prep.md](./02-python-coding/sql-python-data-prep.md) | DAU/WAU/MAU, retention, funnels |
| 5 | [recommend-two-hop-follows.md](./02-python-coding/recommend-two-hop-follows.md) | Graph BFS, set difference |
| 6 | [python-sql-data-tasks.md](./02-python-coding/python-sql-data-tasks.md) | `flatten(nested)` + SQL aggregation |
| 7 | [recommend-friends-of-friends.md](./02-python-coding/recommend-friends-of-friends.md) | FoF recommendation |
| 8 | [check-carpool-trip-feasibility.md](./02-python-coding/check-carpool-trip-feasibility.md) | Sweep-line feasibility |
| 9 | [top-3-books-by-borrowed-time.md](./02-python-coding/top-3-books-by-borrowed-time.md) | Date diff aggregation |
| 10 | [library-sql-python-tasks.md](./02-python-coding/library-sql-python-tasks.md) | Library SQL + Python |
| 11 | [library-coding-tasks-python.md](./02-python-coding/library-coding-tasks-python.md) | Library Python only |

### High-priority Python subset to drill first
- #5 recommend-two-hop-follows — graph + set difference, classic DE pattern
- #6 python-sql-data-tasks — `flatten(nested)` is a phone-screen favorite
- #7 recommend-friends-of-friends — same pattern, different framing
- #3 top-3-content-per-category — heap-based top-k
- #8 check-carpool-trip-feasibility — sweep-line interval merge

---

## 03 — System design (6)

The 45-minute on-site design rounds. Spend the most prep time here.

| # | File | Topic |
|---|---|---|
| 1 | [dimensional-modeling-transactional.md](./03-system-design/dimensional-modeling-transactional.md) | Star schema, SCD2, near real-time |
| 2 | [batch-streaming-etl-architecture.md](./03-system-design/batch-streaming-etl-architecture.md) | Medallion, Kafka + Flink + Iceberg |
| 3 | [feed-content-shares-data-model.md](./03-system-design/feed-content-shares-data-model.md) | Polymorphic feed entities, sharding |
| 4 | [event-driven-metrics-schema.md](./03-system-design/event-driven-metrics-schema.md) | High-cardinality event analytics |
| 5 | [short-videos-reels-measurement.md](./03-system-design/short-videos-reels-measurement.md) | A/B test design, OEC, CUPED |
| 6 | [product-features-metrics-data-model.md](./03-system-design/product-features-metrics-data-model.md) | Metric pyramid + semantic layer |

**Drill order:** dimensional modeling → ETL architecture → feed data model → event schema → product metrics.

---

## 04 — Analytics & experimentation (6)

Product-sense / experimentation rounds. Often a 30-45 min case-style round.

| # | File | Topic |
|---|---|---|
| 1 | [01-streaming-metrics-visualization.md](./04-analytics-experimentation/01-streaming-metrics-visualization.md) | Monitoring vs. diagnosis dashboards |
| 2 | [02-private-account-product-metrics.md](./04-analytics-experimentation/02-private-account-product-metrics.md) | Metric diagnostics for a privacy feature |
| 3 | [03-short-form-video-feed-metrics.md](./04-analytics-experimentation/03-short-form-video-feed-metrics.md) | Engagement + creator metric |
| 4 | [04-netflix-metric-trend-visualization.md](./04-analytics-experimentation/04-netflix-metric-trend-visualization.md) | Trend + anomaly charts |
| 5 | [05-social-feed-success-metrics.md](./04-analytics-experimentation/05-social-feed-success-metrics.md) | North-star + guardrails |
| 6 | [06-game-monetization-metric-repair.md](./04-analytics-experimentation/06-game-monetization-metric-repair.md) | Data quality repair for a monetization report |

---

## 05 — Behavioral & leadership (5)

5 STAR stories to prepare — pre-write them, then rehearse out loud.

| # | File | Topic |
|---|---|---|
| 1 | [demonstrate-behavioral-competencies.md](./05-behavioral/demonstrate-behavioral-competencies.md) | Ownership / ambiguity / collaboration / prioritization |
| 2 | [de-behavioral-and-rampup-questions.md](./05-behavioral/de-behavioral-and-rampup-questions.md) | Tight deadline + ramp-up playbook |
| 3 | [project-impact-mentorship-credit.md](./05-behavioral/project-impact-mentorship-credit.md) | Mentoring + fair credit |
| 4 | [conflicts-deadlines-persuasion.md](./05-behavioral/conflicts-deadlines-persuasion.md) | Cross-functional conflict |
| 5 | [ownership-and-conflict-resolution.md](./05-behavioral/ownership-and-conflict-resolution.md) | 0→1 initiative + prioritization |

---

## Study plan

### Week 1 — Foundations
- Day 1-2: SQL warm-up — `01-sql-coding/09-library-analytics-sql.md`, `08-count-renewal-pct-unreturned-good.md`, `06-reservation-diff-largest-member.md`, `16-...-top-3-books` (easy → medium)
- Day 3-4: SQL core — `02-python-coding/04-sql-python-data-prep.md` (DAU/retention), `01-sql-coding/10-car-rental-utilization-by-city.md` (multi-join), `02-aggregate-netflix-metrics.md` (windows)
- Day 5: SQL intervals — `01-sql-coding/03-validate-carpool-capacity.md` or `02-python-coding/check-carpool-trip-feasibility.md` (pick one; same pattern)
- Day 6-7: Python graphs & top-k — `02-python-coding/05-recommend-two-hop-follows.md`, `07-recommend-friends-of-friends.md`, `03-top-3-content-per-category.md`

### Week 2 — System design
- Day 1: `03-system-design/dimensional-modeling-transactional.md`
- Day 2: `03-system-design/batch-streaming-etl-architecture.md`
- Day 3: `03-system-design/feed-content-shares-data-model.md` + `event-driven-metrics-schema.md`
- Day 4: `03-system-design/product-features-metrics-data-model.md` + `short-videos-reels-measurement.md`
- Day 5: Time yourself — pick any one and present it in 25 min

### Week 3 — Analytics + behavioral
- Day 1-2: Analytics — read all 6 files in `04-analytics-experimentation/`, focus on metric definitions and pitfalls
- Day 3-5: Write 5 STAR stories from `05-behavioral/`, time each at 3 minutes
- Day 6-7: Mock round with a friend (one of each: SQL, system design, behavioral)

### Final 2 days
- Re-read your optimized solutions
- Cold-write the SQL for `02-python-coding/04-sql-python-data-prep.md` and `01-sql-coding/10-car-rental-utilization-by-city.md` from memory
- Practice saying each STAR story in 2 minutes