# 50 Data Modeling Questions — Meta Data Engineer framing

Source: DataVidhya, *"50 Data Modeling Interview Questions for DEs (2026 Guide)"*.

This file re-answers all 50 for a **Meta DE (Product Analytics)** loop. The
article's answers are correct but generic; what Meta scores is different:

> **The number is not the answer. The grain, the trade-off, and what you'd check
> when the number moves — that's the answer.**

Per the repo README, the most-reported rejection pattern is the *silent SQL
savant*: correct work with no narration, graded "strong technically, no product
signal." So each entry below is written as **what to say**, not what to know.

**Format.** Each question gets: the answer in Meta terms → **Say:** the one
sentence that earns the signal → **Trap:** the specific way it goes wrong.
Questions with a runnable proof in this folder are marked ▶.

---

## How to answer ANY modeling question here

Five steps, in order. Say each one out loud:

1. **Restate the business process.** "So this is about attributing Reels watch
   time to creators." Not the tables — the process.
2. **State the grain as a sentence.** "One row per user per Reel per session."
   If you can't say it in a sentence, stop and ask questions.
3. **Name the dimensions**, and which are conformed.
4. **Name what changes over time** and pick an SCD type for each attribute —
   not for the whole table.
5. **Then** write DDL. Optimize (partition, cluster, broadcast) last.

Meta's stack is internal — Presto, Spark, Hive-style tables, Scuba. Don't
volunteer Snowflake/BigQuery specifics unless asked; translate to
"columnar warehouse" and move on.

---

# Core Concepts & Fundamentals

### 1. What is data modeling, and why does it matter?
Defining how data is structured, related, and *named* so that a metric means one
thing across the company. At Meta scale the failure isn't a slow query, it's
three teams shipping three definitions of "active user" and a VP getting three
numbers in one review.

**Say:** "Modeling is mostly a definitions problem. The schema is where you make
a definition enforceable instead of tribal."

**Trap:** Describing it as a one-time design phase. It's continuous — every new
surface (Reels, Threads) renegotiates the model.

### 2. What is an ER diagram, and when would you use one?
Entities, attributes, relationships. Most valuable for OLTP where referential
integrity is enforced; in a warehouse its main job is getting stakeholder
agreement on **cardinality** before anyone writes DDL.

**Say:** "I draw it to force the cardinality conversation early — that's the
decision that's expensive to reverse."

**Trap:** Presenting it as documentation. Its value is as a *pre-commitment
device*.

### 3. Conceptual vs logical vs physical model.
Conceptual: "Creator posts Reel." Logical: attributes, types, keys, engine-
agnostic. Physical: actual types, partitioning, clustering, file format.

**Say:** "The layers exist so the grain argument happens before the partitioning
argument. Jumping conceptual → physical is how you end up with a schema only
its author understands."

**Trap:** Treating them as academic. The real function is sequencing the
decisions by cost-to-reverse.

### 4. Normalization — 1NF, 2NF, 3NF.
1NF: atomic values, no repeating groups. 2NF: no partial dependency on part of a
composite key. 3NF: no transitive dependency.

**Say it with an example, always:** "In `fact_ad_spend`, storing
`advertiser_name` next to `advertiser_id` breaks 3NF — the name depends on the
advertiser, not on the spend event."

**Trap:** Reciting definitions with no example. Also: implying 3NF is the goal
in a warehouse. It's the goal in the *raw* layer.

### 5. When should you denormalize, and what are the risks?
When reads dominate writes — warehouse serving layer. Risk is inconsistency:
one attribute now lives in N places.

**Say:** "Normalize the source-of-truth layer, denormalize the serving layer.
Naming the layer is the whole answer — 'should we denormalize' is unanswerable
without it."

**Trap:** Denormalizing in staging. You lose the ability to restructure when
requirements change (see Q50).

### 6. Primary key vs surrogate key.
Natural key = business data (`email`, `order_number`). Surrogate = meaningless
generated id.

**Say:** "Surrogates, because natural keys change — accounts merge, handles get
reassigned. And they're required for SCD Type 2, since the natural key is no
longer unique once you have versions."

