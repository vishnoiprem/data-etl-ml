"""Tests for the Reddit service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import RedditService, hot_score  # noqa: E402


class RedditServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = RedditService()
        self.svc.create_user(1, "alice")
        self.svc.create_user(2, "bob")
        self.sub = self.svc.create_subreddit("python", "lang")

    def test_full_flow(self):
        self.svc.subscribe(1, self.sub.subreddit_id)
        p1 = self.svc.create_post(2, self.sub.subreddit_id, "title1")
        p2 = self.svc.create_post(2, self.sub.subreddit_id, "title2")
        self.svc.vote(p1.post_id, 1, 1)
        self.svc.vote(p2.post_id, 1, 1)
        top = self.svc.subreddit_top(self.sub.subreddit_id, limit=5)
        self.assertEqual(len(top), 2)

    def test_hot_score_ordering(self):
        # More recent and more votes should rank higher
        a = self.svc.create_post(1, self.sub.subreddit_id, "a")
        b = self.svc.create_post(1, self.sub.subreddit_id, "b")
        self.svc.vote(a.post_id, 1, 1)
        self.svc.vote(a.post_id, 2, 1)
        self.svc.vote(b.post_id, 1, 1)
        top = self.svc.subreddit_top(self.sub.subreddit_id)
        # 'a' has more upvotes and is older-or-equal; either way a wins
        self.assertEqual(top[0]["post_id"], a.post_id)

    def test_vote_retract(self):
        p = self.svc.create_post(1, self.sub.subreddit_id, "x")
        self.svc.vote(p.post_id, 1, 1)
        self.svc.vote(p.post_id, 1, 0)
        post = self.svc.get_post(p.post_id)
        self.assertEqual(post.upvotes, 0)

    def test_vote_change(self):
        p = self.svc.create_post(1, self.sub.subreddit_id, "x")
        self.svc.vote(p.post_id, 1, 1)
        self.svc.vote(p.post_id, 1, -1)
        post = self.svc.get_post(p.post_id)
        self.assertEqual(post.upvotes, 0)
        self.assertEqual(post.downvotes, 1)

    def test_home_feed(self):
        s2 = self.svc.create_subreddit("django", "web")
        self.svc.subscribe(1, self.sub.subreddit_id)
        self.svc.subscribe(1, s2.subreddit_id)
        self.svc.create_post(2, self.sub.subreddit_id, "py1")
        self.svc.create_post(2, s2.subreddit_id, "dj1")
        feed = self.svc.home(1, limit=10)
        self.assertEqual(len(feed), 2)

    def test_hot_score_function(self):
        s1 = hot_score(10, 0, 1_700_000_000)
        s2 = hot_score(100, 0, 1_700_000_000)
        self.assertGreater(s2, s1)
        s3 = hot_score(10, 0, 1_700_010_000)
        self.assertGreater(s3, s1)


if __name__ == "__main__":
    unittest.main()
