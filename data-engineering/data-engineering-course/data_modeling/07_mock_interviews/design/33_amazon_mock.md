# Lesson 33 — Mock Interview: Amazon Marketplace Schema

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the *grain choices for the four
> fact-table types*.

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

> Design a data warehouse for an Amazon-style
> marketplace. We have sellers, buyers, products,
> orders, shipments, returns, and reviews. We want to
> report on GMV (gross merchandise value), seller
> performance, fulfillment metrics (time to ship, on-time
> delivery rate), and product reviews.

---

## The transcript

**Interviewer:** Design a data warehouse for an
Amazon-style marketplace.

**Candidate:** OK. Amazon has many sub-domains. Let
me confirm the scope before I draw.

**Interviewer:** Focus on the order-fulfillment
lifecycle: order placed, payment, shipment, delivery,
return, review. Skip search, ads, and recommendations.

**Candidate:** Good. Three clarifying questions:

1. **"Order" — at the order level or the order line
   level?** I.e., is the grain "one row per order"
   (cart-level) or "one row per line item" (per
   product purchased)?

2. **"Shipment" — does one order have many
   shipments?** Amazon often splits an order into
   multiple shipments if items are in different
   warehouses.

3. **Returns — full-order or partial?** A buyer
   might return one of five items.

**Interviewer:** Order line level. One order, many
shipments allowed. Returns can be partial.

**Candidate:** Good. That gives me four distinct
facts:

1. `fact_order_lines` — transactional, at the
   line-item grain.
2. `fact_shipments` — transactional, at the
   shipment line grain (a shipment has many lines).
3. `fact_inventory_snapshot` — periodic snapshot,
   daily grain.
4. `fact_returns` — transactional, at the return
   line grain.
5. Plus a factless `fact_reviews` for review
   submissions.

Let me draw each.

**Candidate:** OK, `fact_order_lines` — the central
transactional fact. Grain: one row per order line
item. Measures:

- `quantity` (additive)
- `unit_price` (non-additive)
- `gross_amount` (additive)
- `discount_amount` (additive)
- `tax_amount` (additive)
- `net_amount` (additive)
- `shipping_fee` (additive)

Dimensions:

- `dim_customer` — SCD 2. Buyer attributes: name,
  email, prime_member (boolean, slowly changing),
  signup_date, country, city, segment.
- `dim_seller` — SCD 2. Seller attributes: name,
  country, store_url, tier (basic / pro / brand
  registry), fulfillment_method (FBA / FBM).
- `dim_product` — SCD 2. Product attributes: name,
  category, subcategory, brand, list_price, weight.
- `dim_date` — conformed. Role-played for
  `order_date_key` and `promised_ship_date_key`.
- `dim_promotion` — small dim. Promo code, type
  (percentage / fixed), start / end.
- `dim_payment_method` — small dim. Credit card,
  gift card, Amazon Pay, etc.

Foreign keys on the fact:

```sql
FOREIGN KEY (customer_key)      REFERENCES dim_customer(customer_key),
FOREIGN KEY (seller_key)        REFERENCES dim_seller(seller_key),
FOREIGN KEY (product_key)       REFERENCES dim_product(product_key),
FOREIGN KEY (order_date_key)    REFERENCES dim_date(date_key),
FOREIGN KEY (promised_ship_date_key) REFERENCES dim_date(date_key),
FOREIGN KEY (promotion_key)     REFERENCES dim_promotion(promotion_key),
FOREIGN KEY (payment_method_key) REFERENCES dim_payment_method(payment_method_key)
```

**Interviewer:** Why SCD 2 on the product?

**Candidate:** Because product attributes change.
Categories get reclassified, brands get acquired,
list prices change. A buyer in Q1 bought a "Home &
Kitchen" product; today it's classified as
"Home Improvement." We want Q1 reports to attribute
to "Home & Kitchen." SCD 2.

**Interviewer:** What's the GMV query?

**Candidate:** GMV is the sum of `net_amount` over a
date range, grouped by some dimension. The simplest:

```sql
SELECT order_date_key, SUM(net_amount) AS gmv
FROM fact_order_lines
WHERE order_date_key BETWEEN 20240101 AND 20240131
GROUP BY order_date_key;
```

If we want GMV by category:

```sql
SELECT p.category, SUM(f.net_amount) AS gmv
FROM fact_order_lines f
JOIN dim_product p ON f.product_key = p.product_key
WHERE f.order_date_key BETWEEN 20240101 AND 20240131
GROUP BY p.category;
```