**Trap:** Only citing "integer joins are faster." True but minor. The SCD2 point
is the one that matters.

### 7. Foreign keys — why do warehouses skip enforcing them?
Enforcement costs a check on every write; most cloud warehouses accept the
declaration but don't enforce. They still document intent and can inform the
optimizer.

**Say:** "Declare for documentation, enforce upstream in the pipeline with a
referential-integrity test. Unenforced FKs mean orphan rows are a *data quality*
problem, not a database problem." ▶ `08_null_fk_unknown_member.py`

**Trap:** Assuming enforcement exists. Orphan facts are normal at scale — plan
for them.

### 8. Composite keys — when necessary?
When no single column is unique: `(order_id, line_number)`.

**Say:** "They appear naturally in fact tables as the combination of dimension
FKs — that combination *is* the grain. I avoid them in dimensions by using a
surrogate."

**Trap:** 4+ column composite keys. Verbose joins, easy to get wrong, and a sign
the grain is confused.

### 9. Candidate key vs alternate key.
Every uniquely-identifying column set is a candidate; the one you pick is
primary, the rest are alternate.

**Say:** "It's a reminder that primary key selection is a *choice* — and in a
warehouse I almost always choose a surrogate and leave the natural key as an
alternate, indexed for lookups."

**Trap:** Missing that this is a design-choice question, not a vocabulary one.

### 10. What does cardinality mean?
One-to-one, one-to-many, many-to-many between entities.

**Say:** "Cardinality determines grain, so getting it wrong is the most
expensive mistake available. Model a one-to-many as one-to-one and you drop
rows; model one-to-one as many-to-many and you inflate every aggregate. I ask
about cardinality before proposing a schema." ▶ `04_bridge_table_double_count.py`

**Trap:** Not asking. The *asking* is scored.

---

# Star Schema & Dimensional Modeling

### 11. What is a star schema?
Central fact, dimensions one hop away via FKs.

**Say:** "Default choice for a serving layer: one join from fact to any
dimension, and BI tools generate sane SQL against it. I'd need a specific reason
to do anything else."

**Trap:** Being unable to say why *not* snowflake (Q29).

### 12. Fact vs dimension table.
Facts: numeric, additive, one row per event. Dimensions: descriptive context.

**Say:** "Facts are skinny and long, dimensions wide and short. Meta example:
`fact_reel_view` holds watch_ms and a handful of keys; `dim_creator` holds
everything you'd ever describe a creator with."

**Trap:** Putting descriptive attributes in the fact "to avoid a join." At 40B
rows/day that's the expensive choice, not the cheap one. ▶ `05_junk_dimension.py`

### 13. What is grain, and why is it the most important decision? ▶
The level of detail in one fact row.

**Say — verbatim, before describing any fact table:** "The grain of this table
is one row per *X* per *Y* per *Z*." Then: "and here's the query that proves it."

```sql
SELECT ad_id, campaign_id, placement, event_date, COUNT(*)
FROM fact_ad_performance
GROUP BY 1,2,3,4 HAVING COUNT(*) > 1;
```

**Trap:** Never stating it. This is the #1 cause of inflated metrics, and the
grain check belongs in the pipeline as a *blocking test*, not a dashboard.
▶ `01_grain_violation_detection.py`

### 14. The three types of fact tables.
- **Transaction** — one row per event. `fact_reel_view`.
- **Periodic snapshot** — state at intervals. `fact_creator_followers_daily`.
- **Accumulating snapshot** — one row per process instance, updated through its
  lifecycle. `fact_ad_review` (submitted → in_review → approved).

**Say:** "Defaulting to transaction facts for everything is the mistake. 'What's
the current follower count' wants a periodic snapshot; 'how long does ad review
take' wants an accumulating one — and that's the only fact type you UPDATE."

**Trap:** Not knowing accumulating snapshots are mutable. That's their defining
property and it conflicts with append-only lake assumptions.

### 15. The Kimball approach.
Bottom-up: business-process-specific dimensional marts, tied together by
conformed dimensions.

**Say:** "Kimball for speed-to-value, which is almost always right — but it only
works if conformed dimensions are actually governed. Without that you get marts
that disagree, which is worse than being slow."

