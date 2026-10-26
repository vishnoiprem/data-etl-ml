"""Tests for the Instagram service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import InstagramService  # noqa: E402


class InstagramServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = InstagramService()

    def test_full_flow(self):
        self.svc.create_user(1, "u1", "User 1")
        self.svc.create_user(2, "u2", "User 2")
        self.svc.follow(1, 2)
        p = self.svc.upload(2, "hi")
        feed = self.svc.feed(1, limit=5)
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0].photo_id, p.photo_id)

    def test_follow_update_counts(self):
        self.svc.create_user(1, "u1", "User 1")
        self.svc.create_user(2, "u2", "User 2")
        self.svc.follow(1, 2)
        u1 = self.svc.get_user(1)
        u2 = self.svc.get_user(2)
        self.assertEqual(u1.following_count, 1)
        self.assertEqual(u2.followers_count, 1)
        self.svc.unfollow(1, 2)
        u1 = self.svc.get_user(1)
        u2 = self.svc.get_user(2)
        self.assertEqual(u1.following_count, 0)
        self.assertEqual(u2.followers_count, 0)

    def test_followers(self):
        self.svc.create_user(1, "u1", "1")
        self.svc.create_user(2, "u2", "2")
        self.svc.create_user(3, "u3", "3")
        self.svc.follow(2, 1)
        self.svc.follow(3, 1)
        self.assertEqual(set(self.svc.followers_of(1)), {2, 3})

    def test_no_follow_self(self):
        with self.assertRaises(ValueError):
            self.svc.follow(1, 1)

    def test_like(self):
        self.svc.create_user(1, "u1", "1")
        p = self.svc.upload(1, "hi")
        self.svc.like(p.photo_id)
        self.svc.like(p.photo_id)
        self.assertEqual(self.svc.get_photo(p.photo_id).likes, 2)

    def test_feed_time_order(self):
        self.svc.create_user(1, "u1", "1")
        self.svc.create_user(2, "u2", "2")
        self.svc.follow(1, 2)
        p1 = self.svc.upload(2, "first")
        p2 = self.svc.upload(2, "second")
        feed = self.svc.feed(1, limit=10)
        # Newer first
        self.assertEqual(feed[0].photo_id, p2.photo_id)
        self.assertEqual(feed[1].photo_id, p1.photo_id)


if __name__ == "__main__":
    unittest.main()
