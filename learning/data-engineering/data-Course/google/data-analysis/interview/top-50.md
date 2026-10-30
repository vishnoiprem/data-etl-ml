# Top 50 — Semantic Layers, BI & Data Quality

> **50 questions · The highest-yield subset · Read this the night before**

These fifty questions were selected from the full bank by five criteria:
**high decision impact** (the answer changes what you build), **cross-layer**
(the answer connects the grain to the measures to the operations),
**quantifiable** (a number is attached), **contested** (reasonable senior
engineers disagree), and **common misconception** (the wrong answer is what a
lot of people say).

Every answer is written the way a senior engineer who has actually run this
in production would say it out loud: the direct answer first, then the
mechanism, then when the obvious alternative wins, then the failure you have
seen, and the numbers.

---

## The model

### 1. What is a semantic layer, and what does it actually buy you?

A shared, machine-readable definition of the metrics an organisation reports
on — the measures, the dimensions, the joins, and the grain of every table.

It does **not** make numbers correct. It makes them **the same number**, and
that is the property that was missing. A BI tool without one is a consumer
tool: every author defines their own calculated fields, their own joins, their
own filters. Two reports about revenue are two unrelated implementations that
eventually disagree.

**Failure story:** a retailer ran a Looker Studio dashboard for gross revenue
and a finance spreadsheet for net revenue. For seven months both were
presented in planning meetings, both labelled "revenue". The gap was the
discount rate — about 4%. The discovery was not a bug fix; it was a
re-baselining of two years of forecasts.

### 2. What is the grain, and why is it the most important sentence about a table?

The answer to "one row per what?" — and the most consequential property a
table has.

For this course's `orders` table, one row per **order line**. That single
sentence determines that `line_id` is the primary key and `order_id` is not;
that `SUM(total_amount)` rolls up correctly; that `COUNT(*)` counts lines
(901) and not orders (450); and that `orders → customers` is safe while
`customers → orders` fans out.

**Failure story:** a "revenue by customer" report summed a customer-level
`lifetime_value` over a join to the order-line table. The join was
cardinality-legal, the SQL was correct, and the number was wrong by a factor
of the average lines-per-order — 7.45 in this dataset.

### 3. What is additivity, and how do you check it?

Whether a measure can be summed over a finer breakdown and still equal the
coarser value. Three kinds: **additive** (`SUM`), **non-additive**
(`COUNT_DISTINCT`, `AVG`), and **ratio** (`SUM(n)/SUM(d)`) — which looks
additive and is not.

The check is one comparison: compute the measure coarse, compute it fine, sum
the fine numbers, compare.

**The number:** `distinct_orders` here sums to **799** across the four
regions (191 + 193 + 219 + 196) against a true global total of **450** — a
**77.6%** inflation, visible only if you put the two numbers side by side.

### 4. Why must a ratio be `SUM(numerator) / SUM(denominator)`?

Because the average-of-ratios weights every **row** equally while the correct
ratio weights every **unit of denominator** equally. Small-denominator rows —
refunds, near-zero-margin items — get too much say, so the naive answer is
**always low**.

Two rows: £900/£810 and £100/£10. Correct = `820/1000 = 0.82`. Naive =
`(0.9 + 0.1)/2 = 0.50`. A **32-point** error.

**Failure story:** a Looker Studio dashboard reported margin as 49% when
it was 52%. Three points on £1.1M is about £34,000 a year of mis-stated
profitability — and it survived because the number was still plausible.

### 5. What is fan-out, and how do you detect it?

Row multiplication when a join matches more than one row on the far side. It
happens when you traverse **from the "one" side to the "many" side**.

Detect it by comparing the measure with and without the join. If they differ,
the join changed the number.

**Failure story:** a company added a customer-attributes table with two rows
per customer. Revenue went from £1,128,941.37 to £2,257,882.74 overnight. It
took three weeks to find, because "revenue doubled" is the most welcome
possible message and nobody interrogates good news.