**Trap:** Presenting it as purely better than Inmon (Q48).

### 16. Conformed dimensions — why do they matter?
The same dimension, identically defined, shared across marts.

**Say:** "This is the governance question wearing a modeling costume. Without a
conformed `dim_user`, the Ads team counts 2.1B users and the Feed team counts
2.0B, and the disagreement surfaces in a leadership review. It needs an owner
and a change process, not just a shared table name."

**Trap:** Answering only mechanically. Name the ownership requirement.

### 17. What is a degenerate dimension?
A dimension key living in the fact with no dimension table — `order_number`,
`session_id`, `request_id`. It groups rows but has no attributes worth a table.

**Say:** "If the only attribute is the key itself, a dimension table adds a join
and no information."

**Trap:** Building `dim_session` with one column.

### 18. The role of a date dimension. ▶
Pre-computes `fiscal_quarter`, `is_holiday`, `day_of_week`, `week_number` once,
so fiscal-calendar logic isn't reimplemented in forty queries. ~7,300 rows for
20 years — always broadcasts.

**Say:** "It's the first dimension I build, and it's really a *definitions*
table. The moment fiscal quarter logic lives in queries instead of here, two
queries will disagree."

**Trap:** Storing raw dates and parsing at query time — you can't filter
`is_holiday` without reimplementing a holiday list.
▶ `06_role_playing_dimension.py`

### 19. Many-to-many in a star schema. ▶
A bridge table resolves it into two one-to-many relationships.

**Say:** "And the bridge *fans out the fact*, so I need a weighting factor or an
explicit 'this column doesn't total' caveat. A Reel with 3 hashtags triples its
views in a hashtag rollup."

Two valid fixes — name both: **allocate** (weight = 1/n, totals reconcile, use
for revenue) or **don't add** (report per-hashtag impact, state it isn't
summable). ▶ `04_bridge_table_double_count.py`

**Trap:** Describing the bridge and stopping. The double-count *is* the question.

### 20. What is a factless fact table? ▶
Dimension keys, no measures. Two kinds: **event tracking** (the measure is
`COUNT(*)`) and **coverage** (what *could* have happened).

**Say:** "Coverage is the interesting one — it's how you answer 'what did NOT
happen', which is unanswerable from events alone because absence leaves no row."
▶ `10_factless_coverage_fact.py`

**Trap:** Only giving the event-tracking type.

---

# SCDs & History Tracking

### 21. What are Slowly Changing Dimensions?
Patterns for handling attribute changes over time.

**Say:** "The decision is per-*attribute*, not per-table. On `dim_advertiser`,
`tier` needs Type 2 because revenue is attributed by the tier held at the time;
`last_login_at` is Type 1 because versioning it would create a row per login."

**Trap:** Picking one type for the whole dimension. That framing is the mistake.

### 22. SCD Type 1, 2, 3.
- **1** overwrite, no history.
- **2** new row per change + `effective_from` / `effective_to` / `is_current`.
- **3** a `previous_x` column holding exactly one prior value.

**Say:** "Type 2 by default. And the detail that matters: intervals are
`[from, to)` — half-open. With an inclusive end, a point-in-time join matches
two versions on the boundary date and silently doubles revenue."

**Trap:** Not mentioning the interval convention. It's the difference between
having built one and having read about one. ▶ `02_scd_type2_merge.py`

### 23. How do you implement SCD Type 2 in SQL? ▶
Two writes in one transaction: **expire** the open row for changed keys, then
**insert** the new version. Plus a third case: brand-new keys need only the
insert.

**Say:** "Detect change with a hash of the tracked columns, not an OR-chain —
with 30 attributes the OR-chain breaks silently the day someone adds column 31.
And both writes go in one MERGE, or a crash between them leaves a key with zero
or two current rows."

The production shape (Delta/Iceberg):
```sql
MERGE INTO dim_advertiser t USING staging s ON t.advertiser_id = s.advertiser_id
                                           AND t.is_current
WHEN MATCHED AND t.tracked_hash <> s.tracked_hash
  THEN UPDATE SET effective_to = current_date(), is_current = false
WHEN NOT MATCHED THEN INSERT (...) VALUES (...);
-- then insert the new versions for the keys just expired
```

