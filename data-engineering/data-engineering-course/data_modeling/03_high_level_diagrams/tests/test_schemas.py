"""Tests for the practice star schemas and the ER-to-table translator.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

import sys
import unittest
from pathlib import Path

# Make `common` and the local `code/` importable.
HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(COURSE_ROOT))
sys.path.insert(0, str(HERE.parent / "code"))

from common import QueryRunner  # type: ignore

from diagrams import (  # type: ignore
    ecommerce_er,
    instagram_er,
    render_er,
    render_text_star,
    rideshare_er,
    spotify_er,
    support_er,
)
from er_to_tables import (  # type: ignore
    Entity,
    Relationship,
    derived_attribute_note,
    entity_to_table,
    relationship_to_fk,
    split_multivalued,
    translate_er,
)
from star_schemas import (  # type: ignore
    build_cloud_services_schema,
    build_ecommerce_schema,
    build_instagram_schema,
    build_online_advertising_schema,
    build_rideshare_schema,
    build_spotify_schema,
    build_support_schema,
)


# ---- star_schemas.py ----------------------------------------------------


class TestEcommerceStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_ecommerce_schema(q)
        for n in (
            "dim_customers",
            "dim_products",
            "dim_orders",
            "dim_date",
            "fact_order_items",
        ):
            self.assertIn(n, names)

    def test_fact_has_required_measures_and_dim_keys(self):
        with QueryRunner(":memory:") as q:
            build_ecommerce_schema(q)
            cols = {row["name"] for row in q.query_all("PRAGMA table_info(fact_order_items)")}
        for needle in (
            "quantity",
            "unit_price",
            "gross_amount",
            "discount_amount",
            "net_amount",
            "tax_amount",
            "customer_key",
            "product_key",
            "order_key",
            "order_date_key",
        ):
            self.assertIn(needle, cols, f"missing {needle!r} on fact_order_items")

    def test_sample_rows_join_through_dim(self):
        with QueryRunner(":memory:") as q:
            build_ecommerce_schema(q)
            rows = q.query_all(
                """
                SELECT f.net_amount, c.country
                FROM fact_order_items f
                JOIN dim_customers c ON f.customer_key = c.customer_key
                """
            )
        self.assertEqual(len(rows), 5)
        countries = {r["country"] for r in rows}
        # We inserted 5 distinct customers; at least 4 distinct
        # countries should appear (one country is shared).
        self.assertGreaterEqual(len(countries), 4)


class TestRideshareStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_rideshare_schema(q)
        for n in (
            "dim_drivers",
            "dim_riders",
            "dim_cities",
            "dim_date",
            "dim_time_of_day",
            "fact_trips",
            "fact_cancellations",
        ):
            self.assertIn(n, names)

    def test_fact_trips_carries_revenue_measures(self):
        with QueryRunner(":memory:") as q:
            build_rideshare_schema(q)
            cols = {row["name"] for row in q.query_all("PRAGMA table_info(fact_trips)")}
        for needle in (
            "distance_km",
            "duration_min",
            "surge_multiplier",
            "fare",
            "tip",
            "total_revenue",
        ):
            self.assertIn(needle, cols)

    def test_trip_join_to_city(self):
        with QueryRunner(":memory:") as q:
            build_rideshare_schema(q)
            rows = q.query_all(
                """
                SELECT t.total_revenue, c.city_name
                FROM fact_trips t
                JOIN dim_cities c ON t.city_key = c.city_key
                """
            )
        self.assertEqual(len(rows), 5)
        cities = {r["city_name"] for r in rows}
        self.assertGreaterEqual(len(cities), 3)


class TestInstagramStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_instagram_schema(q)
        for n in (
            "dim_users",
            "dim_posts",
            "dim_event_type",
            "dim_date",
            "fact_post_events",
        ):
            self.assertIn(n, names)

    def test_fact_carries_event_and_actor(self):
        with QueryRunner(":memory:") as q:
            build_instagram_schema(q)
            cols = {row["name"] for row in q.query_all("PRAGMA table_info(fact_post_events)")}
        for needle in (
            "post_key",
            "actor_user_key",
            "author_user_key",
            "event_type_key",
        ):
            self.assertIn(needle, cols)

    def test_count_events_by_type(self):
        with QueryRunner(":memory:") as q:
            build_instagram_schema(q)
            rows = q.query_all(
                """
                SELECT et.event_type, COUNT(*) AS n
                FROM fact_post_events f
                JOIN dim_event_type et ON f.event_type_key = et.event_type_key
                GROUP BY et.event_type
                ORDER BY n DESC
                """
            )
        self.assertGreater(len(rows), 0)
        total = sum(r["n"] for r in rows)
        self.assertEqual(total, 10)


class TestSupportStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_support_schema(q)
        for n in (
            "dim_customers",
            "dim_tickets",
            "dim_agents",
            "dim_event_type",
            "dim_date",
            "fact_ticket_events",
        ):
            self.assertIn(n, names)

    def test_ticket_event_joins(self):
        with QueryRunner(":memory:") as q:
            build_support_schema(q)
            rows = q.query_all(
                """
                SELECT t.subject, et.event_type
                FROM fact_ticket_events f
                JOIN dim_tickets t ON f.ticket_key = t.ticket_key
                JOIN dim_event_type et ON f.event_type_key = et.event_type_key
                """
            )
        self.assertEqual(len(rows), 10)


class TestSpotifyStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_spotify_schema(q)
        for n in (
            "dim_users",
            "dim_artists",
            "dim_albums",
            "dim_songs",
            "dim_device_type",
            "dim_date",
            "fact_streams",
        ):
            self.assertIn(n, names)

    def test_fact_streams_aggregates_skip_rate(self):
        with QueryRunner(":memory:") as q:
            build_spotify_schema(q)
            rows = q.query_all(
                """
                SELECT
                    s.release_decade,
                    COUNT(*) AS n,
                    SUM(was_skipped) AS n_skipped
                FROM fact_streams f
                JOIN dim_songs s ON f.song_key = s.song_key
                GROUP BY s.release_decade
                """
            )
        self.assertEqual(len(rows), 2)  # we inserted 2 decades
        # sanity: skipped count <= total
        for r in rows:
            self.assertLessEqual(r["n_skipped"], r["n"])


class TestCloudServicesStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_cloud_services_schema(q)
        for n in (
            "dim_customer",
            "dim_service",
            "dim_region",
            "dim_usage_type",
            "dim_date",
            "fact_usage",
        ):
            self.assertIn(n, names)

    def test_fact_usage_carries_cost(self):
        with QueryRunner(":memory:") as q:
            build_cloud_services_schema(q)
            cols = {row["name"] for row in q.query_all("PRAGMA table_info(fact_usage)")}
        for needle in (
            "usage_qty",
            "unit_price",
            "cost_usd",
            "customer_key",
            "service_key",
            "region_key",
        ):
            self.assertIn(needle, cols)

    def test_cost_rollup_by_service(self):
        with QueryRunner(":memory:") as q:
            build_cloud_services_schema(q)
            rows = q.query_all(
                """
                SELECT s.service_name, SUM(f.cost_usd) AS total_cost
                FROM fact_usage f
                JOIN dim_service s ON f.service_key = s.service_key
                GROUP BY s.service_name
                """
            )
        # 3 services have usage rows
        self.assertEqual(len(rows), 3)
        # sum of cost_usd in the inserted data is 5 + 10 + 18 = 33
        total = sum(r["total_cost"] for r in rows)
        self.assertAlmostEqual(total, 33.0, places=2)


class TestOnlineAdvertisingStar(unittest.TestCase):
    def test_creates_all_tables(self):
        with QueryRunner(":memory:") as q:
            names = build_online_advertising_schema(q)
        for n in (
            "dim_advertiser",
            "dim_campaign",
            "dim_creative",
            "dim_event_type",
            "dim_date",
            "fact_ad_events",
        ):
            self.assertIn(n, names)

    def test_fact_ad_events_carries_event_flags(self):
        with QueryRunner(":memory:") as q:
            build_online_advertising_schema(q)
            cols = {row["name"] for row in q.query_all("PRAGMA table_info(fact_ad_events)")}
        for needle in (
            "impressions",
            "clicks",
            "conversions",
            "cost_usd",
            "revenue_usd",
            "advertiser_key",
            "campaign_key",
        ):
            self.assertIn(needle, cols)

    def test_ctr_by_campaign(self):
        with QueryRunner(":memory:") as q:
            build_online_advertising_schema(q)
            rows = q.query_all(
                """
                SELECT
                    c.campaign_name,
                    SUM(f.impressions) AS imps,
                    SUM(f.clicks)      AS cls
                FROM fact_ad_events f
                JOIN dim_campaign c ON f.campaign_key = c.campaign_key
                GROUP BY c.campaign_name
                """
            )
        # 2 campaigns have rows; sanity check the totals
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertGreaterEqual(r["imps"], 1)
            self.assertGreaterEqual(r["cls"], 0)


# ---- er_to_tables.py -----------------------------------------------------


class TestERTranslation(unittest.TestCase):
    def test_entity_to_table_uses_id_pk(self):
        e = Entity("User", ["id", "name", "email"])
        t = entity_to_table(e)
        self.assertEqual(t.name, "users")
        self.assertEqual(t.primary_key, ["id"])

    def test_one_to_many_adds_fk_on_many_side(self):
        rel = Relationship("does", "User", "Workout", "1:N")
        t = relationship_to_fk(rel, "users", "workouts")
        self.assertIsNotNone(t)
        self.assertEqual(t.foreign_keys, [
            "FOREIGN KEY (user_id) REFERENCES users(id)"
        ])

    def test_many_to_many_creates_bridge(self):
        rel = Relationship("includes", "Workout", "Exercise", "N:M")
        t = relationship_to_fk(rel, "workouts", "exercises")
        self.assertIsNotNone(t)
        self.assertEqual(t.name, "workouts_exercises")
        self.assertIn("workout_id", t.columns)
        self.assertIn("exercise_id", t.columns)

    def test_translate_er_full(self):
        entities = [
            Entity("User", ["id", "name"]),
            Entity("Workout", ["id", "duration_min"]),
            Entity("Exercise", ["id", "name"]),
        ]
        rels = [
            Relationship("does", "User", "Workout", "1:N"),
            Relationship("includes", "Workout", "Exercise", "N:M"),
        ]
        tables = translate_er(entities, rels)
        for t in ("users", "workouts", "exercises", "workouts_exercises"):
            self.assertIn(t, tables)

    def test_multivalued_attribute_split(self):
        e = Entity("User", ["id", "name", "phone_numbers"])
        t = split_multivalued(e, "phone_numbers")
        self.assertEqual(t.name, "user_phone_number")
        self.assertIn("user_id", t.columns)

    def test_derived_attribute_note(self):
        msg = derived_attribute_note("lifetime_revenue")
        self.assertIn("derived", msg)
        self.assertIn("lifetime_revenue", msg)

    def test_unknown_cardinality_raises(self):
        rel = Relationship("weird", "A", "B", "X:Y")
        with self.assertRaises(ValueError):
            relationship_to_fk(rel, "as", "bs")


# ---- diagrams.py ---------------------------------------------------------


class TestDiagramRenderers(unittest.TestCase):
    def test_mermaid_er_starts_with_er_diagram(self):
        out = ecommerce_er()
        self.assertTrue(out.startswith("erDiagram"))
        self.assertIn("fact_order_items", out)

    def test_each_schema_er_returns_valid_block(self):
        for fn in (
            ecommerce_er,
            rideshare_er,
            instagram_er,
            support_er,
            spotify_er,
        ):
            out = fn()
            self.assertTrue(out.startswith("erDiagram"))
            self.assertIn("fact_", out)

    def test_render_er_generic(self):
        out = render_er("test", [("a", "||--o{", "b")])
        self.assertIn("a ||--o{ b", out)

    def test_render_text_star_marks_fact(self):
        from common import Column, Table

        tables = [
            Table("dim_x", [Column("id", "INTEGER", primary_key=True)]),
            Table("fact_y", [Column("id", "INTEGER", primary_key=True)]),
        ]
        out = render_text_star(tables)
        self.assertIn("★ fact_y", out)
        self.assertIn("  dim_x", out)


if __name__ == "__main__":
    unittest.main()
