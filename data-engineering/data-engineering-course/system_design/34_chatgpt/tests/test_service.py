"""Unit tests for the ChatGPT-style service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.service import ChatService, estimate_tokens, _mock_complete  # noqa: E402


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_chat",
            persist_path=os.path.join(self.tmpdir, "chat.json"),
        )
        self.svc = ChatService(store=self.store, context_window=4)

    # ---- token estimate -------------------------------------------------

    def test_estimate_tokens_short(self):
        self.assertGreaterEqual(estimate_tokens("hello world"), 1)

    def test_estimate_tokens_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    # ---- mock LLM -------------------------------------------------------

    def test_mock_complete_returns_string(self):
        from code.service import ChatMessage
        ctx = [ChatMessage(role="user", content="hi")]
        out = _mock_complete(ctx, "mock-fast")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 0)

    # ---- conversations --------------------------------------------------

    def test_create_conversation_persists_system_prompt(self):
        c = self.svc.create_conversation("u1", "mock-fast")
        self.assertEqual(c.messages[0].role, "system")
        again = self.svc.get_conversation(c.conversation_id)
        self.assertIsNotNone(again)
        self.assertEqual(again.user_id, "u1")

    def test_create_rejects_unknown_model(self):
        with self.assertRaises(ValueError):
            self.svc.create_conversation("u1", "no-such-model")

    def test_create_rejects_missing_user(self):
        with self.assertRaises(ValueError):
            self.svc.create_conversation("", "mock-fast")

    # ---- messages -------------------------------------------------------

    def test_add_message_validation(self):
        c = self.svc.create_conversation("u1")
        with self.assertRaises(ValueError):
            self.svc.add_message(c.conversation_id, "user", "")
        with self.assertRaises(ValueError):
            self.svc.add_message(c.conversation_id, "admin", "x")

    def test_add_message_persists(self):
        c = self.svc.create_conversation("u1")
        m = self.svc.add_message(c.conversation_id, "user", "hello")
        self.assertEqual(m.role, "user")
        again = self.svc.get_conversation(c.conversation_id)
        self.assertEqual(len(again.messages), 2)  # system + user

    def test_add_message_truncates_long_input(self):
        c = self.svc.create_conversation("u1")
        long = "x" * 10_000
        m = self.svc.add_message(c.conversation_id, "user", long)
        self.assertLessEqual(len(m.content), 4_001)  # MAX + ellipsis

    # ---- completion -----------------------------------------------------

    def test_complete_appends_assistant_message(self):
        c = self.svc.create_conversation("u1")
        self.svc.add_message(c.conversation_id, "user", "how does this work?")
        reply = self.svc.complete(c.conversation_id)
        self.assertEqual(reply.role, "assistant")
        self.assertGreater(len(reply.content), 0)
        again = self.svc.get_conversation(c.conversation_id)
        # system + user + assistant = 3
        self.assertEqual(len(again.messages), 3)

    def test_complete_context_window_truncates(self):
        c = self.svc.create_conversation("u1")
        # Push 10 user messages with a context window of 4.
        for i in range(10):
            self.svc.add_message(c.conversation_id, "user", f"msg-{i}")
        # Make sure complete doesn't error.
        reply = self.svc.complete(c.conversation_id)
        self.assertEqual(reply.role, "assistant")

    # ---- streaming ------------------------------------------------------

    def test_stream_yields_growing_chunks(self):
        c = self.svc.create_conversation("u1")
        self.svc.add_message(c.conversation_id, "user", "explain caching")
        chunks = list(self.svc.stream(c.conversation_id))
        self.assertGreater(len(chunks), 1)
        # Each chunk is a prefix of the next.
        for a, b in zip(chunks, chunks[1:]):
            self.assertTrue(b.content.startswith(a.content))
        # Final message was appended.
        again = self.svc.get_conversation(c.conversation_id)
        self.assertEqual(again.messages[-1].role, "assistant")

    # ---- stats ----------------------------------------------------------

    def test_stats(self):
        c = self.svc.create_conversation("u1")
        self.svc.add_message(c.conversation_id, "user", "hi")
        s = self.svc.stats()
        self.assertEqual(s["conversations"], 1)
        self.assertGreaterEqual(s["messages"], 2)  # system + user


if __name__ == "__main__":
    unittest.main()