**Trap:** Expiring and reinserting *every* incoming key. The dimension then
grows by its full size daily. ▶ `02_scd_type2_merge.py`

### 24. When Type 3 over Type 2?
When you need only the immediately-prior value of one attribute — a territory
reassignment where you want current-vs-previous for a transition period.

**Say:** "Rare in practice. It scales badly: tracking 5 attributes means 10
columns. I default to Type 2 unless storage or query complexity is a hard
constraint."

**Trap:** Over-selling it. Saying it's rare is the credible answer.

### 25. What is a mini-dimension? ▶
Extract rapidly-changing attributes from a huge dimension into a small separate
dimension with its own key. The fact carries both keys.

**Say:** "`dim_user` is ~3B rows. If `engagement_band` and `follower_band` are
recomputed weekly, Type 2 on the full dimension adds 3B rows a week. A
mini-dimension holds the *distinct band combinations* — a few dozen rows,
forever, independent of user count."

**Say also:** "Banding is what makes it work. Raw `follower_count` has billions
of distinct values, so the mini-dimension would be as big as the dimension."

**Trap:** Not knowing the fact needs both FKs, and that the profile key must be
stamped **at event time** — resolve it at query time and you've rebuilt Type 1.
▶ `11_mini_dimension.py`

### 26. Bridge tables and SCDs. ▶
When the many-to-many relationship *itself* changes over time, the bridge needs
effective/end dates — plus the weighting factor to prevent double-counting.

**Say:** "So it's a bridge with SCD2 semantics on the bridge rows, and a
point-in-time join through it. That's two places the boundary convention has to
be right."

**Trap:** Forgetting the weighting factor once dates are added.
▶ `04_bridge_table_double_count.py`

### 27. How do you handle late-arriving dimensions? ▶
Insert an **inferred member**: a placeholder row keyed on the real natural key,
flagged `is_inferred`, then UPDATE it in place when the real data lands.

**Say:** "Three options and I'd reject two. Dropping the fact loses revenue.
NULLing the FK loses it one step later at the join. Inferred member keeps the
row joinable today and resolvable tomorrow."

**Say the subtle part:** "When it resolves, `effective_from` must be **backdated
to the date the fact first appeared**, not today — otherwise every event between
arrival and resolution falls into a coverage gap and the point-in-time join
drops exactly the rows you were saving."

**Trap:** Conflating an inferred member with the Unknown (-1) member. `-1` is
shared and *unresolvable* — you no longer know which advertiser each fact meant.
▶ `07_late_arriving_dimension.py`

### 28. What is a Type 6 (hybrid) SCD? ▶
1 + 2 + 3. Type 2 rows for history, a Type 1 `current_x` column stamped on
**every** version, optionally a Type 3 `previous_x`.

**Say:** "It lets one join answer both questions — read `tier` for as-was
attribution, `current_tier` for as-is rollups — with no second dimension and no
self-join."

**Trap:** Stamping `current_x` only on the open row. The as-is query then breaks
on exactly the expired rows where it matters. ▶ `03_scd_type6_hybrid.py`

---

# Advanced Patterns

### 29. Snowflake vs star schema.
Snowflake normalizes dimensions into sub-dimensions.

**Say:** "Star by default. In a columnar engine storage is cheap and joins
aren't, so normalizing a dimension trades the cheap resource for the expensive
one. I'd snowflake only for a very large dimension with a deep redundant
hierarchy."

**Trap:** Citing storage savings as if storage were the constraint.

### 30. What is Data Vault modeling? ▶
Hubs (business keys), Links (relationships), Satellites (attributes + history).
Separates structure from content.

**Say:** "Vault layer, with a Kimball star projected on top for consumption.
Positioning matters — it's not *instead of* a star schema. Its win is that
onboarding a new source system is a new satellite, an additive change, rather
than an ALTER on a shared dimension. Its cost is real: a 5-table star becomes
15+ tables."

