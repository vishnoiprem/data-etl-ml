# Module 1 — Foundations & the Semantic Layer

> **14 questions · Module 1 · Foundations & the Semantic Layer**

---

## The fundamentals

### 1. What is a semantic layer, and what problem does it solve that a BI tool does not?

**A semantic layer is a shared, machine-readable definition of the metrics an organisation reports on.** It sits between the raw tables and the report authors, and it holds the measures, the dimensions, the joins and — critically — the **grain** of every table.

A BI tool without one is a **consumer** tool. Looker Studio, for example, lets every report author define their own calculated fields, their own joins and their own filters. The consequence is not that the reports are individually wrong; it is that two reports about revenue are two unrelated implementations that will eventually disagree.

The mechanism of the disagreement is precise. Two authors define "revenue" separately. One writes `SUM(total_amount)`; the other writes `SUM(total_amount - discount)`. Both are defensible readings of the word, and neither author can see the other's definition because it lives in a field picker rather than in a shared repository.

**The failure story:** a retailer ran a Looker Studio dashboard for gross revenue and a finance spreadsheet for net revenue. For seven months the two numbers were reported side by side in planning meetings without anyone reconciling them, because both were labelled "revenue". The gap was roughly 4% — the discount rate. When it was finally found, the discovery was not a bug fix; it was a re-baselining of two years of forecasts.

The number that makes the point: the semantic layer does not make the numbers *correct*. It makes them **the same number**, which is the property that was missing.

### 2. What are the four objects a semantic layer is made of, and what does each one do?

**Models, measures, dimensions and explores.** There is nothing else, and the simplicity is the point — the four objects are the same in LookML, in dbt's semantic layer, and in most proprietary tools.

- A **model** is a table plus what it means: its grain, its primary key, its description. The model is where the contract lives.
- A **measure** is a number with an aggregation: `SUM(total_amount)`, `COUNT_DISTINCT(order_id)`, `SUM(margin) / SUM(revenue)`. The measure is what a report author drags onto a chart.
- A **dimension** is a grouping key with a type: region (string), revenue (number), order date (time). The type decides what the tool allows you to do with it.
- An **explore** is a starting point: a base model plus the joins available from it, with the fan-out risk of each join made explicit.

The failure that comes from getting this wrong is a naming failure more often than a structural one. A tool with a `revenue` measure and a `revenue_ex_gst` measure, both on the same explore, will have every author guessing. The four objects are a naming discipline as much as a data structure.

**Failure story:** a company built a semantic layer with forty measures and no naming hierarchy — `revenue`, `net_revenue`, `revenue_gross`, `total_revenue` — all on the same explore. Adoption was 3%. Every report author picked one at random, because the layer made all four look equally plausible. The metrics team spent two years explaining why their numbers were right. The fix was to *delete* measures and rename the rest, so that `order_line_count` versus `order_count` could not be confused.

### 3. What is the grain, and why is it the most important sentence about a table?

**The grain is the answer to "one row per what?"** — and it is the single most consequential property of a table.

For this course's `orders` table, the grain is **one row per order line**. Not per order. Not per customer. That distinction determines almost everything else:

- `line_id` is the primary key; `order_id` is **not** unique.
- `SUM(total_amount)` is additive and rolls up correctly.
- `COUNT(*)` counts **lines**, not orders — and here it gives 901 against 450 real orders.
- `orders → customers` is `many_to_one` and cannot fan out; `customers → orders` is `one_to_many` and absolutely can.

The failure story is the canonical one. A team built "revenue by customer" by joining `customers` to `orders` and summing a customer-level `lifetime_value` over the joined result. The join was cardinality-legal, the SQL was correct, and the number was wrong by a factor of the average lines-per-order. The busiest customers looked implausibly profitable, because they were counted most often. Nothing errored. The chart looked like a chart.

**The number:** in this course's dataset, 901 order lines belong to 121 customers — an average of 7.45 lines per customer. A customer-level measure summed over that join inflates by exactly that factor.

### 4. What is additivity, and how do you check it?

**Additivity is whether a measure can be summed over a finer breakdown and still equal the coarser value.** It is the property that decides whether a number can be rolled up, and it comes in three kinds:

