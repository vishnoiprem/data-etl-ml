"""Tests for the Slack service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import SlackService  # noqa: E402


class SlackServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = SlackService()

    def test_workspace_and_channel(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        self.assertEqual(ch.workspace_id, w.workspace_id)
        self.assertEqual([c.name for c in self.svc.channels_in(w.workspace_id)], ["general"])

    def test_post_and_fetch(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        m = self.svc.post_message(ch.channel_id, user_id=1, body="hello world")
        msgs = self.svc.fetch_messages(ch.channel_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].body, "hello world")
        self.assertEqual(msgs[0].message_id, m.message_id)

    def test_mention_parsing(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        m = self.svc.post_message(ch.channel_id, 1, "ping @42 and @7")
        self.assertIn(42, m.mentions)
        self.assertIn(7, m.mentions)
        # Inbox of 42 should have the message.
        inbox = self.svc.fetch_mentions(42)
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].message_id, m.message_id)

    def test_thread_basic(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        m = self.svc.post_message(ch.channel_id, 1, "parent")
        r1 = self.svc.post_message(ch.channel_id, 2, "reply 1", thread_to=m.message_id)
        r2 = self.svc.post_message(ch.channel_id, 3, "reply 2", thread_to=m.message_id)
        thread = self.svc.fetch_thread(m.message_id)
        self.assertEqual(len(thread), 2)
        self.assertEqual([r.message_id for r in thread], [r1.message_id, r2.message_id])

    def test_thread_validation(self):
        w = self.svc.create_workspace("acme")
        ch1 = self.svc.create_channel(w.workspace_id, "a", creator_id=1)
        ch2 = self.svc.create_channel(w.workspace_id, "b", creator_id=1)
        m = self.svc.post_message(ch1.channel_id, 1, "in a")
        with self.assertRaises(ValueError):
            # parent in a different channel
            self.svc.post_message(ch2.channel_id, 1, "x", thread_to=m.message_id)
        r = self.svc.post_message(ch1.channel_id, 1, "r1", thread_to=m.message_id)
        with self.assertRaises(ValueError):
            # can't reply to a reply
            self.svc.post_message(ch1.channel_id, 1, "r2", thread_to=r.message_id)

    def test_search(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        self.svc.post_message(ch.channel_id, 1, "deploy pipeline failed")
        self.svc.post_message(ch.channel_id, 1, "lunch plans")
        self.svc.post_message(ch.channel_id, 1, "pipeline restarted successfully")
        results = self.svc.search("pipeline")
        self.assertEqual(len(results), 2)
        bodies = sorted(m.body for m in results)
        self.assertEqual(bodies, [
            "deploy pipeline failed",
            "pipeline restarted successfully",
        ])

    def test_search_recency_order(self):
        w = self.svc.create_workspace("acme")
        ch = self.svc.create_channel(w.workspace_id, "general", creator_id=1)
        import time
        m1 = self.svc.post_message(ch.channel_id, 1, "alpha beat")
        time.sleep(0.01)
        m2 = self.svc.post_message(ch.channel_id, 1, "alpha second")
        results = self.svc.search("alpha")
        self.assertEqual(results[0].message_id, m2.message_id)
        self.assertEqual(results[1].message_id, m1.message_id)


if __name__ == "__main__":
    unittest.main()