### 6. What is grain mismatch, and why is it harder to catch than fan-out?

A wrong number from a join that does **not** fan out. The rows are correct;
the **measure** is counted at the wrong level.

The rule: never aggregate a measure at a grain coarser than the grain you
are joining at.

**Why it's harder:** there is no row multiplication to notice. A team
summing customer-grain `lifetime_value` over a line-grain join kept the
customer count at 121 — the join looked perfectly safe — while the top-10
list became entirely the highest-frequency buyers, whose revenue *per order*
was below average.

### 7. What are the four join cardinalities, and which can fan out?

`one_to_one`, `many_to_one`, `one_to_many`, `many_to_many`. Fan-out is
possible from the "one" side of `one_to_many` and `many_to_many`; it is
impossible from the "many" side of `many_to_one`.

**The direction is the whole decision.** `orders → customers` is
`many_to_one` and safe. `customers → orders` is `one_to_many` and fans out.
Same tables, same keys, opposite outcomes.

Modern tools make you declare the relationship (`relationship:` in LookML,
entity roles in dbt) **and use it to rewrite the join** so it cannot fan out.
That declaration is a constraint, not documentation.

### 8. What is the difference between `count` and `count_distinct`?

`COUNT(*)` counts rows; `COUNT(DISTINCT key)` counts unique keys. On a fact
table at line grain, 901 versus 450 here.

The trap is not that `count` is wrong — it is that `count` is *correct for
its grain* and silently wrong for the question asked. The fix is naming:
`order_line_count` versus `order_count` versus `distinct_orders`. A measure
named `count` tells the author nothing.

**Failure story:** a weekly "orders" metric built on `COUNT(*)` over an
order-line fact was 2.0x the truth for a year. It only ever went up, so
nobody reconciled it against the warehouse's separate order count — which was
on a different dashboard and therefore never on the same screen.

### 9. What is a date spine, and what breaks without it?

A generated calendar — one row per day — left-joined to the facts so days
with no activity become explicit **zeros**.

Without it, a time series shows only the periods that had data. A slow week
looks like a cliff, because the empty days are not on the chart at all. The
chart is not misrepresenting a value; it is **omitting a row**.

Two details: `LEFT JOIN`, not `INNER JOIN` (an inner join throws away the
rows you built the spine for), and `COALESCE` the measures to zero (without
it the gap is `NULL`, and a chart renders `NULL` as a gap).

**Failure story:** a subscription company's daily-signups chart showed a
smooth upward trend through nine days when signups were actually zero — the
tracking SDK had broken. Gaps are invisible when only dates-with-data are
plotted.

### 10. Why do date filter bounds have to be computed before truncation?

Because truncation moves the bounds. Truncating the *end* of a March filter
to the month turns 31 March into 1 March, and the filter silently loses 30
days.

And the validation has to come first: comparing *truncated* start against
*truncated* end can mask an inverted range, because 31 March and 1 March both
truncate to 1 March and look valid. An inverted filter must **raise**, not
swap — a silently-swapped filter returns a plausible number for the wrong
period.

### 11. What is a timeframe, and what convention should you pick?

A truncation of a date to a reporting grain: raw → day → week → month →
quarter → year.

The convention that matters: **ISO weeks start on Monday**. `2026-03-15`
truncates to week `2026-03-09`. Under the US convention it would be
`2026-03-08`. A weekly number that silently changes definition between two
dashboards cannot be reconciled — which is worse than a number that is
consistently wrong, because it at least can be compared.

Decide it, write it in the model's description, put it in the runbook.

### 12. What is the difference between Looker Studio, Looker and dbt?

Three tools, three layers.

- **Looker Studio** — consumer BI. No shared semantic layer: every author
  defines their own calculated fields and joins.
- **Looker** — a semantic layer plus exploration. Definitions live in
  LookML, versioned and reviewed. Needs a licence and git discipline.