**Trap:** Proposing analysts query the vault directly. The same answer goes from
1 join to 4 joins plus a window. ▶ `12_data_vault_hub_link_sat.py`

### 31. Hub, Link, Satellite. ▶
Hub: business key + load metadata. Link: many-to-many between hubs. Satellite:
descriptive attributes with effective dates, hung off a hub or link.

**Say:** "Hubs and links are stable — business keys and relationships rarely
change. Satellites absorb all the volatility. And the keys are *hashes* of the
business key, so every table loads in parallel with no sequence lookups."

Example: `hub_advertiser`, `hub_campaign`, `link_advertiser_campaign`,
`sat_advertiser_details`.

**Trap:** Using a source system's surrogate as the hub key. Two platforms both
using `id = 1` collide — hash the business key *and the source* if the key is
only unique per source. ▶ `12_data_vault_hub_link_sat.py`

### 32. One Big Table (OBT) — when appropriate?
Pre-join everything into one wide denormalized table.

**Say:** "It's a *serving-layer* optimization, not a replacement for modeling in
the transformation layer. Works when reads dominate and dimension attributes are
stable; the cost is that changing one attribute rewrites every row referencing
it."

**Trap:** OBT in staging. See Q43 and Q50.

### 33. What is a junk dimension? ▶
Collapses several unrelated low-cardinality flags into one dimension whose rows
are the observed *combinations*.

**Say:** "`fact_ad_impression` carries six flags at 40B rows/day. A junk
dimension replaces six string columns with one int key, and keeps six tiny
dimension tables out of the star. 'Junk' describes the attributes, not the
quality."

**Trap:** Two things. Building the full Cartesian product instead of the observed
combinations; and putting a high-cardinality attribute in it — add `country` and
the combination count multiplies by 200. Also: assign the key
**deterministically** (or hash it), or a rebuild renumbers the dimension and
every historical fact row is mislabelled. ▶ `05_junk_dimension.py`

### 34. What is a role-playing dimension? ▶
One physical dimension referenced multiple times with different meanings —
`order_date_key`, `ship_date_key`, `delivery_date_key` all → `dim_date`.

**Say:** "One physical table, N views with role-prefixed column aliases. Without
the aliases you get three columns named `year` and `SELECT year` is ambiguous —
which either errors or silently resolves to the wrong role."

**Trap:** Forgetting optional roles are NULLable. `ship_date` is NULL for an
unshipped order, so an INNER JOIN on that role drops every pending order.
▶ `06_role_playing_dimension.py`

### 35. Factless fact for coverage analysis. ▶
Load the universe of what *could* happen, then anti-join against what did.

**Say:** "Which eligible tier-market combinations generated zero promoted views?
A GROUP BY over events can't answer it — zero-activity combinations aren't in
the result, and no HAVING recovers them because there's no row to filter."

```sql
SELECT e.creator_tier, e.market
FROM factless_promo_eligibility e
LEFT ANTI JOIN factless_promoted_view v USING (promo_id, creator_tier, market);
```

**Trap:** Building coverage as a blind Cartesian product. It invents
combinations that were never eligible and reports them as failures.
▶ `10_factless_coverage_fact.py`

### 36. How does the Activity Schema pattern work?
All user actions in one narrow table: `entity_id`, `activity_type`, `timestamp`,
JSON features. Self-join to build journeys and funnels.

**Say:** "Useful for event-driven product analytics where the event taxonomy
churns weekly — which is Meta-shaped. The cost is that every question becomes a
self-join on a very large table, so it's not a warehouse replacement."

**Trap:** Presenting it as strictly modern/better.

### 37. Wide tables vs normalized tables in a modern stack.
Wide: pre-joined, read-optimized. Normalized: minimal redundancy, write-safe.

**Say:** "Columnar engines only scan requested columns, so 200 columns doesn't
penalize a 5-column query. So: normalize in the transformation layer, materialize
wide at the serving layer. Thinking in layers beats picking a side."

**Trap:** Answering as an either/or.

### 38. How do you model semi-structured data (JSON, arrays)?
Flatten known fields into typed columns during transformation; keep raw JSON as
a fallback.

