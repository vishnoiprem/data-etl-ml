"""HTTP-level tests for the typeahead service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import TypeaheadService  # noqa: E402


class TypeaheadAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = TypeaheadService(k=5)
        self.svc.load_default()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)

    def test_suggest(self):
        r = self.client.get("/suggest?q=py&k=3")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["q"], "py")
        self.assertLessEqual(len(body["suggestions"]), 3)

    def test_reload(self):
        r = self.client.post("/api/reload")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["loaded"])

    def test_metrics(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("suggest_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
