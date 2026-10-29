"""Unit tests for the video service core."""

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
from code.service import VideoService  # noqa: E402


class VideoServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_vs",
            persist_path=os.path.join(self.tmpdir, "vs.json"),
        )
        self.cache = TTLCache(ttl_seconds=60, max_entries=100)
        self.svc = VideoService(
            store=self.store, cache=self.cache, window_seconds=60
        )

    # ---- validation / happy path -------------------------------------

    def test_upload_returns_video_id(self):
        u = self.svc.create_user("alice")
        v = self.svc.upload_video(u.user_id, "lesson 1", 600)
        self.assertIsNotNone(v.video_id)
        self.assertGreater(v.video_id, 0)
        self.assertEqual(v.title, "lesson 1")
        self.assertEqual(v.duration_s, 600)
        self.assertEqual(v.user_id, u.user_id)
        self.assertEqual(v.views, 0)

    def test_upload_rejects_invalid_inputs(self):
        u = self.svc.create_user("alice")
        with self.assertRaises(ValueError):
            self.svc.upload_video(u.user_id, "", 100)
        with self.assertRaises(ValueError):
            self.svc.upload_video(u.user_id, "ok", 0)
        with self.assertRaises(ValueError):
            self.svc.upload_video(u.user_id, "ok", -5)
        with self.assertRaises(ValueError):
            self.svc.upload_video(999_999_999, "ok", 100)

    def test_get_video_returns_record(self):
        u = self.svc.create_user("alice")
        v = self.svc.upload_video(u.user_id, "lesson x", 100)
        got = self.svc.get_video(v.video_id)
        self.assertIsNotNone(got)
        self.assertEqual(got.title, "lesson x")
        self.assertEqual(got.video_id, v.video_id)

    def test_get_video_missing(self):
        self.assertIsNone(self.svc.get_video(424242))

    # ---- views + trending -------------------------------------------

    def test_record_view_increments(self):
        u = self.svc.create_user("alice")
        v = self.svc.upload_video(u.user_id, "v", 100)
        for _ in range(3):
            self.svc.record_view(v.video_id, u.user_id)
        got = self.svc.get_video(v.video_id)
        self.assertEqual(got.views, 3)
        # The in-memory deque is also tracking 3 recent views.
        self.assertEqual(len(self.svc._recent_views[v.video_id]), 3)

    def test_trending_orders_by_recent_views(self):
        u = self.svc.create_user("alice")
        v_hot = self.svc.upload_video(u.user_id, "hot", 100)
        v_mid = self.svc.upload_video(u.user_id, "mid", 100)
        v_cold = self.svc.upload_video(u.user_id, "cold", 100)
        # Inject views at controlled times.
        now = time.time()
        self.svc._recent_views[v_hot.video_id].extend([now] * 10)
        self.svc._recent_views[v_mid.video_id].extend([now] * 4)
        self.svc._recent_views[v_cold.video_id].extend([now] * 1)
        top = self.svc.trending(limit=5)
        ids = [vid for vid, _n, _t in top]
        self.assertEqual(ids[0], v_hot.video_id)
        self.assertEqual(ids[1], v_mid.video_id)
        # And counts come back too.
        counts = {vid: n for vid, n, _ in top}
        self.assertEqual(counts[v_hot.video_id], 10)
        self.assertEqual(counts[v_mid.video_id], 4)

    def test_trending_drops_old_views(self):
        u = self.svc.create_user("alice")
        v = self.svc.upload_video(u.user_id, "v", 100)
        # Pretend a view happened 5 minutes ago — outside the 60s window.
        self.svc._recent_views[v.video_id].append(time.time() - 300)
        # And one recent view.
        self.svc.record_view(v.video_id, u.user_id)
        top = self.svc.trending(limit=5)
        # Only the recent view counts.
        self.assertEqual(len(self.svc._recent_views[v.video_id]), 1)

    # ---- recommendation ---------------------------------------------

    def test_recommend_returns_popular_videos_for_cold_user(self):
        u = self.svc.create_user("alice")
        v1 = self.svc.upload_video(u.user_id, "popular", 100)
        v2 = self.svc.upload_video(u.user_id, "less popular", 100)
        # Several users watch v1 and v2.
        for i in range(5):
            ui = self.svc.create_user(f"user_{i}")
            self.svc.record_view(v1.video_id, ui.user_id)
        for i in range(2):
            ui = self.svc.create_user(f"luser_{i}")
            self.svc.record_view(v2.video_id, ui.user_id)
        # Cold user — no history.
        cold = self.svc.create_user("cold")
        recs = self.svc.recommend(cold.user_id, limit=5)
        ids = [vid for vid, _t, _s in recs]
        # Most popular should be first.
        self.assertEqual(ids[0], v1.video_id)

    def test_recommend_uses_co_watch(self):
        alice = self.svc.create_user("alice")
        bob = self.svc.create_user("bob")
        carol = self.svc.create_user("carol")
        v_a = self.svc.upload_video(alice.user_id, "A", 100)
        v_b = self.svc.upload_video(alice.user_id, "B", 100)
        v_c = self.svc.upload_video(alice.user_id, "C", 100)
        # Alice watches A. Bob watches A and C. Carol watches A and B.
        # → for Alice, we expect B and C (both co-watched by similar users).
        self.svc.record_view(v_a.video_id, alice.user_id)
        self.svc.record_view(v_a.video_id, bob.user_id)
        self.svc.record_view(v_c.video_id, bob.user_id)
        self.svc.record_view(v_a.video_id, carol.user_id)
        self.svc.record_view(v_b.video_id, carol.user_id)
        recs = self.svc.recommend(alice.user_id, limit=5)
        ids = {vid for vid, _t, _s in recs}
        # A is in alice's history — must not be recommended.
        self.assertNotIn(v_a.video_id, ids)
        # B and C are the co-watched candidates — at least one must show.
        self.assertTrue({v_b.video_id, v_c.video_id} & ids)

    def test_recommend_excludes_already_watched(self):
        alice = self.svc.create_user("alice")
        v1 = self.svc.upload_video(alice.user_id, "v1", 100)
        v2 = self.svc.upload_video(alice.user_id, "v2", 100)
        bob = self.svc.create_user("bob")
        # Alice watches v1, bob also watches v1 and v2.
        self.svc.record_view(v1.video_id, alice.user_id)
        self.svc.record_view(v1.video_id, bob.user_id)
        self.svc.record_view(v2.video_id, bob.user_id)
        recs = self.svc.recommend(alice.user_id, limit=5)
        ids = [vid for vid, _t, _s in recs]
        self.assertNotIn(v1.video_id, ids)
        # v2 should be the top candidate.
        self.assertIn(v2.video_id, ids)

    # ---- caching -----------------------------------------------------

    def test_get_video_caches_after_first_call(self):
        u = self.svc.create_user("alice")
        v = self.svc.upload_video(u.user_id, "cached", 100)
        # First call → populates cache.
        self.svc.get_video(v.video_id)
        cache_key = f"video:{v.video_id}"
        self.assertIsNotNone(self.cache.get(cache_key))
        # Second call should be a cache hit.
        before_hits = self.cache.stats()["hits"]
        self.svc.get_video(v.video_id)
        after_hits = self.cache.stats()["hits"]
        self.assertGreater(after_hits, before_hits)

    def test_multiple_users_share_recommendations(self):
        alice = self.svc.create_user("alice")
        bob = self.svc.create_user("bob")
        carol = self.svc.create_user("carol")
        v1 = self.svc.upload_video(alice.user_id, "v1", 100)
        v2 = self.svc.upload_video(alice.user_id, "v2", 100)
        # All three watch v1, then bob and carol also watch v2.
        for u in (alice, bob, carol):
            self.svc.record_view(v1.video_id, u.user_id)
        self.svc.record_view(v2.video_id, bob.user_id)
        self.svc.record_view(v2.video_id, carol.user_id)
        # Alice and Bob both have v1 in history; both should see v2.
        recs_alice = self.svc.recommend(alice.user_id, limit=5)
        recs_bob = self.svc.recommend(bob.user_id, limit=5)
        ids_alice = {vid for vid, _t, _s in recs_alice}
        ids_bob = {vid for vid, _t, _s in recs_bob}
        self.assertIn(v2.video_id, ids_alice)
        self.assertIn(v2.video_id, ids_bob)


if __name__ == "__main__":
    unittest.main()
