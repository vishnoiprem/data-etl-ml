"""Unit tests for the AI-Powered Customer Support core service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.service import SupportService, tokenize  # noqa: E402


class SupportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_ai_support",
            persist_path=os.path.join(self.tmpdir, "ai.json"),
        )
        self.svc = SupportService(store=self.store, top_k=2)

    # ---- tokenize -------------------------------------------------------

    def test_tokenize_strips_stopwords(self):
        self.assertEqual(tokenize("the cat is on the mat"), ["cat", "mat"])

    def test_tokenize_lowercases(self):
        self.assertEqual(tokenize("Hello WORLD"), ["hello", "world"])

    # ---- article ingest -------------------------------------------------

    def test_ingest_article_assigns_id(self):
        a = self.svc.ingest_article("Refunds", "Refunds within 30 days.", tags=["refund"])
        self.assertEqual(a.article_id, 1)
        self.assertEqual(a.tags, ["refund"])

    def test_ingest_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.svc.ingest_article("", "body")
        with self.assertRaises(ValueError):
            self.svc.ingest_article("title", "")

    # ---- retrieval ------------------------------------------------------

    def test_retrieve_returns_top_k(self):
        self.svc.ingest_article(
            "Reset password",
            "Click Forgot Password to reset your password.",
            tags=["login"],
        )
        self.svc.ingest_article(
            "Refunds",
            "Refunds within 30 days, no questions asked.",
            tags=["refund"],
        )
        scored = self.svc.retrieve("I forgot my password")
        self.assertGreaterEqual(len(scored), 1)
        # First hit should be the password article.
        self.assertIn("password", scored[0][0].title.lower())

    def test_retrieve_empty_query(self):
        self.svc.ingest_article("A", "Article body", tags=["x"])
        self.assertEqual(self.svc.retrieve(""), [])

    # ---- tickets --------------------------------------------------------

    def test_open_ticket_persists(self):
        t = self.svc.open_ticket("u1", "Login broken", "I can't log in")
        again = self.svc.get_ticket(t.ticket_id)
        self.assertIsNotNone(again)
        self.assertEqual(again.user_id, "u1")
        self.assertEqual(again.status, "open")
        self.assertEqual(again.messages[-1].role, "user")

    def test_open_ticket_validation(self):
        with self.assertRaises(ValueError):
            self.svc.open_ticket("", "x", "y")
        with self.assertRaises(ValueError):
            self.svc.open_ticket("u1", "", "y")
        with self.assertRaises(ValueError):
            self.svc.open_ticket("u1", "x", "")

    # ---- auto-reply -----------------------------------------------------

    def test_auto_reply_uses_citations(self):
        self.svc.ingest_article(
            "Reset password",
            "Click Forgot Password on the login page to reset.",
            tags=["login"],
        )
        t = self.svc.open_ticket(
            "u1",
            "Can't log in",
            "I forgot my password and the reset email never arrived.",
        )
        reply = self.svc.auto_reply(t.ticket_id)
        self.assertIsNotNone(reply)
        self.assertEqual(reply.role, "assistant")
        self.assertGreater(len(reply.citations), 0)
        # The ticket transitions to auto_replied and tracks citation count.
        again = self.svc.get_ticket(t.ticket_id)
        self.assertEqual(again.status, "auto_replied")
        self.assertEqual(again.citation_count, len(reply.citations))

    def test_auto_reply_no_citations_uses_default(self):
        t = self.svc.open_ticket("u1", "Anything", "Random gibberish xyzzy")
        reply = self.svc.auto_reply(t.ticket_id)
        self.assertIsNotNone(reply)
        # No articles match → no citations, but we still produce a reply.
        self.assertEqual(reply.citations, [])
        self.assertIn("References", reply.content)  # empty references block is fine
        # The mock falls back to "general" tag.
        self.assertIn("knowledge base", reply.content.lower())

    def test_agent_and_user_replies(self):
        t = self.svc.open_ticket("u1", "Help", "I need help")
        self.svc.agent_reply(t.ticket_id, "We're looking into it.")
        self.svc.user_reply(t.ticket_id, "Thanks!")
        again = self.svc.get_ticket(t.ticket_id)
        roles = [m.role for m in again.messages]
        self.assertEqual(roles, ["user", "agent", "user"])
        # After the user's reply, status flips back to "open".
        self.assertEqual(again.status, "open")

    def test_auto_reply_on_missing_ticket(self):
        self.assertIsNone(self.svc.auto_reply(999))

    def test_stats(self):
        self.svc.ingest_article("a", "b")
        self.svc.open_ticket("u", "s", "x")
        s = self.svc.stats()
        self.assertEqual(s["articles"], 1)
        self.assertEqual(s["tickets"], 1)


if __name__ == "__main__":
    unittest.main()