- **Additive** — `SUM(revenue)`, `COUNT(*)` on a fact table. Sum of parts equals whole.
- **Non-additive** — `COUNT_DISTINCT`, `AVG`. Summing the parts double-counts.
- **Ratio** — `SUM(numerator) / SUM(denominator)`. Looks additive, is not.

The check is mechanical and takes one query: compute the measure at the coarse grain, compute it at the fine grain, sum the fine numbers, and compare. If they differ, the measure is not additive.

**The failure story:** a dashboard showed "distinct customers" broken down by region, and the four regional numbers summed to more than the headline figure. Nobody had checked, because each regional number was individually plausible — and the headline was on a different tab of the same dashboard, so the two numbers were never on screen at the same time. A customer who bought in two regions was counted twice.

**The number:** `distinct_orders` in this course sums to 799 across the four regions (191 + 193 + 219 + 196), against a true global total of 450. The inflation is **77.6%** — and it is *only* visible if you put the two numbers side by side.

### 5. What is the ratio problem, and why is the wrong answer always low?

**A ratio must be computed as `SUM(numerator) / SUM(denominator)`, never as the average of the per-row ratios.** The two are different numbers, and the difference has a consistent direction.

The mechanism: the average-of-ratios weights every **row** equally, while the correct ratio weights every **unit of denominator** equally. A row with £10 of revenue counts as much as a row with £900. Since small-denominator rows are typically the extreme ones (a £10 sale that was refunded, or a near-zero-margin item), they get too much say — and the average-of-ratios lands **low**.

Concretely, two rows: £900 revenue with £810 margin, and £100 revenue with £10 margin. The correct ratio is `820 / 1000 = 0.82`. The average of the per-row ratios is `(0.9 + 0.1) / 2 = 0.5`. The naive answer is **39 percentage points low**.

**Failure story:** a Looker Studio dashboard reported gross margin as 49% when it was 52%. The calculated field was `margin_amount / total_amount`, evaluated after aggregation. Three points of margin, on a £1.1M revenue base, is roughly £34,000 a year of mis-stated profitability. It survived because the number was still plausible.

### 6. What is the difference between `count` and `count_distinct`, and why does the naming matter?

**`count` counts rows; `count_distinct` counts unique keys.** On a fact table at line grain, those are different numbers for the same table — 901 versus 450 orders in this course's data.

The trap is not that `count` is wrong. It is that `count` is *correct for the grain it is on* and silently wrong for the question being asked. `COUNT(*)` on the order-line grain gives lines, and the report author calls it "orders" because that is the word in the requirement.

This is why naming is a mechanism, not documentation. `order_line_count` versus `order_count` versus `distinct_orders` — three names for three numbers, and the name tells the author which one they are holding. A measure named `count` tells the author nothing.

**The failure story:** a retailer's weekly "orders" metric was built on `COUNT(*)` over an order-line fact table. The metric was 2.0x the truth and had been for a year. Because the metric only ever went up — order volume was growing — nobody ever reconciled it against the order count in the warehouse, which was always available as a separate number on a different dashboard. The two numbers were never on the same screen.

### 7. What is fan-out, and how do you detect it?

**Fan-out is the row multiplication that happens when a join matches more than one row on the far side.** It is the most consequential BI bug because it produces no error, no warning and no broken chart — just a number that is too large and looks like growth.

The rule that removes all guesswork: **fan-out happens when you traverse from the "one" side to the "many" side.** Traversing the other way is always safe.

The detection is one query — compare the measure computed on the fact table alone against the same measure computed after the join:

```sql
SELECT
    (SELECT SUM(total_amount) FROM analytics.orders)        AS alone,
    (SELECT SUM(o.total_amount)
       FROM analytics.orders o
       JOIN analytics.customers c ON o.customer_id = c.customer_id) AS after_join;
```

If those differ, a join changed the number.

**The failure story:** a company added a `customer_segments` table with one row per customer-segment assignment — and customers with two segments. Joining it to `orders` doubled every revenue figure. Revenue grew 100% overnight on the dashboard, and the growth was real in the sense that the pipeline was working perfectly. It took three weeks to find because "revenue doubled" is the most welcome possible message. The correct revenue was £1,128,941.37; the dashboard showed £2,257,882.74.

