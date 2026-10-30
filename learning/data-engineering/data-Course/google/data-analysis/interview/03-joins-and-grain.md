# Module 3 — Joins, Grain & Slowly Changing Dimensions

> **14 questions · Module 3 · Joins, Grain & SCDs**

---

## The grain

### 1. What is the grain of a table, and how do you write it down?

**The grain is the answer to "one row per what?"** — the level of detail the table records.

You write it as a sentence, and you write it in **three places**:

1. **The DDL comment** — the machine-checked statement:
   ```sql
   -- The grain: one row per order LINE.
   --
   -- `order_id` is deliberately NOT the primary key and is NOT unique.
   -- An order with three lines has three rows.
   PRIMARY KEY (line_id)
   ```
2. **The model description** — the thing the report author reads:
   ```
   One row per order line. Note the grain: a single order with three
   lines appears three times.
   ```
3. **The test** — the thing that fails the build:
   ```python
   def test_the_grain_is_one_row_per_order_line():
       model = build_sales_model()
       assert model.grain == "one row per order line"
       assert model.primary_key == "line_id"
   ```

Three places, three different mechanisms — a comment nobody reads, a description everybody reads, and a test that fails the build. **The test is the one that matters**, because it is the only one that cannot be ignored.

**The number:** in this course's dataset, 901 order lines belong to 450 orders and 121 customers — 2.00 lines per order, 7.45 lines per customer. Every one of those three numbers is a different answer to "how many X are there?", and picking the wrong grain silently picks the wrong one.

**Failure story:** a team wrote the grain in the model's description but nowhere else — no DDL comment, no test. The description said "one row per order" and the table actually held one row per order *line*, because the table had been built at line grain and later described at order grain to match what the business wanted to talk about. Every revenue number was right. Every *order count* was double, because `COUNT(*)` on a line-grain table counts lines. The description was correct about the business and wrong about the table, and nobody had a test to catch the difference.

### 2. Why is the primary key a function of the grain?

**Because the primary key is the grain made machine-checkable.** One row per order line → `line_id` is unique and `order_id` is not.

The mistake this prevents is picking the key that is *convenient* rather than the key that is *correct*. `order_id` is shorter, more meaningful to a human, and the natural thing to reach for. It is also not unique on a line-grain table — and a primary key that is not unique is not a primary key.

**The failure story:** a team built a fact table at order grain but stored one row per line, and used `order_id` as the primary key. The warehouse accepted it — BigQuery's `REQUIRED` and the `unique` test were not both enabled. Six months later, a backfill re-ran a subset of the data and the "primary key" appeared to be duplicated. The reconciliation against the source found 47,000 extra rows, and the cause was that the key was never unique, so the merge could not deduplicate. The fix was a `line_id` and a backfill.

### 3. What is grain mismatch, and how does it differ from fan-out?

**Grain mismatch is a wrong number produced by a join that does not fan out.** It is the more common bug and the harder one to see, because the join looks fine.

Fan-out multiplies **rows**. Grain mismatch leaves the rows correct and counts a **measure** at the wrong level.

The rule that prevents it: **never aggregate a measure at a grain coarser than the grain you are joining at.** If you need a total at the order grain, aggregate it to the order grain *before* the join.

**The failure story:** a "revenue by customer" report summed a customer-level `lifetime_value` over a join to the order-line table. The customer count stayed at 121, so there was no visible row multiplication — the join looked perfectly safe. But `lifetime_value` was summed once per order line, so the highest-frequency customers appeared to be the most valuable. The top-10 list was entirely made up of customers whose revenue *per order* was below average.

### 4. How do you detect fan-out in a query?

**Compare the measure computed on the fact table alone against the same measure computed after the join.** If they differ, the join changed the number.

```sql
SELECT
    (SELECT SUM(total_amount) FROM analytics.orders) AS alone,
    (SELECT SUM(o.total_amount)
       FROM analytics.orders o
       JOIN analytics.customers c ON o.customer_id = c.customer_id) AS after_join;
```

The check needs to be **per join**, not per dashboard — the same measure over two different explores can give two different answers, and the dashboard is where you would never notice.