**Say:** "Relying on JSON path access in production dashboards is fragile — a
source schema change silently breaks downstream queries with no error. And
unnesting arrays into rows *changes the grain*, so that's a grain decision, not
a parsing decision."

**Trap:** Missing the grain implication of `explode`.

---

# Warehouse Design & Real-World Scenarios

### 39. OLTP vs OLAP.
OLTP: high-volume low-latency writes, normalized (3NF), row-oriented. OLAP:
read-heavy aggregate scans, denormalized (star), columnar.

**Say:** "The model follows the access pattern: 3NF minimizes write anomalies,
star minimizes join overhead. Same data, opposite optimization targets."

**Trap:** Listing technologies without connecting to *why the model differs*.

### 40. How does partitioning improve query performance?
Splits a table into segments, usually by date, so filters scan only relevant
partitions.

**Say:** "And the predicate has to stay **sargable**. `WHERE YEAR(event_date) =
2026` wraps the column in a function and kills pruning; `event_date >=
DATE'2026-01-01' AND event_date < DATE'2027-01-01'` prunes."

**Trap:** Over-partitioning. Partitioning by `user_id` makes millions of tiny
files and is slower than no partitioning. Moderate cardinality only.

### 41. Clustering / sort keys.
Physically orders data within partitions so the engine skips blocks that can't
match.

**Say:** "80/20 rule: partition on the time column, cluster on the most common
filter or join key. Snowflake calls it micro-partition pruning, Redshift calls
it sort keys, but it's the same idea."

**Trap:** Treating it as an alternative to partitioning rather than a complement.

### 42. Data lake vs warehouse vs lakehouse.
Lake: cheap raw object storage, no ACID/schema enforcement. Warehouse:
governed, optimized, expensive. Lakehouse: open formats on object storage plus
ACID, schema enforcement, SQL engines.

**Say:** "Delta Lake, Apache Iceberg, Apache Hudi are the three table formats
that make the lakehouse work — the enabling trick is a metadata/manifest layer
giving you atomic commits over immutable files."

**Trap:** Naming the categories but not the table formats.

### 43. Star schema or OBT for a new project?
Start star in the transformation layer, then decide the serving layer by
audience.

**Say:** "How many consumers, and how sophisticated? One analytics team using
dbt — star is fine. Fifty self-serve Looker users where every extra join
produces a wrong number — materialize an OBT *fed by* the star. It's not
either/or."

**Trap:** Picking a side. The layered answer is stronger.

### 44. How do you handle NULLs in dimension tables? ▶
Never leave a NULL FK in a fact. Add an **Unknown** member (`-1`) per dimension
and point NULL FKs at it.

**Say:** "Two payoffs: every fact row joins so counts reconcile against the raw
event count, and 'Unknown' becomes an explicit filterable category. I'd also
distinguish `-1` Unknown from `-2` Not Applicable — 'we don't know the user' and
'there is no user' are different facts analysts will ask about."

**Say the part people miss:** "A LEFT JOIN isn't the fix. It keeps the row but
NULLs the attributes, and then `WHERE country <> 'US'` excludes it — because
`NULL <> 'US'` is NULL, not true. The rows survive the join and disappear at the
filter." ▶ `08_null_fk_unknown_member.py`

**Trap:** Thinking LEFT JOIN solves it.

### 45. Write a SQL query to identify grain violations. ▶
```sql
SELECT ad_id, campaign_id, placement, event_date, COUNT(*) AS row_count
FROM fact_ad_performance
GROUP BY 1,2,3,4
HAVING COUNT(*) > 1
ORDER BY row_count DESC
LIMIT 20;
```

**Say:** "And I'd classify the duplicates, because two kinds need different
fixes: identical rows mean a re-run appended twice (dedup); rows with *differing
measures* mean a join fanned out (fix the join). `COUNT(DISTINCT spend)` per key
separates them."

**Say:** "Then report blast radius, not row count — '142 keys overstating revenue
by $2.1M, all from placement=Reels after the Nov 3 backfill' is actionable."

**Trap:** Offering the query but not the classification or the impact.
Also: a NULL in a grain column makes this check *pass* while the dimension join
still drops the row. ▶ `01_grain_violation_detection.py`

### 46. Materialized view vs table?
MV: precomputed result, auto/scheduled refresh. Table: refreshed by your
pipeline, full control over timing.

**Say:** "MV when the aggregation is expensive, frequent, and the source changes
infrequently. A pipeline-managed table when refresh timing has to coordinate
with upstream SLAs — which in practice is most of the time, because 'refreshes
automatically' and 'refreshes after the upstream partition lands' aren't the
same thing."

**Trap:** Not raising the dependency/timing issue.

### 47. How do you model a multi-currency fact table? ▶
Store `local_amount` + `currency_code` + the rate **on the transaction date**;
derive the converted amount.

**Say:** "Never store only the converted amount — rates get restated and you
lose the ability to re-derive. And the rate dimension is snapshotted, one row per
currency per day, which is what makes closed periods *stable*. A single 'current'
rate means last quarter's revenue changes overnight and finance stops trusting
the warehouse."

```sql
SELECT f.revenue_id, f.local_amount, f.currency_code,
       ROUND(f.local_amount * er.rate_to_usd, 2) AS usd_amount