### 8. What is grain mismatch, and how is it different from fan-out?

**Grain mismatch is a wrong number produced by a join that does not fan out.** It is the more common bug and the harder one, because the join looks correct.

The mechanism: you join a fact table at line grain to a table at order grain, and then aggregate a measure that lives at the *order* grain across the *line* grain. Each order's total is counted once per line.

The rule: **never aggregate a measure at a grain coarser than the grain you are joining at.** If you need a total at the order grain, aggregate it to the order grain *before* the join.

This is the inverse of the fan-out case. In fan-out, the *rows* multiply. In grain mismatch, the rows are correct and the *measure* is counted at the wrong level.

**The failure story:** a "revenue by customer" report summed a customer-level `lifetime_value` over a join to the order-line table. The customer count stayed at 121 — no fan-out — so the join looked fine. But `lifetime_value` was summed once per order line, so customers with more orders appeared more valuable. The top-10 list was entirely made up of the highest-frequency buyers, whose revenue per order was below average.

### 9. What are the four join cardinalities, and which ones can fan out?

**`one_to_one`, `many_to_one`, `one_to_many` and `many_to_many`.** Fan-out is possible from the "one" side of `one_to_many` and `many_to_many`, and impossible from the "many" side of `many_to_one`.

The practical consequence: the *direction* of the join is the whole decision. `orders → customers` is `many_to_one` and safe. `customers → orders` is `one_to_many` and fans out. Same two tables, same keys, opposite outcomes.

The mechanism is row multiplicity. A row in the "one" table matches N rows in the "many" table, so joining duplicates the "one" row N times. Any measure on the "one" side gets counted N times.

**The failure story:** a report author on a BI tool with no `relationship:` declaration had to write the join by hand. They wrote `customers JOIN orders` in a customer-facing explore — the direction that fans out — and every revenue-by-segment number was inflated. Looker and most modern tools make you declare the relationship, and *use it to rewrite the join* so it cannot fan out. That declaration is not documentation; it is a constraint.

### 10. What is a date spine, and what breaks without it?

**A date spine is a table with one row per calendar day over the range you care about, left-joined to the facts so that days with no activity become explicit zeros.**

Without it, a time series shows only the periods that had data. A slow week looks like a cliff, because the days with no sales are not on the chart at all — the line connects Tuesday straight to Friday and the reader sees a decline that did not happen. The chart is not lying by misrepresenting a value; it is lying by **omitting a row**.

The spine also has to be *generated*, not derived from the facts. A spine derived from the facts would have exactly the gaps you are trying to fill.

**The failure story:** a subscription company's "daily signups" chart showed a smooth upward trend through a period when signups had actually collapsed to zero for nine days — the tracking SDK had broken and the events were being dropped before they reached the warehouse. The chart showed no gaps at all, because a gap is invisible when the only dates on the chart are the dates with data. The trend line went up. Nine days of zero signups produced a *rising* chart.

### 11. Why must a date filter's bounds be computed before truncation?

**Because truncation moves the bounds, and a moved bound silently includes a period the filter was supposed to exclude.**

Consider a filter for March 2026 at month grain. The raw start is 1 March and the raw end is 31 March. Truncate the *end* to the month and you get 1 March — and the filter now covers only one day of the month. Truncate the *start* and you get the right answer by accident; truncate the end and you silently lose 30 days.

The correct order is: **parse the raw dates, validate them against each other, then truncate.** The validation has to happen first, because comparing a truncated start against a truncated end can mask an inverted range — a filter from 31 March to 1 March truncates to 1 March on both sides and looks valid.

An inverted date filter must **raise**, not swap. A silently-swapped filter returns a plausible number for the wrong period, and nobody ever notices.

**Failure story:** a reporting tool normalised an inverted range by swapping the endpoints, so a request for "March to January" silently became "January to March". A monthly close report requested the wrong quarter for three consecutive months. Each report was internally consistent, each was read by a different person, and nobody compared them against the calendar — the numbers were plausible, and plausible numbers do not get checked.

