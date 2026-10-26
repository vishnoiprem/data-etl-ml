"""Tests for the trie data structure."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.trie import Trie  # noqa: E402


class TrieTests(unittest.TestCase):
    def test_empty(self):
        t = Trie()
        self.assertEqual(t.suggest("xyz"), [])

    def test_insert_and_suggest(self):
        t = Trie(k=5)
        t.insert("flask", 1000)
        t.insert("flash", 800)
        t.insert("flat", 600)
        t.insert("apple", 500)
        out = [w for w, _ in t.suggest("fla")]
        self.assertEqual(out, ["flask", "flash", "flat"])
        self.assertEqual(t.suggest("apple"), [])  # "apple" doesn't start with "fla"
        self.assertEqual(t.suggest("xyz"), [])

    def test_top_k_respected(self):
        t = Trie(k=3)
        for i, w in enumerate(["aa", "ab", "ac", "ad", "ae"]):
            t.insert(w, 100 - i)
        out = [w for w, _ in t.suggest("a")]
        self.assertEqual(out, ["aa", "ab", "ac"])

    def test_case_insensitive(self):
        t = Trie()
        t.insert("Flask", 100)
        self.assertEqual([w for w, _ in t.suggest("FLA")], ["flask"])

    def test_frequency_ranking(self):
        t = Trie()
        t.insert("apple", 10)
        t.insert("apricot", 100)
        t.insert("apex", 50)
        out = [w for w, _ in t.suggest("ap")]
        self.assertEqual(out, ["apricot", "apex", "apple"])


if __name__ == "__main__":
    unittest.main()
