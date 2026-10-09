"""Tests for the 14 M09 (Hard) practice SQL problems.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQL_DIR = HERE.parent / "code"
COURSE_ROOT = HERE.parent.parent.parent

sys.path.insert(0, str(COURSE_ROOT))

from common import QueryRunner  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_solutions() -> dict[int, str]:
    text = _read(SQL_DIR / "solutions.sql")
    pattern = re.compile(
        r"^--\s*Problem\s+(\d+):[^\n]*\n(.*?)(?=^--\s*Problem\s+\d+:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    out: dict[int, str] = {}
    for m in pattern.finditer(text):
        n = int(m.group(1))
        body = m.group(2)
        sql_lines = [ln for ln in body.splitlines() if not ln.strip().startswith("--")]
        sql = "\n".join(sql_lines).strip().rstrip(";").strip()
        if sql:
            out[n] = sql
    return out


SOLUTIONS = _load_solutions()


def _fresh_runner() -> QueryRunner:
    q = QueryRunner(":memory:")
    raw = _read(SQL_DIR / "schema.sql")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    cleaned = "\n".join(lines)
    for stmt in cleaned.split(";"):
        s = stmt.strip()
        if s:
            q.execute(s)
    return q


# ---- 14 tests, one per problem ----------------------------------------


class TestProblem85MedianPerGroup(unittest.TestCase):
    def test_median(self):
        rows = _fresh_runner().query_all(SOLUTIONS[85])
        as_d = {r["departmentId"]: r["median_salary"] for r in rows}
        # Dept 1: 90k, 85k, 70k, 60k → avg(85k, 70k) = 77500
        # Dept 2: 100k, 95k, 80k, 75k → avg(95k, 80k) = 87500
        self.assertAlmostEqual(as_d[1], 77500.0)
        self.assertAlmostEqual(as_d[2], 87500.0)


class TestProblem86CumulativeSumWithReset(unittest.TestCase):
    def test_reset(self):
        rows = _fresh_runner().query_all(SOLUTIONS[86])
        # Expected: (1, add, 10, 10), (2, add, 20, 30),
        # (3, reset, 0, 0), (4, add, 15, 15),
        # (5, add, 25, 40), (6, reset, 0, 0),
        # (7, add, 5, 5)
        as_d = {r["id"]: r["running_sum"] for r in rows}
        self.assertEqual(as_d, {1: 10, 2: 30, 3: 0, 4: 15, 5: 40, 6: 0, 7: 5})


class TestProblem87TournamentWinners(unittest.TestCase):
    def test_top_per_group(self):
        rows = _fresh_runner().query_all(SOLUTIONS[87])
        as_d = {r["group_id"]: r["player_id"] for r in rows}
        # Group 1: Alice (100). Group 2: Frank (92). Group 3: Hank (88).
        self.assertEqual(as_d, {1: 1, 2: 6, 3: 7})


class TestProblem88TieBreaking(unittest.TestCase):
    def test_dept_top_with_ties(self):
        rows = _fresh_runner().query_all(SOLUTIONS[88])
        by_dept: dict[int, list[str]] = {}
        for r in rows:
            by_dept.setdefault(r["departmentId"], []).append(r["name"])
        # Dept 1: Alice and Bob tied at 90k.
        # Dept 2: Eve and Frank tied at 85k.
        self.assertEqual(sorted(by_dept[1]), ["Alice", "Bob"])
        self.assertEqual(sorted(by_dept[2]), ["Eve", "Frank"])


class TestProblem89StockMaxProfit(unittest.TestCase):
    def test_max_profit(self):
        rows = _fresh_runner().query_all(SOLUTIONS[89])
        # Max profit for stock 1: 20 (120 - 100, where the
        # min-so-far is 100 right before the price 120).
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["stock_id"], 1)
        self.assertEqual(rows[0]["max_profit"], 20)


class TestProblem90EmployeeBonus(unittest.TestCase):
    def test_bonus(self):
        rows = _fresh_runner().query_all(SOLUTIONS[90])
        as_d = {r["name"]: r for r in rows}
        self.assertEqual(as_d["Alice"]["bonus"], 5000)
        self.assertEqual(as_d["Alice"]["total_comp"], 55000)
        self.assertEqual(as_d["Bob"]["bonus"], 0)
        self.assertEqual(as_d["Bob"]["total_comp"], 60000)
        self.assertEqual(as_d["Dan"]["bonus"], 0)
        self.assertEqual(as_d["Dan"]["total_comp"], 80000)


class TestProblem91ConsecutiveSeats(unittest.TestCase):
    def test_consecutive(self):
        rows = _fresh_runner().query_all(SOLUTIONS[91])
        # Seats: 1, 0, 1, 1, 0, 1, 1, 1, 0. Consecutive
        # free pairs at 3-4 and 6-7, 7-8. So seat_ids 3, 6, 7.
        self.assertEqual([r["seat_id"] for r in rows], [3, 6, 7])


class TestProblem92RankScores(unittest.TestCase):
    def test_rank(self):
        rows = _fresh_runner().query_all(SOLUTIONS[92])
        as_d = {r["score"]: r["rank"] for r in rows}
        # 100→1, 90→2, 80→3, 75→4.
        self.assertEqual(as_d, {100: 1, 90: 2, 80: 3, 75: 4})


class TestProblem93DepartmentStats(unittest.TestCase):
    def test_stats(self):
        rows = _fresh_runner().query_all(SOLUTIONS[93])
        as_d = {r["name"]: r for r in rows}
        self.assertEqual(as_d["Engineering"]["n_employees"], 3)
        self.assertEqual(as_d["Engineering"]["max_salary"], 90000)
        self.assertEqual(as_d["Engineering"]["min_salary"], 70000)
        self.assertAlmostEqual(as_d["Engineering"]["avg_salary"], 81666.67, places=1)
        self.assertEqual(as_d["Sales"]["n_employees"], 2)
        self.assertEqual(as_d["Sales"]["max_salary"], 95000)
        self.assertEqual(as_d["Marketing"]["n_employees"], 1)
        self.assertEqual(as_d["Marketing"]["min_salary"], 60000)


class TestProblem94CancellationRate(unittest.TestCase):
    def test_rates(self):
        rows = _fresh_runner().query_all(SOLUTIONS[94])
        as_d = {r["Day"]: r["Cancellation Rate"] for r in rows}
        # 2024-01-01: 2 of 3 → 0.67
        # 2024-01-02: 0 of 2 → 0.0
        # 2024-01-03: 3 of 4 → 0.75
        self.assertAlmostEqual(as_d["2024-01-01"], 0.67, places=2)
        self.assertAlmostEqual(as_d["2024-01-02"], 0.0)
        self.assertAlmostEqual(as_d["2024-01-03"], 0.75, places=2)


class TestProblem95MarketAnalysisII(unittest.TestCase):
    def test_same_brand(self):
        rows = _fresh_runner().query_all(SOLUTIONS[95])
        as_d = {r["buyer_id"]: r["same_brand_purchases"] for r in rows}
        # Alice (1): bought Sony + Apple. Sold brands: Apple.
        #   Sony != Apple, Apple == Apple → 1 match.
        # Bob (2): bought Apple, Samsung, Apple. Sold brands:
        #   Samsung, Apple. All 3 match → 3 matches.
        # Carol (3): bought Apple, Samsung, Sony. Sold
        #   brands: Samsung, Apple. Apple ✓, Samsung ✓,
        #   Sony ✗ → 2 matches.
        # Dan (4): bought Samsung, Apple. Sold brands: Sony,
        #   Samsung. Samsung ✓, Apple ✗ → 1 match.
        self.assertEqual(as_d[1], 1)
        self.assertEqual(as_d[2], 3)
        self.assertEqual(as_d[3], 2)
        self.assertEqual(as_d[4], 1)


class TestProblem96SalesByYear(unittest.TestCase):
    def test_yoy(self):
        rows = _fresh_runner().query_all(SOLUTIONS[96])
        # Product 1: 2022 (100) → 2023 (200), growth 100.
        # Product 2: 2022 (150) → 2023 (250), growth 100.
        #            2023 (250) → 2024 (180), growth -70.
        as_d = {(r["product_id"], r["sale_date"]): r["yoy_growth"]
                for r in rows}
        self.assertEqual(as_d[(1, "2023-06-15")], 100)
        self.assertEqual(as_d[(2, "2023-07-01")], 100)
        self.assertEqual(as_d[(2, "2024-07-01")], -70)


class TestProblem97TransactionsPerVisit(unittest.TestCase):
    def test_counts(self):
        rows = _fresh_runner().query_all(SOLUTIONS[97])
        as_d = {(r["user_id"], r["visit_date"]): r["n_transactions"]
                for r in rows}
        self.assertEqual(as_d[(1, "2024-01-01")], 2)
        self.assertEqual(as_d[(1, "2024-01-02")], 1)
        self.assertEqual(as_d[(1, "2024-01-04")], 0)
        self.assertEqual(as_d[(2, "2024-01-01")], 1)
        self.assertEqual(as_d[(3, "2024-01-02")], 1)


class TestProblem98LastPersonToFit(unittest.TestCase):
    def test_last(self):
        rows = _fresh_runner().query_all(SOLUTIONS[98])
        # Cumulative: 300, 700, 1200, 1400, 1750. Capacity 1000.
        # Last person with cumulative <= 1000: turn 2 (Bob).
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Bob")


if __name__ == "__main__":
    unittest.main()
