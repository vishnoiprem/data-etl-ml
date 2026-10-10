"""Solutions to the M07 mock interview problems.

Six end-to-end star schemas with sample data, in
working SQLite:

  * Ride-sharing (Lesson 31) — `build_ride_sharing`.
  * Customer support (Lesson 32) — `build_customer_support`.
  * Airbnb (Lesson 33) — `build_airbnb`.
  * Stripe (Lesson 34) — `build_stripe`.
  * Instagram (Lesson 35) — `build_instagram`.
  * Amazon (Lesson 36) — `build_amazon`.

Each function returns the list of tables it created,
so the tests can inspect them.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from typing import List

from common import Column, QueryRunner, Table


# ---- Ride-Sharing -------------------------------------------------------


def build_ride_sharing(q: QueryRunner) -> List[str]:
    """Ride-sharing star schema (Uber / Lyft).

    Central fact: `fact_trips`, grain = one row per
    trip. Dimensions: rider (SCD 2), driver (SCD 2),
    city, date (role-played), time (role-played),
    payment_method, promotion, surge_zone.
    """
    dim_rider = Table("dim_rider", [
        Column("rider_key", "INTEGER", primary_key=True),
        Column("rider_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("home_city", "TEXT", nullable=False),
        Column("rating", "REAL"),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_driver = Table("dim_driver", [
        Column("driver_key", "INTEGER", primary_key=True),
        Column("driver_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("vehicle_make", "TEXT"),
        Column("vehicle_model", "TEXT"),
        Column("city", "TEXT", nullable=False),
        Column("rating", "REAL"),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_city = Table("dim_city", [
        Column("city_key", "INTEGER", primary_key=True),
        Column("city_name", "TEXT", nullable=False),
        Column("state", "TEXT"),
        Column("country", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
        Column("month", "INTEGER"),
        Column("year", "INTEGER"),
    ])
    dim_time = Table("dim_time", [
        Column("time_key", "INTEGER", primary_key=True),
        Column("hour", "INTEGER", nullable=False),
        Column("minute", "INTEGER", nullable=False),
        Column("hour_bucket", "TEXT"),
    ])
    dim_payment_method = Table("dim_payment_method", [
        Column("payment_method_key", "INTEGER", primary_key=True),
        Column("method_name", "TEXT", nullable=False),
    ])
    dim_promotion = Table("dim_promotion", [
        Column("promotion_key", "INTEGER", primary_key=True),
        Column("promo_code", "TEXT", nullable=False),
        Column("discount_pct", "REAL", nullable=False),
    ])
    fact_trips = Table("fact_trips", [
        Column("trip_key", "INTEGER", primary_key=True),
        Column("rider_key", "INTEGER", nullable=False,
               references="dim_rider(rider_key)"),
        Column("driver_key", "INTEGER", nullable=False,
               references="dim_driver(driver_key)"),
        Column("city_key", "INTEGER", nullable=False,
               references="dim_city(city_key)"),
        Column("request_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("pickup_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("dropoff_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("request_time_key", "INTEGER", nullable=False,
               references="dim_time(time_key)"),
        Column("pickup_time_key", "INTEGER", nullable=False,
               references="dim_time(time_key)"),
        Column("dropoff_time_key", "INTEGER", nullable=False,
               references="dim_time(time_key)"),
        Column("payment_method_key", "INTEGER", nullable=False,
               references="dim_payment_method(payment_method_key)"),
        Column("promotion_key", "INTEGER",
               references="dim_promotion(promotion_key)"),
        Column("fare_amount", "REAL", nullable=False),
        Column("surge_multiplier", "REAL", nullable=False, default="1.0"),
        Column("total_amount", "REAL", nullable=False),
        Column("tip_amount", "REAL", nullable=False, default="0"),
        Column("distance_miles", "REAL"),
        Column("duration_seconds", "INTEGER"),
        Column("driver_payout", "REAL", nullable=False),
    ])
    tables = [
        dim_rider, dim_driver, dim_city, dim_date, dim_time,
        dim_payment_method, dim_promotion, fact_trips,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_rider VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1001, "Alice", "NYC",  4.8, 20240101, None,     1),
            (2, 1002, "Bob",   "NYC",  4.6, 20240101, None,     1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_driver VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 501, "Carlos", "Toyota",  "Prius",  "NYC", 4.9, 20240101, None, 1),
            (2, 502, "Dana",   "Honda",   "Civic",  "NYC", 4.7, 20240101, None, 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_city VALUES (?,?,?,?)",
        [(1, "NYC", "NY", "USA"), (2, "SF", "CA", "USA")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?)",
        [
            (20240110, "2024-01-10", 1, 2024),
            (20240111, "2024-01-11", 1, 2024),
            (20240112, "2024-01-12", 1, 2024),
        ],
    )
    q.executemany(
        "INSERT INTO dim_time VALUES (?,?,?,?)",
        [
            (540,  9,  0, "morning"),
            (1080, 18, 0, "evening"),
            (1140, 19, 0, "evening"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_payment_method VALUES (?,?)",
        [(1, "credit_card"), (2, "apple_pay")],
    )
    q.executemany(
        "INSERT INTO dim_promotion VALUES (?,?,?)",
        [(1, "NONE", 0.0), (2, "WELCOME10", 10.0)],
    )
    # 3 trips, one with a promo.
    q.executemany(
        "INSERT INTO fact_trips VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 20240110, 20240110, 20240110,
             540, 545, 575, 1, 2, 25.0, 1.0, 25.0, 0.0,
             3.2, 1800, 18.0),
            (2, 1, 2, 1, 20240111, 20240111, 20240111,
             1080, 1085, 1115, 1, 1, 15.0, 1.5, 22.5, 3.0,
             2.0, 1800, 16.0),
            (3, 2, 1, 1, 20240112, 20240112, 20240112,
             1140, 1145, 1170, 2, 1, 20.0, 1.0, 20.0, 0.0,
             1.8, 1500, 14.0),
        ],
    )
    return [t.name for t in tables]


# ---- Customer Support ---------------------------------------------------


def build_customer_support(q: QueryRunner) -> List[str]:
    """Customer support star schema (Zendesk / Intercom).

    Central fact: `fact_ticket_events`, grain = one
    row per ticket lifecycle event. Plus
    `fact_csat_surveys` for the survey workflow.
    """
    dim_ticket = Table("dim_ticket", [
        Column("ticket_key", "INTEGER", primary_key=True),
        Column("ticket_id", "INTEGER", nullable=False),
        Column("subject", "TEXT", nullable=False),
        Column("priority", "TEXT", nullable=False),
        Column("product", "TEXT"),
        Column("created_at", "INTEGER", nullable=False),
    ])
    dim_agent = Table("dim_agent", [
        Column("agent_key", "INTEGER", primary_key=True),
        Column("agent_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("team", "TEXT", nullable=False),
        Column("tier", "TEXT", nullable=False),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("plan", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
    ])
    dim_channel = Table("dim_channel", [
        Column("channel_key", "INTEGER", primary_key=True),
        Column("channel_name", "TEXT", nullable=False),
    ])
    dim_event_type = Table("dim_event_type", [
        Column("event_type_key", "INTEGER", primary_key=True),
        Column("event_type_name", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact_ticket_events = Table("fact_ticket_events", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("ticket_key", "INTEGER", nullable=False,
               references="dim_ticket(ticket_key)"),
        Column("agent_key", "INTEGER",
               references="dim_agent(agent_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("channel_key", "INTEGER", nullable=False,
               references="dim_channel(channel_key)"),
        Column("event_type_key", "INTEGER", nullable=False,
               references="dim_event_type(event_type_key)"),
        Column("event_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("event_ts", "INTEGER", nullable=False),
        Column("from_status", "TEXT"),
        Column("to_status", "TEXT"),
        Column("response_seconds", "INTEGER"),
        Column("is_sla_breach", "INTEGER", nullable=False, default="0"),
    ])
    fact_csat_surveys = Table("fact_csat_surveys", [
        Column("survey_key", "INTEGER", primary_key=True),
        Column("ticket_key", "INTEGER", nullable=False,
               references="dim_ticket(ticket_key)"),
        Column("agent_key", "INTEGER",
               references="dim_agent(agent_key)"),
        Column("channel_key", "INTEGER", nullable=False,
               references="dim_channel(channel_key)"),
        Column("survey_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("rating", "INTEGER", nullable=False),
        Column("response_lag_hours", "INTEGER", nullable=False),
    ])
    tables = [
        dim_ticket, dim_agent, dim_customer, dim_channel,
        dim_event_type, dim_date,
        fact_ticket_events, fact_csat_surveys,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_ticket VALUES (?,?,?,?,?,?)",
        [
            (1, 9001, "Login broken",  "P1", "web",    20240110),
            (2, 9002, "Slow checkout", "P2", "web",    20240111),
            (3, 9003, "Bug in export", "P3", "mobile", 20240112),
        ],
    )
    q.executemany(
        "INSERT INTO dim_agent VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 201, "Eve",   "T1", "tier1", 20240101, None,     1),
            (2, 202, "Frank", "T2", "tier2", 20240101, None,     1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?,?)",
        [
            (1, 7001, "Acme",   "pro",   "USA"),
            (2, 7002, "Globex", "free",  "USA"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_channel VALUES (?,?)",
        [(1, "email"), (2, "chat"), (3, "phone")],
    )
    q.executemany(
        "INSERT INTO dim_event_type VALUES (?,?)",
        [
            (1, "created"),
            (2, "replied"),
            (3, "status_changed"),
            (4, "resolved"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240110, "2024-01-10"),
            (20240111, "2024-01-11"),
            (20240112, "2024-01-12"),
            (20240113, "2024-01-13"),
        ],
    )
    # Ticket 1: created email, replied chat, resolved.
    # Ticket 2: created email, status changed pending, replied, resolved.
    # Ticket 3: created phone, no reply yet.
    q.executemany(
        "INSERT INTO fact_ticket_events VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, None, 1, 1, 1, 20240110, 1000, None, "new",          None, 0),
            (2, 1, 1,    1, 2, 2, 20240110, 1300, None, None,           300,  0),
            (3, 1, 1,    1, 2, 4, 20240110, 1900, None, "resolved",     None, 0),
            (4, 2, None, 2, 1, 1, 20240111, 2000, None, "new",          None, 0),
            (5, 2, 1,    2, 1, 3, 20240111, 2100, "new", "pending",     None, 0),
            (6, 2, 2,    2, 2, 2, 20240112, 900,  None, None,           9000, 1),
            (7, 2, 2,    2, 2, 4, 20240112, 1500, None, "resolved",     None, 0),
            (8, 3, None, 1, 3, 1, 20240112, 1100, None, "new",          None, 0),
        ],
    )
    q.executemany(
        "INSERT INTO fact_csat_surveys VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 2, 20240111, 5, 8),
            (2, 2, 2, 2, 20240113, 4, 24),
        ],
    )
    return [t.name for t in tables]


# ---- Airbnb -------------------------------------------------------------


def build_airbnb(q: QueryRunner) -> List[str]:
    """Airbnb star schema.

    Three facts: `fact_search_events` (per-search),
    `fact_search_impressions` (per-listing shown),
    `fact_bookings` (per-booking). Plus `fact_reviews`.
    """
    dim_listing = Table("dim_listing", [
        Column("listing_key", "INTEGER", primary_key=True),
        Column("listing_id", "INTEGER", nullable=False),
        Column("host_key", "INTEGER", nullable=False),
        Column("title", "TEXT", nullable=False),
        Column("property_type", "TEXT"),
        Column("city", "TEXT", nullable=False),
        Column("base_price_cents", "INTEGER", nullable=False),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_host = Table("dim_host", [
        Column("host_key", "INTEGER", primary_key=True),
        Column("host_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
        Column("is_superhost", "INTEGER", nullable=False, default="0"),
    ])
    dim_guest = Table("dim_guest", [
        Column("guest_key", "INTEGER", primary_key=True),
        Column("guest_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
    ])
    dim_location = Table("dim_location", [
        Column("location_key", "INTEGER", primary_key=True),
        Column("country", "TEXT", nullable=False),
        Column("state", "TEXT"),
        Column("city", "TEXT", nullable=False),
        Column("neighborhood", "TEXT"),
        Column("parent_location_key", "INTEGER"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact_search_events = Table("fact_search_events", [
        Column("search_key", "INTEGER", primary_key=True),
        Column("guest_key", "INTEGER", nullable=False,
               references="dim_guest(guest_key)"),
        Column("destination_location_key", "INTEGER", nullable=False,
               references="dim_location(location_key)"),
        Column("search_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("checkin_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("checkout_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("num_guests", "INTEGER", nullable=False),
        Column("num_results", "INTEGER", nullable=False),
    ])
    fact_search_impressions = Table("fact_search_impressions", [
        Column("impression_key", "INTEGER", primary_key=True),
        Column("search_key", "INTEGER", nullable=False,
               references="fact_search_events(search_key)"),
        Column("listing_key", "INTEGER", nullable=False,
               references="dim_listing(listing_key)"),
        Column("position", "INTEGER", nullable=False),
        Column("price_shown_cents", "INTEGER", nullable=False),
        Column("was_clicked", "INTEGER", nullable=False, default="0"),
    ])
    fact_bookings = Table("fact_bookings", [
        Column("booking_key", "INTEGER", primary_key=True),
        Column("listing_key", "INTEGER", nullable=False,
               references="dim_listing(listing_key)"),
        Column("guest_key", "INTEGER", nullable=False,
               references="dim_guest(guest_key)"),
        Column("host_key", "INTEGER", nullable=False,
               references="dim_host(host_key)"),
        Column("referrer_search_key", "INTEGER",
               references="fact_search_events(search_key)"),
        Column("book_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("checkin_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("checkout_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("nights", "INTEGER", nullable=False),
        Column("total_payout_cents", "INTEGER", nullable=False),
        Column("platform_fee_cents", "INTEGER", nullable=False),
    ])
    fact_reviews = Table("fact_reviews", [
        Column("review_key", "INTEGER", primary_key=True),
        Column("booking_key", "INTEGER", nullable=False,
               references="fact_bookings(booking_key)"),
        Column("listing_key", "INTEGER", nullable=False,
               references="dim_listing(listing_key)"),
        Column("guest_key", "INTEGER", nullable=False,
               references="dim_guest(guest_key)"),
        Column("review_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("rating_overall", "INTEGER", nullable=False),
        Column("sentiment_score", "REAL"),
    ])
    tables = [
        dim_listing, dim_host, dim_guest, dim_location, dim_date,
        fact_search_events, fact_search_impressions,
        fact_bookings, fact_reviews,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_listing VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 11, 1, "Cozy loft in Paris",  "apartment", "Paris",  15000, 20240101, None, 1),
            (2, 12, 2, "Beach house in Nice", "house",     "Nice",   25000, 20240101, None, 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_host VALUES (?,?,?,?,?)",
        [
            (1, 100, "Hilde",  "France", 1),
            (2, 101, "Pierre", "France", 0),
        ],
    )
    q.executemany(
        "INSERT INTO dim_guest VALUES (?,?,?,?)",
        [
            (1, 901, "Alice", "USA"),
            (2, 902, "Bob",   "UK"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_location VALUES (?,?,?,?,?,?)",
        [
            (1, "France", None,    "Paris",  "Marais",  None),
            (2, "France", None,    "Nice",   "Old Town", None),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240110, "2024-01-10"),
            (20240111, "2024-01-11"),
            (20240112, "2024-01-12"),
        ],
    )
    # 2 searches, each with 2 impressions.
    q.executemany(
        "INSERT INTO fact_search_events VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240110, 20240115, 20240120, 2, 42),
            (2, 2, 1, 20240111, 20240118, 20240122, 1, 38),
        ],
    )
    q.executemany(
        "INSERT INTO fact_search_impressions VALUES (?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 15000, 1),
            (2, 1, 2, 2, 25000, 0),
            (3, 2, 1, 1, 15000, 1),
            (4, 2, 2, 2, 25000, 0),
        ],
    )
    # 2 bookings, both from search 1 (referrer).
    q.executemany(
        "INSERT INTO fact_bookings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 20240111, 20240115, 20240120, 5, 75000, 7500),
            (2, 2, 1, 1, 1, 20240111, 20240115, 20240120, 5, 125000, 12500),
        ],
    )
    q.executemany(
        "INSERT INTO fact_reviews VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 20240120, 5, 0.92),
            (2, 2, 2, 1, 20240120, 4, 0.65),
        ],
    )
    return [t.name for t in tables]


# ---- Stripe -------------------------------------------------------------


def build_stripe(q: QueryRunner) -> List[str]:
    """Stripe payments star schema.

    Three facts: `fact_charge_events` (charge
    lifecycle), `fact_payouts` (payout legs),
    `fact_disputes` (dispute lifecycle). Plus
    `fact_balance_ledger` for reconciliation.
    """
    dim_merchant = Table("dim_merchant", [
        Column("merchant_key", "INTEGER", primary_key=True),
        Column("merchant_id", "INTEGER", nullable=False),
        Column("business_name", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
        Column("default_currency", "TEXT", nullable=False),
        Column("plan", "TEXT", nullable=False),
    ])
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("email", "TEXT", nullable=False),
    ])
    dim_currency = Table("dim_currency", [
        Column("currency_key", "INTEGER", primary_key=True),
        Column("currency_code", "TEXT", nullable=False),
        Column("decimal_places", "INTEGER", nullable=False),
    ])
    dim_country = Table("dim_country", [
        Column("country_key", "INTEGER", primary_key=True),
        Column("iso_code", "TEXT", nullable=False),
        Column("name", "TEXT", nullable=False),
    ])
    dim_charge = Table("dim_charge", [
        Column("charge_key", "INTEGER", primary_key=True),
        Column("charge_id", "TEXT", nullable=False),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("description", "TEXT"),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact_charge_events = Table("fact_charge_events", [
        Column("event_key", "INTEGER", primary_key=True),
        Column("charge_key", "INTEGER", nullable=False,
               references="dim_charge(charge_key)"),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("currency_key", "INTEGER", nullable=False,
               references="dim_currency(currency_key)"),
        Column("country_key", "INTEGER", nullable=False,
               references="dim_country(country_key)"),
        Column("event_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("event_type", "TEXT", nullable=False),
        Column("amount_minor", "INTEGER", nullable=False),
        Column("amount_usd_minor", "INTEGER", nullable=False),
        Column("fee_minor", "INTEGER", nullable=False, default="0"),
        Column("net_minor", "INTEGER", nullable=False, default="0"),
        Column("is_successful", "INTEGER", nullable=False, default="1"),
    ])
    fact_payouts = Table("fact_payouts", [
        Column("payout_leg_key", "INTEGER", primary_key=True),
        Column("payout_id", "TEXT", nullable=False),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("currency_key", "INTEGER", nullable=False,
               references="dim_currency(currency_key)"),
        Column("arrival_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("amount_minor", "INTEGER", nullable=False),
        Column("amount_usd_minor", "INTEGER", nullable=False),
        Column("status", "TEXT", nullable=False),
    ])
    fact_disputes = Table("fact_disputes", [
        Column("dispute_event_key", "INTEGER", primary_key=True),
        Column("dispute_id", "TEXT", nullable=False),
        Column("charge_key", "INTEGER", nullable=False,
               references="dim_charge(charge_key)"),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("event_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("event_type", "TEXT", nullable=False),
        Column("amount_minor", "INTEGER", nullable=False),
        Column("reason", "TEXT"),
    ])
    fact_balance_ledger = Table("fact_balance_ledger", [
        Column("ledger_key", "INTEGER", primary_key=True),
        Column("merchant_key", "INTEGER", nullable=False,
               references="dim_merchant(merchant_key)"),
        Column("event_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("event_type", "TEXT", nullable=False),
        Column("amount_minor", "INTEGER", nullable=False),
        Column("balance_after_minor", "INTEGER", nullable=False),
        Column("charge_key", "INTEGER",
               references="dim_charge(charge_key)"),
        Column("payout_id", "TEXT"),
    ])
    tables = [
        dim_merchant, dim_customer, dim_currency, dim_country,
        dim_charge, dim_date,
        fact_charge_events, fact_payouts, fact_disputes,
        fact_balance_ledger,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_merchant VALUES (?,?,?,?,?,?)",
        [
            (1, 1, "Acme",  "USA", "USD", "standard"),
            (2, 2, "Globex", "FR", "EUR", "custom"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?)",
        [
            (1, 100, 1, "alice@acme.com"),
            (2, 101, 1, "bob@acme.com"),
            (3, 200, 2, "pierre@globex.com"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_currency VALUES (?,?,?)",
        [(1, "USD", 2), (2, "EUR", 2)],
    )
    q.executemany(
        "INSERT INTO dim_country VALUES (?,?,?)",
        [(1, "US", "United States"), (2, "FR", "France")],
    )
    q.executemany(
        "INSERT INTO dim_charge VALUES (?,?,?,?,?)",
        [
            (1, "ch_001", 1, 1, "T-shirt"),
            (2, "ch_002", 1, 2, "Mug"),
            (3, "ch_003", 2, 3, "Shoes"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240110, "2024-01-10"),
            (20240111, "2024-01-11"),
            (20240115, "2024-01-15"),
        ],
    )
    # 3 charges, each goes captured.  One refund.
    q.executemany(
        "INSERT INTO fact_charge_events VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 1, 1, 1, 20240110, "created",  2500, 2500, 0,    0,    1),
            (2, 1, 1, 1, 1, 1, 20240110, "captured", 2500, 2500, 87,   2413, 1),
            (3, 1, 1, 1, 1, 1, 20240110, "refunded", -500, -500, 0,    0,    1),
            (4, 2, 1, 1, 1, 1, 20240111, "created",  1500, 1500, 0,    0,    1),
            (5, 2, 1, 1, 1, 1, 20240111, "captured", 1500, 1500, 58,   1442, 1),
            (6, 3, 1, 2, 2, 2, 20240110, "created",  5000, 5400, 0,    0,    1),
            (7, 3, 1, 2, 2, 2, 20240110, "captured", 5000, 5400, 175,  5225, 1),
        ],
    )
    q.executemany(
        "INSERT INTO fact_payouts VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, "po_001", 1, 1, 20240115, 3855, 3855, "paid"),
            (2, "po_002", 2, 2, 20240115, 5225, 5652, "paid"),
        ],
    )
    q.executemany(
        "INSERT INTO fact_disputes VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, "dp_001", 1, 1, 20240112, "opened",   2500, "fraud"),
            (2, "dp_001", 1, 1, 20240114, "won",      2500, "fraud"),
        ],
    )
    q.executemany(
        "INSERT INTO fact_balance_ledger VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 1, 20240110, "charge",  2413, 2413, 1, None),
            (2, 1, 20240110, "refund",   -500, 1913, 1, None),
            (3, 1, 20240111, "charge",  1442, 3355, 2, None),
            (4, 1, 20240115, "payout",  -3355,    0, None, "po_001"),
            (5, 2, 20240110, "charge",  5225, 5225, 3, None),
            (6, 2, 20240115, "payout",  -5225,    0, None, "po_002"),
        ],
    )
    return [t.name for t in tables]


# ---- Instagram ----------------------------------------------------------


def build_instagram(q: QueryRunner) -> List[str]:
    """Instagram engagement warehouse.

    Pre-aggregated rollups: `fact_post_daily`,
    `fact_story_daily`, `fact_ad_impressions`.
    (Raw 500B-event stream lives in the data lake,
    not the warehouse.)
    """
    dim_user = Table("dim_user", [
        Column("user_key", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("username", "TEXT", nullable=False),
        Column("country", "TEXT", nullable=False),
        Column("is_creator", "INTEGER", nullable=False, default="0"),
        Column("follower_count", "INTEGER", nullable=False, default="0"),
    ])
    dim_creator = Table("dim_creator", [
        Column("creator_key", "INTEGER", primary_key=True),
        Column("user_id", "INTEGER", nullable=False),
        Column("category", "TEXT"),
        Column("monetization_enabled", "INTEGER", nullable=False,
               default="0"),
        Column("effective_date", "INTEGER", nullable=False),
        Column("expiry_date", "INTEGER"),
        Column("is_current", "INTEGER", nullable=False, default="1"),
    ])
    dim_post = Table("dim_post", [
        Column("post_key", "INTEGER", primary_key=True),
        Column("post_id", "TEXT", nullable=False),
        Column("creator_key", "INTEGER", nullable=False,
               references="dim_creator(creator_key)"),
        Column("post_type", "TEXT", nullable=False),
        Column("created_at", "INTEGER", nullable=False),
    ])
    dim_story = Table("dim_story", [
        Column("story_key", "INTEGER", primary_key=True),
        Column("story_id", "TEXT", nullable=False),
        Column("creator_key", "INTEGER", nullable=False,
               references="dim_creator(creator_key)"),
        Column("num_frames", "INTEGER", nullable=False),
        Column("created_at", "INTEGER", nullable=False),
    ])
    dim_ad = Table("dim_ad", [
        Column("ad_key", "INTEGER", primary_key=True),
        Column("ad_id", "TEXT", nullable=False),
        Column("advertiser_key", "INTEGER", nullable=False),
        Column("format", "TEXT", nullable=False),
        Column("objective", "TEXT", nullable=False),
    ])
    dim_advertiser = Table("dim_advertiser", [
        Column("advertiser_key", "INTEGER", primary_key=True),
        Column("advertiser_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("industry", "TEXT"),
    ])
    dim_country = Table("dim_country", [
        Column("country_key", "INTEGER", primary_key=True),
        Column("iso_code", "TEXT", nullable=False),
        Column("name", "TEXT", nullable=False),
    ])
    dim_age_band = Table("dim_age_band", [
        Column("age_band_key", "INTEGER", primary_key=True),
        Column("band_name", "TEXT", nullable=False),
    ])
    dim_gender = Table("dim_gender", [
        Column("gender_key", "INTEGER", primary_key=True),
        Column("gender_name", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact_post_daily = Table("fact_post_daily", [
        Column("post_day_key", "INTEGER", primary_key=True),
        Column("post_key", "INTEGER", nullable=False,
               references="dim_post(post_key)"),
        Column("creator_key", "INTEGER", nullable=False,
               references="dim_creator(creator_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("impressions", "INTEGER", nullable=False),
        Column("unique_viewers", "INTEGER", nullable=False),
        Column("likes", "INTEGER", nullable=False, default="0"),
        Column("comments", "INTEGER", nullable=False, default="0"),
        Column("shares", "INTEGER", nullable=False, default="0"),
        Column("saves", "INTEGER", nullable=False, default="0"),
        Column("engagement_rate", "REAL", nullable=False, default="0"),
    ])
    fact_story_daily = Table("fact_story_daily", [
        Column("story_frame_key", "INTEGER", primary_key=True),
        Column("story_key", "INTEGER", nullable=False,
               references="dim_story(story_key)"),
        Column("creator_key", "INTEGER", nullable=False,
               references="dim_creator(creator_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("frame_number", "INTEGER", nullable=False),
        Column("impressions", "INTEGER", nullable=False),
        Column("unique_viewers", "INTEGER", nullable=False),
        Column("completion_rate", "REAL", nullable=False, default="0"),
    ])
    fact_ad_impressions = Table("fact_ad_impressions", [
        Column("ad_day_key", "INTEGER", primary_key=True),
        Column("ad_key", "INTEGER", nullable=False,
               references="dim_ad(ad_key)"),
        Column("advertiser_key", "INTEGER", nullable=False,
               references="dim_advertiser(advertiser_key)"),
        Column("date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("country_key", "INTEGER", nullable=False,
               references="dim_country(country_key)"),
        Column("age_band_key", "INTEGER", nullable=False,
               references="dim_age_band(age_band_key)"),
        Column("gender_key", "INTEGER", nullable=False,
               references="dim_gender(gender_key)"),
        Column("impressions", "INTEGER", nullable=False),
        Column("clicks", "INTEGER", nullable=False, default="0"),
        Column("spend_usd_cents", "INTEGER", nullable=False),
        Column("ctr", "REAL", nullable=False, default="0"),
    ])
    tables = [
        dim_user, dim_creator, dim_post, dim_story,
        dim_ad, dim_advertiser, dim_country, dim_age_band, dim_gender,
        dim_date,
        fact_post_daily, fact_story_daily, fact_ad_impressions,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_user VALUES (?,?,?,?,?,?)",
        [
            (1, 1, "creatorA", "USA", 1, 1_500_000),
            (2, 2, "creatorB", "FRA", 1,   200_000),
            (3, 3, "regular",  "USA", 0,       120),
        ],
    )
    q.executemany(
        "INSERT INTO dim_creator VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, "fitness", 1, 20240101, None, 1),
            (2, 2, "food",    1, 20240101, None, 1),
        ],
    )
    q.executemany(
        "INSERT INTO dim_post VALUES (?,?,?,?,?)",
        [
            (1, "p_001", 1, "reel",  20240110),
            (2, "p_002", 2, "photo", 20240110),
        ],
    )
    q.executemany(
        "INSERT INTO dim_story VALUES (?,?,?,?,?)",
        [
            (1, "s_001", 1, 5, 20240110),
        ],
    )
    q.executemany(
        "INSERT INTO dim_advertiser VALUES (?,?,?,?)",
        [(1, 1, "ShoeBrand", "retail")],
    )
    q.executemany(
        "INSERT INTO dim_ad VALUES (?,?,?,?,?)",
        [(1, "a_001", 1, "reel", "awareness")],
    )
    q.executemany(
        "INSERT INTO dim_country VALUES (?,?,?)",
        [(1, "US", "United States")],
    )
    q.executemany(
        "INSERT INTO dim_age_band VALUES (?,?)",
        [(1, "18-24"), (2, "25-34")],
    )
    q.executemany(
        "INSERT INTO dim_gender VALUES (?,?)",
        [(1, "female"), (2, "male")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240110, "2024-01-10"),
            (20240111, "2024-01-11"),
        ],
    )
    # 2 posts x 1 day each; 1 story with 5 frames x 1 day;
    # 1 ad x 1 day x 1 country x 2 age bands x 2 genders.
    q.executemany(
        "INSERT INTO fact_post_daily VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240110, 100000, 80000, 5000, 200, 100, 80,
             0.0675),
            (2, 2, 2, 20240110,  30000, 25000, 1200,  60,  20, 10,
             0.043),
        ],
    )
    story_rows = []
    for frame in range(1, 6):
        # Frame 5 has lower impressions (drop-off).
        imps = 40000 - (frame - 1) * 5000
        viewers = imps - 100
        rate = 0.75 if frame == 5 else 0.0
        story_rows.append(
            (frame, 1, 1, 20240110, frame, imps, viewers, rate)
        )
    q.executemany(
        "INSERT INTO fact_story_daily VALUES (?,?,?,?,?,?,?,?)",
        story_rows,
    )
    q.executemany(
        "INSERT INTO fact_ad_impressions VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240110, 1, 1, 1, 500000, 2500, 50000, 0.005),
            (2, 1, 1, 20240110, 1, 1, 2, 400000, 1800, 40000, 0.0045),
            (3, 1, 1, 20240110, 1, 2, 1, 300000, 1200, 30000, 0.004),
            (4, 1, 1, 20240110, 1, 2, 2, 250000, 1000, 25000, 0.004),
        ],
    )
    return [t.name for t in tables]


# ---- Amazon -------------------------------------------------------------


def build_amazon(q: QueryRunner) -> List[str]:
    """Amazon marketplace star schema.

    Four fact-table types: `fact_order_lines`
    (transactional), `fact_shipments` (transactional),
    `fact_inventory_snapshot` (periodic snapshot),
    `fact_returns` (transactional), `fact_reviews`
    (lean transactional).
    """
    dim_customer = Table("dim_customer", [
        Column("customer_key", "INTEGER", primary_key=True),
        Column("customer_id", "INTEGER", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("is_prime", "INTEGER", nullable=False, default="0"),
        Column("country", "TEXT", nullable=False),
    ])
    dim_seller = Table("dim_seller", [
        Column("seller_key", "INTEGER", primary_key=True),
        Column("seller_id", "INTEGER", nullable=False),
        Column("seller_name", "TEXT", nullable=False),
        Column("tier", "TEXT", nullable=False),
        Column("fulfillment_method", "TEXT", nullable=False),
    ])
    dim_product = Table("dim_product", [
        Column("product_key", "INTEGER", primary_key=True),
        Column("product_id", "INTEGER", nullable=False),
        Column("title", "TEXT", nullable=False),
        Column("category", "TEXT", nullable=False),
        Column("brand", "TEXT"),
        Column("list_price", "REAL", nullable=False),
    ])
    dim_warehouse = Table("dim_warehouse", [
        Column("warehouse_key", "INTEGER", primary_key=True),
        Column("warehouse_id", "INTEGER", nullable=False),
        Column("warehouse_name", "TEXT", nullable=False),
        Column("city", "TEXT", nullable=False),
    ])
    dim_carrier = Table("dim_carrier", [
        Column("carrier_key", "INTEGER", primary_key=True),
        Column("carrier_name", "TEXT", nullable=False),
    ])
    dim_payment_method = Table("dim_payment_method", [
        Column("payment_method_key", "INTEGER", primary_key=True),
        Column("method_name", "TEXT", nullable=False),
    ])
    dim_date = Table("dim_date", [
        Column("date_key", "INTEGER", primary_key=True),
        Column("date", "TEXT", nullable=False),
    ])
    fact_order_lines = Table("fact_order_lines", [
        Column("order_line_key", "INTEGER", primary_key=True),
        Column("order_id", "INTEGER", nullable=False),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("seller_key", "INTEGER", nullable=False,
               references="dim_seller(seller_key)"),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("order_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("payment_method_key", "INTEGER", nullable=False,
               references="dim_payment_method(payment_method_key)"),
        Column("quantity", "INTEGER", nullable=False),
        Column("unit_price", "REAL", nullable=False),
        Column("gross_amount", "REAL", nullable=False),
        Column("discount_amount", "REAL", nullable=False, default="0"),
        Column("tax_amount", "REAL", nullable=False, default="0"),
        Column("net_amount", "REAL", nullable=False),
    ])
    fact_shipments = Table("fact_shipments", [
        Column("shipment_line_key", "INTEGER", primary_key=True),
        Column("shipment_id", "INTEGER", nullable=False),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("seller_key", "INTEGER", nullable=False,
               references="dim_seller(seller_key)"),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("warehouse_key", "INTEGER", nullable=False,
               references="dim_warehouse(warehouse_key)"),
        Column("carrier_key", "INTEGER", nullable=False,
               references="dim_carrier(carrier_key)"),
        Column("ship_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("delivery_date_key", "INTEGER",
               references="dim_date(date_key)"),
        Column("quantity_shipped", "INTEGER", nullable=False),
        Column("shipping_cost", "REAL", nullable=False, default="0"),
        Column("delivered_on_time", "INTEGER", nullable=False,
               default="1"),
    ])
    fact_inventory_snapshot = Table("fact_inventory_snapshot", [
        Column("snapshot_key", "INTEGER", primary_key=True),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("warehouse_key", "INTEGER", nullable=False,
               references="dim_warehouse(warehouse_key)"),
        Column("snapshot_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("on_hand_qty", "INTEGER", nullable=False),
        Column("reserved_qty", "INTEGER", nullable=False, default="0"),
        Column("available_qty", "INTEGER", nullable=False),
    ])
    fact_returns = Table("fact_returns", [
        Column("return_key", "INTEGER", primary_key=True),
        Column("order_line_key", "INTEGER", nullable=False,
               references="fact_order_lines(order_line_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("return_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("return_quantity", "INTEGER", nullable=False),
        Column("return_amount", "REAL", nullable=False),
        Column("restocking_fee", "REAL", nullable=False, default="0"),
    ])
    fact_reviews = Table("fact_reviews", [
        Column("review_key", "INTEGER", primary_key=True),
        Column("product_key", "INTEGER", nullable=False,
               references="dim_product(product_key)"),
        Column("customer_key", "INTEGER", nullable=False,
               references="dim_customer(customer_key)"),
        Column("review_date_key", "INTEGER", nullable=False,
               references="dim_date(date_key)"),
        Column("rating", "INTEGER", nullable=False),
        Column("helpful_votes", "INTEGER", nullable=False, default="0"),
        Column("verified_purchase", "INTEGER", nullable=False,
               default="0"),
    ])
    tables = [
        dim_customer, dim_seller, dim_product, dim_warehouse,
        dim_carrier, dim_payment_method, dim_date,
        fact_order_lines, fact_shipments, fact_inventory_snapshot,
        fact_returns, fact_reviews,
    ]
    for t in tables:
        q.execute(t.to_ddl())

    q.executemany(
        "INSERT INTO dim_customer VALUES (?,?,?,?,?)",
        [
            (1, 1001, "Alice", 1, "USA"),
            (2, 1002, "Bob",   0, "USA"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_seller VALUES (?,?,?,?,?)",
        [
            (1, 201, "AcmeStore",  "pro",   "FBA"),
            (2, 202, "BobsDeals",  "basic", "FBM"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_product VALUES (?,?,?,?,?,?)",
        [
            (1, 301, "Bluetooth headphones", "Electronics", "AcmeAudio",  79.99),
            (2, 302, "Coffee mug",          "Home",        "MugCo",      12.50),
        ],
    )
    q.executemany(
        "INSERT INTO dim_warehouse VALUES (?,?,?,?)",
        [
            (1, 1, "Reno DC",  "Reno"),
            (2, 2, "Newark DC", "Newark"),
        ],
    )
    q.executemany(
        "INSERT INTO dim_carrier VALUES (?,?)",
        [(1, "UPS"), (2, "FedEx"), (3, "AMZL")],
    )
    q.executemany(
        "INSERT INTO dim_payment_method VALUES (?,?)",
        [(1, "credit_card"), (2, "gift_card")],
    )
    q.executemany(
        "INSERT INTO dim_date VALUES (?,?)",
        [
            (20240110, "2024-01-10"),
            (20240112, "2024-01-12"),
            (20240115, "2024-01-15"),
            (20240120, "2024-01-20"),
        ],
    )
    # 2 order lines, 2 shipments, 2 inventory snapshots,
    # 1 return, 2 reviews.
    q.executemany(
        "INSERT INTO fact_order_lines VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 5001, 1, 1, 1, 20240110, 1, 1, 79.99,
             79.99, 0,    6.40, 86.39),
            (2, 5001, 1, 1, 2, 20240110, 1, 2, 12.50,
             25.00, 0,    2.00, 27.00),
            (3, 5002, 2, 2, 1, 20240112, 2, 1, 79.99,
             79.99, 5.00, 5.99, 80.98),
        ],
    )
    q.executemany(
        "INSERT INTO fact_shipments VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, 6001, 1, 1, 1, 1, 1, 20240112, 20240115,
             1, 5.00, 1),
            (2, 6001, 1, 1, 2, 1, 1, 20240112, 20240120,
             2, 5.00, 0),
            (3, 6002, 2, 2, 1, 2, 3, 20240115, 20240120,
             1, 7.00, 1),
        ],
    )
    q.executemany(
        "INSERT INTO fact_inventory_snapshot VALUES "
        "(?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240120, 500,  20, 480),
            (2, 2, 1, 20240120, 1000, 50, 950),
        ],
    )
    q.executemany(
        "INSERT INTO fact_returns VALUES (?,?,?,?,?,?,?,?)",
        [
            (1, 2, 1, 2, 20240120, 1, 12.50, 2.50),
        ],
    )
    q.executemany(
        "INSERT INTO fact_reviews VALUES (?,?,?,?,?,?,?)",
        [
            (1, 1, 1, 20240120, 5, 10, 1),
            (2, 1, 2, 20240120, 4,  2, 1),
        ],
    )
    return [t.name for t in tables]


# ---- demo ----------------------------------------------------------------


if __name__ == "__main__":
    print("Building M07 mock interview schemas...\n")
    for name, fn in [
        ("ride_sharing",      build_ride_sharing),
        ("customer_support",  build_customer_support),
        ("airbnb",            build_airbnb),
        ("stripe",            build_stripe),
        ("instagram",         build_instagram),
        ("amazon",            build_amazon),
    ]:
        with QueryRunner(":memory:") as q:
            tables = fn(q)
            print(f"[{name}]  tables: {tables}")
            for tn in tables:
                if tn.startswith("fact_"):
                    rows = q.query_all(f"SELECT * FROM {tn}")
                    print(f"   {tn}: {len(rows)} rows")
        print()
