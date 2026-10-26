"""Tests for Module 08 — Graphs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p54_number_of_islands import solve_number_of_islands  # type: ignore  # noqa: E402
from p55_clone_graph import solve_clone_graph  # type: ignore  # noqa: E402
from p56_course_schedule import solve_course_schedule  # type: ignore  # noqa: E402
from p57_pacific_atlantic import solve_pacific_atlantic  # type: ignore  # noqa: E402
from p58_word_ladder import solve_word_ladder  # type: ignore  # noqa: E402
from p59_alien_dictionary import solve_alien_dictionary  # type: ignore  # noqa: E402
from p60_graph_valid_tree import solve_graph_valid_tree  # type: ignore  # noqa: E402
from p61_rotting_oranges import solve_rotting_oranges  # type: ignore  # noqa: E402
from p62_network_delay import solve_network_delay  # type: ignore  # noqa: E402
from _graph_helpers import neighbors_to_adj, Node  # type: ignore  # noqa: E402


def _adj_clone_input():
    """Build a 4-node graph: 1-2, 2-3, 3-4, 1-4 (a 4-cycle)."""
    return neighbors_to_adj([[2, 4], [1, 3], [2, 4], [1, 3]])


class NumberOfIslandsTests(unittest.TestCase):
    def test_basic(self):
        g = [
            ["1", "1", "0", "0", "0"],
            ["1", "1", "0", "0", "0"],
            ["0", "0", "1", "0", "0"],
            ["0", "0", "0", "1", "1"],
        ]
        self.assertEqual(solve_number_of_islands([row[:] for row in g]), 3)

    def test_empty(self):
        self.assertEqual(solve_number_of_islands([]), 0)

    def test_all_water(self):
        self.assertEqual(solve_number_of_islands([["0", "0"], ["0", "0"]]), 0)

    def test_all_land(self):
        g = [["1", "1"], ["1", "1"]]
        self.assertEqual(solve_number_of_islands([row[:] for row in g]), 1)


class CloneGraphTests(unittest.TestCase):
    def test_basic(self):
        root = _adj_clone_input()
        clone = solve_clone_graph(root)
        self.assertIsNotNone(clone)
        self.assertEqual(clone.val, 1)
        self.assertEqual(sorted(n.val for n in clone.neighbors), [2, 4])
        # Ensure it's a deep copy (different objects).
        for nbr in clone.neighbors:
            self.assertIsNot(nbr, [n for n in root.neighbors if n.val == nbr.val][0])

    def test_none(self):
        self.assertIsNone(solve_clone_graph(None))


class CourseScheduleTests(unittest.TestCase):
    def test_feasible(self):
        self.assertTrue(solve_course_schedule(2, [[1, 0]]))

    def test_cycle(self):
        self.assertFalse(solve_course_schedule(2, [[1, 0], [0, 1]]))

    def test_no_prereqs(self):
        self.assertTrue(solve_course_schedule(3, []))


class PacificAtlanticTests(unittest.TestCase):
    def test_basic(self):
        h = [
            [1, 2, 2, 3, 5],
            [3, 2, 3, 4, 4],
            [2, 4, 5, 3, 1],
            [6, 7, 1, 4, 5],
            [5, 1, 1, 2, 4],
        ]
        cells = solve_pacific_atlantic(h)
        # Cells that can reach both oceans (a known set for this grid).
        self.assertEqual(
            sorted(cells),
            sorted([[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]),
        )

    def test_empty(self):
        self.assertEqual(solve_pacific_atlantic([]), [])


class WordLadderTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_word_ladder("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]),
            5,
        )

    def test_no_path(self):
        self.assertEqual(solve_word_ladder("hit", "cog", ["hot", "dot", "dog"]), 0)


class AlienDictionaryTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_alien_dictionary(["wrt", "wrf", "er", "ett", "rftt"]), "wertf"
        )

    def test_invalid_prefix(self):
        self.assertEqual(solve_alien_dictionary(["abc", "ab"]), "")

    def test_single_word(self):
        self.assertEqual(solve_alien_dictionary(["z"]), "z")


class GraphValidTreeTests(unittest.TestCase):
    def test_tree(self):
        self.assertTrue(solve_graph_valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]))

    def test_cycle(self):
        self.assertFalse(solve_graph_valid_tree(3, [[0, 1], [1, 2], [2, 0]]))

    def test_disconnected(self):
        self.assertFalse(solve_graph_valid_tree(3, [[0, 1]]))


class RottingOrangesTests(unittest.TestCase):
    def test_basic(self):
        g = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
        self.assertEqual(solve_rotting_oranges([row[:] for row in g]), 4)

    def test_no_fresh(self):
        self.assertEqual(solve_rotting_oranges([[0]]), 0)

    def test_unreachable(self):
        g = [[2, 1, 1], [0, 1, 1], [1, 0, 1]]
        self.assertEqual(solve_rotting_oranges([row[:] for row in g]), -1)


class NetworkDelayTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            solve_network_delay(4, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2), 2
        )

    def test_unreachable(self):
        self.assertEqual(solve_network_delay(2, [[1, 2, 1]], 2), -1)


if __name__ == "__main__":
    unittest.main()
