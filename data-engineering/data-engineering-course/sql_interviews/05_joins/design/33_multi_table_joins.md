# Lesson 33 — Multiple-Table Joins

> **Goal:** joining 3+ tables. The pattern behind every
> real analytics query.

---

## The shape

```sql
SELECT <columns>
FROM   A
JOIN   B ON A.b_id = B.id
JOIN   C ON B.c_id = C.id
LEFT JOIN D ON A.d_id = D.id
WHERE  <predicates>
GROUP BY <columns>
ORDER BY <columns>;
```

Most production queries are some elaboration of this.
Familiarize yourself with it.

---

## A worked example

Three tables: `Orders(id, customer_id, order_date)`,
`Customer(id, name, country)`, `OrderItem(id, order_id,
product_id, quantity, unit_price)`.

> "For each order, show the customer name, country, the
> number of line items, and the total amount."

```sql
SELECT
  o.id                AS order_id,
  c.name              AS customer_name,
  c.country           AS country,
  COUNT(oi.id)        AS n_items,
  SUM(oi.quantity * oi.unit_price) AS total
FROM   Orders     o
JOIN   Customer   c  ON o.customer_id = c.id
LEFT JOIN OrderItem oi ON oi.order_id = o.id
GROUP BY o.id, c.name, c.country
ORDER BY o.id;
```

A few things to note:

- The `LEFT JOIN` to `OrderItem` keeps orders with zero line
  items. With `JOIN`, those orders would disappear and
  `COUNT(oi.id)` would not count them.
- `COUNT(oi.id)` counts non-NULL `oi.id`, which is 0 for
  orders with no items. `COUNT(*)` would be 1.
- The GROUP BY columns are `o.id, c.name, c.country`. Strict
  databases require every non-aggregate SELECT column here.

---

## Mixing INNER and OUTER

```sql
SELECT
  o.id,
  c.name,
  p.name AS product_name
FROM   Orders     o
JOIN   Customer   c  ON o.customer_id = c.id        -- inner: required
LEFT JOIN OrderItem oi ON oi.order_id = o.id        -- outer: keep orders
LEFT JOIN Product    p  ON oi.product_id = p.id;    -- outer: keep items
```

The first JOIN is INNER because an order without a customer
is meaningless (data error). The second and third are
LEFT JOIN because an order without line items or a product
without a name is real (data we want to keep).

**Order matters for OUTER JOINs, not for INNER JOINs.** A
LEFT JOIN followed by another LEFT JOIN keeps the unmatched
rows from the first. A LEFT JOIN followed by an INNER JOIN
can drop the unmatched rows from the first, because the
INNER JOIN's null-padded row fails the predicate.

---

## The order of joins

The SQL `FROM` clause is evaluated left to right (with the
optimizer free to reorder INNER JOINs). For OUTER JOINs,
the order is more constrained:

- A LEFT JOIN's right side can reference the left side.
- A LEFT JOIN's right side can be joined further (with
  another LEFT JOIN).
- A LEFT JOIN's *result* cannot be referenced from the
  *left* of an earlier join.

This sounds abstract. In practice:

```sql
-- OK
SELECT *
FROM   A
LEFT JOIN B ON A.b_id = B.id
LEFT JOIN C ON B.c_id = C.id;          -- C can reference B (from same JOIN block)

-- Also OK: A -> B -> C
SELECT *
FROM   A
LEFT JOIN B ON A.b_id = B.id
LEFT JOIN C ON A.c_id = C.id;          -- C can reference A directly
```

You cannot have a LEFT JOIN *preceded* by a clause that
references its output. So the order in your FROM clause is
roughly the order of dependencies between tables.

---

## Comma joins

The old-style comma-separated FROM is still valid SQL:

```sql
SELECT e.name, d.department_name
FROM   Employee e, Department d
WHERE  e.department_id = d.id;
```

This is an *implicit* CROSS JOIN with a WHERE filter. It's
equivalent to `... FROM Employee e CROSS JOIN Department d
WHERE e.department_id = d.id`, which is the same as `...
FROM Employee e JOIN Department d ON e.department_id =
d.id`.

**Avoid the comma form.** Modern JOIN syntax is clearer,
harder to get wrong (no accidental CROSS JOIN), and the
recommended style in every style guide.

---

## A common bug: filter vs join

```sql
-- BUG: filter in JOIN drops rows that should be kept
SELECT o.id, c.name
FROM   Orders o
LEFT JOIN Customer c ON o.customer_id = c.id
WHERE  c.country = 'US';

-- FIX: filter in ON keeps the LEFT JOIN semantics
SELECT o.id, c.name
FROM   Orders o
LEFT JOIN Customer c ON o.customer_id = c.id
                    AND c.country = 'US';
```

This is the Lesson 29 lesson applied to multi-table joins.
The first query drops every order whose customer is not
from the US (or who has no customer at all). The second
query keeps every order; for orders with a non-US customer
or no customer, `c.name` is NULL.

---

## Try it

Given `Orders(id, customer_id, order_date)`,
`Customer(id, name, country)`, `OrderItem(id, order_id,
product_id, quantity, unit_price)`, `Product(id, name,
category)`:

1. List every order with the customer name, country, and
   total spend. Use INNER JOINs.
2. Same as 1, but also include the names of the products
   on each line. (You'll need a row per line item, not per
   order.)
3. Find every order placed by a US customer, including
   orders with no line items. (Use LEFT JOIN.)