- **dbt** — a transformation framework. Where the tables and their tests are
  built; its semantic layer now covers metric definitions too.

The recommendation: dbt to build and test the tables, LookML to define the
metrics, Looker Studio only for dashboards that genuinely need a consumer
UI. The failure is using Looker Studio for the *metrics*, because that is
the one configuration where the definitions cannot be reviewed.

### 13. What is a LookML reference, and why is it a build-time safety net?

A field reference into another view — `${customers.customer_segment}` —
resolved when the model is compiled. A reference to a non-existent field is
a **build error**, not a runtime error.

That distinction is the whole value: a runtime error means the mistake
reaches a dashboard and a user sees it; a build error means it never leaves
the repository and the person who made it is told immediately.

**Failure story:** a shared LookML file for "common dimensions" had
`${common.customer_tier}` referenced from eight views. Someone renamed the
field. In a query-time-resolution tool, eight dashboards would fail at 9am on
Monday, one report author at a time. In Looker, the model failed to compile
on Friday.

The reason to reproduce the check locally: `lookml-validate` needs a Looker
instance and a licence. As a unit test it takes a quarter of a second with
no credentials.

### 14. What must a measure's description contain?

Four questions: **what is it**, **what grain is it over**, **what does it
exclude**, and **how does it behave when rolled up**.

It is a guard rail, not documentation. "Margin over revenue" permits every
mistake while appearing to be documentation. "Margin over revenue. The
denominator is total_amount — the SUM of both, never the average of per-row
margins" prevents the specific one.

**Failure story:** a `conversion_rate` measure with the description
"Conversion rate." Eleven dashboards used it; three used it over a fan-out
join to a campaign table, and the rate exceeded 100% on the
highest-touch campaigns. Nobody had asked what the measure excluded, because
the description did not say.

### 15. What is the difference between a measure's aggregation and its type?

The aggregation is the SQL function (`SUM`); the type is the semantic
contract about how it behaves (`sum`, `count`, `count_distinct`, `average`,
`ratio`).

Keeping both matters because the type is what a **downstream tool** reads.
LookML's `type:` drives whether a pivot table subtotals correctly. A tool
that knows only "there is a `SUM` here" cannot warn you that summing it
across a fan-out is wrong.

**Failure story:** a team migrated Looker Studio to Looker and set every
`type:` to `sum` because that was what the SQL did. `distinct_orders`
became a sum of distinct counts — 799 instead of 450 — and went unnoticed for
two months because the chart's shape was identical.

### 16. When should you use `COUNT_DISTINCT` versus a pre-aggregated count?

`COUNT_DISTINCT` is correct but expensive — it holds the distinct values for
the whole group. Pre-aggregating to a table at the right grain is fast and
correct, **provided the join to it does not fan out**.

**Failure story:** a query took 90 seconds on a 400-million-row fact table.
The team pre-aggregated to a daily user table and made it fast — and
introduced a grain mismatch, because a user with orders on 5 days was
counted 5 times instead of once. The fix was a separate monthly-grain
rollup joined only to a monthly-grain fact.

### 17. What is a filtered measure, and why should the filter live in the measure?

A measure with a built-in exclusion — "revenue excluding refunds" — so every
consumer gets the same exclusion. The filter is part of the definition, not
part of the query, and it travels with the measure into every dashboard.

**Failure story:** a company had both `net_revenue` (excl. refunds) and
`total_revenue`. An analyst built a board deck on `total_revenue` because
the name sounded more authoritative. The deck reported £1.13M against
finance's £1.06M — the 6% refund difference, presented to the board as
growth.

### 18. Why not just delete a deprecated measure?

Because a measure is a **contract with every dashboard that references it**,
and an invisible measure is still a contract. A report you cannot see is
still a report somebody will build.

The safe sequence: add the new measure beside the old, migrate the
dashboards one at a time comparing the numbers, then deprecate — do not
delete.

