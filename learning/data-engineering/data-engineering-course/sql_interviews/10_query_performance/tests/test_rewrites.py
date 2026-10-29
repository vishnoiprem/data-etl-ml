"""Tests for the Query Performance module (M10).

Lesson 04 (query rewrites) gives 10 before/after patterns. We
turn the 4 most-asked ones into test cases that run against a
seeded in-memory SQLite and assert the rewrite produces the
same rows as the original (in fewer logical steps where the
test can measure).

The other 3 lessons (EXPLAIN plans, index strategy, join
optimization) are conceptual — the test is that the lesson
files exist and reference real operators.
"""

import os
import sys
import unittest

# Make the course root importable so we can use common.query
HERE = os.path.dirname(os.path.abspath(__file__))
COURSE_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, COURSE_ROOT)

from common.query import QueryRunner  # type: ignore  # noqa: E402


def _names(rows):
    """Helper: pull the ``name`` field from a list of dicts."""
    return tuple(sorted(r["name"] for r in rows))


class TestQueryRewrites(unittest.TestCase):
    """Lesson 04: the 10 most-asked query-rewrite patterns.

    We test 4 of them concretely: subquery-to-JOIN, NOT IN vs
    NOT EXISTS, UNION vs UNION ALL, and the EXISTS-vs-IN rewrite.
    The other 6 are documented in the lesson file.
    """

    @classmethod
    def setUpClass(cls):
        cls.db = QueryRunner(":memory:")
        # Schema
        cls.db.execute(
            "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)"
        )
        cls.db.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, "
            "customer_id INTEGER, total REAL)"
        )
        # Data
        cls.db.executemany(
            "INSERT INTO customers (id, name) VALUES (?, ?)",
            [(1, "Alice"), (2, "Bob"), (3, "Carol"), (4, "Dave")],
        )
        cls.db.executemany(
            "INSERT INTO orders (id, customer_id, total) VALUES (?, ?, ?)",
            [(10, 1, 100.0), (11, 1, 50.0), (12, 2, 200.0)],
        )

    def test_subquery_to_join_pattern(self):
        """The `WHERE x IN (SELECT ...)` form must be expressible as a JOIN.

        Both forms return the same rows; the JOIN form is the one
        a senior candidate writes in the interview because the
        optimizer has more freedom.
        """
        subquery = self.db.query_all(
            """
            SELECT name FROM customers
            WHERE id IN (SELECT customer_id FROM orders)
            ORDER BY name
            """
        )
        join_form = self.db.query_all(
            """
            SELECT DISTINCT c.name FROM customers c
            JOIN orders o ON c.id = o.customer_id
            ORDER BY c.name
            """
        )
        self.assertEqual(_names(subquery), _names(join_form))
        self.assertEqual(_names(subquery), ("Alice", "Bob"))

    def test_not_in_vs_not_exists_with_null_safety(self):
        """NOT IN with NULLs silently returns zero rows. NOT EXISTS does not.

        This is the most famous gotcha in SQL performance
        interviews. The lesson calls it out as a senior-level
        signal.
        """
        # Insert a NULL customer_id so NOT IN would (correctly) misbehave.
        self.db.execute(
            "INSERT INTO orders (id, customer_id, total) VALUES (99, NULL, NULL)"
        )
        # NOT IN: returns empty set because of NULL semantics.
        not_in = self.db.query_all(
            """
            SELECT name FROM customers
            WHERE id NOT IN (SELECT customer_id FROM orders)
            """
        )
        # NOT EXISTS: returns Carol + Dave (the customers without any order).
        not_exists = self.db.query_all(
            """
            SELECT name FROM customers c
            WHERE NOT EXISTS (
                SELECT 1 FROM orders o WHERE o.customer_id = c.id
            )
            ORDER BY name
            """
        )
        self.assertEqual(not_in, [])
        self.assertEqual(_names(not_exists), ("Carol", "Dave"))

    def test_union_vs_union_all(self):
        """UNION de-duplicates; UNION ALL does not. Always prefer UNION ALL
        when you know the inputs are disjoint or you don't need dedup."""

        # Two disjoint result sets; UNION and UNION ALL produce the same rows.
        a = self.db.query_all(
            """
            SELECT name FROM customers WHERE id <= 2
            UNION
            SELECT name FROM customers WHERE id >= 3
            ORDER BY name
            """
        )
        b = self.db.query_all(
            """
            SELECT name FROM customers WHERE id <= 2
            UNION ALL
            SELECT name FROM customers WHERE id >= 3
            ORDER BY name
            """
        )
        self.assertEqual(_names(a), _names(b))
        self.assertEqual(_names(a), ("Alice", "Bob", "Carol", "Dave"))

    def test_exists_vs_in_pattern(self):
        """EXISTS short-circuits on first match; IN materializes the subquery.

        For correlated subqueries, EXISTS is usually faster and
        always NULL-safe. The lesson recommends EXISTS as the
        default for senior candidates.
        """
        with_exists = self.db.query_all(
            """
            SELECT name FROM customers c
            WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)
            ORDER BY name
            """
        )
        with_in = self.db.query_all(
            """
            SELECT name FROM customers
            WHERE id IN (SELECT customer_id FROM orders)
            ORDER BY name
            """
        )
        self.assertEqual(_names(with_exists), _names(with_in))
        self.assertEqual(_names(with_exists), ("Alice", "Bob"))


class TestLessonFilesExist(unittest.TestCase):
    """The other 3 lessons in this module are conceptual; we assert
    the design files exist and reference real operators."""

    def test_lesson_files_present(self):
        design_dir = os.path.join(HERE, "..", "design")
        for fname in (
            "01_explain_plans.md",
            "02_index_strategy.md",
            "03_join_optimization.md",
            "04_query_rewrites.md",
        ):
            path = os.path.join(design_dir, fname)
            self.assertTrue(
                os.path.exists(path), f"missing lesson file: {fname}"
            )

    def test_explain_plans_references_real_operators(self):
        """Lesson 01 should mention at least 4 real plan operators."""
        with open(os.path.join(HERE, "..", "design", "01_explain_plans.md")) as f:
            content = f.read().lower()
        for op in ("seq scan", "index scan", "hash join", "nested loop", "sort"):
            self.assertIn(op, content, f"missing operator: {op}")

    def test_index_strategy_references_real_index_types(self):
        """Lesson 02 should mention the 4 main index types."""
        with open(os.path.join(HERE, "..", "design", "02_index_strategy.md")) as f:
            content = f.read().lower()
        for ix in ("b-tree", "bitmap", "partial", "composite", "covering"):
            self.assertIn(ix, content, f"missing index type: {ix}")

    def test_join_optimization_references_real_strategies(self):
        """Lesson 03 should mention broadcast vs shuffle and join algorithms."""
        with open(os.path.join(HERE, "..", "design", "03_join_optimization.md")) as f:
            content = f.read().lower()
        for kw in ("broadcast", "shuffle", "hash join", "nested loop"):
            self.assertIn(kw, content, f"missing join concept: {kw}")


if __name__ == "__main__":
    unittest.main()