**Interviewer:** What about the seller performance
report?

**Candidate:** That's a multi-fact query. The
seller's GMV is from `fact_order_lines`. The
seller's fulfillment metrics are from
`fact_shipments` (time to ship, on-time delivery).
The seller's review score is from `fact_reviews`.

Three separate fact tables, joined on `seller_key`:

```sql
SELECT s.seller_id, s.seller_name,
       COALESCE(orders.gmv, 0) AS gmv,
       COALESCE(ship.on_time_pct, 0) AS on_time_pct,
       COALESCE(rev.avg_rating, 0) AS avg_rating
FROM dim_seller s
LEFT JOIN (
  SELECT seller_key, SUM(net_amount) AS gmv
  FROM fact_order_lines
  WHERE order_date_key BETWEEN 20240101 AND 20240131
  GROUP BY seller_key
) orders ON s.seller_key = orders.seller_key
LEFT JOIN (
  SELECT seller_key,
         100.0 * SUM(CASE WHEN delivered_on_time THEN 1 ELSE 0 END) / COUNT(*) AS on_time_pct
  FROM fact_shipments
  WHERE ship_date_key BETWEEN 20240101 AND 20240131
  GROUP BY seller_key
) ship ON s.seller_key = ship.seller_key
LEFT JOIN (
  SELECT product_key, AVG(rating) AS avg_rating
  FROM fact_reviews
  WHERE review_date_key BETWEEN 20240101 AND 20240131
  GROUP BY product_key
) rev ON ...
;
```

The seller is the conformed dimension across all
three facts. That's why SCD 2 on the seller is
worth it.

**Interviewer:** Walk me through `fact_shipments`.

**Candidate:** Grain: one row per shipment line. A
shipment has many lines (one per product in the
shipment). The shipment itself is identified by
`shipment_id`; the line is identified by
`(shipment_id, line_number)`.

Measures:

- `quantity_shipped`
- `quantity_returned` (after the fact)
- `shipping_cost`
- `weight_kg`

Dimensions:

- `dim_customer` (recipient)
- `dim_seller`
- `dim_product`
- `dim_warehouse` (which warehouse shipped it)
- `dim_carrier` (UPS, FedEx, USPS, Amazon Logistics)
- `dim_date` — role-played for `ship_date_key` and
  `delivery_date_key`.

Degenerate dim: `shipment_id` (no separate dim, the
ID is on the fact row).

The key fact for fulfillment is the *lag* between
ship date and delivery date:

```sql
SELECT d_ship.date_key AS ship_day,
       d_deliv.date_key AS delivery_day,
       d_deliv.date_key - d_ship.date_key AS days_to_deliver
FROM fact_shipments f
JOIN dim_date d_ship  ON f.ship_date_key = d_ship.date_key
JOIN dim_date d_deliv ON f.delivery_date_key = d_deliv.date_key;
```

Or as a measure: `days_to_deliver` is computed at
load time and stored on the fact row. Tradeoff —
stored measures are faster to query but go stale
if the dim dates change.

**Interviewer:** Walk me through the inventory
snapshot.

**Candidate:** `fact_inventory_snapshot` is a
*periodic snapshot* fact, not transactional. Grain:
one row per (product, warehouse, day). Loaded daily.

Measures:

- `on_hand_qty`
- `reserved_qty` (orders not yet shipped)
- `available_qty` (on_hand - reserved)

Dimensions:

- `dim_product`
- `dim_warehouse`
- `dim_date` (one row per day)

The query "what was the inventory of product X on
2024-03-15?" is a point lookup on
`(product_key, warehouse_key, snapshot_date_key)`.
Fast if we have a B-tree index on those three.

The query "how many days of inventory do we have
left?" needs a *rolling* calculation. For each
(product, warehouse) pair, look at the average
daily shipments over the last 30 days and divide
on_hand by that average. That's a window function
on the snapshot fact.

**Interviewer:** Why is inventory a periodic
snapshot, not transactional?

**Candidate:** Because inventory is *state*, not
*events*. Each event ("received 100 units,"
"shipped 5 units") doesn't tell you the current
inventory; the current inventory is the *result* of
all events so far. A periodic snapshot captures
the state at a point in time. The alternative
(transactional fact with a "balance" measure) is
non-additive and doesn't work for a "what was
inventory on day X?" query.

The tradeoff: snapshot is larger (one row per
product per warehouse per day) but queryable. If
we have 10M products × 100 warehouses × 365 days
= 365 billion rows, that's too many. We'd then
sub-partition or only snapshot products that have
changed.