**Failure story:** a team deleted `revenue_gross` after migrating three
dashboards. Two months later an analyst needed it for a regulatory filing and
reimplemented it from a saved query with a subtly different filter. The wrong
number went into a filing, and the only thing that caught it was the
auditors' reconciliation.

### 19. What is a slowly changing dimension, and what are the three types?

A dimension whose attributes change over time while facts keep recording what
was true at the time.

- **Type 1** — overwrite. History lost; cohort analysis impossible.
- **Type 2** — new row with a validity window. History preserved; the
  dimension now has more rows than entities.
- **Type 3** — new column (`segment_current`, `segment_historical`). History
  preserved in the names; the table widens with every change.

**Failure story:** a retailer used Type 1 for customer tier. "How much did
customers spend before they became gold?" returned nothing — the tier had
been overwritten and every past order now carried the current tier. The
question had been unanswerable for the entire two years the data existed,
and nobody knew, because the tier looked correct in every report.

### 20. How do you join a Type 2 dimension correctly?

On the key **and** the validity window:

```sql
JOIN customers_hist c
  ON f.customer_id = c.customer_id
 AND f.order_date >= c.valid_from
 AND f.order_date <  c.valid_to
```

The `<` matters: with `<=`, a customer who changes tier exactly on the order
date matches two rows and you get a fan-out that looks like a legitimate
join.

**Failure story:** a team implemented Type 2 correctly but forgot
`valid_to` in one downstream view. Every customer with a tier change was
counted twice — inflation of 11%, concentrated on exactly the subset the
dashboard was built to study.

### 21. What is a surrogate key, and why not use the business key?

An artificial unique identifier on a dimension row. It exists because Type 2
dimensions make the business key non-unique: `customer_sk` is unique,
`customer_id` is not.

**Failure story:** a team keyed the customer dimension by email and updated
the key in place when a customer changed it — the classic silent history
loss. A year later the order history before the email change no longer
joined, because the facts stored the old email. The join *dropped* rows
rather than duplicating them, so it looked like a data-quality issue rather
than a key-design issue.

### 22. What is a factless fact table, and what is it for?

A fact table with no measures — rows recording the *occurrence* of something
rather than an amount. A **cohort table** is the canonical example: one row
per customer per acquisition month, every customer, always.

They exist because some analyses need a **grain** to hang measures off, and
the grain is the point.

**Failure story:** a retention analysis built from the orders table could
not be computed, because that table only has rows for customers who
*ordered*. Customers who signed up and never bought were invisible, so
"retention" was silently "share of customers with an order in month N".
Retention looked like 80% when the true figure was 31%.

### 23. What is an unresolved foreign key, and why is it worse than a wrong total?

A fact row whose foreign key matches no dimension row. In a left join it gets
a blank label — **and the row still counts towards the total**.

Worse than either being wrong alone, because the total is right and the
breakdown is wrong. And because the total is right, nobody checks the parts.

It is usually a *timing* problem — the fact arrived before the dimension row
— which makes it worse: the report is right again by lunchtime, and nobody
ever diagnosed it.

**Failure story:** a payments fact loaded before the customer dimension for
new signups. Revenue by customer was right in total with a growing "blank"
bucket, reaching 8% of revenue. The team backfilled the dimension nightly and
never once looked at why the bucket existed.

### 24. When is a `many_to_many` join acceptable, and how do you make it safe?

When the bridge table has a well-defined grain **and** the measures on both
sides are non-additive — typically distinct counts.

A `many_to_many` join multiplies rows on *both* sides, inflating every
measure on either side by the average degree of the bridge. Two fixes:
aggregate the bridge to the grain you need first, or use only distinct-count
measures and say so in the description.

**Failure story:** a "customers who bought product X" report joined orders to
a product-customer bridge to find the customers, then summed `total_amount`
for them over the joined rows. Each customer appeared once per (order ×
bridge row). Segment revenue was inflated **3.4x**. The fix was two steps:
find the customer IDs in a subquery, then join back to orders on customer ID
alone.

