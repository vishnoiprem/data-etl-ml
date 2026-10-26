"""Tests for the WhatsApp service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import WhatsAppService  # noqa: E402


class WhatsAppServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = WhatsAppService()

    def test_create_group_basic(self):
        g = self.svc.create_group("family", creator_id=1, members=[1, 2, 3])
        self.assertEqual(g.name, "family")
        self.assertIn(1, g.members)
        self.assertIn(2, g.members)
        self.assertIn(3, g.members)
        self.assertEqual(g.key_version, 1)

    def test_creator_added_if_missing(self):
        g = self.svc.create_group("g", creator_id=5, members=[1, 2])
        self.assertIn(5, g.members)

    def test_add_remove_member_rotates_key(self):
        g = self.svc.create_group("g", creator_id=1, members=[1, 2])
        old_key = g.key_id
        g2 = self.svc.add_member(g.group_id, 3)
        self.assertIn(3, g2.members)
        self.assertNotEqual(g2.key_id, old_key)
        self.assertEqual(g2.key_version, 2)
        g3 = self.svc.remove_member(g.group_id, 2)
        self.assertNotIn(2, g3.members)
        self.assertEqual(g3.key_version, 3)

    def test_send_and_fetch(self):
        g = self.svc.create_group("g", creator_id=1, members=[1, 2])
        m = self.svc.send_message(g.group_id, sender_id=1, body="hi all")
        msgs = self.svc.fetch_messages(g.group_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].body, "hi all")
        self.assertEqual(msgs[0].key_id, g.key_id)

    def test_non_member_cannot_send(self):
        g = self.svc.create_group("g", creator_id=1, members=[1, 2])
        with self.assertRaises(ValueError):
            self.svc.send_message(g.group_id, sender_id=99, body="nope")

    def test_inbox_fanout(self):
        g = self.svc.create_group("g", creator_id=1, members=[1, 2, 3])
        self.svc.send_message(g.group_id, 1, "hi")
        self.assertEqual(len(self.svc.fetch_inbox(1)), 1)
        self.assertEqual(len(self.svc.fetch_inbox(2)), 1)
        self.assertEqual(len(self.svc.fetch_inbox(3)), 1)

    def test_media_message(self):
        g = self.svc.create_group("g", creator_id=1, members=[1])
        m = self.svc.send_message(
            g.group_id, 1, body="", media_url="https://cdn/x.jpg"
        )
        self.assertEqual(m.media_url, "https://cdn/x.jpg")
        # body can be empty when media is present.
        msgs = self.svc.fetch_messages(g.group_id)
        self.assertEqual(len(msgs), 1)

    def test_groups_for_user(self):
        self.svc.create_group("a", 1, [1, 2])
        self.svc.create_group("b", 2, [2, 3])
        self.svc.create_group("c", 3, [3, 4])
        names = sorted(g.name for g in self.svc.groups_for(2))
        self.assertEqual(names, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
