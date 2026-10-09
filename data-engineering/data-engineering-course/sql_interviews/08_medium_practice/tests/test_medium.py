"""Tests for the 31 M08 (Medium) practice SQL problems.

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


# ---- 31 tests, one per problem ----------------------------------------


class TestProblem54ConsecutiveNumbers(unittest.TestCase):
    def test_three_in_a_row(self):
        rows = _fresh_runner().query_all(SOLUTIONS[54])
        # Three 1s in a row at ids 1, 2, 3. (1, 2, 1, 2, 2
        # don't form a 3-streak.)
        self.assertEqual([r["ConsecutiveNums"] for r in rows], [1])


class TestProblem55NthHighestSalary(unittest.TestCase):
    def test_second_highest(self):
        rows = _fresh_runner().query_all(SOLUTIONS[55])
        # 100, 200, 300 → 2nd = 200
        self.assertEqual(rows[0]["SecondHighestSalary"], 200)


class TestProblem56DepartmentTop3(unittest.TestCase):
    def test_top_3_per_dept(self):
        rows = _fresh_runner().query_all(SOLUTIONS[56])
        by_dept: dict[str, list[tuple[str, int]]] = {}
        for r in rows:
            by_dept.setdefault(r["Department"], []).append(
                (r["Employee"], r["salary"])
            )
        self.assertEqual(by_dept["Engineering"],
                         [("Alice", 90000), ("Bob", 85000), ("Carol", 70000)])
        self.assertEqual(by_dept["Sales"],
                         [("Eve", 100000), ("Frank", 95000), ("Grace", 80000)])


class TestProblem57FriendRequests(unittest.TestCase):
    def test_top_friend_count(self):
        rows = _fresh_runner().query_all(SOLUTIONS[57])
        # Each accepted request counts as one friend for
        # both the requester and the accepter. User 1
        # appears 3 times (1,2)+(1) = 3. User 3 appears
        # 3 times (3)+(3,4) = 3. Users 2 and 4 appear 2
        # times each. So the winners are 1 and 3 (tied).
        ids = sorted(r["id"] for r in rows)
        self.assertEqual(ids, [1, 3])
        for r in rows:
            self.assertEqual(r["num"], 3)


class TestProblem58GamePlayI(unittest.TestCase):
    def test_first_login(self):
        rows = _fresh_runner().query_all(SOLUTIONS[58])
        as_d = {r["player_id"]: r["first_login"] for r in rows}
        self.assertEqual(as_d[1], "2024-01-01")
        self.assertEqual(as_d[2], "2024-01-01")
        self.assertEqual(as_d[3], "2024-01-02")


class TestProblem59GamePlayII(unittest.TestCase):
    def test_first_device(self):
        rows = _fresh_runner().query_all(SOLUTIONS[59])
        as_d = {r["player_id"]: r["device_id"] for r in rows}
        # Player 1 first on day 2024-01-01 → device 2
        # Player 2 first on day 2024-01-01 → device 1
        # Player 3 first on day 2024-01-02 → device 2
        self.assertEqual(as_d[1], 2)
        self.assertEqual(as_d[2], 1)
        self.assertEqual(as_d[3], 2)


class TestProblem60GamePlayIII(unittest.TestCase):
    def test_running_total(self):
        rows = _fresh_runner().query_all(SOLUTIONS[60])
        as_d = {(r["player_id"], r["event_date"]): r["games_played_so_far"]
                for r in rows}
        # Player 1: 5, 5+6=11, 11+7=18
        self.assertEqual(as_d[(1, "2024-01-01")], 5)
        self.assertEqual(as_d[(1, "2024-01-02")], 11)
        self.assertEqual(as_d[(1, "2024-01-03")], 18)
        # Player 2: 4, 4+3=7
        self.assertEqual(as_d[(2, "2024-01-01")], 4)
        self.assertEqual(as_d[(2, "2024-01-05")], 7)


class TestProblem61GamePlayIV(unittest.TestCase):
    def test_retention(self):
        rows = _fresh_runner().query_all(SOLUTIONS[61])
        # 1 of 3 players logged in next day → 0.33
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["fraction"], 0.33, places=2)


class TestProblem62SalesAnalysisIII(unittest.TestCase):
    def test_q1_only(self):
        rows = _fresh_runner().query_all(SOLUTIONS[62])
        as_d = {r["product_id"]: r["product_name"] for r in rows}
        # Product 1: 2024-01-15, 2024-03-10 → Q1 only ✓
        # Product 2: 2024-04-05 → not Q1
        # Product 3: 2024-02-20 → Q1 only ✓
        self.assertEqual(as_d, {1: "Widget A", 3: "Widget C"})


class TestProblem63TreeNode(unittest.TestCase):
    def test_classify(self):
        rows = _fresh_runner().query_all(SOLUTIONS[63])
        as_d = {r["id"]: r["Type"] for r in rows}
        # 1: p_id NULL → Root
        # 2: p_id=1, IS parent → Inner
        # 3: p_id=1, NOT parent → Leaf
        # 4: p_id=2, NOT parent → Leaf
        # 5: p_id=2, NOT parent → Leaf
        self.assertEqual(as_d, {1: "Root", 2: "Inner",
                                3: "Leaf", 4: "Leaf", 5: "Leaf"})


class TestProblem64MedianEmployeeSalary(unittest.TestCase):
    def test_median_per_company(self):
        rows = _fresh_runner().query_all(SOLUTIONS[64])
        as_d = {r["company"]: r["median"] for r in rows}
        # A: 1534, 2241, 2341, 3701, 4021 → 2341
        # B: 5423, 6321, 8213, 9432 → avg(6321, 8213) = 7267
        # C: 1023, 3000, 5500 → 3000
        self.assertAlmostEqual(as_d["A"], 2341.0)
        self.assertAlmostEqual(as_d["B"], 7267.0)
        self.assertAlmostEqual(as_d["C"], 3000.0)


class TestProblem65SwapSalary(unittest.TestCase):
    def test_swap(self):
        q = _fresh_runner()
        q.execute(SOLUTIONS[65])
        rows = q.query_all("SELECT id, name, sex FROM Salary ORDER BY id")
        as_d = {r["name"]: r["sex"] for r in rows}
        self.assertEqual(as_d, {"Alice": "f", "Bob": "m",
                                "Carol": "f", "Dan": "m"})


class TestProblem66TripsAndUsers(unittest.TestCase):
    def test_cancellation_rate(self):
        rows = _fresh_runner().query_all(SOLUTIONS[66])
        as_d = {r["request_at"]: r["cancellation_rate"] for r in rows}
        # 2024-01-01: 2 trips (1 completed, 1 cancelled) → 0.5
        self.assertAlmostEqual(as_d["2024-01-01"], 0.5)
        # 2024-01-02: 0 trips after filtering (clients/drivers
        # banned) → no row in result
        self.assertNotIn("2024-01-02", as_d)


class TestProblem67HumanTraffic(unittest.TestCase):
    def test_three_day_window(self):
        rows = _fresh_runner().query_all(SOLUTIONS[67])
        ids = sorted(r["id"] for r in rows)
        # Days with people >= 100: 3 (105), 4 (200), 6 (300).
        # Each such day appears because the window ±2 contains
        # at least one high-traffic day on each side.
        self.assertEqual(ids, [3, 4, 6])


class TestProblem68DepartmentHighestSalary(unittest.TestCase):
    def test_per_dept_top(self):
        rows = _fresh_runner().query_all(SOLUTIONS[68])
        as_d = {(r["Department"], r["Employee"]): r["salary"] for r in rows}
        self.assertEqual(as_d[("Engineering", "Alice")], 90000)
        self.assertEqual(as_d[("Sales", "Carol")], 95000)


class TestProblem69ExchangeSeats(unittest.TestCase):
    def test_swap(self):
        rows = _fresh_runner().query_all(SOLUTIONS[69])
        as_d = {r["id"]: r["student"] for r in rows}
        # 5 seats: 1<->2, 3<->4, 5 stays.
        self.assertEqual(as_d, {1: "Bob", 2: "Alice", 3: "Dan", 4: "Carol", 5: "Eve"})


class TestProblem70BoughtAllProducts(unittest.TestCase):
    def test_all_products(self):
        rows = _fresh_runner().query_all(SOLUTIONS[70])
        # Customer 1 has 3 products, total products = 3.
        self.assertEqual([r["customer_id"] for r in rows], [1])


class TestProblem71ProductSalesI(unittest.TestCase):
    def test_total_units(self):
        rows = _fresh_runner().query_all(SOLUTIONS[71])
        as_d = {r["product_id"]: r["total_units"] for r in rows}
        # Product 1: 100+200+150=450, Product 2: 300+250=550
        self.assertEqual(as_d, {1: 450, 2: 550})


class TestProblem72ProductSalesII(unittest.TestCase):
    def test_first_sale(self):
        rows = _fresh_runner().query_all(SOLUTIONS[72])
        as_d = {r["product_id"]: r["first_sale"] for r in rows}
        self.assertEqual(as_d, {1: "2024-01-15", 2: "2024-01-22"})


class TestProblem73ProductSalesIII(unittest.TestCase):
    def test_avg_units(self):
        rows = _fresh_runner().query_all(SOLUTIONS[73])
        as_d = {r["product_id"]: r["avg_units"] for r in rows}
        # Product 1: 450/3=150, Product 2: 550/2=275
        self.assertEqual(as_d, {1: 150.0, 2: 275.0})


class TestProblem74DailyLeadsAndPartners(unittest.TestCase):
    def test_per_day_make(self):
        rows = _fresh_runner().query_all(SOLUTIONS[74])
        as_d = {(r["date_id"], r["make_name"]): r for r in rows}
        self.assertEqual(as_d[("2024-01-01", "Toyota")]["unique_leads"], 3)
        self.assertEqual(as_d[("2024-01-01", "Toyota")]["unique_partners"], 3)
        self.assertEqual(as_d[("2024-01-02", "Toyota")]["unique_leads"], 2)
        self.assertEqual(as_d[("2024-01-01", "Honda")]["unique_leads"], 1)


class TestProblem75CommentsPerPost(unittest.TestCase):
    def test_counts(self):
        rows = _fresh_runner().query_all(SOLUTIONS[75])
        as_d = {r["id"]: r["n_comments"] for r in rows}
        # Post 1: 2, Post 2: 1, Post 3: 0
        self.assertEqual(as_d, {1: 2, 2: 1, 3: 0})


class TestProblem76PageRecommendations(unittest.TestCase):
    def test_friend_likes(self):
        rows = _fresh_runner().query_all(SOLUTIONS[76])
        # User 1's friends (2, 3, 4) like pages 100, 200.
        self.assertEqual(sorted(r["page_id"] for r in rows), [100, 200])


class TestProblem77CapitalGainLoss(unittest.TestCase):
    def test_per_stock(self):
        rows = _fresh_runner().query_all(SOLUTIONS[77])
        as_d = {r["stock_name"]: r["capital_gain_loss"] for r in rows}
        # AAPL: 200-100+150-50=200. GOOG: 600-500=100.
        self.assertEqual(as_d, {"AAPL": 200, "GOOG": 100})


class TestProblem78Winners(unittest.TestCase):
    def test_top_per_contest(self):
        rows = _fresh_runner().query_all(SOLUTIONS[78])
        as_d = {r["contest_id"]: r["name"] for r in rows}
        # Contest 1: Alice (100). Contest 2: Bob (95).
        # Contest 3: Carol (100).
        self.assertEqual(as_d, {1: "Alice", 2: "Bob", 3: "Carol"})


class TestProblem79ConfirmationRate(unittest.TestCase):
    def test_rates(self):
        rows = _fresh_runner().query_all(SOLUTIONS[79])
        as_d = {r["user_id"]: r["confirmation_rate"] for r in rows}
        # User 1: 2 of 3 confirmed → 0.667
        # User 2: 1 of 1 confirmed → 1.0
        # User 3: 0 of 1 confirmed → 0.0
        self.assertAlmostEqual(as_d[1], 0.667, places=3)
        self.assertAlmostEqual(as_d[2], 1.0)
        self.assertAlmostEqual(as_d[3], 0.0)


class TestProblem80StudentsExams(unittest.TestCase):
    def test_cross_join(self):
        rows = _fresh_runner().query_all(SOLUTIONS[80])
        as_d = {(r["student_id"], r["subject_name"]): r["attended_exams"]
                for r in rows}
        # 3 students × 3 subjects = 9 rows
        self.assertEqual(len(rows), 9)
        self.assertEqual(as_d[(1, "Math")], 1)
        self.assertEqual(as_d[(1, "Physics")], 1)
        self.assertEqual(as_d[(1, "Chemistry")], 0)
        self.assertEqual(as_d[(2, "Math")], 1)
        self.assertEqual(as_d[(2, "Physics")], 0)
        self.assertEqual(as_d[(3, "Math")], 0)


class TestProblem81UserActivity(unittest.TestCase):
    def test_daily_active(self):
        rows = _fresh_runner().query_all(SOLUTIONS[81])
        as_d = {r["activity_date"]: r["active_users"] for r in rows}
        # 4 distinct days in the 2024-01-01..2024-01-30 range.
        self.assertEqual(as_d["2024-01-01"], 1)
        self.assertEqual(as_d["2024-01-05"], 1)
        self.assertEqual(as_d["2024-01-15"], 1)
        self.assertEqual(as_d["2024-01-20"], 1)


class TestProblem82ImmediateDelivery(unittest.TestCase):
    def test_fraction(self):
        rows = _fresh_runner().query_all(SOLUTIONS[82])
        # 3 of 5 deliveries are immediate.
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["immediate_fraction"], 0.6)


class TestProblem83SalesAnalysisI(unittest.TestCase):
    def test_max_year(self):
        rows = _fresh_runner().query_all(SOLUTIONS[83])
        as_d = {r["product_id"]: (r["year"], r["total"]) for r in rows}
        # Product 1: 2023 (1320 > 1000). Product 2: 2024 (640 > 250).
        self.assertEqual(as_d[1], (2023, 1320))
        self.assertEqual(as_d[2], (2024, 640))


class TestProblem84DailyActiveUsers(unittest.TestCase):
    def test_dau(self):
        rows = _fresh_runner().query_all(SOLUTIONS[84])
        as_d = {r["login_date"]: r["dau"] for r in rows}
        self.assertEqual(as_d["2024-01-01"], 2)
        self.assertEqual(as_d["2024-01-02"], 2)
        self.assertEqual(as_d["2024-01-03"], 3)


if __name__ == "__main__":
    unittest.main()