### 25. What is a conformed dimension, and why does it matter?

A dimension with the same definition — same name, same values, same grain —
shared across every fact that uses it. It is what lets you compare facts and
build a star schema rather than a snowflake.

The semantic layer is where conformance is *enforced*, because it is where
the dimension is defined once.

**Failure story:** "region" in the sales warehouse meant the shipping region;
"region" in the marketing warehouse meant the customer's home region. A
combined revenue-by-region report added the two. Nobody noticed for two
quarters because both were called region and both were four or five plausible
values. The report was wrong by about 30%.

## Operations and quality

### 26. What is a validation gate, and what does it protect?

An automated set of checks that runs before a number reaches a dashboard. It
protects the **promise a dashboard makes** — that some number, computed some
way, means something.

It catches the four quiet breaks: fan-out doubling a number, a missing
dimension value dropping rows from a total, a late-arriving fact changing
yesterday's number after it was read, and a schema change zeroing a metric —
which looks like a business event, not a bug.

**Failure story:** a nightly job set a "validated" flag after checking only
that the file existed and was non-empty. A scheduler quota stopped the job
for four nights; the pipeline wrote an empty extract, which passed. The
dashboard showed zero revenue for four days and nobody looked, because zero
is plausible and the flag said fine.

### 27. What are the four families of validation check?

**Grain** (is the primary key unique?), **referential integrity** (do the
foreign keys resolve?), **completeness** (are required fields populated?),
and **freshness** (is the data recent enough to be believed?).

Grain comes first, because a duplicated primary key invalidates every
measure over the table — any later check that computes a number over it is
computing a wrong number.

**Failure story:** a team checked completeness and freshness but not grain.
Freshness was green every day, completeness was green, and revenue was 4%
too high for eleven months because one line was written twice by a retry in
the ingestion code.

### 28. How do you decide whether a check should fail the build?

ERROR only for things that make the number wrong or not current. WARNING for
things worth a look. INFO for things that passed. And: **never fail a build
on a check that has fired before without a human deciding what to do.**

**Failure story:** a team checked for null `product_id`. Product IDs were
legitimately null for gift-card orders — 3% of volume. The check failed
daily; within two weeks they added `OR status = 'gift_card'`; within a month
someone added `OR 1=1`. The check was still in the file, still green, and
protecting nothing — worse than not having it, because it created the
*appearance* of a gate.

### 29. Why does freshness need a separate check, when the pipeline would fail anyway?

Because "the pipeline ran" and "the data is current" are different claims. A
successful run against a source that stopped changing produces a perfectly
valid extract of stale data — complete, correct schema, intact grain, and
every number wrong by the length of the outage.

Freshness is also what catches *partial* failures: a pipeline that loaded
three of four source files is successful by every structural check.

**Failure story:** an extract read from a source whose ingestion had failed
for six days. The extract succeeded daily and wrote a valid file. The
dashboard showed revenue frozen at a six-day-old level, and it was read as
"revenue has plateaued" — because a flat line is an ordinary thing to see.

### 30. How do you tell a stale extract from a genuine business event?

**A stale extract produces a flat line; a genuine event produces a change.**
The distinguishing signal is the freshness check, not the chart.

Here the newest row is **126 days** old, so any chart over the last 126 days
is flat at the end, and the "drop" is 126 days of missing data.

The fix is not the chart, it is the **label**: "data as of 2026-05-05" makes
staleness visible at the point of use. The cheapest control in the discipline
and the one most often omitted.

### 31. What should a validation finding contain?

Severity, a machine-readable code, a human-readable message, and a count of
affected rows.

The code is what you alert on and trend over. The message matters because a
gate saying "check failed" gets muted, while one saying "primary key
'line_id' is not unique: 1 value(s) repeat. Every measure over this table is
inflated" gets acted on. The count separates "one bad row" from "the table is
broken".

