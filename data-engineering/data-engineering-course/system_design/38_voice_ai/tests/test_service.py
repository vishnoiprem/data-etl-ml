"""Unit tests for the real-time voice AI service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.service import (
    VoiceService,
    _mock_stt,
    _mock_llm,
    _mock_tts_synth,
)  # noqa: E402


class VoiceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_voice",
            persist_path=os.path.join(self.tmpdir, "v.json"),
        )
        self.svc = VoiceService(store=self.store)

    # ---- mock STT/LLM/TTS ----------------------------------------------

    def test_stt_is_deterministic(self):
        a = _mock_stt(b"\x00\x01")
        b = _mock_stt(b"\x00\x01")
        self.assertEqual(a, b)
        self.assertGreater(len(a), 0)

    def test_stt_empty_audio(self):
        self.assertEqual(_mock_stt(b""), "")

    def test_llm_handles_intent(self):
        self.assertIn("partly cloudy", _mock_llm("what's the weather").lower())
        self.assertIn("reminder", _mock_llm("remind me to call mom").lower())
        self.assertIn("jazz", _mock_llm("play some jazz music").lower())

    def test_llm_handles_empty(self):
        out = _mock_llm("")
        self.assertIn("try again", out.lower())

    def test_tts_synth_produces_chunks(self):
        chunks = _mock_tts_synth("hello world this is a test")
        # 6 words → 6 chunks (one per word).
        self.assertEqual(len(chunks), 6)
        for c in chunks:
            self.assertEqual(len(c), 256)

    def test_tts_synth_empty(self):
        self.assertEqual(_mock_tts_synth(""), [])

    # ---- session lifecycle --------------------------------------------

    def test_create_session(self):
        s = self.svc.create_session("u1")
        self.assertEqual(s.user_id, "u1")
        self.assertEqual(s.state, "idle")
        again = self.svc.get_session(s.session_id)
        self.assertIsNotNone(again)

    def test_create_session_validation(self):
        with self.assertRaises(ValueError):
            self.svc.create_session("")

    # ---- pipeline: audio in -------------------------------------------

    def test_push_audio_runs_full_pipeline(self):
        s = self.svc.create_session("u1")
        chunks = self.svc.push_audio(s.session_id, b"\x00\x01\x02")
        again = self.svc.get_session(s.session_id)
        # Pipeline progressed.
        self.assertIn(again.state, ("playing", "done"))
        # Transcript has both user and assistant lines.
        roles = [t.role for t in again.transcript]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)
        # Outbox is populated.
        self.assertGreater(len(again.outbox), 0)
        # Returned chunks match outbox contents.
        self.assertEqual(len(chunks), len(again.outbox))

    def test_push_audio_empty_returns_no_chunks(self):
        s = self.svc.create_session("u1")
        chunks = self.svc.push_audio(s.session_id, b"")
        self.assertEqual(chunks, [])

    def test_push_audio_rejects_oversize(self):
        s = self.svc.create_session("u1")
        with self.assertRaises(ValueError):
            self.svc.push_audio(s.session_id, b"x" * (self.svc.max_chunk_bytes + 1))

    def test_push_audio_rejects_non_bytes(self):
        s = self.svc.create_session("u1")
        with self.assertRaises(ValueError):
            self.svc.push_audio(s.session_id, "not bytes")  # type: ignore[arg-type]

    def test_push_audio_unknown_session(self):
        with self.assertRaises(ValueError):
            self.svc.push_audio(999, b"\x00")

    # ---- streaming / transcript ---------------------------------------

    def test_get_transcript(self):
        s = self.svc.create_session("u1")
        self.svc.push_audio(s.session_id, b"\x00")
        t = self.svc.get_transcript(s.session_id)
        self.assertGreater(len(t), 0)

    def test_clear_outbox(self):
        s = self.svc.create_session("u1")
        self.svc.push_audio(s.session_id, b"\x00")
        n = self.svc.clear_outbox(s.session_id)
        self.assertGreater(n, 0)
        again = self.svc.get_session(s.session_id)
        self.assertEqual(len(again.outbox), 0)
        self.assertEqual(again.state, "idle")

    def test_iter_outbox(self):
        s = self.svc.create_session("u1")
        self.svc.push_audio(s.session_id, b"\x00")
        chunks = list(self.svc.iter_outbox(s.session_id, since=0))
        self.assertGreater(len(chunks), 0)

    def test_stats(self):
        s = self.svc.create_session("u1")
        self.svc.push_audio(s.session_id, b"\x00")
        st = self.svc.stats()
        self.assertEqual(st["sessions"], 1)
        self.assertEqual(st["turns"], 1)
        self.assertGreater(st["audio_in_bytes"], 0)
        self.assertGreater(st["audio_out_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
