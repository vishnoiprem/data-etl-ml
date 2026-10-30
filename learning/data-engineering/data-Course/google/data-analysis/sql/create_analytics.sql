-- create_analytics.sql — the tables the semantic layer sits on.
--
-- The DDL encodes the two decisions the chapters argue about:
--
--   1. The **grain**. `orders` is one row per order *line*, and the
--      primary key says so. `orders.order_id` is deliberately NOT
--      unique, and there is a comment next to it saying why — because
--      the next engineer to arrive will try to make it unique and break
--      the model.
--
--   2. The **join keys**. Every foreign key is indexed, because a
--      dashboard that joins without an index does not time out, it
--      just gets slow enough that people stop refreshing it.

CREATE TABLE IF NOT EXISTS analytics.customers (
    customer_id      STRING    NOT NULL,
    name             STRING    NOT NULL,
    segment          STRING    NOT NULL,
    country          STRING    NOT NULL,
    signup_date      DATE      NOT NULL,
    lifetime_value   NUMERIC   DEFAULT 0,

    -- One row per customer. This is the grain.
    PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS analytics.products (
    product_id       STRING    NOT NULL,
    name             STRING    NOT NULL,
    category         STRING    NOT NULL,
    supplier         STRING    NOT NULL,
    cost             NUMERIC   DEFAULT 0,
    list_price       NUMERIC   DEFAULT 0,

    -- One row per product. This is the grain.
    PRIMARY KEY (product_id)
);

CREATE TABLE IF NOT EXISTS analytics.orders (
    line_id          STRING    NOT NULL,
    order_id         STRING    NOT NULL,
    customer_id      STRING    NOT NULL,
    product_id       STRING,
    quantity         INT64     DEFAULT 1,
    unit_price       NUMERIC   DEFAULT 0,
    total_amount     NUMERIC   DEFAULT 0,
    margin_amount    NUMERIC   DEFAULT 0,
    region           STRING,
    channel          STRING,
    status           STRING,
    product_category STRING,
    created_at       TIMESTAMP NOT NULL,

    -- The grain: one row per order LINE.
    --
    -- `order_id` is deliberately NOT the primary key and is NOT unique.
    -- An order with three lines has three rows. Every measure over this
    -- table is a measure over order lines — which is why "count" here
    -- counts lines and not orders.
    PRIMARY KEY (line_id),

    -- The join keys, indexed. A fan-out join without an index does not
    -- fail; it just gets slow enough that people stop using the report.
    FOREIGN KEY (customer_id) REFERENCES analytics.customers (customer_id),
    FOREIGN KEY (product_id)  REFERENCES analytics.products (product_id)
);

-- The date spine.
--
-- A fact table has no row for a day on which nothing happened. Joining
-- the fact table to this spine is what turns a gap in the chart into a
-- zero.
--
-- `calendar_date` is generated, not loaded, so it can never have a hole
-- in it. `is_holiday` and `event_name` are optional enrichment.
CREATE TABLE IF NOT EXISTS analytics.date_spine (
    calendar_date    DATE      NOT NULL,
    year             INT64     NOT NULL,
    quarter          INT64     NOT NULL,
    month            INT64     NOT NULL,
    week             INT64     NOT NULL,
    day_of_week      INT64     NOT NULL,
    year_month       STRING    NOT NULL,
    year_quarter     STRING    NOT NULL,
    is_holiday       BOOL      DEFAULT FALSE,
    event_name       STRING,

    PRIMARY KEY (calendar_date)
);