**Failure story:** a team's validation output was a boolean. `False` meant
broken, and the on-call engineer had to write a query to find out what was
wrong — two hours on one Saturday, for a check that could have said exactly
what was wrong in one line.

### 32. What is reconciliation, and why compare values rather than counts?

Comparing the dashboard's numbers against the source of truth, at the level of
individual values.

Most reconciliation attempts compare row counts, and counts are weak: two
systems can have identical counts and entirely different contents. The three
outcomes are `MISSING`, `EXTRA`, and **`VALUE_MISMATCH`** — and the third is
the one a count comparison can never see.

**Failure story:** a team reconciled daily revenue totals against the source
for a year. It always matched, because the dashboard and the source were both
reading the same table. The reconciliation was a tautology and would have
caught a broken pipeline exactly zero times. Only a genuine second source — a
payment processor's settlement file — found that 2% of transactions were
being dropped.

### 33. Why does the reconciliation query use `IS DISTINCT FROM` rather than `<>`?

Because **`NULL <> NULL` is `NULL`, not `TRUE`**. A `<>` comparison silently
drops every row where either side is null — and a null is exactly where
reconciliation problems hide.

`IS DISTINCT FROM` is null-safe: `TRUE` when the values differ *or* when
exactly one is null.

**Failure story:** a reconciliation using `<>` reported zero differences for
six months. The actual state was that 4% of rows had a null in the
warehouse and a value in the dashboard. The `<>` filtered them out and the
query reported a clean bill of health for a pipeline losing data in one
direction.

### 34. What is a grain check, and why is it separate from a value check?

A check that the two systems agree on the **level of detail**, not just the
values. The same total can come from completely different row structures —
450 rows averaging £2,509 and 901 rows averaging £1,253 agree perfectly on
the total and disagree completely on the grain.

The grain check compares row counts and distinct primary key counts. It is
the check that catches a fan-out, because a fan-out changes the row count.

**Failure story:** a dashboard's revenue matched the warehouse exactly every
night for eight months — the dashboard summed an order-grain table and the
warehouse a line-grain table. The row counts were 450 and 901. Nobody
checked, because the totals always agreed, and the totals are what everybody
looks at.

### 35. What is a fan-out check, and how does it differ from the grain check?

The grain check compares **row counts**. The fan-out check compares the
**measure** with and without the join.

They catch different things: a fan-out check catches a measure that changes,
which a count comparison can miss entirely — a join that fans out by exactly
1.0x, or one that changes the measure without changing the row count.

**Failure story:** a pipeline's row count matched the source exactly, every
night, for a year. The grain check was green. But the pipeline had started
filtering out refunds and adding them back at the aggregate level, so the
count matched and every number was wrong. Only a value-level check would have
found it.

### 36. What is a freshness SLO, and how do you set one?

A stated maximum age for the newest row in a model, in hours, with an owner.
The number is less important than the statement: without an SLO, "is the data
fresh?" is a judgement call made by whoever is looking, and the answer depends
on how urgently they need it.

Set it from the business's tolerance for being wrong, not from the pipeline's
current performance. If the report goes out at 8am, the SLO is 6am — even
though the pipeline currently delivers at 4am. A performance measurement is
not a requirement.

### 37. What belongs in a runbook for a semantic layer?

Five things: the grain of every table; the fan-out risk of every join; the
freshness expectation for every model; **the exact queries to run, in order,
when a number is questioned**; and who to page.

Item 4 is what makes it operational rather than descriptive. When someone
says "revenue looks wrong", the runbook should say: run this, then this,
then this.

**Failure story:** a company had a 200-page wiki and no runbook. When a
metric was questioned, the engineer read the wiki, found nothing, searched
Slack for how the last investigation was done, and rebuilt the query from
scratch — forty minutes, for a question that had taken six the previous time.

### 38. What is the query-cost problem, and how do you detect it?

A dashboard whose query scans far more bytes than the fact table is fanning
out — and the problem gets worse as the data grows.

