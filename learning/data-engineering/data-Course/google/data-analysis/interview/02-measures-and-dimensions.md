# Module 2 — Measures, Dimensions & Joins in Depth

> **14 questions · Module 2 · Measures, Dimensions & Joins**

---

## Measures

### 1. What are the three kinds of measure, and what can you do with each?

**Additive, non-additive, and ratio.** The kind is determined by the aggregation, and it decides whether the measure can be rolled up.

- **Additive** — `SUM(revenue)`, `COUNT(*)` on a fact table. Sum of parts equals whole, so it rolls up cleanly.
- **Non-additive** — `COUNT_DISTINCT`, `AVG`. Summing the parts double-counts, so it does not roll up.
- **Ratio** — `SUM(numerator) / SUM(denominator)`. Looks additive, is not, and is the one people get wrong.

The practical consequence of knowing the kind: a non-additive measure can still be reported at a coarse grain, but you cannot add up the pieces. A ratio can be reported at any grain, but only if it is computed as sum-over-sum at that grain.

**The failure story:** a finance team asked for "average order value" by region. Someone built it as `AVG(total_amount)` over the order-line table — which is the average *line* value, not the average order value. It came out at £1,252.99 against a true average order value of £2,508.76 — exactly half, because this dataset's orders average two lines each. The two numbers were on the same dashboard under similar labels for eight months. `AVG` over a fact table is only the right measure when the fact grain *is* the grain you want.

### 2. Why must a ratio be `SUM(numerator) / SUM(denominator)` and not the average of per-row ratios?

**Because the two weight the data differently, and the naive one is systematically biased low.**

The average-of-ratios weights every **row** equally. The correct ratio weights every **unit of denominator** equally. A row with £10 of revenue counts as much as a row with £900, so the extreme small-denominator rows — a refunded sale, a near-zero-margin item — get far more say than they deserve.

Two rows: £900 revenue with £810 margin, and £100 revenue with £10 margin.

- Correct: `820 / 1000 = 0.82`
- Naive: `(0.9 + 0.1) / 2 = 0.50`

A **32 percentage-point** error, and always in the low direction.

**Failure story:** a Looker Studio dashboard reported gross margin as 49% when it was 52%. The calculated field was `margin_amount / total_amount`, evaluated after aggregation. On £1.1M of revenue, three points of margin is roughly £34,000 a year of mis-stated profitability. The number survived because it was still plausible — nobody knows what the margin *should* be without recomputing it correctly, which is the whole problem.

### 3. Why does the Looker Studio calculated-field trap exist, and how do you avoid it?

**Because Looker Studio evaluates calculated fields after aggregation.** The field operates on the values that came out of the query, not on the rows.

So this is wrong:

```
margin_rate = margin_amount / total_amount
```

The engine divides two *already-summed* numbers per row and then averages the results — which is the naive average-of-ratios, biased low.

This is right:

```
margin_rate = SUM(margin_amount) / SUM(total_amount)
```

And guard the denominator, so a zero produces a `NULL` — which charts render as a gap — rather than a divide-by-zero:

```
margin_rate = SUM(margin_amount) / NULLIF(SUM(total_amount), 0)
```

The trap exists because the field editor does not tell you when aggregation happens, and the "obvious" expression is the wrong one. It is also worth knowing that Looker Studio's *scoring* table is where aggregates live: a metric in the scorecard card is already aggregated, so a calculated field referencing it inherits the same trap.

**Failure story:** a marketing team built a "conversion rate" scorecard in Looker Studio — numerator from a scoring table, denominator from a second one — and then layered a calculated field on top to convert the score to a percentage. The scorecard numbers were already aggregates, so the field divided two aggregated values and averaged the results across rows. The conversion rate came out at 4% against a true figure of 11%. The team had checked the scorecard's own numbers against the raw events and found them correct, so the error was invisible until the field was added.

### 4. What is the difference between a measure's aggregation and its type, and why keep both?

**The aggregation is the SQL function; the type is the semantic contract about how it behaves.**

`SUM` is the aggregation for `total_revenue`, whose type is `sum`. `COUNT` is the aggregation for `order_count`, whose type is `count`. The type is what tells the tool — and the report author — whether the measure can be rolled up, whether it has a denominator, and how it should be displayed.

Keeping both matters because the type is what a **downstream tool** reads. LookML's `type:` field is the type, and it drives whether a pivot table subtotals correctly. dbt's semantic layer has `agg:` for the aggregation and the measure's behaviour follows from it. A tool that knows only "there is a `SUM` here" cannot warn you that summing it across a fan-out join is wrong.

**The failure story:** a team migrated a Looker Studio dashboard to Looker and set every measure's `type:` to `sum` because that was what the SQL did. The `distinct_orders` measure became a `sum` of distinct counts — 799 instead of 450 — and nobody noticed for two months because the *shape* of the chart was identical.

