"""Tests for the Twitter / X service.

See ``design/README.md`` for the system architecture these tests exercise.
We hit the service layer directly (no HTTP).
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import TwitterService, CELEB_THRESHOLD  # noqa: E402


class TwitterServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        # A fresh in-memory service per test.
        self.svc = TwitterService()

    # --- 1. end-to-end: post -> follower's timeline ---------------------
    def test_e2e_post_and_read_timeline(self):
        """Design §6: a normal-author tweet reaches the follower's
        timeline via fanout-on-write."""
        self.svc.create_user(1, "u1", "User 1")
        self.svc.create_user(2, "u2", "User 2")
        self.svc.follow(1, 2)
        t = self.svc.post_tweet(2, "hello world")
        feed = self.svc.timeline(1, limit=10)
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0].tweet_id, t.tweet_id)
        self.assertEqual(feed[0].text, "hello world")

    # --- 2. follow / unfollow update counts ------------------------------
    def test_follow_updates_counts(self):
        """Design §4/§5: follow edges maintain live follower / following
        counts on both ends."""
        self.svc.create_user(10, "a", "A")
        self.svc.create_user(20, "b", "B")
        self.svc.follow(10, 20)
        a, b = self.svc.get_user(10), self.svc.get_user(20)
        self.assertEqual(a.following_count, 1)
        self.assertEqual(b.followers_count, 1)
        self.svc.unfollow(10, 20)
        a, b = self.svc.get_user(10), self.svc.get_user(20)
        self.assertEqual(a.following_count, 0)
        self.assertEqual(b.followers_count, 0)

    # --- 3. fanout reaches followers ------------------------------------
    def test_fanout_reaches_followers(self):
        """Design §8: a normal-author tweet is pushed into every
        follower's materialised feed list."""
        self.svc.create_user(1, "u1", "U1")
        for uid in (2, 3, 4, 5):
            self.svc.create_user(uid, f"u{uid}", f"U{uid}")
            self.svc.follow(uid, 1)  # 2,3,4,5 follow user 1
        t = self.svc.post_tweet(1, "broadcast")
        for uid in (2, 3, 4, 5):
            feed = self.svc.timeline(uid, limit=10)
            ids = [x.tweet_id for x in feed]
            self.assertIn(t.tweet_id, ids)

    # --- 4. celebrity hybrid: do NOT fanout, pull at read ----------------
    def test_celebrity_uses_hybrid_pull(self):
        """Design §7b / §8: a user above CELEB_THRESHOLD followers is
        treated as a celebrity — their tweet is NOT fanned out into any
        feed list, but DOES appear in followers' timelines via the
        celeb bucket (pull-on-read)."""
        celeb = 100
        self.svc.create_user(celeb, "celeb", "Celeb")
        # Bump the celeb's followers_count up to the threshold so the
        # service classifies them as a celeb on the next post.
        u = self.svc.get_user(celeb)
        u.followers_count = CELEB_THRESHOLD + 5
        self.svc.users.set(f"user:{celeb}", u.to_dict())

        # Followers who never had anything pushed to them.
        for uid in (201, 202, 203):
            self.svc.create_user(uid, f"f{uid}", f"F{uid}")
            self.svc.follow(uid, celeb)

        t = self.svc.post_tweet(celeb, "from the celeb")

        # The celeb's tweet must NOT be in any follower's materialised
        # feed list — that's the whole point of the celeb threshold.
        for uid in (201, 202, 203):
            feed_list = self.svc.feeds.get(f"feed:{uid}") or []
            self.assertNotIn(t.tweet_id, feed_list)

        # But it MUST appear in each follower's assembled timeline
        # because the read path pulls from the celeb bucket.
        for uid in (201, 202, 203):
            tl = self.svc.timeline(uid, limit=10)
            ids = [x.tweet_id for x in tl]
            self.assertIn(t.tweet_id, ids)

        # And it should be in the celeb's bucket.
        bucket = self.svc.celeb_buckets.get(f"celeb:{celeb}") or []
        self.assertIn(t.tweet_id, bucket)

    # --- 5. retweet is first-class and reaches followers ----------------
    def test_retweet_works_and_carries_lineage(self):
        """Design §7a: a retweet is a real tweet with retweet_of /
        retweet_of_user set, and fans out to followers like any tweet."""
        self.svc.create_user(1, "u1", "U1")
        self.svc.create_user(2, "u2", "U2")
        self.svc.create_user(3, "u3", "U3")
        # 1 follows 2; 3 follows 1.
        self.svc.follow(1, 2)
        self.svc.follow(3, 1)

        original = self.svc.post_tweet(2, "the original")
        rt = self.svc.post_tweet(1, "RT @u2 the original", retweet_of=original.tweet_id)

        # Lineage is set.
        self.assertEqual(rt.retweet_of, original.tweet_id)
        self.assertEqual(rt.retweet_of_user, original.user_id)
        # Original's retweet counter was bumped.
        self.assertEqual(self.svc.get_tweet(original.tweet_id).retweets, 1)
        # The RT reached user 3 (follows 1).
        tl3 = [x.tweet_id for x in self.svc.timeline(3, limit=10)]
        self.assertIn(rt.tweet_id, tl3)
        # The RT is NOT in the original author's timeline (2 doesn't follow 1).
        tl2 = [x.tweet_id for x in self.svc.timeline(2, limit=10)]
        self.assertNotIn(rt.tweet_id, tl2)

    # --- 6. timeline is reverse-chronological across merge --------------
    def test_timeline_reverse_chronological_with_celeb_merge(self):
        """Design §6: pushed and pulled entries are merged and ranked
        newest-first. We mix a fanned-out author and a celebrity, and
        verify ordering across both."""
        normal = 1
        celeb = 2
        viewer = 9
        for uid in (normal, celeb, viewer):
            self.svc.create_user(uid, f"u{uid}", f"U{uid}")
        # Make user 2 a celebrity.
        u2 = self.svc.get_user(celeb)
        u2.followers_count = CELEB_THRESHOLD + 1
        self.svc.users.set(f"user:{celeb}", u2.to_dict())
        # viewer follows both.
        self.svc.follow(viewer, normal)
        self.svc.follow(viewer, celeb)

        # Three posts from the normal author (pushed), then one from the
        # celeb (pulled). Posts are time-ordered, so the celeb tweet
        # should be newest.
        a = self.svc.post_tweet(normal, "a")
        b = self.svc.post_tweet(normal, "b")
        c = self.svc.post_tweet(normal, "c")
        d = self.svc.post_tweet(celeb, "d from celeb")

        tl = self.svc.timeline(viewer, limit=10)
        ids = [t.tweet_id for t in tl]
        # Newest first: d, c, b, a.
        self.assertEqual(ids, [d.tweet_id, c.tweet_id, b.tweet_id, a.tweet_id])

    # --- bonus: cannot follow self --------------------------------------
    def test_cannot_follow_self(self):
        with self.assertRaises(ValueError):
            self.svc.follow(1, 1)

    # --- bonus: like -----------------------------------------------------
    def test_like_increments(self):
        self.svc.create_user(1, "u1", "U1")
        t = self.svc.post_tweet(1, "like me")
        self.assertEqual(self.svc.like_tweet(t.tweet_id), 1)
        self.assertEqual(self.svc.like_tweet(t.tweet_id), 2)
        self.assertEqual(self.svc.get_tweet(t.tweet_id).likes, 2)


if __name__ == "__main__":
    unittest.main()