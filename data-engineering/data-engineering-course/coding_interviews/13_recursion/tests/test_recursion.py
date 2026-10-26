"""Tests for Module 13 — Recursion & Backtracking."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE_DIR = HERE.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from p91_subsets import solve_subsets  # type: ignore  # noqa: E402
from p92_permutations import solve_permutations  # type: ignore  # noqa: E402
from p93_combination_sum import solve_combination_sum  # type: ignore  # noqa: E402
from p94_word_search import solve_word_search  # type: ignore  # noqa: E402
from p95_generate_parens import solve_generate_parens  # type: ignore  # noqa: E402
from p96_letter_combinations import solve_letter_combinations  # type: ignore  # noqa: E402
from p97_sudoku_solver import solve_sudoku  # type: ignore  # noqa: E402
from p98_n_queens import solve_n_queens  # type: ignore  # noqa: E402
from p99_palindrome_partitioning import solve_palindrome_partitioning  # type: ignore  # noqa: E402
from p100_restore_ip import solve_restore_ip_addresses  # type: ignore  # noqa: E402
from p101_expression_add_operators import solve_expression_add_operators  # type: ignore  # noqa: E402
from p102_word_break_ii import solve_word_break_ii  # type: ignore  # noqa: E402


class SubsetsTests(unittest.TestCase):
    def test_three(self):
        out = solve_subsets([1, 2, 3])
        normalized = sorted([tuple(sorted(s)) for s in out])
        self.assertEqual(normalized, sorted([(), (1,), (1, 2), (1, 2, 3),
                                             (1, 3), (2,), (2, 3), (3,)]))

    def test_empty(self):
        self.assertEqual(solve_subsets([]), [[]])


class PermutationsTests(unittest.TestCase):
    def test_three(self):
        self.assertEqual(len(solve_permutations([1, 2, 3])), 6)

    def test_empty(self):
        self.assertEqual(solve_permutations([]), [[]])


class CombinationSumTests(unittest.TestCase):
    def test_basic(self):
        out = solve_combination_sum([2, 3, 6, 7], 7)
        normalized = sorted([tuple(sorted(c)) for c in out])
        self.assertEqual(normalized, sorted([(7,), (2, 2, 3)]))

    def test_no_solution(self):
        self.assertEqual(solve_combination_sum([2], 7), [])


class WordSearchTests(unittest.TestCase):
    def test_found(self):
        b = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
        self.assertTrue(solve_word_search(b, "ABCCED"))

    def test_not_found(self):
        b = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
        self.assertFalse(solve_word_search(b, "ABCB"))


class GenerateParensTests(unittest.TestCase):
    def test_three(self):
        out = solve_generate_parens(3)
        self.assertEqual(len(out), 5)
        self.assertIn("((()))", out)
        self.assertIn("()()()", out)


class LetterCombinationsTests(unittest.TestCase):
    def test_basic(self):
        out = solve_letter_combinations("23")
        self.assertEqual(len(out), 9)
        self.assertIn("ad", out)

    def test_empty(self):
        self.assertEqual(solve_letter_combinations(""), [])


class SudokuTests(unittest.TestCase):
    def test_solve(self):
        board = [
            ["5", "3", ".", ".", "7", ".", ".", ".", "."],
            ["6", ".", ".", "1", "9", "5", ".", ".", "."],
            [".", "9", "8", ".", ".", ".", ".", "6", "."],
            ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
            ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
            ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
            [".", "6", ".", ".", ".", ".", "2", "8", "."],
            [".", ".", ".", "4", "1", "9", ".", ".", "5"],
            [".", ".", ".", ".", "8", ".", ".", "7", "9"],
        ]
        solve_sudoku(board)
        # Every row contains 1..9 exactly once.
        for row in board:
            self.assertEqual(sorted(row), [str(i) for i in range(1, 10)])


class NQueensTests(unittest.TestCase):
    def test_four(self):
        self.assertEqual(len(solve_n_queens(4)), 2)

    def test_zero(self):
        self.assertEqual(solve_n_queens(0), [[]])


class PalindromePartitionTests(unittest.TestCase):
    def test_basic(self):
        out = solve_palindrome_partitioning("aab")
        normalized = sorted([tuple(p) for p in out])
        self.assertEqual(normalized, [("a", "a", "b"), ("aa", "b")])


class RestoreIPTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            sorted(solve_restore_ip_addresses("25525511135")),
            ["255.255.11.135", "255.255.111.35"],
        )


class ExpressionOperatorsTests(unittest.TestCase):
    def test_basic(self):
        out = solve_expression_add_operators("123", 6)
        self.assertEqual(set(out), {"1+2+3", "1*2*3"})

    def test_zero_target(self):
        out = solve_expression_add_operators("100", 0)
        self.assertIn("1*0*0", out)


class WordBreakIITests(unittest.TestCase):
    def test_basic(self):
        out = solve_word_break_ii("catsanddog", ["cat", "cats", "and", "sand", "dog"])
        self.assertEqual(sorted(out), ["cat sand dog", "cats and dog"])

    def test_no_break(self):
        self.assertEqual(solve_word_break_ii("catsandog", ["cat", "sand", "dog"]), [])


if __name__ == "__main__":
    unittest.main()
