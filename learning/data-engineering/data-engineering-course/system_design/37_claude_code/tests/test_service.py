"""Unit tests for the agentic coding service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.service import AgentService, _safe_join  # noqa: E402


class AgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_agent",
            persist_path=os.path.join(self.tmpdir, "agent.json"),
        )
        self.svc = AgentService(
            store=self.store,
            workspace_root=self.tmpdir,
            default_workspace="ws",
        )

    # ---- session creation ----------------------------------------------

    def test_create_session_seeds_workspace(self):
        s = self.svc.create_session("u1")
        self.assertEqual(s.user_id, "u1")
        again = self.svc.get_session(s.session_id)
        self.assertIsNotNone(again)
        files = self.svc.list_files(s.session_id)
        self.assertTrue(any(f["path"] == "README.md" for f in files))

    def test_create_session_validation(self):
        with self.assertRaises(ValueError):
            self.svc.create_session("")

    # ---- agent loop ----------------------------------------------------

    def test_run_turn_with_list_request(self):
        s = self.svc.create_session("u1")
        turns = self.svc.run_turn(s.session_id, "list the files please")
        # At least the assistant turn and the tool observation.
        self.assertGreaterEqual(len(turns), 2)
        # The first assistant turn has a tool_call.
        self.assertIsNotNone(turns[0].tool_call)
        self.assertEqual(turns[0].tool_call.name, "list_dir")
        # The tool observation references the workspace contents.
        tool_turn = next(t for t in turns if t.role == "tool")
        self.assertIn("README.md", tool_turn.content)

    def test_run_turn_with_create_request(self):
        s = self.svc.create_session("u1")
        self.svc.run_turn(s.session_id, "create hello.txt with a message")
        files = self.svc.list_files(s.session_id)
        paths = [f["path"] for f in files]
        self.assertIn("hello.txt", paths)

    def test_run_turn_respects_max_iterations(self):
        # The deterministic policy is bounded; after MAX_ITERATIONS it stops.
        s = self.svc.create_session("u1")
        turns = self.svc.run_turn(s.session_id, "do something ambiguous")
        # We never exceed MAX_ITERATIONS tool calls.
        tool_calls = [t for t in turns if t.tool_call is not None]
        self.assertLessEqual(len(tool_calls), 5)
        # The last assistant turn has no tool_call (final reply).
        last_assistant = [t for t in turns if t.role == "assistant"][-1]
        self.assertIsNone(last_assistant.tool_call)

    def test_run_turn_unknown_session(self):
        with self.assertRaises(ValueError):
            self.svc.run_turn(999, "hi")

    def test_run_turn_validation(self):
        s = self.svc.create_session("u1")
        with self.assertRaises(ValueError):
            self.svc.run_turn(s.session_id, "")

    # ---- file inspection -----------------------------------------------

    def test_read_file(self):
        s = self.svc.create_session("u1")
        self.svc.run_turn(s.session_id, "create note.md with body 'agent note'")
        text = self.svc.read_file(s.session_id, "note.md")
        self.assertIn("agent note", text)

    def test_read_file_rejects_traversal(self):
        s = self.svc.create_session("u1")
        with self.assertRaises(ValueError):
            self.svc.read_file(s.session_id, "../etc/passwd")

    def test_safe_join_blocks_traversal(self):
        from pathlib import Path
        ws = Path(self.tmpdir) / "ws"
        with self.assertRaises(ValueError):
            _safe_join(ws, "../../etc/passwd")

    # ---- list files ----------------------------------------------------

    def test_list_files(self):
        s = self.svc.create_session("u1")
        self.svc.run_turn(s.session_id, "create a.txt")
        files = self.svc.list_files(s.session_id)
        paths = [f["path"] for f in files]
        self.assertIn("a.txt", paths)

    # ---- run_command tool ----------------------------------------------

    def test_run_command_succeeds(self):
        s = self.svc.create_session("u1")
        turns = self.svc.run_turn(s.session_id, "run ls -la")
        tool_turn = next(t for t in turns if t.role == "tool")
        self.assertEqual(tool_turn.tool_call.status, "ok")
        self.assertIn("README.md", tool_turn.content)

    def test_run_command_blocks_dangerous(self):
        from code.service import tool_run_command
        from pathlib import Path
        ws = Path(self.tmpdir) / "ws"
        c = tool_run_command(ws, {"command": "rm -rf /"})
        self.assertEqual(c.status, "error")
        self.assertIn("safety", c.error.lower())


if __name__ == "__main__":
    unittest.main()