**The failure story:** a company's revenue dashboard was correct for eight months, then a new customer-attributes table was added to the explore. Revenue doubled overnight — from £1,128,941.37 to £2,257,882.74 — and the growth was real in the sense that the pipeline was working perfectly. It took three weeks to find, because "revenue doubled" is the most welcome possible message and nobody interrogates good news. The cause was a customer with two attribute rows.

### 5. What is an unresolved foreign key, and why is it worse than a wrong total?

**A fact row whose foreign key does not match any row in the dimension table.** In a left join it gets a blank label — and the row still counts towards the total.

That combination is worse than either being wrong alone: the **total is right** and the **breakdown is wrong**. And because the total is right, nobody checks the parts.

This is almost always a **timing** problem — the fact arrived before the dimension row did — which means it is often transient, which makes it worse: the report is right again by lunchtime, and nobody ever diagnosed it.

**The failure story:** a payments fact loads before the customer dimension for new signups. Revenue by customer was right in total and had a growing "blank" bucket. Over a month the blank bucket reached 8% of revenue. The team added the missing dimension rows nightly and never once looked at *why* the bucket existed.

### 6. How do you model a relationship where the foreign key can be null?

**Model it, and decide what "null" means — do not filter it out silently.**

The options are: the fact has no dimension (a true "unknown" or "not yet classified" member); the fact arrived early (a timing artefact); or the source is genuinely incomplete. Each needs different handling, and the difference is usually invisible in the data.

The best practice is to add an **"Unknown" member row** to the dimension and point the null foreign keys at it. Then the total is preserved, the breakdown has a named bucket, and the bucket is *visible* on a dashboard instead of being a blank that nobody investigates.

**The failure story:** a team filtered `WHERE customer_id IS NOT NULL` to "clean up" the revenue query. That silently dropped 8% of revenue. The dashboard showed a decline that was actually a filter, and it was reported as a business event.

## Slowly changing dimensions

### 7. What is a slowly changing dimension, and what are the types?

**A dimension whose attributes change over time, while the fact table keeps recording what was true at the time.** The classic problem: an order records `customer_segment = 'gold'`, but the customer has since been downgraded to 'silver'. Which segment do you report the order under?

The three types:

- **Type 1 — overwrite.** The attribute changes in place. History is lost. Segment analysis is impossible; you can only see the current value.
- **Type 2 — new row.** A new row with a new key and a validity window. History is preserved, but the dimension now has more rows than entities, and every join must respect the validity window.
- **Type 3 — new column.** A new attribute column (`segment_current`, `segment_historical`). History is preserved in the column names, but the table gets wider with every change.

The choice depends on whether you need to analyse *history* or just *current state*.

**The failure story:** a retailer's customer tier used Type 1. A cohort analysis of "how much did customers who later became gold spend before they became gold?" returned nothing, because the tier had been overwritten and every past order now carried the current tier. The question was unanswerable, and it had been unanswerable for the entire two years the data existed — nobody knew, because the tier looked correct in every report.

### 8. How do you join a Type 2 dimension correctly?

**On the key *and* the validity window.** The fact's date must fall between the dimension row's `valid_from` and `valid_to`.

```sql
JOIN analytics.customers_hist c
  ON f.customer_id = c.customer_id
 AND f.order_date >= c.valid_from
 AND f.order_date <  c.valid_to
```

The `<` on `valid_to` matters — with `<=` a customer who changes tier exactly on the order date matches two rows, and you get a fan-out that looks like a legitimate join.

The mechanism: Type 2 makes the dimension row-key unique but the *entity*-key non-unique. `customer_sk` is unique; `customer_id` is not. So the dimension's primary key is the surrogate key, and the "many" side of the join is the fact.

**The failure story:** a team implemented Type 2 correctly but forgot the `valid_to` condition in one downstream view. Every customer with a tier change was counted twice. Revenue by tier was inflated by 11%, but only for the customers who had changed tier — which was the subset the dashboard was specifically built to study.

### 9. What is a surrogate key, and why not just use the business key?

**A surrogate key is an artificial, unique identifier assigned to a dimension row.** It exists because Type 2 dimensions make the business key non-unique.

Without it you have two bad options: join on the business key (which fans out on a Type 2 dimension) or maintain a mutable key (which breaks every historical join when the key changes).

**The failure story:** a team used the customer email as the dimension key. When a customer changed their email, the team updated the key in place — the classic silent history loss. A year later, the order history before the email change no longer joined, because the fact table stored the old email. The join dropped rows rather than duplicating them, which made it *look* like a data-quality issue rather than a key-design issue.