The check is a ratio: bytes scanned by the dashboard's query ÷ bytes of the
fact table. Near 1.0 means the query costs about what reading the fact
costs; 100 means the joins are multiplying work by two orders of magnitude.

**Why it matters more than the runtime:** a dashboard that takes 30 seconds
is annoying. One that scans 2 TB because of a fan-out is *expensive*, and the
cost grows with the data while the useful information does not. It becomes
unaffordable precisely as the company succeeds.

**Failure story:** a reporting dashboard cost £4,200 a month because it
joined a 200-million-row fact to a dimension with duplicate rows. Twelve
seconds, "fast enough". The fix was a relationship declaration that made the
tool rewrite the join.

### 39. How should you change a measure without breaking every dashboard?

Additively: add the new measure beside the old, migrate the dashboards one
at a time **comparing the numbers**, then deprecate the old one — do not
delete it.

The comparison step is what distinguishes a *correction* from a
*redefinition*, and those need different treatment. A correction should
make the numbers match; a redefinition should not.

**Failure story:** a team redefined `revenue` to exclude refunds, in place.
Twelve dashboards moved at once, over a weekend, with no comparison. Monday
opened with "revenue is down 6%" and an argument about double-counted
refunds. The definition was correct; the rollout was the failure.

### 40. How do you make a semantic layer that people actually use?

Name things so the right choice is obvious; make the wrong thing hard to do;
make the right thing the default.

The most common outcome of building a semantic layer is that nobody uses it —
and it is a design problem, not a marketing problem. The layer usually makes
the *hard* questions easy and the *easy* questions slightly harder. A report
author who wants "revenue by region" must pick the right explore and the
right measure — and if the wrong choice is also available, they will pick it,
because they do not know the difference.

**Failure story:** a team launched a semantic layer with 40 measures, several
of which meant subtly different things. Adoption was 3%. The metrics team
spent two years explaining why their numbers were right. The fix was to
*delete* measures and rename the rest, so that `order_line_count` versus
`order_count` could not be confused.

## Working with people

### 41. Who owns a semantic layer, and why does it matter?

**A named person, not a team.** The layer encodes business rules that took
months to learn, and it is the only place they are written down.

Treat it accordingly: version-controlled, reviewed like code, tested like
code, documented in the descriptions rather than in a wiki, and owned by
someone whose name is attached to it.

The failure mode of "owned by the data team" is that no individual is
accountable for a measure being *correct* — only for the layer being
*available*.

### 42. How do you handle a request for a metric nobody has defined yet?

**Define it properly in the layer, with a description, rather than letting
each requester build it in their own report.**

The temptation is to say yes quickly — it is one calculated field. The cost
is that two months later there are four implementations of "active customer"
and nobody can say which one the board was shown.

The pragmatic sequence: define it in the layer if it will be used more than
once; if it is genuinely one-off, say so explicitly and record that it is not
a governed metric. The second option is legitimate — what is not legitimate
is the ambiguity in between.

### 43. How do you convince a team to migrate off a spreadsheet?

**Do not argue about the spreadsheet. Give them the number they need, faster
and with the caveat they care about.**

Most spreadsheet resistance is not about trust in the pipeline; it is about
control and about the spreadsheet having one extra column they built
themselves. A migration that removes that capability will fail, correctly.

The successful migrations I have seen all did the same thing: put the
governed number next to the spreadsheet number, let them see they match, and
keep the ability to slice the spreadsheet for the one-off analysis. The
spreadsheet becomes a scratchpad rather than a source of truth — which is the
right outcome, and one they accept once they trust the number.

### 44. How do you handle two teams that want the same metric to mean different things?

**Do not average them and do not pick a winner without evidence. Find out what
each one is actually measuring, because they are usually measuring different
things and both are right.**

This is where the description earns its keep. "Revenue" might mean gross
merchandise value for one team and net of refunds for another. The resolution
is rarely "one of you is wrong" — it is usually "you want two measures, and
they should have two names". Then the disagreement becomes a naming problem,
which is solvable, instead of a data problem, which is not.

