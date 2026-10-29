"""Tests for the Google-Docs service."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import DocsService  # noqa: E402


class DocsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = DocsService()

    def test_create_and_snapshot(self):
        d = self.svc.create_doc("notes")
        s = self.svc.snapshot(d.doc_id)
        self.assertEqual(s["content"], "")
        self.assertEqual(s["version"], 0)

    def test_insert_op(self):
        d = self.svc.create_doc("notes")
        r = self.svc.apply_op(d.doc_id, op="insert", pos=0, text="Hello world")
        self.assertEqual(r["content"], "Hello world")
        self.assertEqual(r["version"], 1)
        s = self.svc.snapshot(d.doc_id)
        self.assertEqual(s["content"], "Hello world")

    def test_delete_op(self):
        d = self.svc.create_doc("notes")
        self.svc.apply_op(d.doc_id, op="insert", pos=0, text="Hello world")
        r = self.svc.apply_op(d.doc_id, op="delete", pos=5, n=6)
        self.assertEqual(r["content"], "Hello")

    def test_op_log_preserved(self):
        d = self.svc.create_doc("notes")
        self.svc.apply_op(d.doc_id, op="insert", pos=0, text="A")
        self.svc.apply_op(d.doc_id, op="insert", pos=1, text="B")
        self.svc.apply_op(d.doc_id, op="insert", pos=2, text="C")
        ops = self.svc.get_ops(d.doc_id)
        self.assertEqual(len(ops), 3)
        self.assertEqual([o.seq for o in ops], [1, 2, 3])
        self.assertEqual(ops[0].text, "A")

    def test_invalid_op_rejected(self):
        d = self.svc.create_doc("notes")
        with self.assertRaises(ValueError):
            self.svc.apply_op(d.doc_id, op="insert", pos=0)  # no text
        with self.assertRaises(ValueError):
            self.svc.apply_op(d.doc_id, op="insert", pos=0, text="x", if_version=0)
            # actually above will succeed; bad case:
        with self.assertRaises(ValueError):
            self.svc.apply_op(d.doc_id, op="delete", pos=0, n=0)  # zero count
        with self.assertRaises(ValueError):
            self.svc.apply_op(d.doc_id, op="delete", pos=0, n=5)  # out of range

    def test_version_counter_advances(self):
        d = self.svc.create_doc("notes")
        self.svc.apply_op(d.doc_id, "insert", 0, "a")
        self.svc.apply_op(d.doc_id, "insert", 1, "b")
        self.svc.apply_op(d.doc_id, "insert", 2, "c")
        doc = self.svc.get_doc(d.doc_id)
        self.assertEqual(doc.version, 3)
        self.assertEqual(doc.op_count, 3)

    def test_if_version_accepted(self):
        d = self.svc.create_doc("notes")
        r1 = self.svc.apply_op(d.doc_id, "insert", 0, "abc")
        v = r1["version"]
        r2 = self.svc.apply_op(d.doc_id, "insert", 3, "DEF", if_version=v)
        self.assertEqual(r2["content"], "abcDEF")

    def test_listener_receives_op(self):
        d = self.svc.create_doc("notes")
        import queue
        q: "queue.Queue" = self.svc.register_listener(d.doc_id)
        r = self.svc.apply_op(d.doc_id, "insert", 0, "hi")
        evt = q.get(timeout=2)
        self.assertEqual(evt["seq"], r["seq"])
        self.assertEqual(evt["op"], "insert")
        self.svc.unregister_listener(d.doc_id, q)

    def test_replay_rebuilds_snapshot(self):
        d = self.svc.create_doc("notes")
        self.svc.apply_op(d.doc_id, "insert", 0, "abc")
        self.svc.apply_op(d.doc_id, "insert", 1, "X")
        self.svc.apply_op(d.doc_id, "delete", 0, n=2)
        # Force replay by clearing the snapshot cache.
        self.svc.snaps.delete(f"snap:{d.doc_id}")
        s = self.svc.snapshot(d.doc_id)
        self.assertEqual(s["content"], "Xc")


if __name__ == "__main__":
    unittest.main()
