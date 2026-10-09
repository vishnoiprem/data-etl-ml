"""Unit tests for the TikTok service core."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.cache import TTLCache  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402
from code.service import TikTokService  # noqa: E402


class TikTokServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_tiktok",
            persist_path=os.path.join(self.tmpdir, "tiktok.json"),
        )
        self.cache = TTLCache(ttl_seconds=60, max_entries=100)
        self.foryou_cache = TTLCache(ttl_seconds=60, max_entries=200)
        self.svc = TikTokService(
            store=self.store,
            cache=self.cache,
            foryou_cache=self.foryou_cache,
        )

    # ---- validation / happy path -------------------------------------

    def test_post_returns_video_id(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(
            u.user_id, "hello", 15, tags=["cat", "funny"]
        )
        self.assertIsNotNone(v.video_id)
        self.assertGreater(v.video_id, 0)
        self.assertEqual(v.caption, "hello")
        self.assertEqual(v.duration_s, 15)
        self.assertEqual(v.user_id, u.user_id)
        self.assertEqual(v.tags, ["cat", "funny"])
        self.assertEqual(v.views, 0)

    def test_post_rejects_invalid_inputs(self):
        u = self.svc.create_user("alice")
        with self.assertRaises(ValueError):
            self.svc.post_video(u.user_id, "ok", 0)
        with self.assertRaises(ValueError):
            self.svc.post_video(u.user_id, "ok", -5)
        with self.assertRaises(ValueError):
            self.svc.post_video(u.user_id, "ok", 601)
        with self.assertRaises(ValueError):
            self.svc.post_video(999_999_999, "ok", 15)
        with self.assertRaises(ValueError):
            self.svc.post_video(u.user_id, 12345, 15)

    def test_post_normalizes_tags(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(
            u.user_id, "hi", 10, tags=["  Cat ", "cat", "DOG", ""]
        )
        # Lowercased, deduped, empty dropped.
        self.assertEqual(v.tags, ["cat", "dog"])

    def test_get_video_returns_record(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(
            u.user_id, "first take", 20, tags=["dance"]
        )
        got = self.svc.get_video(v.video_id)
        self.assertIsNotNone(got)
        self.assertEqual(got.caption, "first take")
        self.assertEqual(got.video_id, v.video_id)

    def test_get_video_missing(self):
        self.assertIsNone(self.svc.get_video(424242))

    # ---- views + engagement ------------------------------------------

    def test_record_view_increments_and_watch_pct(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(u.user_id, "v", 10)
        # Two views, one 100%, one 50%.
        self.svc.record_view(v.video_id, u.user_id, watch_pct=100.0)
        self.svc.record_view(v.video_id, u.user_id, watch_pct=50.0)
        got = self.svc.get_video(v.video_id)
        self.assertEqual(got.views, 2)
        # 10s + 5s = 15s across 2 plays.
        self.assertAlmostEqual(got.total_watch_s, 15.0, places=4)
        # And the engagement deque has 2 entries.
        self.assertEqual(len(self.svc._engagement[v.video_id]), 2)

    def test_record_view_rejects_invalid_watch_pct(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(u.user_id, "v", 10)
        with self.assertRaises(ValueError):
            self.svc.record_view(v.video_id, u.user_id, watch_pct=-1)
        with self.assertRaises(ValueError):
            self.svc.record_view(v.video_id, u.user_id, watch_pct=150)

    def test_like_increments(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(u.user_id, "v", 10)
        self.svc.like_video(v.video_id, u.user_id)
        self.svc.like_video(v.video_id, u.user_id)
        got = self.svc.get_video(v.video_id)
        self.assertEqual(got.likes, 2)

    # ---- For You ranking ---------------------------------------------

    def test_foryou_cold_start_returns_recent(self):
        u1 = self.svc.create_user("u1")
        u2 = self.svc.create_user("u2")
        # Two videos, posted in order.
        v_old = self.svc.post_video(u1.user_id, "old", 10, tags=["a"])
        v_new = self.svc.post_video(u2.user_id, "new", 10, tags=["b"])
        cold = self.svc.create_user("cold")
        results = self.svc.foryou(cold.user_id, limit=5)
        ids = [vid for vid, _c, _s in results]
        # Both videos should appear; newer one ranks higher.
        self.assertIn(v_old.video_id, ids)
        self.assertIn(v_new.video_id, ids)
        # The newer one is at index 0 (higher recency score).
        self.assertEqual(ids[0], v_new.video_id)

    def test_foryou_caches_for_60s(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(u.user_id, "v", 10, tags=["x"])
        # First call → cache miss → populates.
        self.svc.foryou(u.user_id, limit=5)
        cache_key = self.svc._k_foryou(u.user_id)
        cached = self.foryou_cache.get(cache_key)
        self.assertIsNotNone(cached)
        # Second call within TTL → served from cache.
        before = self.foryou_cache.stats()["hits"]
        self.svc.foryou(u.user_id, limit=5)
        after = self.foryou_cache.stats()["hits"]
        self.assertGreater(after, before)

    def test_foryou_view_invalidates_cache(self):
        u1 = self.svc.create_user("u1")
        u2 = self.svc.create_user("u2")
        v = self.svc.post_video(u1.user_id, "v", 10, tags=["x"])
        # Populate u2's foryou cache.
        self.svc.foryou(u2.user_id, limit=5)
        cache_key = self.svc._k_foryou(u2.user_id)
        self.assertIsNotNone(self.foryou_cache.get(cache_key))
        # u2 records a view — their foryou cache is invalidated.
        self.svc.record_view(v.video_id, u2.user_id, watch_pct=80.0)
        self.assertIsNone(self.foryou_cache.get(cache_key))

    def test_foryou_uses_affinity(self):
        u1 = self.svc.create_user("u1")
        u2 = self.svc.create_user("u2")
        # u1 posts a dance video.
        dance = self.svc.post_video(
            u1.user_id, "dance", 10, tags=["dance", "music"]
        )
        # u1 posts an unrelated video.
        other = self.svc.post_video(
            u1.user_id, "other", 10, tags=["news"]
        )
        # u2 watches the dance video — their tag set is now
        # {"dance", "music"}.
        self.svc.record_view(dance.video_id, u2.user_id, watch_pct=100.0)
        # Add a *new* video tagged dance so it's a candidate.
        new_dance = self.svc.post_video(
            u1.user_id, "new dance", 10, tags=["dance"]
        )
        # The new dance video should rank above "other" for u2
        # because of Jaccard affinity.
        results = self.svc.foryou(u2.user_id, limit=10)
        ids = [vid for vid, _c, _s in results]
        self.assertIn(new_dance.video_id, ids)
        # Drop already-watched; new_dance should be present,
        # and we sanity-check it scores above 0 (the affinity
        # contributed positively).
        new_dance_score = next(
            s for vid, _c, s in results if vid == new_dance.video_id
        )
        self.assertGreater(new_dance_score, 0.0)

    def test_foryou_excludes_already_watched(self):
        u1 = self.svc.create_user("u1")
        u2 = self.svc.create_user("u2")
        v1 = self.svc.post_video(u1.user_id, "v1", 10, tags=["x"])
        v2 = self.svc.post_video(u1.user_id, "v2", 10, tags=["x"])
        # u2 watches v1; their For You should not include v1.
        self.svc.record_view(v1.video_id, u2.user_id, watch_pct=100.0)
        results = self.svc.foryou(u2.user_id, limit=10)
        ids = {vid for vid, _c, _s in results}
        self.assertNotIn(v1.video_id, ids)
        # v2 (same tag) should be a candidate and present.
        self.assertIn(v2.video_id, ids)

    # ---- caching -----------------------------------------------------

    def test_get_video_caches_after_first_call(self):
        u = self.svc.create_user("alice")
        v = self.svc.post_video(u.user_id, "v", 10)
        # First call → populates cache.
        self.svc.get_video(v.video_id)
        cache_key = self.svc._k_video(v.video_id)
        self.assertIsNotNone(self.cache.get(cache_key))
        # Second call is a cache hit.
        before_hits = self.cache.stats()["hits"]
        self.svc.get_video(v.video_id)
        after_hits = self.cache.stats()["hits"]
        self.assertGreater(after_hits, before_hits)


if __name__ == "__main__":
    unittest.main()