The second, quieter failure is truncating before validating: a filter from 31 March to 1 March truncates to 1 March on *both* ends, so it looks valid. The check has to happen on the raw dates.

### 12. What is the difference between Looker Studio, Looker and dbt?

**Three tools, three layers, and confusing them is expensive because each solves a different problem.**

| | Looker Studio | Looker | dbt |
|---|---|---|---|
| What it is | a consumer BI tool | a semantic layer + exploration | a transformation framework |
| Who uses it | everyone | analysts and engineers | engineers |
| Where definitions live | inside each report | in LookML, versioned | in SQL models |
| The risk | every report re-defines revenue | licence cost + git discipline | no exploration layer |

The structural difference is that **Looker Studio has no shared semantic layer**. Every report author defines their own calculated fields and joins. Looker fixes this by putting the definitions in LookML in a repository, reviewed like code. dbt goes further down the stack: it is where the tables and their tests are built, and its semantic layer now covers the metric definitions too.

The recommendation I give: use dbt to build and test the tables, LookML to define the metrics, and Looker Studio only for the dashboards that genuinely need a consumer UI. The failure is using Looker Studio for the metrics, because that is the one configuration where the definitions cannot be reviewed.

**Failure story:** a company built its board reporting in Looker Studio, with each metric defined as a calculated field in the report. When the board asked to change the definition of revenue, there were eleven reports and eleven definitions. The change took a quarter to roll out, and for three months during the rollout there were three different revenue numbers in circulation, all labelled the same. Nothing was technically wrong at any point — the tool did exactly what it was designed to do, which is let each author define their own numbers.

### 13. What is a LookML `{{ }}` reference, and why is it a build-time safety net?

**A field reference into another view — `${customers.customer_segment}` — resolved by Looker when the model is compiled.** A reference to a field that does not exist is a **build error**, not a runtime error.

That distinction is the entire value. A runtime error means the mistake reaches a dashboard, and someone sees it. A build error means the mistake never leaves the repository, and the person who made it is told immediately.

**The failure story:** a team kept a shared LookML file for "common dimensions" and referenced `${common.customer_tier}` from eight views. Someone renamed the field to `customer_tier_code` in the common file. In a tool where references are resolved at query time, eight dashboards would have started failing at 9am on Monday, one report author at a time. In Looker, the model failed to compile at deploy, on Friday, and the rename was reverted before it ever reached a user.

The reason to have this check locally is that Looker's own `lookml-validate` needs a Looker instance and a licence. Reproducing the check as a unit test — "every reference resolves to an available field" — catches it in a quarter of a second with no credentials.

### 14. How do you change a measure without breaking every dashboard that uses it?

**Additively: add the new measure beside the old one, migrate the dashboards one at a time comparing the numbers, then deprecate the old one — but never delete it.**

The mechanism is that a measure is not just a formula; it is a **contract with every dashboard that references it**. Changing it in place changes all of them simultaneously, which means you can no longer attribute a movement to the change.

The step most teams skip is the second one: moving the dashboards over *one at a time*, comparing the old and new numbers on each. That comparison is what tells you whether the new definition is a correction or a redefinition — and those need different treatment. A correction should make the numbers match; a redefinition should not.

**Never delete.** A measure you cannot see is still a measure somebody will build. This rule is uncomfortable and correct: deleting a measure does not remove the possibility of a report using it, it just moves the reimplementation into a calculated field where nobody can review it.

**The failure story:** a team redefined `revenue` to exclude refunds, in place. Twelve dashboards moved at once, over a weekend, with no comparison. The Monday morning meeting opened with "revenue is down 6%" and an argument about whether refunds were being double-counted. The definition was correct; the rollout was the failure.

---

## The mental model, in one paragraph

A semantic layer exists to make one number into **one** number. The grain says what a row is. The measures say how to reduce rows to a number. The joins say what happens when you combine tables — and whether that combination is safe. The explores are the door into all of it, and they are where you warn the report author. Everything else in this course — the validation gate, the reconciliation, the runbook — exists to keep that layer true over time, because a semantic layer that nobody trusts is worse than none at all: it looks like governance and delivers only the appearance of it.
