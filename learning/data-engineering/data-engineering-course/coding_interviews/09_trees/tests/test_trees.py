"""Tests for Module 09 — Trees."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p63_max_depth import solve_max_depth  # type: ignore  # noqa: E402
from p64_validate_bst import solve_validate_bst  # type: ignore  # noqa: E402
from p65_level_order import solve_level_order  # type: ignore  # noqa: E402
from p66_invert_tree import solve_invert_tree  # type: ignore  # noqa: E402
from p67_kth_smallest_bst import solve_kth_smallest_bst  # type: ignore  # noqa: E402
from p68_lca import solve_lca  # type: ignore  # noqa: E402
from p69_build_tree import solve_build_tree  # type: ignore  # noqa: E402
from p70_serialize import solve_serialize, solve_deserialize  # type: ignore  # noqa: E402
from p71_max_path_sum import solve_max_path_sum  # type: ignore  # noqa: E402
from _tree_helpers import from_level_order  # type: ignore  # noqa: E402


class MaxDepthTests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([3, 9, 20, None, None, 15, 7])
        self.assertEqual(solve_max_depth(root), 3)

    def test_empty(self):
        self.assertEqual(solve_max_depth(None), 0)

    def test_single(self):
        self.assertEqual(solve_max_depth(from_level_order([1])), 1)


class ValidateBSTTests(unittest.TestCase):
    def test_valid(self):
        root = from_level_order([2, 1, 3])
        self.assertTrue(solve_validate_bst(root))

    def test_invalid(self):
        root = from_level_order([5, 1, 4, None, None, 3, 6])
        self.assertFalse(solve_validate_bst(root))

    def test_empty(self):
        self.assertTrue(solve_validate_bst(None))


class LevelOrderTests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([3, 9, 20, None, None, 15, 7])
        self.assertEqual(solve_level_order(root), [[3], [9, 20], [15, 7]])

    def test_empty(self):
        self.assertEqual(solve_level_order(None), [])

    def test_single(self):
        self.assertEqual(solve_level_order(from_level_order([1])), [[1]])


class InvertTreeTests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([4, 2, 7, 1, 3, 6, 9])
        inv = solve_invert_tree(root)
        self.assertEqual(solve_level_order(inv), [[4], [7, 2], [9, 6, 3, 1]])

    def test_empty(self):
        self.assertIsNone(solve_invert_tree(None))


class KthSmallestTests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([3, 1, 4, None, 2])
        self.assertEqual(solve_kth_smallest_bst(root, 1), 1)
        self.assertEqual(solve_kth_smallest_bst(root, 3), 3)

    def test_empty(self):
        self.assertIsNone(solve_kth_smallest_bst(None, 1))


class LCATests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p, q = root.left, root.right
        self.assertIs(solve_lca(root, p, q), root)

    def test_descendant(self):
        root = from_level_order([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
        p, q = root.left, root.left.right.right  # 5 and 4
        self.assertIs(solve_lca(root, p, q), root.left)


class BuildTreeTests(unittest.TestCase):
    def test_basic(self):
        root = solve_build_tree([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])
        self.assertEqual(root.val, 3)
        self.assertEqual(root.left.val, 9)
        self.assertEqual(root.right.val, 20)

    def test_empty(self):
        self.assertIsNone(solve_build_tree([], []))


class SerializeTests(unittest.TestCase):
    def test_round_trip(self):
        root = from_level_order([1, 2, 3, None, None, 4, 5])
        s = solve_serialize(root)
        out = solve_deserialize(s)
        self.assertEqual(solve_serialize(out), s)

    def test_none(self):
        self.assertEqual(solve_serialize(None), "N")
        self.assertIsNone(solve_deserialize("N"))


class MaxPathSumTests(unittest.TestCase):
    def test_basic(self):
        root = from_level_order([-10, 9, 20, None, None, 15, 7])
        self.assertEqual(solve_max_path_sum(root), 42)

    def test_single(self):
        self.assertEqual(solve_max_path_sum(from_level_order([-3])), -3)


if __name__ == "__main__":
    unittest.main()
