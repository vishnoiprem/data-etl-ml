"""Tests for the TypeaheadService (loads default dictionary)."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import TypeaheadService  # noqa: E402


class TypeaheadServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = TypeaheadService(k=5)
        self.assertTrue(self.svc.load_default(), "sample data missing")

    def test_default_loaded(self):
        self.assertGreater(self.svc.stats()["trie_nodes"], 0)

    def test_known_prefix(self):
        out = self.svc.suggest("py")
        words = [w for w, _ in out]
        self.assertIn("python", words)

    def test_cache_hits(self):
        self.svc.suggest("fla")
        self.svc.suggest("fla")
        s = self.svc.stats()
        self.assertGreaterEqual(s["hits"], 1)

    def test_k_limit(self):
        out = self.svc.suggest("a", k=2)
        self.assertLessEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