FROM fact_ad_revenue f
JOIN dim_exchange_rate er
  ON er.currency_code = f.currency_code
 AND er.rate_date     = f.revenue_date;   -- BOTH, or the fact fans out
```

**Trap:** Joining on currency alone (fans out to one row per rate-day), and
missing rates on weekends — `SUM` skips the resulting NULLs, so the USD total
under-reports while the local total is right. Forward-fill the rate dimension.
▶ `09_multi_currency_fact.py`

### 48. Inmon vs Kimball.
Inmon: top-down normalized EDW, then derive marts. Kimball: bottom-up
dimensional marts, conformed via shared dimensions.

**Say:** "Kimball for speed-to-value in most projects; Inmon where a single
canonical model is non-negotiable — heavily regulated industries. And note the
modern hybrid: Data Vault raw layer with Kimball marts on top gets you Inmon's
auditability with Kimball's consumption model."

**Trap:** Not knowing the hybrid, which is what most large orgs actually run.

### 49. Design a schema for an e-commerce company from scratch.
Walk the methodology — the process is what's scored:

1. **Business processes** → fact tables: orders, shipments, returns, inventory.
2. **Grain, stated** → `fact_order_line`: one row per order per product.
3. **Dimensions** → `dim_customer`, `dim_product`, `dim_date`, `dim_store`;
   conformed from day one.
4. **What changes** → SCD2 on `dim_customer` address/segment; Type 1 on
   `last_login`.
5. **Physical** → partition facts by `order_date`; cluster by `customer_id` or
   `product_id` per the dominant query pattern.
6. **Edges** → Unknown members for NULL FKs; role-playing `dim_date` for
   order/ship/delivery; multi-currency if international.

**Say:** "Returns are the interesting one — I'd model them as a separate fact
rather than negative rows in orders, so 'gross vs net' is a join choice rather
than a filter everyone has to remember."

**Trap:** Jumping to DDL. Interviewers care about the sequence.

### 50. Most common data modeling mistakes in production.
1. **Undefined grain** → duplicates, inflated metrics. ▶ `01_`
2. **Skipping conformed dimensions** → two customer counts, one leadership
   review, no trust.
3. **Premature denormalization** → OBT in staging, impossible to restructure.
4. **NULL FKs in fact-to-dimension joins** → silent row loss. ▶ `08_`
5. **Bridge tables without weighting** → aggregates inflated by fan-out. ▶ `04_`
6. **Defaulting to SCD Type 1** → the point-in-time question arrives six months
   later and the data is gone.

**Say:** "Name one you personally caught and fixed, with the number." That's
what makes this answer land instead of sounding like a listicle.

---

## Runnable proofs in this folder

Each file is self-contained and self-asserting — every claim above that's marked
▶ is verified by code, including the failure modes:

| File | Question(s) | Proves |
|---|---|---|
| `01_grain_violation_detection.py` | 13, 45 | duplicate classification, blast radius, NULL-grain blind spot |
| `02_scd_type2_merge.py` | 22, 23 | expire+insert upsert, hash change detection, boundary double-count |
| `03_scd_type6_hybrid.py` | 28 | 1+2+3 in one table, as-was vs as-is from one join |
| `04_bridge_table_double_count.py` | 10, 19, 26 | 2.33x inflation, weighted allocation, unbridged facts |
| `05_junk_dimension.py` | 12, 33 | 6 cols → 1 key, cardinality blowup, rebuild renumbering |
| `06_role_playing_dimension.py` | 18, 34 | 3 roles over 1 table, ambiguity error, NULL-role drop |
| `07_late_arriving_dimension.py` | 27 | inferred member, in-place resolution, backdating trap |
| `08_null_fk_unknown_member.py` | 7, 44 | silent 38% loss, `NULL <> 'US'`, Unknown vs Not Applicable |
| `09_multi_currency_fact.py` | 47 | snapshotted rates, restated history, fan-out, forward fill |
| `10_factless_coverage_fact.py` | 20, 35 | anti-join coverage, why GROUP BY can't answer it |
| `11_mini_dimension.py` | 25 | 12 rows vs 156B, banding, stamp-at-event-time |
| `12_data_vault_hub_link_sat.py` | 30, 31 | hub/link/sat, audit trail, 4 joins vs 1, key collision |
| `13_product_funnel_star_schema.py` | 13, 14, 21, 49 | full star schema for the *Product Funnel & Conversion Analytics* design question |

```bash
cd 13_Data_Modeling_Meta
../../../../.env/bin/python 01_grain_violation_detection.py
```

## The end-to-end design question

`13_product_funnel_star_schema.py` is the one full schema-design exercise:
DataVidhya's **Product Funnel & Conversion Analytics**. It takes the 6 given
OLTP tables (`User_Events`, `Purchases`, `Users`, `Products`, `AB_Tests`,
`Sessions`) and builds the complete model — two facts plus four dimensions —
then answers all six of the product team's questions and asserts every trap.

**The answer to "why two fact tables":**

| | grain | role |
|---|---|---|
| `fact_funnel_event` | one row per user per session per stage **occurrence** | source of truth; stages repeat, so it must be event-grain |
| `fact_session_funnel` | one row per **session** | accumulating snapshot; one timestamp column per milestone |

The accumulating snapshot is what makes the funnel cheap: *"how many reached
checkout"* becomes `COUNT(checkout_ts IS NOT NULL)` and *"time from view to
purchase"* becomes a subtraction, instead of a self-join per question. Naming
that fact type is the signal — it's the one candidates forget exists.

**What the file proves, beyond the happy path:**

- **Loose vs strict funnels give different curves.** Loose counting produces
  *negative* drop-off (a stage exceeding its predecessor); strict requires the
  full ordered chain. One user purchases with no `add_to_cart` — counted under
  loose, excluded under strict. Ask which the team means.
- **The strict chain must be cumulative.** Checking only the immediate
  predecessor lets that user rejoin the funnel at purchase, so the curve rises
  again at the end. Both formulations are asserted side by side.
- **Distinct users, not events.** `view_product` has 5 events from 3 people.
- **SCD2 point-in-time vs `is_current`.** Joining on `is_current` relabels a
  January purchase as `vip` and flatters the vip cohort — survivorship.
- **`purchase_amount` is NULL for non-purchases**, so AOV is 299.00 over
  purchasers but 119.60 spread over all sessions. State the denominator.
- **The 24h session rule is validated, not assumed** — re-derived with
  gap-and-island and reconciled against the source `session_id`.
- **A/B assignment is per user, not per session.** Deriving it per session
  would let one user see two variants and invalidate the test.

## Related folders

- `07_Star_Schema_Modeling/` — Marketplace, News Feed, Reels schemas (DDL + reasoning)
- `08_SCD_Types/` — Type 1/2/3 derived from a change log via `LEAD` (the batch
  rebuild path; `02_scd_type2_merge.py` here is the incremental upsert path)
- `12_DataVidhya_Meta_Set/` — all 76 Meta-tagged SQL problems
