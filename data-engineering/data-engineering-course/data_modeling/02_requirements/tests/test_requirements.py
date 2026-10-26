"""Tests for the requirements doc and the discovery question bank.

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

from discovery_questions import (  # type: ignore
    DISCOVERY_QUESTIONS,
    by_category,
    pick_top,
)
from requirements_doc import FactSpec, RequirementsDoc  # type: ignore


class TestRequirementsDoc(unittest.TestCase):
    """Tests for the RequirementsDoc builder."""

    def test_empty_doc_renders_minimally(self):
        doc = RequirementsDoc(product="EmptyApp")
        out = doc.render()
        self.assertIn("# Requirements — EmptyApp", out)

    def test_add_consumer_records_purpose(self):
        doc = RequirementsDoc(product="X")
        doc.add_consumer("Analytics", "Engagement dashboard")
        self.assertEqual(len(doc.consumers), 1)
        self.assertEqual(doc.consumers[0]["name"], "Analytics")
        self.assertIn("Engagement", doc.render())

    def test_add_use_case_renders_numbered(self):
        doc = RequirementsDoc(product="X")
        doc.add_use_case("MAU")
        doc.add_use_case("LTV")
        out = doc.render()
        self.assertIn("1. MAU", out)
        self.assertIn("2. LTV", out)

    def test_add_source_renders_table(self):
        doc = RequirementsDoc(product="X")
        doc.add_source("users", "OLTP PostgreSQL", "1k rows/day", "real-time")
        out = doc.render()
        self.assertIn("| name | system |", out)
        self.assertIn("OLTP PostgreSQL", out)
        self.assertIn("real-time", out)

    def test_add_fact_records_grain_and_dimensions(self):
        doc = RequirementsDoc(product="X")
        doc.add_fact(
            "fact_workouts",
            "one row per workout session",
            measures=["duration_minutes", "calories_burned"],
            dimensions=["dim_users", "dim_workout_types"],
        )
        self.assertEqual(len(doc.facts), 1)
        self.assertEqual(doc.facts[0].grain, "one row per workout session")
        self.assertIn("dim_users", doc.render())

    def test_non_functional_block_renders(self):
        doc = RequirementsDoc(
            product="X",
            volume="1M events/day",
            freshness="hourly",
            retention="2 years",
        )
        out = doc.render()
        self.assertIn("**Volume:** 1M events/day", out)
        self.assertIn("**Freshness:** hourly", out)
        self.assertIn("**Retention:** 2 years", out)

    def test_notes_render_under_assumptions(self):
        doc = RequirementsDoc(product="X")
        doc.add_note("Assuming USD cents")
        out = doc.render()
        self.assertIn("## Assumptions", out)
        self.assertIn("USD cents", out)

    def test_to_dict_round_trip(self):
        doc = RequirementsDoc(product="X")
        doc.add_consumer("Analytics", "dashboards")
        doc.add_use_case("DAU")
        doc.add_source("users", "Postgres", "1k/day")
        doc.add_fact("fact_events", "one row per event")
        doc.add_note("Assumes UTC")
        d = doc.to_dict()
        self.assertEqual(d["product"], "X")
        self.assertEqual(len(d["consumers"]), 1)
        self.assertEqual(len(d["use_cases"]), 1)
        self.assertEqual(d["facts"][0]["name"], "fact_events")
        self.assertEqual(d["facts"][0]["grain"], "one row per event")

    def test_full_doc_render_is_well_formed(self):
        doc = RequirementsDoc(
            product="FitnessApp",
            volume="10M events/day",
            freshness="hourly",
            retention="2 years",
        )
        doc.add_consumer("Analytics", "Engagement dashboard")
        doc.add_consumer("Data Science", "Cohort model")
        doc.add_use_case("MAU by month")
        doc.add_use_case("Avg workouts per user per week")
        doc.add_source("users", "PostgreSQL", "1k/day", "real-time")
        doc.add_source("events", "Kafka", "10M/day", "real-time")
        doc.add_fact(
            "fact_workouts",
            "one row per workout session",
            ["duration_minutes", "calories_burned"],
            ["dim_users", "dim_workout_types"],
        )
        out = doc.render()
        # The doc should mention every important section.
        for needle in [
            "FitnessApp",
            "Analytics",
            "Data Science",
            "MAU by month",
            "PostgreSQL",
            "Kafka",
            "fact_workouts",
            "one row per workout session",
            "10M events/day",
            "hourly",
        ]:
            self.assertIn(needle, out, f"missing {needle!r} in render")


class TestDiscoveryQuestions(unittest.TestCase):
    """Tests for the discovery question bank."""

    def test_bank_has_at_least_50_questions(self):
        self.assertGreaterEqual(len(DISCOVERY_QUESTIONS), 50)

    def test_each_question_has_a_category(self):
        for q in DISCOVERY_QUESTIONS:
            self.assertIn("category", q)
            self.assertIn("question", q)
            self.assertGreater(len(q["question"]), 10)

    def test_by_category_groups(self):
        grouped = by_category()
        # Must cover at least the 5 Ws + how + scale + historical + edge.
        for cat in ("who", "what", "when", "where", "why", "how", "scale"):
            self.assertIn(cat, grouped, f"missing category {cat!r}")
            self.assertGreater(len(grouped[cat]), 0)

    def test_pick_top_is_deterministic(self):
        a = pick_top(8, seed=7)
        b = pick_top(8, seed=7)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 8)
        c = pick_top(8, seed=99)
        # Different seed should (almost always) produce different output.
        self.assertNotEqual(a, c)

    def test_pick_top_within_bounds(self):
        for n in (1, 5, 10, 25):
            out = pick_top(n, seed=n)
            self.assertEqual(len(out), n)
            for q in out:
                self.assertIn(q, DISCOVERY_QUESTIONS)


if __name__ == "__main__":
    unittest.main()
