"""Tests for the 6 Meta onsite-flavored SQL problems."""

from __future__ import annotations

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
    text = _read(SQL_DIR / "meta_onsite_sql.sql")
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


class TestProblem1MessengerVideoPct(unittest.TestCase):
    def test_runs_and_returns_scalar(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(1))
        self.assertEqual(len(out), 1)
        self.assertIn('video_pct', out[0])


class TestProblem2FirstCountryRetention(unittest.TestCase):
    def test_returns_countries(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(2))
        countries = {r['country'] for r in out}
        # Sample data: US, IN, BR.
        self.assertIn('US', countries)


class TestProblem3WhatsAppCohort(unittest.TestCase):
    def test_returns_cohort_size(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(3))
        self.assertEqual(len(out), 1)
        self.assertIn('cohort_size', out[0])
        # Senders 501 (first msg 2024-01-15) and 502 (2024-02-15) both in Q1.
        self.assertEqual(out[0]['cohort_size'], 2)


class TestProblem4TopAdSets(unittest.TestCase):
    def test_returns_columns(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(4))
        # Sample data: 1 advertiser with 3 ad-sets; threshold is 5.
        # So no advertisers qualify -> empty.
        self.assertEqual(out, [])


class TestProblem5EngagementByHour(unittest.TestCase):
    def test_returns_24_hour_buckets(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(5))
        # Sample posts are at hours 10, 11; so 2 hours have data.
        hours = {r['hour'] for r in out}
        self.assertIn(10, hours)
        self.assertIn(11, hours)


class TestProblem6AuctionTimeTravel(unittest.TestCase):
    def test_returns_winning_bid(self):
        qr = _fresh_runner()
        out = qr.query_all(_load_problem(6).replace(
            ':ad_id', '1001').replace(':as_of_ts', "'2026-01-01T10:00:05'"))
        # ad 1001 won at 10:00:00 and 10:00:02; latest before 10:00:05 is 10:00:02.
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0]['bid_amount'], 1.60)


if __name__ == "__main__":
    unittest.main()
