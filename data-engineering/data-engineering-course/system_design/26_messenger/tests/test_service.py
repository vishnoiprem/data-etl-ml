"""Tests for the Messenger service."""

from __future__ import annotations

import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import MessengerService  # noqa: E402


class MessengerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = MessengerService()

    def test_create_conversation_idempotent(self):
        c1 = self.svc.create_conversation(1, 2)
        c2 = self.svc.create_conversation(2, 1)  # same pair
        self.assertEqual(c1.conversation_id, c2.conversation_id)

    def test_no_self_conversation(self):
        with self.assertRaises(ValueError):
            self.svc.create_conversation(1, 1)

    def test_send_and_fetch(self):
        cid = self.svc.create_conversation(1, 2).conversation_id
        m = self.svc.send_message(cid, sender_id=1, body="hello")
        msgs = self.svc.fetch_messages(cid)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].message_id, m.message_id)
        self.assertEqual(msgs[0].body, "hello")

    def test_inbox_fanout_both_participants(self):
        cid = self.svc.create_conversation(1, 2).conversation_id
        self.svc.send_message(cid, sender_id=1, body="ping")
        self.assertEqual(len(self.svc.fetch_inbox(1)), 1)
        self.assertEqual(len(self.svc.fetch_inbox(2)), 1)

    def test_non_participant_cannot_send(self):
        cid = self.svc.create_conversation(1, 2).conversation_id
        with self.assertRaises(ValueError):
            self.svc.send_message(cid, sender_id=99, body="x")

    def test_presence_online_offline(self):
        self.assertFalse(self.svc.is_online(7))
        self.svc.heartbeat(7)
        self.assertTrue(self.svc.is_online(7))
        self.assertIsNotNone(self.svc.last_seen(7))

    def test_fetch_since_ts(self):
        cid = self.svc.create_conversation(1, 2).conversation_id
        self.svc.send_message(cid, 1, "first")
        time.sleep(0.01)
        cutoff = time.time()
        time.sleep(0.01)
        self.svc.send_message(cid, 1, "second")
        older = self.svc.fetch_messages(cid, since_ts=0)
        recent = self.svc.fetch_messages(cid, since_ts=cutoff)
        self.assertEqual(len(older), 2)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].body, "second")

    def test_listener_receives_new_message(self):
        cid = self.svc.create_conversation(1, 2).conversation_id
        q = self.svc.register_listener(2)
        m = self.svc.send_message(cid, sender_id=1, body="live!")
        evt = q.get(timeout=2)
        self.assertEqual(evt["message_id"], m.message_id)
        self.svc.unregister_listener(2, q)


if __name__ == "__main__":
    unittest.main()
