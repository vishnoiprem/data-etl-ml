"""Unit tests for the Twitch service core."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.cache import TTLCache  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402
from code.service import TwitchService  # noqa: E402


class TwitchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_twitch",
            persist_path=os.path.join(self.tmpdir, "twitch.json"),
        )
        self.cache = TTLCache(ttl_seconds=60, max_entries=200)
        self.svc = TwitchService(
            store=self.store, cache=self.cache, heartbeat_timeout_s=30.0
        )

    # ---- validation / happy path -------------------------------------

    def test_start_stream_returns_id(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "playing zelda", "Zelda")
        self.assertIsNotNone(s.stream_id)
        self.assertGreater(s.stream_id, 0)
        self.assertEqual(s.title, "playing zelda")
        # Game is lowercased.
        self.assertEqual(s.game, "zelda")
        self.assertTrue(s.live)
        self.assertEqual(s.peak_viewers, 0)

    def test_start_stream_rejects_invalid_inputs(self):
        u = self.svc.create_user("alice")
        with self.assertRaises(ValueError):
            self.svc.start_stream(u.user_id, "", "zelda")
        with self.assertRaises(ValueError):
            self.svc.start_stream(u.user_id, "ok", "")
        with self.assertRaises(ValueError):
            self.svc.start_stream(999_999_999, "ok", "zelda")

    def test_end_stream_marks_not_live(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        ended = self.svc.end_stream(s.stream_id)
        self.assertIsNotNone(ended)
        self.assertFalse(ended.live)
        self.assertIsNotNone(ended.ended_at)

    def test_get_stream_missing(self):
        self.assertIsNone(self.svc.get_stream(424242))

    # ---- chat --------------------------------------------------------

    def test_post_chat_returns_message(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        m = self.svc.post_chat(s.stream_id, u.user_id, "hello chat")
        self.assertIsNotNone(m.msg_id)
        self.assertEqual(m.body, "hello chat")
        self.assertEqual(m.user_id, u.user_id)
        self.assertEqual(m.stream_id, s.stream_id)

    def test_post_chat_rejects_invalid_inputs(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        with self.assertRaises(ValueError):
            self.svc.post_chat(s.stream_id, u.user_id, "")
        with self.assertRaises(ValueError):
            self.svc.post_chat(s.stream_id, u.user_id, "x" * 501)
        with self.assertRaises(ValueError):
            self.svc.post_chat(999_999_999, u.user_id, "hi")
        with self.assertRaises(ValueError):
            self.svc.post_chat(s.stream_id, 999_999_999, "hi")

    def test_post_chat_rejects_when_not_live(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        self.svc.end_stream(s.stream_id)
        with self.assertRaises(ValueError):
            self.svc.post_chat(s.stream_id, u.user_id, "hi")

    def test_get_chat_log_returns_recent(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        for i in range(5):
            self.svc.post_chat(s.stream_id, u.user_id, f"msg {i}")
        log = self.svc.get_chat_log(s.stream_id, limit=3)
        self.assertEqual(len(log), 3)
        # Most-recent-first would be nice, but a deque is FIFO.
        # The test just confirms the log has the most recent N.
        bodies = [m["body"] for m in log]
        self.assertIn("msg 2", bodies)
        self.assertIn("msg 4", bodies)

    # ---- chat fanout / pub/sub --------------------------------------

    def test_subscribe_receives_messages(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        sub_id, q = self.svc.subscribe(s.stream_id)
        try:
            self.svc.post_chat(s.stream_id, u.user_id, "hello")
            payload = q.get(timeout=2.0)
            self.assertEqual(payload["body"], "hello")
            self.assertEqual(payload["stream_id"], s.stream_id)
        finally:
            self.svc.unsubscribe(s.stream_id, sub_id)

    def test_unsubscribe_stops_delivery(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        sub_id, q = self.svc.subscribe(s.stream_id)
        self.svc.unsubscribe(s.stream_id, sub_id)
        # Subscriber count drops to zero.
        self.assertEqual(self.svc.subscriber_count(s.stream_id), 0)
        # Posting doesn't error — fanout is a no-op for empty subs.
        self.svc.post_chat(s.stream_id, u.user_id, "after unsub")
        # And the queue is empty (we didn't get a message).
        with self.assertRaises(Exception):
            q.get(timeout=0.2)

    def test_end_stream_closes_subscribers(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        sub_id, q = self.svc.subscribe(s.stream_id)
        try:
            # End the stream on a background thread so the SSE-style
            # blocking q.get can return the sentinel.
            t = threading.Thread(
                target=lambda: self.svc.end_stream(s.stream_id)
            )
            t.start()
            try:
                payload = q.get(timeout=2.0)
            finally:
                t.join(timeout=2.0)
            self.assertTrue(payload.get("__end__"))
        finally:
            self.svc.unsubscribe(s.stream_id, sub_id)

    # ---- viewer count via heartbeat ---------------------------------

    def test_heartbeat_increments_viewer_count(self):
        u1 = self.svc.create_user("broadcaster")
        u2 = self.svc.create_user("viewer1")
        u3 = self.svc.create_user("viewer2")
        s = self.svc.start_stream(u1.user_id, "title", "game")
        r1 = self.svc.heartbeat(s.stream_id, u2.user_id)
        r2 = self.svc.heartbeat(s.stream_id, u3.user_id)
        self.assertEqual(r1["viewers"], 1)
        self.assertEqual(r2["viewers"], 2)
        # And the same viewer heartbeating doesn't double-count.
        r3 = self.svc.heartbeat(s.stream_id, u2.user_id)
        self.assertEqual(r3["viewers"], 2)
        # Peak tracks the high-water mark.
        self.assertEqual(s.peak_viewers, 0)
        self.assertEqual(self.svc.get_stream(s.stream_id).peak_viewers, 2)

    def test_heartbeat_rejects_unknown_user(self):
        u = self.svc.create_user("alice")
        s = self.svc.start_stream(u.user_id, "title", "game")
        with self.assertRaises(ValueError):
            self.svc.heartbeat(s.stream_id, 999_999_999)

    def test_heartbeat_rejects_offline_stream(self):
        u1 = self.svc.create_user("alice")
        u2 = self.svc.create_user("bob")
        s = self.svc.start_stream(u1.user_id, "title", "game")
        self.svc.end_stream(s.stream_id)
        with self.assertRaises(ValueError):
            self.svc.heartbeat(s.stream_id, u2.user_id)

    def test_heartbeat_evicts_stale_viewers(self):
        u1 = self.svc.create_user("alice")
        u2 = self.svc.create_user("bob")
        s = self.svc.start_stream(u1.user_id, "title", "game")
        # Use a tiny timeout so the test is fast.
        svc = TwitchService(
            store=self.store,
            cache=self.cache,
            heartbeat_timeout_s=0.05,
        )
        s2 = svc.start_stream(u1.user_id, "title", "game")
        svc.heartbeat(s2.stream_id, u2.user_id)
        self.assertEqual(svc.viewer_count(s2.stream_id), 1)
        time.sleep(0.1)  # exceed the 50ms timeout
        # Next call to viewer_count (or any heartbeat) evicts.
        self.assertEqual(svc.viewer_count(s2.stream_id), 0)

    # ---- directory ---------------------------------------------------

    def test_list_streams_by_game(self):
        u = self.svc.create_user("alice")
        s1 = self.svc.start_stream(u.user_id, "a", "zelda")
        s2 = self.svc.start_stream(u.user_id, "b", "minecraft")
        s3 = self.svc.start_stream(u.user_id, "c", "zelda")
        zelda = self.svc.list_streams(game="zelda")
        ids = {s.stream_id for s in zelda}
        self.assertIn(s1.stream_id, ids)
        self.assertIn(s3.stream_id, ids)
        self.assertNotIn(s2.stream_id, ids)
        # Case-insensitive game filter.
        zelda_upper = self.svc.list_streams(game="ZELDA")
        self.assertEqual(
            {s.stream_id for s in zelda_upper}, ids
        )

    def test_list_streams_live_only_default(self):
        u = self.svc.create_user("alice")
        s_live = self.svc.start_stream(u.user_id, "a", "g")
        s_ended = self.svc.start_stream(u.user_id, "b", "g")
        self.svc.end_stream(s_ended.stream_id)
        only_live = self.svc.list_streams()
        ids = {s.stream_id for s in only_live}
        self.assertIn(s_live.stream_id, ids)
        self.assertNotIn(s_ended.stream_id, ids)
        # With include_ended=True, both are returned.
        all_streams = self.svc.list_streams(live_only=False)
        all_ids = {s.stream_id for s in all_streams}
        self.assertIn(s_live.stream_id, all_ids)
        self.assertIn(s_ended.stream_id, all_ids)


if __name__ == "__main__":
    unittest.main()
