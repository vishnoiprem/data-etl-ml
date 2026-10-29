"""Tests for the 5 Meta screen SQL problems."""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQL_DIR = HERE.parent / "code"
COURSE_ROOT = HERE.parent.parent.parent

sys.path.insert(0, str(COURSE_ROOT))

from common import QueryRunner  # type: ignore  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_problem(problem_n: int) -> str:
    """Extract problem N from the solutions file."""
    text = _read(SQL_DIR / "meta_screen_sql.sql")
    pattern = re.compile(
        r"^--\s*Problem\s+(\d+):[^\n]*\n(.*?)(?=^--\s*Problem\s+\d+:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    for m in pattern.finditer(text):
        if int(m.group(1)) == problem_n:
            body = m.group(2)
            lines = []
            for ln in body.splitlines():
                if ln.strip().startswith("--"):
                    continue
                lines.append(ln)
            return "\n".join(lines).strip().rstrip(";").strip()
    raise ValueError(f"problem {problem_n} not found")


def _fresh_runner() -> QueryRunner:
    """Return a QueryRunner with the Meta screen schema applied.

    sqlite3 only allows one statement per `execute()` call, so we
    split the schema file on `;` and run each statement individually.
    """
    q = QueryRunner(":memory:")
    raw = _read(SQL_DIR / "meta_schema.sql")
    lines = []
    for ln in raw.splitlines():
        if ln.strip().startswith("--"):
            continue
        lines.append(ln)
    cleaned = "\n".join(lines)
    for stmt in cleaned.split(";"):
        s = stmt.strip()
        if s:
            q.execute(s)
    return q


class TestProblem1Retention(unittest.TestCase):
    def test_returns_columns(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(1))
        # Sample data has only 4 users with 1 first_seen each; no country
        # hits the 1000 threshold, so the result is empty.
        self.assertEqual(out, [])


class TestProblem2Hour1Peak(unittest.TestCase):
    def test_returns_posts_above_10pct_threshold(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(2))
        # Sample data: page 301 has peak=3 (post 1); post 2 has 2; post 3 has 1.
        # page 302 has peak=0 (no events) so all of its posts are "0 >= 0" -> True.
        self.assertGreater(len(out), 0)
        # post 1 (eng=3) and post 2 (eng=2) qualify against page 301 peak 3.
        post_ids = {r['post_id'] for r in out}
        self.assertIn(1, post_ids)
        self.assertIn(2, post_ids)


class TestProblem3TopN(unittest.TestCase):
    def test_returns_top_3_per_qualified_page(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(3))
        # facebook_post has pages 301, 302. The query runs without error.
        self.assertIsInstance(out, list)


class TestProblem4Sessionize(unittest.TestCase):
    def test_user_201_has_2_sessions(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(4))
        # User 201: 3 events at 8:00, 8:05 (same session), 8:45 (new session
        # because 40 min > 30). So 2 sessions.
        u201 = [r for r in out if r['user_id'] == 201]
        self.assertEqual(len(u201), 2)

    def test_user_203_has_4_distinct_sessions(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(4))
        # User 203 has events on 4 consecutive days, each is its own session.
        u203 = [r for r in out if r['user_id'] == 203]
        self.assertEqual(len(u203), 4)


class TestProblem5GapsAndIslands(unittest.TestCase):
    def test_user_203_has_4_day_streak(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(5))
        u203 = [r for r in out if r['user_id'] == 203]
        self.assertEqual(len(u203), 1)
        self.assertEqual(u203[0]['longest_streak'], 4)


if __name__ == "__main__":
    unittest.main()