### 10. What is a factless fact table, and what is it for?

**A fact table with no measures — rows that record the *occurrence* of something rather than an amount.**

The canonical examples: a **cohort table** (one row per customer per acquisition month, used to hold the cohort against later periods), an **association table** (customer ↔ campaign, with no amount), and a **coverage table** (which entities were present in which period).

They are not a mistake. They exist because some analyses need a **grain** to hang measures off, and the grain is the point.

**The failure story:** a team tried to build a retention cohort analysis from the orders table and could not, because the orders table only has rows for customers who *ordered*. A customer who signed up and never bought was invisible, so retention was computed as "share of customers with an order in month N", which silently excluded the churned customers who had no rows at all. Retention looked like 80% when the true figure was 31%. The fix was a cohort table — one row per customer per acquisition month, every customer, always.

### 11. What is a degenerate dimension, and when do you need one?

**A dimension that is really the fact's primary key stored as a dimension — the order number, the invoice number.**

It exists because you often want to group by it — "show me the top 10 orders" — and grouping by a degenerate dimension is much cheaper than grouping by a surrogate key and then joining to get the business number.

**The failure story:** a "top customers" report grouped by the customer's surrogate key and then joined back to the dimension to display the customer name. The join to the dimension was `many_to_one` and safe, but the report ran over a 400-million-row fact table and the extra join added 30 seconds. Grouping by the degenerate dimension and joining a small lookup of only the top 50 results cut it to 4 seconds.

## The joins, in practice

### 12. What is the difference between a foreign key join and a conformed-dimension join?

**A foreign key join connects a fact to a dimension row. A conformed-dimension join connects a fact to a dimension that another fact also uses, at the same grain.**

Both are `many_to_one` and both are safe. The difference is what conformance buys you: the ability to compare across facts, and to build a star schema rather than a snowflake.

The failure that comes from *not* having conformance: two facts each with their own `region` column, each internally consistent, disagreeing with each other. There is no fan-out and no grain mismatch — just two definitions of the same word.

**Failure story:** a retailer's "region" in the sales warehouse meant the shipping region; "region" in the marketing warehouse meant the customer's home region. A combined revenue-by-region report added the two, and nobody noticed for two quarters because both were called region and both had four or five plausible values. The report was wrong by roughly the difference between where people buy and where they live — about 30%. It was found not by a test but by a finance analyst who noticed the combined total was 30% above the sum of the two source reports.

### 13. When is a `many_to_many` join acceptable, and how do you make it safe?

**When the bridge table has a well-defined grain and the measures on both sides are non-additive — typically distinct counts.**

The mechanism of the danger: a `many_to_many` join multiplies the rows on *both* sides. Every measure on either side is inflated by the average degree of the bridge.

It can be made safe in two ways:

1. **Aggregate the bridge to the grain you need first**, so the join is `many_to_one`.
2. **Use only distinct-count measures across it**, and say so in the measure description — because a distinct count of the *far* side is unaffected by how many times each row is repeated.

**The failure story:** a "customers who bought product X" report joined orders to a product-customer bridge to find which customers bought X, then summed `total_amount` for those customers over the joined rows. Each customer appeared once per (order × bridge-row) pair. Revenue for the segment was inflated by roughly 3.4x. The fix was a two-step query: find the customer IDs in a subquery, then join back to orders on the customer ID alone.

### 14. What belongs in a join's description, and why put it there?

**The relationship, the direction, and the fan-out risk — with the specific measure that is safe across it.**

The mechanism: the join's description travels with the join into every tool that renders it. In LookML it is the `description:` on the join block, and it appears in the UI next to the field. In dbt it is the description on the relationship.

Compare:

Thin: *"Customer join."*

Good: *"One customer has many orders. Traversing this fan-outs the order lines — and therefore the revenue — unless the measure is a distinct count."*

The good one names the risk **and** names the exception. A report author reading only that line knows both that they need to be careful and that a distinct count is safe.

**The failure story:** a team had a well-written model description and a bare join description. The model description said the grain; the join description said nothing. A report author joined customers to orders and summed revenue. Because the *model* description was correct, nobody reviewing the model spotted anything — the mistake lived in the join, and the join said nothing.