### 5. What should a measure's description contain, and why does it matter?

**Four questions: what is it, what grain is it over, what does it exclude, and how does it behave when rolled up.**

This is not documentation. It is a **guard rail**, and it is the only defence against a measure being used in a context where it is wrong.

Compare two descriptions for a margin measure:

Thin: *"Margin over revenue."*

Good: *"Margin over revenue. The denominator is total_amount — the SUM of both, never the average of per-row margins."*

The second one prevents the specific mistake. The first one permits every mistake while appearing to be documentation.

**The failure story:** a measure called `conversion_rate` had the description "Conversion rate." Eleven dashboards used it. Three of them used it over a *join to a campaign table*, which fans out, so the numerator was counted once per campaign touch and the rate came out above 100% on the highest-touch campaigns. Nobody had asked what the measure excluded, because the description did not say.

### 6. When should you use `COUNT_DISTINCT` versus a pre-aggregated count, and what does each cost?

**`COUNT_DISTINCT` is correct but expensive; a pre-aggregated count is fast but only correct at one grain.**

`COUNT(DISTINCT customer_id)` has to hold the distinct values for the whole group in memory (or on disk, depending on the engine), so it scales badly with cardinality. On a wide fact table with millions of distinct customers, it is the most expensive thing in the query.

The alternative is to pre-aggregate: build a table at the grain where the count is meaningful, then join it. This is fast, and it is correct — provided the join to it does not fan out.

**The failure story:** a dashboard's query took 90 seconds and timed out because of a `COUNT(DISTINCT user_id)` over a 400-million-row fact table. The team pre-aggregated to a daily user-level table to fix it — and introduced a grain mismatch, because the daily table has one row per user per day, so joining it to orders counted a user once per day they ordered, not once overall. The query got fast and the number got wrong. The fix was a separate monthly-grain rollup table, joined only to a monthly-grain fact.

### 7. What is a filtered measure, and why should the filter live in the measure?

**A measure with a built-in filter — "revenue excluding refunds" — so that every consumer of it gets the same exclusion.**

The mechanism: the filter is part of the definition, not part of the query. It travels with the measure into every dashboard, every explore, every saved report.

The alternative — asking every report author to add "and exclude status = returned" — produces a family of subtly different revenue numbers, one per author, each of which somebody will eventually present as the revenue.

**The failure story:** a company defined `net_revenue` as revenue minus refunds, and left `total_revenue` in place beside it. A new analyst built a board deck on `total_revenue` because the name sounded more authoritative than `net_revenue`. The deck reported £1.13M against the finance team's £1.06M. The difference was refunds — 6% — and it was presented to the board as growth.

### 8. What is a "deprecation" of a measure, and why not just delete it?

**Marking it as deprecated — visible, documented, and no longer recommended — rather than removing it.**

The reason is that a measure is not just a formula. It is a **contract with every dashboard that uses it**, and an invisible measure is still a contract. A report you cannot see is still a report somebody will build.

The safe sequence is: add the new measure beside the old; move the dashboards over one at a time, comparing numbers; deprecate the old one with a note pointing at the replacement.

Deleting it does not prevent the report. It just moves the reimplementation into a calculated field, where it cannot be reviewed.

**The failure story:** a team deleted a `revenue_gross` measure after migrating three dashboards. Two months later, an analyst needed gross revenue for a regulatory filing and reimplemented it from a saved query in a spreadsheet — with a subtly different filter. The number went into a filing. It was wrong by the discount rate, and the only way to find out was the reconciliation the auditors ran, which flagged it as a discrepancy against the warehouse.

## Dimensions

### 9. What does a dimension's type buy you?

**It constrains what the tool allows you to do with it, and it decides whether timeframes apply.**

`string` dimensions group and filter. `number` dimensions can be binned into ranges. `time` dimensions get **timeframes** — the day/week/month/quarter/year drill-down ladder — and can be filtered with a date picker rather than a range string.

The type also protects against a class of mistake: a `time` dimension with a timeframe and a `string` dimension with a timeframe is an error, because truncating a string to a week is not a thing.

**The failure story:** a team modelled `order_month` as a string dimension holding `"2026-03"`. Sorting was alphabetical, so `2026-10` sorted before `2026-02`, and every chart's x-axis was wrong from October onwards. The dimension had a perfectly good value in it — it just had the wrong *type*, and the type was what told the tool how to sort it.

### 10. What is a timeframe, and how does one get applied?

**A timeframe is a truncation of a date to a reporting grain.** The ladder is raw → day → week → month → quarter → year.

The mechanism: the tool truncates the date to the bucket start and groups on that. `2026-03-15` truncated to week is `2026-03-09` — the Monday.

That Monday detail is the thing teams argue about, because **ISO weeks start on Monday** while the US convention starts on Sunday. Under ISO, Friday 3rd April 2026 is in the week beginning 30th March; under the US convention it is in the week beginning 29th March. A weekly number that silently changes definition between two dashboards cannot be reconciled, which is worse than a number that is consistently wrong.

