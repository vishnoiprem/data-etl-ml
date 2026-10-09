# Lesson 15 — Star Schema vs Snowflake Schema

> **What you'll learn:** the difference between a star and a
> snowflake, when to use each, and why star is the default. By
> the end of this lesson you'll be able to defend a star choice
> in the interview.

---

## Star schema

A star schema is a single fact table surrounded by *flat*
(dimensional) tables. Each dim has all its attributes on one
row — denormalized, not normalized.

```
            ┌──────────────┐
            │ dim_products │
            │              │
            │ product_key  │
            │ name         │
            │ category     │  ← category is here, not in a
            │ brand        │    separate dim_brand table
            │ price        │
            └──────┬───────┘
                   │ product_key
                   ▼
┌──────────┐  ┌──────────────┐  ┌──────────┐
│ dim_date │◄─┤  fact_sales  ├─►│dim_stores│
└──────────┘  │              │  └──────────┘
              │ revenue      │
              │ quantity     │
              └──────────────┘
```

Every dimension is one hop from the fact. To answer "what was
revenue by brand by month," you join `fact_sales` to
`dim_products` (which has brand) and `dim_date`. Two joins.

---

## Snowflake schema

A snowflake schema is a star schema with the dimensions
*normalized* — broken out into multiple tables, joined by
foreign keys.

```
            ┌──────────────┐
            │dim_brand     │
            │              │
            │ brand_key    │
            │ brand_name   │
            └──────┬───────┘
                   │ brand_key
                   ▼
            ┌──────────────┐
            │dim_products  │
            │              │
            │ product_key  │
            │ name         │
            │ brand_key    │  ← brand is in a separate table
            │ price        │
            └──────┬───────┘
                   │ product_key
                   ▼
┌──────────┐  ┌──────────────┐  ┌──────────┐
│ dim_date │◄─┤  fact_sales  ├─►│dim_stores│
└──────────┘  │              │  └──────────┘
              │ revenue      │
              │ quantity     │
              └──────────────┘
```

Now to answer "what was revenue by brand by month," you join
through three tables. The query is more complex; the storage
is smaller (you don't repeat the brand name on every product
row).

---

## Why star wins for warehouses

| Concern | Star | Snowflake |
|---|---|---|
| Query complexity | 1 hop per dim | 2+ hops for some dims |
| Read performance | Fast (few joins) | Slower (more joins) |
| Analyst ergonomics | Easy ("join the dim") | Hard ("which dim has brand?") |
| Storage | Bigger (denormalized) | Smaller (normalized) |
| Updates | Slower (denormalized rows) | Faster (single source) |
| Best for | Analytics (read-heavy) | OLTP (write-heavy) |

In a warehouse, the read path is hot and the write path is
cold. You optimize for reads. Star wins on read performance
and analyst ergonomics; those outweigh the storage and update
costs.

The standard rule of thumb: **star is the default**. Snowflake
is the exception. Use it only when:

- A dimension has millions of distinct values (a geographic
  hierarchy, a part-number catalog) and you can't fit it in
  memory denormalized.
- A dimension changes constantly and you want the changes in
  one place (not duplicated across rows).
- The dimensional hierarchy is meaningful and analysts
  commonly drill up/down through it (date → month → quarter
  → year).

---

## The case for snowflake (rare)

There are real reasons to snowflake. Three:

### Reason 1 — A multi-level hierarchy that's hard to denormalize

A geographic hierarchy:

```
country → state → city → zip
```

You can denormalize this onto a `dim_geography` table, but if
your country/state mapping changes (a new postal code
system), you'd have to update millions of rows. Snowflaked,
you update one row in `dim_country`.

### Reason 2 — A shared dimension with high cardinality

A `dim_product_category` that has 10,000 rows and 50
attributes. The category name alone is 1 KB; duplicated on
100,000 products, that's 100 MB of redundant text. Snowflake
saves the storage.

### Reason 3 — A sub-dimension that updates independently

A `dim_promotion` that has a `promotion_type` (percent off,
buy-one-get-one, free shipping). The promotion itself
changes daily; the type changes yearly. Snowflaking the
type out means the daily updates don't touch the type
table.

These are real reasons. They're also rare. In a 30-minute
interview, the default is star.

---

## The "but star has redundant data" objection

Mid-level candidates sometimes object: "star has redundant
data, isn't that bad?" The answer: in a warehouse, redundant
data in a dimension is *fine* for three reasons:

1. **Dims are small.** A 10,000-row dim is 10 MB; a
   1,000,000-row dim is 1 GB. Storage is cheap.
2. **Reads are hot.** The redundant data means a single join
   gets all the attributes. With snowflake, the analyst
   would have to know to join a second dim.
3. **Writes are cold.** The dimension is updated slowly
   (SCD 2 — once per change). The cost of denormalizing a
   row is paid once per change, not once per query.

The redundancy in star is *intentional* — it's the price of
analyst ergonomics and query speed. That's a price worth
paying in a warehouse.

---

## The interview rule

When asked "star or snowflake?":

- Default to star.
- State the assumption: "I'm going to use a star schema
  because the reads are hot, the writes are cold, and the
  dimensions are small."
- Acknowledge the alternative: "If a dimension like
  `dim_geography` has millions of distinct values and
  changes frequently, I'd snowflake that one dim. But the
  default is star."

The interviewer is checking whether you know the tradeoffs,
not whether you can parrot "star wins." A senior candidate
knows when to break the default.

---

## Try it

For each of the 5 canonical modeling questions, write down:

1. Star or snowflake?
2. Which dim, if any, would you snowflake and why?
3. The denormalized attributes on the main dim.

Time yourself: 5 minutes per question. The point isn't
speed — it's that you can make the call, defend it, and move
on.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