**Failure story:** two teams disagreed about revenue for a quarter. The
resolution was that one wanted gross and the other net — and both had been
right. The layer gained `gross_revenue` and `net_revenue`, and the argument
ended in an afternoon.

### 45. What is the difference between "the dashboard is broken" and "the metric is wrong"?

**The dashboard is a rendering; the metric is a definition. A dashboard can
be wrong (a filter, a chart setting, a date range) or the definition can be
wrong, and the two have completely different fixes.**

The diagnostic question is: **does the number change when you use a
different chart or filter?** If yes, the dashboard is at fault. If no, the
definition is.

The failure mode of not distinguishing them is expensive: teams rebuild
dashboards when the metric is wrong, and the rebuilt dashboard is still wrong
and now there are two of them.

### 46. How do you test a semantic layer?

**Assert on the properties, not on the output.** A unit test that says "this
measure is not additive" documents a trap that no UI would let you assert.

The tests that earn their keep:

- the grain is what the description says it is;
- a duplicated primary key fails the validation gate;
- a non-additive measure is documented as non-additive;
- a ratio is not the average of per-row ratios;
- the previous period is the immediately preceding period, including the
  year case (2025, not 2024);
- every `{{ reference }}` in the generated LookML resolves.

The last one is the killer: it reproduces Looker's build-time safety net in a
unit test that runs in a quarter of a second with no licence and no
credentials.

### 47. What is the most common mistake in a semantic layer, and how do you spot it?

**A measure whose description does not say what it excludes.** It is the most
common because it looks like a documentation oversight rather than a design
one, and it is not caught by any test.

The second most common is a **join whose description is bare** — "customer
join" — so the fan-out warning lives nowhere.

The way to spot both is to read the layer as a *report author* rather than as
its author. Ask: given only this layer, could I use this measure safely? If
the answer needs a question to whoever wrote it, the description is
incomplete.

### 48. When should you not build a semantic layer?

**When there is one report, one author, and no disagreement.** The overhead is
real — it is a schema, a review process, and a migration.

The signal that you have outgrown it: **the same metric is computed in three
places and the numbers disagree**, or **a report author has asked you what a
column means**. Both mean the definition is missing from the system, and the
layer is the cheapest place to put it.

The other signal: you are being asked to build it *before* there is a
disagreement. Semantic layers built speculatively get abandoned, because
nothing was wrong and therefore nothing was solved.

### 49. What is the difference between a semantic layer and a metric store?

**A semantic layer defines metrics; a metric store serves them.**

A metric store (MetricFlow, Cube, Transform's hosted metrics) is an
*execution engine* that takes metric definitions and turns them into
optimised queries — column pruning, pre-aggregation, caching, partition
pruning. A semantic layer is the *definition layer*: models, measures,
dimensions, joins, and the grain.

Most modern metric stores are built *on* a semantic layer, and the definitions
live in one — dbt's semantic layer, for instance, can be served by MetricFlow
or by a BI tool's own engine.

The practical question when choosing: do you need the definitions to be
reviewable and portable, or do you need the queries to be fast? Those are
different products, and the answer is usually "both, in that order".

### 50. What is the one-sentence version of everything in this course?

**Know the grain, state it in three places, make the measures say what they
exclude, and check that the numbers are still true every day.**

Everything else follows. The grain determines the keys, the joins and which
questions are even answerable. The descriptions are the guard rails that
stop a correct definition being used incorrectly. The validation gate turns
trust into a mechanism rather than a habit. And the runbook is what makes
the whole thing maintainable by someone who was not there when it was built.

**The failure story that ties it together:** a company had a beautiful
semantic layer, well-documented, well-tested, and it was quietly wrong for
eighteen months because nobody checked whether the underlying data still
matched what the layer said it was. The layer was never the problem and the
layer was never the solution. The gate was.
