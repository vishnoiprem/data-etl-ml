"""Working star schemas, one per practice lesson in module 03.

Each builder function takes a `QueryRunner` (a `common.QueryRunner`),
creates the tables via the `common.schema.Table` helper, and inserts
a small set of sample rows so the schema is queryable. Each
function returns the list of table names it created.

Schemas built:

  1. `build_ecommerce_schema`        — Lesson 16 (e-commerce)
  2. `build_rideshare_schema`        — Lesson 17 (ride-sharing)
  3. `build_instagram_schema`        — Lesson 18 (Instagram — backs the
                                        social-media practice; the
                                        event-grain schema is the
                                        same shape)
  4. `build_support_schema`          — (legacy schema kept for the
                                        working test suite; not in
                                        the current practice lineup)
  5. `build_spotify_schema`          — Lesson 20 (Spotify — backs the
                                        video-streaming practice; the
                                        streaming shape is the same)
  6. `build_cloud_services_schema`   — Lesson 19 (cloud services)
  7. `build_online_advertising_schema` — Lesson 15 (online advertising)

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from typing import List

from common import Column, QueryRunner, Table


# ---- 1. e-commerce -------------------------------------------------------


def build_ecommerce_schema(q: QueryRunner) -> List[str]:
    """E-commerce star schema, grain: one row per order line item.

    Fact table:    fact_order_items
    Dimensions:    dim_customers (SCD 2), dim_products (SCD 2),
                   dim_orders, dim_date.
    """
    dim_customers = Table("dim_customers", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("email", "TEXT", nullable=False),
        Column("country", "TEXT"),
        Column("segment", "TEXT"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_products = Table("dim_products", [
        Column("product_key", "INTEGER", primary_key=True),
        Column("product_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("category", "TEXT"),
        Column("price", "REAL"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_orders = Table("dim_orders", [
        Column("order_key", "INTEGER", primary_key=True),
        Column("order_id", "INTEGER", nullable=False),
        Column("status", "TEXT"),
        Column("payment_method", "TEXT"),
        Column("currency", "TEXT"),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("day_of_week", "INTEGER"),
        Column("week", "INTEGER"),
        Column("month", "INTEGER"),
        Column("quarter", "INTEGER"),
        Column("year", "INTEGER"),
        Column("is_weekend", "INTEGER"),
    ])

    fact_order_items = Table("fact_order_items", [
        Column("order_item_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customers(customer_key)"),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_products(product_key)"),
        Column("order_key", "INTEGER", nullable=False,
               references="dim_orders(order_key)"),
        Column("order_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("quantity", "INTEGER", nullable=False, default="1"),
        Column("unit_price", "REAL", nullable=False),
        Column("gross_amount", "REAL", nullable=False),
        Column("discount_amount", "REAL", nullable=False, default="0"),
        Column("net_amount", "REAL", nullable=False),
        Column("tax_amount", "REAL", nullable=False, default="0"),
    ])

    tables = [dim_customers, dim_products, dim_orders, dim_date, fact_order_items]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customers VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, 101, "Alice Smith", "alice@example.com", "US",
             "VIP", "2023-01-01", "9999-12-31", 1),
            (2, 102, "Bob Jones", "bob@example.com", "UK",
             "regular", "2023-01-01", "9999-12-31", 1),
            (3, 103, "Carol Patel", "carol@example.com", "IN",
             "VIP", "2023-01-01", "9999-12-31", 1),
            (4, 104, "Dan Kim", "dan@example.com", "KR",
             "regular", "2023-01-01", "9999-12-31", 1),
            (5, 105, "Eve Garcia", "eve@example.com", "MX",
             "regular", "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_products VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, "Premium Widget", "electronics", 99.99,
             "2023-01-01", "9999-12-31", 1),
            (2, 2, "Deluxe Gadget", "electronics", 49.99,
             "2023-01-01", "9999-12-31", 1),
            (3, 3, "Basic Doohickey", "home", 19.99,
             "2023-01-01", "9999-12-31", 1),
            (4, 4, "Smart Thingamajig", "electronics", 199.99,
             "2023-01-01", "9999-12-31", 1),
            (5, 5, "Eco Contraption", "garden", 29.99,
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_orders VALUES (?,?,?,?,?)",
        [
            (1, 1001, "delivered", "credit_card", "USD"),
            (2, 1002, "delivered", "paypal", "USD"),
            (3, 1003, "shipped", "credit_card", "EUR"),
            (4, 1004, "pending", "credit_card", "USD"),
            (5, 1005, "delivered", "credit_card", "USD"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?,?,?,?,?)",
        [
            (20240101, "2024-01-01", 1, 1, 1, 1, 2024, 0),
            (20240115, "2024-01-15", 2, 3, 1, 1, 2024, 0),
            (20240201, "2024-02-01", 5, 5, 2, 1, 2024, 0),
            (20240214, "2024-02-14", 4, 7, 2, 1, 2024, 0),
            (20240301, "2024-03-01", 6, 9, 3, 1, 2024, 0),
        ],
    )
    q.executemany(
        "INSERT INTO fact_order_items VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 20240115, 2, 99.99, 199.98, 0.0, 199.98, 16.0),
            (2, 1, 2, 1, 20240115, 1, 49.99, 49.99, 5.0, 44.99, 3.6),
            (3, 2, 3, 2, 20240201, 3, 19.99, 59.97, 0.0, 59.97, 4.8),
            (4, 3, 4, 3, 20240214, 1, 199.99, 199.99, 20.0, 179.99, 14.4),
            (5, 5, 5, 5, 20240301, 4, 29.99, 119.96, 12.0, 107.96, 8.6),
        ],
    )

    return [t.name for t in tables]


# ---- 2. ride-sharing -----------------------------------------------------


def build_rideshare_schema(q: QueryRunner) -> List[str]:
    """Ride-sharing star schema, grain: one row per completed trip.

    Fact tables:   fact_trips, fact_cancellations
    Dimensions:    dim_drivers (SCD 2), dim_riders, dim_cities (SCD 2),
                   dim_date, dim_time_of_day.
    """
    dim_drivers = Table("dim_drivers", [
        Column("driver_key", "INTEGER", primary_key=True),
        Column("driver_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("vehicle_type", "TEXT"),
        Column("rating", "REAL"),
        Column("city_key", "INTEGER", nullable=False,
               references="dim_cities(city_key)"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_riders = Table("dim_riders", [
        Column("rider_key", "INTEGER", primary_key=True),
        Column("rider_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
        Column("country", "TEXT"),
        Column("signup_date", "TEXT"),
    ])

    dim_cities = Table("dim_cities", [
        Column("city_key", "INTEGER", primary_key=True),
        Column("city_id", "INTEGER", nullable=False),
        Column("city_name", "TEXT", nullable=False),
        Column("country", "TEXT"),
        Column("base_fare", "REAL"),
        Column("per_km_rate", "REAL"),
        Column("per_min_rate", "REAL"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("quarter", "INTEGER"),
        Column("year", "INTEGER"),
        Column("day_of_week", "INTEGER"),
    ])

    dim_time_of_day = Table("dim_time_of_day", [
        Column("time_key", "INTEGER", primary_key=True),
        Column("hour", "INTEGER", nullable=False),
        Column("minute", "INTEGER", nullable=False),
        Column("part_of_day", "TEXT", nullable=False),
    ])

    fact_trips = Table("fact_trips", [
        Column("trip_key", "INTEGER", primary_key=True),
        Column("trip_id", "INTEGER", nullable=False),
        Column("driver_key", "INTEGER", nullable=False,
               references="dim_drivers(driver_key)"),
        Column("rider_key", "INTEGER", nullable=False,
               references="dim_riders(rider_key)"),
        Column("city_key", "INTEGER", nullable=False,
               references="dim_cities(city_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("start_time_key", "INTEGER", nullable=False,
               references="dim_time_of_day(time_key)"),
        Column("end_time_key", "INTEGER", nullable=False,
               references="dim_time_of_day(time_key)"),
        Column("distance_km", "REAL", nullable=False),
        Column("duration_min", "REAL", nullable=False),
        Column("surge_multiplier", "REAL", nullable=False, default="1.0"),
        Column("fare", "REAL", nullable=False),
        Column("tip", "REAL", nullable=False, default="0"),
        Column("total_revenue", "REAL", nullable=False),
    ])

    fact_cancellations = Table("fact_cancellations", [
        Column("cancel_key", "INTEGER", primary_key=True),
        Column("trip_id", "INTEGER", nullable=False),
        Column("driver_key", "INTEGER",
               references="dim_drivers(driver_key)"),
        Column("rider_key", "INTEGER",
               references="dim_riders(rider_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("minutes_to_cancel", "REAL", nullable=False),
        Column("canceled_by", "TEXT", nullable=False),
    ])

    tables = [
        dim_drivers, dim_riders, dim_cities, dim_date, dim_time_of_day,
        fact_trips, fact_cancellations,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_cities VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, "San Francisco", "US", 2.50, 1.20, 0.30,
             "2023-01-01", "9999-12-31", 1),
            (2, 2, "New York", "US", 2.75, 1.50, 0.35,
             "2023-01-01", "9999-12-31", 1),
            (3, 3, "London", "UK", 2.80, 1.40, 0.32,
             "2023-01-01", "9999-12-31", 1),
            (4, 4, "Berlin", "DE", 2.50, 1.30, 0.30,
             "2023-01-01", "9999-12-31", 1),
            (5, 5, "Tokyo", "JP", 3.00, 1.60, 0.40,
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_drivers VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, 201, "Frank Driver", "sedan", 4.8, 1,
             "2023-01-01", "9999-12-31", 1),
            (2, 202, "Grace Driver", "suv", 4.9, 1,
             "2023-01-01", "9999-12-31", 1),
            (3, 203, "Hank Driver", "sedan", 4.6, 2,
             "2023-01-01", "9999-12-31", 1),
            (4, 204, "Ivy Driver", "sedan", 4.7, 2,
             "2023-01-01", "9999-12-31", 1),
            (5, 205, "Judy Driver", "van", 4.8, 3,
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_riders VALUES (?,?,?,?,?)",
        [
            (1, 301, "Karen Rider", "US", "2022-06-15"),
            (2, 302, "Leo Rider", "UK", "2022-08-22"),
            (3, 303, "Mia Rider", "IN", "2023-01-05"),
            (4, 304, "Nate Rider", "US", "2023-04-12"),
            (5, 305, "Olive Rider", "DE", "2023-07-18"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?,?,?)",
        [
            (20240301, "2024-03-01", 3, 1, 2024, 6),
            (20240302, "2024-03-02", 3, 1, 2024, 7),
            (20240303, "2024-03-03", 3, 1, 2024, 1),
            (20240304, "2024-03-04", 3, 1, 2024, 2),
            (20240305, "2024-03-05", 3, 1, 2024, 3),
        ],
    )
    q.executemany(
        "INSERT INTO dim_time_of_day VALUES (?,?,?,?)",
        [
            (800, 8, 0, "morning"),
            (1200, 12, 0, "midday"),
            (1800, 18, 0, "evening"),
            (2200, 22, 0, "night"),
            (200, 2, 0, "late_night"),
        ],
    )
    q.executemany(
        "INSERT INTO fact_trips VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 5001, 1, 1, 1, 20240301, 800, 830, 5.2, 25, 1.5,
             18.50, 3.00, 21.50),
            (2, 5002, 2, 2, 1, 20240301, 1200, 1220, 3.1, 18, 1.0,
             11.40, 2.00, 13.40),
            (3, 5003, 3, 3, 2, 20240302, 1800, 1845, 8.7, 40, 2.0,
             42.20, 6.00, 48.20),
            (4, 5004, 4, 4, 2, 20240303, 2200, 2230, 6.4, 28, 1.2,
             25.10, 4.00, 29.10),
            (5, 5005, 5, 5, 3, 20240304, 200, 215, 4.0, 15, 1.0,
             13.50, 0.00, 13.50),
        ],
    )
    q.executemany(
        "INSERT INTO fact_cancellations VALUES (?,?,?,?,?,?,?)",
        [
            (1, 5006, 1, 1, 20240301, 2.0, "rider"),
            (2, 5007, 2, 2, 20240302, 5.0, "driver"),
            (3, 5008, 3, 3, 20240302, 1.5, "rider"),
            (4, 5009, 4, 4, 20240303, 3.0, "rider"),
            (5, 5010, 5, 5, 20240304, 0.5, "platform"),
        ],
    )

    return [t.name for t in tables]


# ---- 3. Instagram --------------------------------------------------------


def build_instagram_schema(q: QueryRunner) -> List[str]:
    """Instagram star schema, grain: one row per post interaction event.

    Fact table:    fact_post_events
    Dimensions:    dim_users (SCD 2), dim_posts, dim_date,
                   dim_event_type.
    """
    dim_users = Table("dim_users", [
        Column("user_key", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("username", "TEXT", nullable=False),
        Column("country", "TEXT"),
        Column("is_creator", "INTEGER", default="0"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_posts = Table("dim_posts", [
        Column("post_key", "INTEGER", primary_key=True),
        Column("post_id", "INTEGER", nullable=False),
        Column("user_key", "INTEGER", nullable=False,
               references="dim_users(user_key)"),
        Column("caption", "TEXT"),
        Column("media_type", "TEXT"),
        Column("posted_at", "TEXT"),
    ])

    dim_event_type = Table("dim_event_type", [
        Column("event_type_key", "INTEGER", primary_key=True),
        Column("event_type", "TEXT", nullable=False),
        Column("is_engagement", "INTEGER", default="1"),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])

    fact_post_events = Table("fact_post_events", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("post_key", "INTEGER", nullable=False,
               references="dim_posts(post_key)"),
        Column("actor_user_key", "INTEGER", nullable=False,
               references="dim_users(user_key)"),
        Column("author_user_key", "INTEGER", nullable=False,
               references="dim_users(user_key)"),
        Column("event_type_key", "INTEGER", nullable=False,
               references="dim_event_type(event_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("minute_of_day", "INTEGER"),
    ])

    tables = [dim_users, dim_posts, dim_event_type, dim_date, fact_post_events]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_users VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 401, "alice_photo", "US", 1,
             "2022-01-01", "9999-12-31", 1),
            (2, 402, "bob_travels", "UK", 1,
             "2022-01-01", "9999-12-31", 1),
            (3, 403, "carol_eats", "IN", 1,
             "2022-01-01", "9999-12-31", 1),
            (4, 404, "dan_codes", "US", 0,
             "2022-01-01", "9999-12-31", 1),
            (5, 405, "eve_runs", "DE", 0,
             "2022-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_posts VALUES (?,?,?,?,?,?)",
        [
            (1, 501, 1, "Sunset in SF 🌅", "image", "2024-01-15T18:00:00Z"),
            (2, 502, 2, "London fog", "image", "2024-01-16T09:00:00Z"),
            (3, 503, 3, "Street food in Mumbai", "image",
             "2024-01-17T20:00:00Z"),
            (4, 504, 1, "Golden Gate at dawn", "image",
             "2024-01-18T07:00:00Z"),
            (5, 505, 2, "Tea time", "image", "2024-01-19T16:00:00Z"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_event_type VALUES (?,?,?)",
        [
            (1, "view", 0),
            (2, "like", 1),
            (3, "comment", 1),
            (4, "share", 1),
            (5, "save", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240115, "2024-01-15", 1, 2024),
            (20240116, "2024-01-16", 1, 2024),
            (20240117, "2024-01-17", 1, 2024),
            (20240118, "2024-01-18", 1, 2024),
            (20240119, "2024-01-19", 1, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_post_events VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, 2, 1, 1, 20240115, 1100),
            (2, 1, 2, 1, 2, 20240115, 1101),
            (3, 1, 3, 1, 2, 20240115, 1105),
            (4, 2, 1, 2, 2, 20240116, 900),
            (5, 3, 1, 3, 3, 20240117, 2030),
            (6, 3, 2, 3, 2, 20240117, 2032),
            (7, 4, 3, 1, 2, 20240118, 715),
            (8, 4, 4, 1, 4, 20240118, 720),
            (9, 5, 1, 2, 5, 20240119, 1605),
            (10, 5, 3, 2, 2, 20240119, 1610),
        ],
    )

    return [t.name for t in tables]


# ---- 4. customer support -------------------------------------------------


def build_support_schema(q: QueryRunner) -> List[str]:
    """Customer support star schema, grain: one row per ticket event.

    Fact table:    fact_ticket_events
    Dimensions:    dim_customers (SCD 2), dim_tickets, dim_agents,
                   dim_date, dim_event_type.
    """
    dim_customers = Table("dim_customers", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
        Column("email", "TEXT"),
        Column("plan", "TEXT"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_tickets = Table("dim_tickets", [
        Column("ticket_key", "INTEGER", primary_key=True),
        Column("ticket_id", "INTEGER", nullable=False),
        Column("subject", "TEXT"),
        Column("category", "TEXT"),
        Column("priority", "TEXT"),
        Column("channel", "TEXT"),
    ])

    dim_agents = Table("dim_agents", [
        Column("agent_key", "INTEGER", primary_key=True),
        Column("agent_id", "INTEGER", nullable=False),
        Column("name", "TEXT"),
        Column("team", "TEXT"),
    ])

    dim_event_type = Table("dim_event_type", [
        Column("event_type_key", "INTEGER", primary_key=True),
        Column("event_type", "TEXT", nullable=False),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])

    fact_ticket_events = Table("fact_ticket_events", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("ticket_key", "INTEGER", nullable=False,
               references="dim_tickets(ticket_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customers(customer_key)"),
        Column("agent_key", "INTEGER",
               references="dim_agents(agent_key)"),
        Column("event_type_key", "INTEGER", nullable=False,
               references="dim_event_type(event_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("minutes_since_open", "REAL"),
    ])

    tables = [
        dim_customers, dim_tickets, dim_agents, dim_event_type, dim_date,
        fact_ticket_events,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customers VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 601, "Paul Customer", "paul@example.com", "free",
             "2023-01-01", "9999-12-31", 1),
            (2, 602, "Quinn Customer", "quinn@example.com", "pro",
             "2023-01-01", "9999-12-31", 1),
            (3, 603, "Rita Customer", "rita@example.com", "enterprise",
             "2023-01-01", "9999-12-31", 1),
            (4, 604, "Sam Customer", "sam@example.com", "pro",
             "2023-01-01", "9999-12-31", 1),
            (5, 605, "Tara Customer", "tara@example.com", "free",
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_tickets VALUES (?,?,?,?,?,?)",
        [
            (1, 701, "Password reset", "account", "low", "email"),
            (2, 702, "App crash on cart", "bug", "high", "in_app"),
            (3, 703, "Refund request", "billing", "medium", "email"),
            (4, 704, "Feature question", "question", "low", "chat"),
            (5, 705, "Login failure", "bug", "high", "email"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_agents VALUES (?,?,?,?)",
        [
            (1, 801, "Uma Agent", "tier1"),
            (2, 802, "Vince Agent", "tier2"),
            (3, 803, "Wendy Agent", "billing"),
            (4, 804, "Xander Agent", "tier1"),
            (5, 805, "Yara Agent", "tier2"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_event_type VALUES (?,?)",
        [
            (1, "opened"),
            (2, "assigned"),
            (3, "responded"),
            (4, "escalated"),
            (5, "resolved"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240401, "2024-04-01", 4, 2024),
            (20240402, "2024-04-02", 4, 2024),
            (20240403, "2024-04-03", 4, 2024),
            (20240404, "2024-04-04", 4, 2024),
            (20240405, "2024-04-05", 4, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_ticket_events VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240401, 0),
            (2, 1, 1, 1, 2, 20240401, 5),
            (3, 1, 1, 1, 3, 20240401, 30),
            (4, 1, 1, 1, 5, 20240401, 240),
            (5, 2, 2, 2, 1, 20240402, 0),
            (6, 2, 2, 2, 4, 20240402, 60),
            (7, 3, 3, 3, 1, 20240403, 0),
            (8, 3, 3, 3, 3, 20240403, 90),
            (9, 4, 4, 4, 1, 20240404, 0),
            (10, 5, 5, 5, 1, 20240405, 0),
        ],
    )

    return [t.name for t in tables]


# ---- 5. Spotify ----------------------------------------------------------


def build_spotify_schema(q: QueryRunner) -> List[str]:
    """Spotify star schema, grain: one row per music stream event.

    Fact table:    fact_streams
    Dimensions:    dim_users (SCD 2), dim_songs, dim_artists, dim_albums,
                   dim_date, dim_device_type.
    """
    dim_users = Table("dim_users", [
        Column("user_key", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("username", "TEXT"),
        Column("country", "TEXT"),
        Column("plan", "TEXT"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_artists = Table("dim_artists", [
        Column("artist_key", "INTEGER", primary_key=True),
        Column("artist_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("genre", "TEXT"),
    ])

    dim_albums = Table("dim_albums", [
        Column("album_key", "INTEGER", primary_key=True),
        Column("album_id", "INTEGER", nullable=False),
        Column("artist_key", "INTEGER", nullable=False,
               references="dim_artists(artist_key)"),
        Column("title", "TEXT", nullable=False),
        Column("release_year", "INTEGER"),
    ])

    dim_songs = Table("dim_songs", [
        Column("song_key", "INTEGER", primary_key=True),
        Column("song_id", "INTEGER", nullable=False),
        Column("album_key", "INTEGER", nullable=False,
               references="dim_albums(album_key)"),
        Column("artist_key", "INTEGER", nullable=False,
               references="dim_artists(artist_key)"),
        Column("title", "TEXT", nullable=False),
        Column("duration_sec", "INTEGER"),
        Column("release_decade", "INTEGER"),
    ])

    dim_device_type = Table("dim_device_type", [
        Column("device_type_key", "INTEGER", primary_key=True),
        Column("device_type", "TEXT", nullable=False),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])

    fact_streams = Table("fact_streams", [
        Column("stream_key", "INTEGER", primary_key=True),
        Column("user_key", "INTEGER", nullable=False,
               references="dim_users(user_key)"),
        Column("song_key", "INTEGER", nullable=False,
               references="dim_songs(song_key)"),
        Column("artist_key", "INTEGER", nullable=False,
               references="dim_artists(artist_key)"),
        Column("album_key", "INTEGER", nullable=False,
               references="dim_albums(album_key)"),
        Column("device_type_key", "INTEGER", nullable=False,
               references="dim_device_type(device_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("ms_played", "INTEGER", nullable=False),
        Column("was_skipped", "INTEGER", nullable=False, default="0"),
    ])

    tables = [
        dim_users, dim_artists, dim_albums, dim_songs, dim_device_type,
        dim_date, fact_streams,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_users VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 901, "Alice Listener", "US", "premium",
             "2022-01-01", "9999-12-31", 1),
            (2, 902, "Bob Listener", "UK", "free",
             "2022-01-01", "9999-12-31", 1),
            (3, 903, "Carol Listener", "IN", "premium",
             "2022-01-01", "9999-12-31", 1),
            (4, 904, "Dan Listener", "DE", "family",
             "2022-01-01", "9999-12-31", 1),
            (5, 905, "Eve Listener", "BR", "premium",
             "2022-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_artists VALUES (?,?,?,?)",
        [
            (1, 1001, "The Synthwave Boys", "synthwave"),
            (2, 1002, "Acoustic Ivy", "indie"),
            (3, 1003, "DJ Pulse", "electronic"),
            (4, 1004, "Forest Folk", "folk"),
            (5, 1005, "Velvet Brass", "jazz"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_albums VALUES (?,?,?,?,?)",
        [
            (1, 2001, 1, "Neon Nights", 2018),
            (2, 2002, 2, "Quiet Mornings", 2020),
            (3, 2003, 3, "Pulse", 2022),
            (4, 2004, 4, "Woods", 2017),
            (5, 2005, 5, "Brass Tacks", 2019),
        ],
    )
    q.executemany(
        "INSERT INTO dim_songs VALUES (?,?,?,?,?,?,?)",
        [
            (1, 3001, 1, 1, "Midnight Drive", 215, 2010),
            (2, 3002, 1, 1, "Ocean Highway", 245, 2010),
            (3, 3003, 2, 2, "First Light", 198, 2020),
            (4, 3004, 3, 3, "Heartbeat", 230, 2020),
            (5, 3005, 4, 4, "Moss", 187, 2010),
            (6, 3006, 5, 5, "Slow Burn", 264, 2010),
        ],
    )
    q.executemany(
        "INSERT INTO dim_device_type VALUES (?,?)",
        [
            (1, "ios"),
            (2, "android"),
            (3, "web"),
            (4, "speaker"),
            (5, "tv"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240501, "2024-05-01", 5, 2024),
            (20240502, "2024-05-02", 5, 2024),
            (20240503, "2024-05-03", 5, 2024),
            (20240504, "2024-05-04", 5, 2024),
            (20240505, "2024-05-05", 5, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_streams VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 1, 20240501, 215000, 0),
            (2, 1, 2, 1, 1, 1, 20240501, 245000, 0),
            (3, 2, 3, 2, 2, 2, 20240501, 198000, 0),
            (4, 2, 3, 2, 2, 2, 20240501, 30000, 1),
            (5, 3, 4, 3, 3, 3, 20240502, 230000, 0),
            (6, 3, 4, 3, 3, 3, 20240502, 230000, 0),
            (7, 4, 5, 4, 4, 4, 20240503, 187000, 0),
            (8, 5, 6, 5, 5, 5, 20240504, 264000, 0),
            (9, 5, 1, 1, 1, 5, 20240505, 215000, 0),
            (10, 1, 4, 3, 3, 1, 20240505, 230000, 0),
        ],
    )

    return [t.name for t in tables]


# ---- 6. cloud services ---------------------------------------------------


def build_cloud_services_schema(q: QueryRunner) -> List[str]:
    """Cloud services platform star schema (Lesson 19).

    Minimal implementation — enough to pass the test, not enough
    to be production. The structure mirrors the lesson's design:
    `fact_usage` with pre-computed `cost_usd`, a `dim_customer`
    on SCD 2, and a `dim_service` / `dim_region` / `dim_date`
    for the analytic dimensions.

    Fact table:    fact_usage
    Dimensions:    dim_customer (SCD 2), dim_service, dim_region,
                   dim_usage_type, dim_date.
    """
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("plan", "TEXT"),
        Column("country", "TEXT"),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_service = Table("dim_service", [
        Column("service_key", "INTEGER", primary_key=True),
        Column("service_id", "INTEGER", nullable=False),
        Column("service_name", "TEXT", nullable=False),
        Column("category", "TEXT"),
        Column("billing_unit", "TEXT"),
    ])

    dim_region = Table("dim_region", [
        Column("region_key", "INTEGER", primary_key=True),
        Column("region_id", "INTEGER", nullable=False),
        Column("region_name", "TEXT", nullable=False),
        Column("geography", "TEXT"),
    ])

    dim_usage_type = Table("dim_usage_type", [
        Column("usage_type_key", "INTEGER", primary_key=True),
        Column("usage_type", "TEXT", nullable=False),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])

    fact_usage = Table("fact_usage", [
        Column("usage_key", "INTEGER", primary_key=True),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("service_key", "INTEGER", nullable=False,
               references="dim_service(service_key)"),
        Column("region_key", "INTEGER", nullable=False,
               references="dim_region(region_key)"),
        Column("usage_type_key", "INTEGER", nullable=False,
               references="dim_usage_type(usage_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("usage_qty", "REAL", nullable=False),
        Column("unit_price", "REAL", nullable=False),
        Column("cost_usd", "REAL", nullable=False),
    ])

    tables = [
        dim_customer, dim_service, dim_region, dim_usage_type,
        dim_date, fact_usage,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1101, "Acme Corp", "enterprise", "US",
             "2023-01-01", "9999-12-31", 1),
            (2, 1102, "Globex", "business", "UK",
             "2023-01-01", "9999-12-31", 1),
            (3, 1103, "Initech", "developer", "IN",
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_service VALUES (?,?,?,?,?)",
        [
            (1, 2001, "EC2", "compute", "per_hour"),
            (2, 2002, "S3", "storage", "per_gb_hour"),
            (3, 2003, "CloudFront", "networking", "per_gb"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_region VALUES (?,?,?,?)",
        [
            (1, 3001, "us-east-1", "US"),
            (2, 3002, "eu-west-1", "EU"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_usage_type VALUES (?,?)",
        [
            (1, "compute_hours"),
            (2, "storage_gb_hours"),
            (3, "network_egress_gb"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240601, "2024-06-01", 6, 2024),
            (20240602, "2024-06-02", 6, 2024),
            (20240603, "2024-06-03", 6, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_usage VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240601, 100.0, 0.05, 5.0),
            (2, 1, 2, 1, 2, 20240601, 500.0, 0.02, 10.0),
            (3, 2, 3, 2, 3, 20240602, 200.0, 0.09, 18.0),
        ],
    )

    return [t.name for t in tables]


# ---- 7. online advertising -----------------------------------------------


def build_online_advertising_schema(q: QueryRunner) -> List[str]:
    """Online advertising platform star schema (Lesson 15).

    Minimal implementation — enough to pass the test, not enough
    to be production. One event-grain fact with 0/1 flag columns
    for impressions / clicks / conversions, plus cost and revenue
    measures, with `dim_advertiser` (SCD 2) and `dim_campaign`
    (SCD 2) as the analytic dimensions.

    Fact table:    fact_ad_events
    Dimensions:    dim_advertiser (SCD 2), dim_campaign (SCD 2),
                   dim_creative, dim_event_type, dim_date.
    """
    dim_advertiser = Table("dim_advertiser", [
        Column("advertiser_key", "INTEGER", primary_key=True),
        Column("advertiser_id", "INTEGER", nullable=False),
        Column("advertiser_name", "TEXT", nullable=False),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_campaign = Table("dim_campaign", [
        Column("campaign_key", "INTEGER", primary_key=True),
        Column("campaign_id", "INTEGER", nullable=False),
        Column("advertiser_key", "INTEGER", nullable=False,
               references="dim_advertiser(advertiser_key)"),
        Column("campaign_name", "TEXT", nullable=False),
        Column("effective_date", "TEXT", nullable=False),
        Column("expiry_date", "TEXT", nullable=False, default="'9999-12-31'"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])

    dim_creative = Table("dim_creative", [
        Column("creative_key", "INTEGER", primary_key=True),
        Column("creative_id", "INTEGER", nullable=False),
        Column("creative_name", "TEXT", nullable=False),
        Column("format", "TEXT"),
    ])

    dim_event_type = Table("dim_event_type", [
        Column("event_type_key", "INTEGER", primary_key=True),
        Column("event_type", "TEXT", nullable=False),
        Column("is_engagement", "INTEGER", default="0"),
    ])

    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])

    fact_ad_events = Table("fact_ad_events", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("advertiser_key", "INTEGER", nullable=False,
               references="dim_advertiser(advertiser_key)"),
        Column("campaign_key", "INTEGER", nullable=False,
               references="dim_campaign(campaign_key)"),
        Column("creative_key", "INTEGER", nullable=False,
               references="dim_creative(creative_key)"),
        Column("event_type_key", "INTEGER", nullable=False,
               references="dim_event_type(event_type_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("impressions", "INTEGER", nullable=False, default="0"),
        Column("clicks", "INTEGER", nullable=False, default="0"),
        Column("conversions", "INTEGER", nullable=False, default="0"),
        Column("cost_usd", "REAL", nullable=False, default="0"),
        Column("revenue_usd", "REAL", nullable=False, default="0"),
    ])

    tables = [
        dim_advertiser, dim_campaign, dim_creative, dim_event_type,
        dim_date, fact_ad_events,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_advertiser VALUES (?,?,?,?,?,?)",
        [
            (1, 4001, "Nike",
             "2023-01-01", "9999-12-31", 1),
            (2, 4002, "Coca-Cola",
             "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_campaign VALUES (?,?,?,?,?,?,?)",
        [
            (1, 5001, 1, "Air Max Q2", "2023-01-01", "9999-12-31", 1),
            (2, 5002, 2, "Summer Soda", "2023-01-01", "9999-12-31", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_creative VALUES (?,?,?,?)",
        [
            (1, 6001, "Sneaker Hero", "image"),
            (2, 6002, "Splash Banner", "display"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_event_type VALUES (?,?,?)",
        [
            (1, "impression", 0),
            (2, "click", 1),
            (3, "conversion", 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240701, "2024-07-01", 7, 2024),
            (20240702, "2024-07-02", 7, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO fact_ad_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240701, 1, 0, 0, 0.50, 0.0),
            (2, 1, 1, 1, 2, 20240701, 0, 1, 0, 0.0, 1.20),
            (3, 2, 2, 2, 1, 20240702, 1, 0, 0, 0.30, 0.0),
        ],
    )

    return [t.name for t in tables]


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Building star schemas for module 03 practice lessons...\n")
    for name, fn in [
        ("ecommerce", build_ecommerce_schema),
        ("rideshare", build_rideshare_schema),
        ("instagram", build_instagram_schema),
        ("support", build_support_schema),
        ("spotify", build_spotify_schema),
        ("cloud_services", build_cloud_services_schema),
        ("online_advertising", build_online_advertising_schema),
    ]:
        with QueryRunner(":memory:") as q:
            tables = fn(q)
            print(f"[{name}]  tables: {tables}")
            # Show one row from the fact table to prove it's queryable.
            for tn in tables:
                if tn.startswith("fact_"):
                    rows = q.query_all(f"SELECT * FROM {tn} LIMIT 1")
                    print(f"   {tn} sample row: {rows[0]}")
        print()
    print("All schemas built and queryable.")
