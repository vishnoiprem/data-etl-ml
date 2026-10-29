"""Tests for the 14 M07 (Easy) practice SQL problems.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Each test method loads the schema, runs the named solution
from code/solutions.sql, and asserts the result rows match
the expected output (by column + value).
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SQL_DIR = HERE.parent / "code"
COURSE_ROOT = HERE.parent.parent.parent

# Make common importable.
sys.path.insert(0, str(COURSE_ROOT))

from common import QueryRunner  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_solutions() -> dict[int, str]:
    """Parse code/solutions.sql into a dict {problem_number: sql}.

    The file format is::
        -- Problem 40: ...
        SELECT ...;
        -- Problem 41: ...
        SELECT ...;
    """
    text = _read(SQL_DIR / "solutions.sql")
    # Find every "-- Problem N: ..." header that is followed
    # by a SQL statement (skip the file-level docstring that
    # merely *mentions* the convention).
    pattern = re.compile(
        r"^--\s*Problem\s+(\d+):[^\n]*\n(.*?)(?=^--\s*Problem\s+\d+:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    out: dict[int, str] = {}
    for m in pattern.finditer(text):
        n = int(m.group(1))
        body = m.group(2)
        # Drop lines that are pure comments so the SQL the
        # test runs is the actual statement, not the prose
        # above it.
        sql_lines = []
        for ln in body.splitlines():
            if ln.strip().startswith("--"):
                continue
            sql_lines.append(ln)
        sql = "\n".join(sql_lines).strip().rstrip(";").strip()
        if sql:
            out[n] = sql
    return out


SOLUTIONS = _load_solutions()


def _fresh_runner() -> QueryRunner:
    """Return a QueryRunner with the M07 schema applied.

    sqlite3 only allows one statement per `execute()` call,
    so we split the schema file on the `;` boundary and run
    each statement individually. We strip `-- ...` comment
    lines first to keep the splitter simple.
    """
    q = QueryRunner(":memory:")
    raw = _read(SQL_DIR / "schema.sql")
    # Drop comment-only lines so we don't split inside them.
    lines = []
    for ln in raw.splitlines():
        stripped = ln.strip()
        if stripped.startswith("--"):
            continue
        lines.append(ln)
    cleaned = "\n".join(lines)
    # Split on `;` and run each non-empty statement.
    for stmt in cleaned.split(";"):
        s = stmt.strip()
        if s:
            q.execute(s)
    return q


# ---- 14 tests, one per problem ------------------------------------------


class TestProblem40TopEarningEmployees(unittest.TestCase):
    """Top earner per department (DENSE_RANK = 1 per dept)."""

    def test_top_per_dept(self):
        rows = _fresh_runner().query_all(SOLUTIONS[40])
        # Expected: (Carol, 150000, 1), (Frank, 130000, 2),
        #           (Hank, 92000, 3), (Ivy, 105000, 4)
        self.assertEqual(
            rows,
            [
                {"name": "Carol", "salary": 150000, "departmentId": 1},
                {"name": "Frank", "salary": 130000, "departmentId": 2},
                {"name": "Hank",  "salary":  92000, "departmentId": 3},
                {"name": "Ivy",   "salary": 105000, "departmentId": 4},
            ],
        )


class TestProblem41EmployeeEarnings(unittest.TestCase):
    """Running total of salary per employee by hire date."""

    def test_running_total(self):
        rows = _fresh_runner().query_all(SOLUTIONS[41])
        # Each employee has exactly one row, so the running
        # total equals the salary.
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(r["running_salary"], r["salary"])
        # Spot-check a few specific rows.
        alice = next(r for r in rows if r["name"] == "Alice")
        self.assertEqual(alice["running_salary"], 120000)


class TestProblem42RemoveDuplicateEmails(unittest.TestCase):
    """DELETE keeps the smallest id per email."""

    def test_keeps_min_id(self):
        q = _fresh_runner()
        # Run the DELETE (solutions.sql contains a DELETE
        # statement at problem 42).
        q.execute(SOLUTIONS[42])
        # Verify the surviving rows: emails a, b, c, d → ids 1, 2, 4, 7.
        rows = q.query_all("SELECT id, email FROM Person ORDER BY id")
        self.assertEqual(
            rows,
            [
                {"id": 1, "email": "a@example.com"},
                {"id": 2, "email": "b@example.com"},
                {"id": 4, "email": "c@example.com"},
                {"id": 7, "email": "d@example.com"},
            ],
        )


class TestProblem43TopSalariesByDepartment(unittest.TestCase):
    """Top 3 salaries per department, with ties preserved."""

    def test_top_three(self):
        rows = _fresh_runner().query_all(SOLUTIONS[43])
        names_by_dept: dict[int, list[str]] = {}
        for r in rows:
            names_by_dept.setdefault(r["departmentId"], []).append(r["name"])
        # Engineering: Carol, Alice, Bob
        self.assertEqual(names_by_dept[1], ["Carol", "Alice", "Bob"])
        # Sales: Frank, Dan, Eve
        self.assertEqual(names_by_dept[2], ["Frank", "Dan", "Eve"])
        # Marketing: only Hank, Grace (no third)
        self.assertEqual(names_by_dept[3], ["Hank", "Grace"])
        # Finance: Ivy, Judy (no third)
        self.assertEqual(names_by_dept[4], ["Ivy", "Judy"])


class TestProblem44InstagramLikes(unittest.TestCase):
    """Users with >=2 posts having more than 100 likes."""

    def test_engaged_users(self):
        rows = _fresh_runner().query_all(SOLUTIONS[44])
        # Only user 1 has 3 posts with > 100 likes.
        self.assertEqual([r["userId"] for r in rows], [1])


class TestProblem45MonthlyPostSuccess(unittest.TestCase):
    """Per (user, month) post counts and like totals."""

    def test_per_user_month(self):
        rows = _fresh_runner().query_all(SOLUTIONS[45])
        # (user 1, 2024-01): 2 posts, 250 likes, 125 avg
        # (user 1, 2024-02): 2 posts, 380 likes, 190 avg
        # (user 2, 2024-01): 1 post,  50 likes,  50 avg
        # (user 2, 2024-02): 1 post,  75 likes,  75 avg
        # (user 2, 2024-03): 1 post, 100 likes, 100 avg
        # (user 3, 2024-01): 1 post, 300 likes, 300 avg
        as_dicts = {
            (r["userId"], r["month"]): (r["n_posts"], r["total_likes"])
            for r in rows
        }
        self.assertEqual(as_dicts[(1, "2024-01")], (2, 250))
        self.assertEqual(as_dicts[(1, "2024-02")], (2, 380))
        self.assertEqual(as_dicts[(2, "2024-01")], (1,  50))
        self.assertEqual(as_dicts[(3, "2024-01")], (1, 300))


class TestProblem46CalculateTestScores(unittest.TestCase):
    """NULL handling in test scores."""

    def test_per_student_avg(self):
        rows = _fresh_runner().query_all(SOLUTIONS[46])
        as_dict = {r["student"]: r for r in rows}
        # A: 90, 85, 95 → avg = 90.0
        self.assertAlmostEqual(as_dict["A"]["avg_score"], 90.0)
        self.assertEqual(as_dict["A"]["n_null"], 0)
        # B: 78, NULL → avg = 78.0, 1 null
        self.assertAlmostEqual(as_dict["B"]["avg_score"], 78.0)
        self.assertEqual(as_dict["B"]["n_null"], 1)
        # C: NULL, 88 → avg = 88.0
        self.assertAlmostEqual(as_dict["C"]["avg_score"], 88.0)
        # D: 92, NULL → avg = 92.0
        self.assertAlmostEqual(as_dict["D"]["avg_score"], 92.0)


class TestProblem47CustomerLTV(unittest.TestCase):
    """Customer lifetime value, delivered orders only."""

    def test_ltv(self):
        rows = _fresh_runner().query_all(SOLUTIONS[47])
        as_dict = {r["name"]: r for r in rows}
        # Karen: 100 + 200 = 300, n=2
        self.assertEqual(as_dict["Karen"]["lifetime_value"], 300)
        self.assertEqual(as_dict["Karen"]["n_orders"], 2)
        # Nate: 400 + 175 = 575
        self.assertEqual(as_dict["Nate"]["lifetime_value"], 575)
        # Olive: no delivered orders, LTV=0, n=0
        self.assertEqual(as_dict["Olive"]["lifetime_value"], 0)
        self.assertEqual(as_dict["Olive"]["n_orders"], 0)
        # All 6 customers present (LEFT JOIN)
        self.assertEqual(len(rows), 6)


class TestProblem48SecondHighestSalary(unittest.TestCase):
    """The second distinct highest salary."""

    def test_second_highest(self):
        rows = _fresh_runner().query_all(SOLUTIONS[48])
        self.assertEqual(len(rows), 1)
        # Salaries: 78k, 85k, 88k, 92k, 95k, 105k, 110k, 120k, 130k, 150k
        # 1st = 150k, 2nd = 130k
        self.assertEqual(rows[0]["second_highest_salary"], 130000)


class TestProblem49CustomersWhoNeverOrder(unittest.TestCase):
    """Customers with no orders (anti-join)."""

    def test_no_orders(self):
        rows = _fresh_runner().query_all(SOLUTIONS[49])
        # Only Paul (id=6) has no orders.
        self.assertEqual([r["name"] for r in rows], ["Paul"])


class TestProblem50DepartmentHighestSalary(unittest.TestCase):
    """Department + employee + salary for the top earner per dept."""

    def test_top_per_dept_with_join(self):
        rows = _fresh_runner().query_all(SOLUTIONS[50])
        as_dict = {r["department"]: r for r in rows}
        self.assertEqual(as_dict["Engineering"]["employee"], "Carol")
        self.assertEqual(as_dict["Engineering"]["salary"], 150000)
        self.assertEqual(as_dict["Sales"]["employee"], "Frank")
        self.assertEqual(as_dict["Sales"]["salary"], 130000)
        self.assertEqual(as_dict["Marketing"]["employee"], "Hank")
        self.assertEqual(as_dict["Marketing"]["salary"], 92000)
        self.assertEqual(as_dict["Finance"]["employee"], "Ivy")
        self.assertEqual(as_dict["Finance"]["salary"], 105000)


class TestProblem51RisingTemperature(unittest.TestCase):
    """Days where temperature was higher than the previous day."""

    def test_rising(self):
        rows = _fresh_runner().query_all(SOLUTIONS[51])
        # Day 2 (15 > 10), Day 4 (20 > 12), Day 6 (25 > 18).
        self.assertEqual([r["id"] for r in rows], [2, 4, 6])


class TestProblem52ClassesMoreThan5Students(unittest.TestCase):
    """Classes with 5 or more students."""

    def test_classes(self):
        rows = _fresh_runner().query_all(SOLUTIONS[52])
        # Math (6), Physics (6). English (4) and History (4) excluded.
        self.assertEqual(sorted(r["class"] for r in rows),
                         ["Math", "Physics"])


class TestProblem53BigCountries(unittest.TestCase):
    """Countries with population > 25M or area > 3M."""

    def test_big(self):
        rows = _fresh_runner().query_all(SOLUTIONS[53])
        names = sorted(r["name"] for r in rows)
        self.assertEqual(names, ["Brazil", "China", "India", "USA"])


if __name__ == "__main__":
    unittest.main()
