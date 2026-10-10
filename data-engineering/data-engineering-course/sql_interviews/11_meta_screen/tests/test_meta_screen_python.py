"""Tests for the 5 Meta screen Python problems."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "code")))

from meta_screen_python import (  # type: ignore  # noqa: E402
    second_highest_per_department,
    summarize_by_page,
    top_5_pages_by_upward_trend,
    tumbling_window_counts,
    users_with_3plus_calls,
)


class TestTop5PagesUpwardTrend(unittest.TestCase):
    def test_returns_pages_with_positive_slope(self):
        df = pd.DataFrame({
            'page_id': [1]*7 + [2]*7 + [3]*7,
            'day': list(range(7)) * 3,
            'impressions': [10, 20, 30, 40, 50, 60, 70,   # up
                            70, 60, 50, 40, 30, 20, 10,   # down
                            10, 10, 10, 10, 10, 10, 10],  # flat
        })
        out = top_5_pages_by_upward_trend(df)
        self.assertEqual(out, [1])

    def test_excludes_pages_with_fewer_than_5_days(self):
        df = pd.DataFrame({
            'page_id': [1]*4 + [2]*7,
            'day': list(range(4)) + list(range(7)),
            'impressions': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
        })
        out = top_5_pages_by_upward_trend(df)
        self.assertEqual(out, [2])


class TestSecondHighest(unittest.TestCase):
    def test_basic(self):
        employees = [
            ('Alice', 'Eng', 100),
            ('Bob',   'Eng', 200),
            ('Carol', 'Eng', 150),
            ('Dan',   'Ops',  90),
        ]
        out = second_highest_per_department(employees)
        self.assertEqual(out, {'Eng': 150, 'Ops': None})

    def test_distinct_vs_raw(self):
        employees = [
            ('A', 'Eng', 100),
            ('B', 'Eng', 100),
            ('C', 'Eng', 50),
        ]
        # Distinct top-2: 100, 50. Second-highest = 50.
        self.assertEqual(
            second_highest_per_department(employees), {'Eng': 50})


class TestSummarizeByPage(unittest.TestCase):
    def test_missing_file(self):
        out = summarize_by_page('/nonexistent/path/data.csv')
        self.assertEqual(out, {})

    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.csv', delete=False) as f:
            f.write('date,page_id,impressions\n')
            f.write('2026-01-01,1,100\n')
            f.write('2026-01-01,1,50\n')
            f.write('2026-01-02,2,200\n')
            f.write('malformed,row,here\n')   # skipped
            f.write('2026-01-03,1,75\n')
            path = f.name
        try:
            out = summarize_by_page(path)
            self.assertEqual(out, {'1': 225, '2': 200})
        finally:
            os.unlink(path)


class TestUsersWith3PlusCalls(unittest.TestCase):
    def test_users_with_3_calls_in_last_week(self):
        now = 1000
        events = [
            (100, 1, 2),   # 1, 2
            (200, 1, 3),   # 1, 3
            (300, 1, 4),   # 1, 4
            (400, 5, 6),   # 5, 6 (no further events)
        ]
        out = users_with_3plus_calls(events, now=now)
        # User 1 appears 3 times -> qualifies.
        self.assertIn(1, out)
        # User 2, 3, 4 each appear once -> don't.
        self.assertNotIn(2, out)
        self.assertNotIn(3, out)
        self.assertNotIn(4, out)


class TestTumblingWindow(unittest.TestCase):
    def test_15_min_buckets(self):
        events = [
            (0,    1),   # bucket 0
            (300,  1),   # bucket 0
            (1200, 1),   # bucket 900 (15-min window)
            (1700, 1),   # bucket 900
        ]
        out = tumbling_window_counts(events, window_seconds=900)
        self.assertEqual(out, [(0, 2), (900, 2)])


if __name__ == "__main__":
    unittest.main()