**The rule:** decide the convention, write it in the model's description, and put it in the runbook.

**Failure story:** a company ran two weekly reports side by side — a sales report built on the BI tool's default week (Sunday-start) and a finance report built on a SQL `DATE_TRUNC` to the Monday. The two weekly figures never matched, and neither team could explain why, because both were "correct". The reconciliation eventually found the two definitions and the report was changed — but the earlier numbers had to be restated, and for two quarters nobody could say which weekly figure had gone into the board pack.

### 11. Why do you need a date spine rather than just truncating the date column?

**Because truncation groups the rows that exist; it does not create the rows that do not.** A day with no sales produces no row, so it never appears in a group-by at all.

The spine is a generated calendar, left-joined to the facts, with `COALESCE` on the measures. It turns "no row" into "a row with zero" — which is the difference between a gap and a flat line at zero.

Two details that are easy to get wrong:

- **`LEFT JOIN`, not `INNER JOIN`.** An inner join throws away exactly the spine rows you built the spine for.
- **`COALESCE` the measures to zero.** Without it the gap is `NULL`, and a chart renders `NULL` as a gap — you have achieved nothing.

**The failure story:** a subscription company's daily-signups chart showed a smooth upward trend through a nine-day period when signups had actually been zero. The tracking SDK had broken. The chart showed no gaps because gaps are invisible when only dates-with-data are plotted. The trend line went *up*.

### 12. What is a conformed dimension, and why does it matter in a semantic layer?

**A dimension with the same definition — same name, same values, same grain — shared across every fact table that uses it.**

The mechanism: it is what lets you compare. Revenue by region from the orders fact and revenue by region from the refunds fact can only be added together if "region" means the same thing in both.

Conformed dimensions are also what make a **star schema** possible: a fact table with foreign keys to conformed dimensions, rather than a wide table with repeated descriptive columns.

The semantic layer is where conformance is enforced, because the layer is where the dimension is defined once. If the layer defines `region` twice — once per fact — then the two definitions will drift, and they will drift silently.

**The failure story:** a "region" in the sales warehouse meant the shipping region; a "region" in the marketing warehouse meant the customer's home region. A combined revenue-by-region report added the two. Nobody noticed for two quarters because both were called region and both were four or five plausible values. The report was wrong by roughly the difference between where people buy and where they live — about 30%.

### 13. What is the difference between a dimension and a dimension *set*, and why does the distinction matter?

**A dimension is one grouping key; a dimension set is a defined collection of them — "date", "customer", "product" — that a report author chooses from.**

The distinction matters because it is where **drill-down paths** live. A dimension set that says customer → order → line tells the tool which drill-downs are legal, and therefore which paths cannot produce a grain mismatch.

When dimension sets are absent, a report author can drill from customer to order to order line and back to customer, and every step that traverses the fan-out join is a chance to double-count.

**The failure story:** a dashboard let authors drill from customer into orders and back out to customer total. The "back to customer" step used the customer-grain `lifetime_value` measure summed over the expanded order rows. Drilling in and back out changed the number, which is the property you would most want a drill-down to preserve.

### 14. What is the difference between a metric, a measure and a dimension in dbt's semantic layer?

**A measure is the metric; a dimension is the grouping; an entity is the join key.**

dbt's semantic layer formalises the same ideas with one addition that LookML does not have as a first-class concept: the **entity**. An entity declares a key and its role — `primary`, `foreign`, `natural` — and the tool uses those declarations to work out the joins, exactly as Looker uses `relationship:`.

```yaml
semantic_models:
  - name: orders
    description: "One row per order line."
    entities:
      - name: line
        type: primary
        expr: line_id
      - name: customer
        type: foreign
        expr: customer_id
    measures:
      - name: total_revenue
        description: "Sum of order line revenue."
        agg: sum
        expr: total_amount
    dimensions:
      - name: created_at
        type: time
        type_params:
          time_granularity: day
```

The `description` field is not optional in practice. It is what appears in the exploration UI, and it is the same guard rail the course's `Measure.description` provides.

**Failure story:** a team moved from LookML to dbt's semantic layer and dropped the descriptions in the port, because the YAML was more compact without them and the definitions "said the same thing". The metric definitions did say the same thing — the *exclusions* did not, because those had only ever been written in prose. Six weeks later a dashboard reported gross margin where the LookML version had reported margin net of refunds, and the difference was invisible in the YAML review because there was nothing in the YAML to review.

---

## The practical summary

The measures in a semantic layer are a **contract**, not a formula. Everything else in this module follows from that: the description exists because the formula alone is not enough information to use correctly; the type exists because the tool needs to know how the measure behaves; the filters exist because exclusions belong to the definition; and the deprecation rule exists because a measure is a promise to every dashboard that references it.