**Interviewer:** What about returns?

**Candidate:** `fact_returns` — transactional, at
the grain of *one row per return line*. A buyer
might return 2 of 5 items in an order, so it's a
separate fact from the order.

Measures:

- `return_quantity`
- `return_amount`
- `restocking_fee`

Dimensions:

- `dim_customer`
- `dim_product`
- `dim_seller`
- `dim_return_reason` (defective, wrong_item, no_longer_wanted, etc.)
- `dim_date` — role-played for `return_request_date_key`
  and `return_completed_date_key`.

The grain is the *return*, not the original order
line. The fact joins back to `fact_order_lines` on
`order_line_id` if we need the original price.

**Interviewer:** Reviews?

**Candidate:** `fact_reviews` — a *factless fact*
(plus a measure or two). One row per review
submission. The "fact" is that a review exists.

Measures:

- `rating` (1–5)
- `helpful_votes` (additive)
- `verified_purchase` (boolean — degenerate flag)

Dimensions:

- `dim_customer`
- `dim_product`
- `dim_date`

Even though it's called a factless fact, the
`rating` and `helpful_votes` make it a regular
transactional fact. I'd call this one a "lean
transactional fact."

**Interviewer:** Tradeoffs?

**Candidate:** Three big ones:

1. **Order line vs order grain.** I picked line
   because Amazon reports on per-product GMV. If
   the only question is "how many orders per day,"
   order grain is fine. Line grain is strictly more
   powerful but larger.

2. **Inventory snapshot vs transactional.** I picked
   snapshot because inventory is state. The
   alternative (a "balance" measure on a
   transactional fact) is brittle.

3. **SCD 2 on product and seller.** Required for
   historical attribution. Cost: doubled dim size
   and temporal join cost. Worth it.

**Interviewer:** What's the most expensive query in
this model?

**Candidate:** Probably the seller performance
report. It joins three facts on the seller key,
each scanned for a date range. The optimizer can
help by pre-aggregating each fact to the
(seller, month) grain. If the seller perf report
is hit often, I'd add a rollup:

```sql
CREATE MATERIALIZED VIEW agg_seller_month AS
SELECT s.seller_key, d.month,
       SUM(f.net_amount) AS gmv,
       COUNT(*) AS order_lines
FROM fact_order_lines f
JOIN dim_seller s ON f.seller_key = s.seller_key
JOIN dim_date d ON f.order_date_key = d.date_key
GROUP BY s.seller_key, d.month;
```

And similar rollups for shipments and reviews. The
seller perf report then reads from the rollups, not
the raw facts.

**Interviewer:** Last question — how do you handle
the "frequently bought together" report?

**Candidate:** That's a *co-occurrence* query, not a
star-schema query. The standard pattern is a market
basket analysis: for each pair of products that
appear in the same order, count how many orders
contain that pair.

```sql
SELECT a.product_key AS product_a,
       b.product_key AS product_b,
       COUNT(*) AS co_purchase_count
FROM fact_order_lines a
JOIN fact_order_lines b
  ON a.order_id = b.order_id
 AND a.product_key < b.product_key
GROUP BY a.product_key, b.product_key
ORDER BY co_purchase_count DESC
LIMIT 100;
```

The fact has `order_id` as a degenerate dim, and
the self-join is on `order_id`. The result is a
"product affinity" table. For real-time
recommendations, this is computed in a batch job
and loaded into a key-value store.

**Interviewer:** That's time.

---

## Rubric scoring (4 buckets)

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about order, shipment, return granularity. |
| **Picks a grain** | 5/5 | Order line, shipment line, snapshot, return line, review. |
| **Makes and defends tradeoffs** | 5/5 | Snapshot vs transactional, line vs order, SCD 2. |
| **Talks while drawing** | 5/5 | Narrated every fact, every dim, every measure. |

---

## Take-aways

- **Four fact-table types, all in one warehouse** —
  transactional, periodic snapshot, factless, plus a
  "lean transactional" for reviews.
- **Conformed seller dim** — the same `dim_seller` is
  joined to orders, shipments, and reviews. That's the
  power of the conformed-dim pattern.
- **Inventory is a snapshot, not a transaction** —
  because inventory is *state*.
- **Co-occurrence query** — the standard market
  basket pattern with a self-join on `order_id`.

---

## Try it

Set a 30-minute timer. Draw all four fact tables and
their shared dimensions. Write the GMV query, the
seller performance query, and the "frequently bought
together" query.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
