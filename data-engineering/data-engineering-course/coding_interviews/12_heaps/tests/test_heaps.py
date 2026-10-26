"""Tests for Module 12 — Heaps."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p86_kth_largest import solve_kth_largest  # type: ignore  # noqa: E402
from p87_top_k_frequent_words import solve_top_k_frequent_words  # type: ignore  # noqa: E402
from p88_median_stream import solve_median_stream  # type: ignore  # noqa: E402
from p89_task_scheduler import solve_task_scheduler  # type: ignore  # noqa: E402
from p90_meeting_rooms import solve_meeting_rooms  # type: ignore  # noqa: E402


class KthLargestTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_kth_largest([3, 2, 1, 5, 6, 4], 2), 5)

    def test_first(self):
        self.assertEqual(solve_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4), 4)

    def test_single(self):
        self.assertEqual(solve_kth_largest([1], 1), 1)


class TopKFrequentWordsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_top_k_frequent_words(["i", "love", "leetcode", "i", "love", "coding"], 2),
            ["i", "love"],
        )

    def test_lexicographic_tiebreak(self):
        self.assertEqual(
            solve_top_k_frequent_words(["a", "b", "c", "a", "b", "a"], 2),
            ["a", "b"],
        )


class MedianStreamTests(unittest.TestCase):
    def test_basic(self):
        ops = [
            ("MedianFinder",),
            ("addNum", 1),
            ("addNum", 2),
            ("findMedian",),
            ("addNum", 3),
            ("findMedian",),
        ]
        self.assertEqual(solve_median_stream(ops), [1.5, 2.0])

    def test_odd_count(self):
        ops = [
            ("MedianFinder",),
            ("addNum", 2),
            ("findMedian",),
            ("addNum", 3),
            ("findMedian",),
        ]
        self.assertEqual(solve_median_stream(ops), [2, 2.5])


class TaskSchedulerTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_task_scheduler(["A", "A", "A", "B", "B", "B"], 2), 8)

    def test_no_cooldown(self):
        # Same task repeating is okay when cooldown is 0.
        self.assertEqual(solve_task_scheduler(["A", "A", "A"], 0), 3)


class MeetingRoomsTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(solve_meeting_rooms([[0, 30], [5, 10], [15, 20]]), 2)

    def test_no_overlap(self):
        self.assertEqual(solve_meeting_rooms([[0, 5], [5, 10], [10, 15]]), 1)

    def test_empty(self):
        self.assertEqual(solve_meeting_rooms([]), 0)


if __name__ == "__main__":
    unittest.main()
