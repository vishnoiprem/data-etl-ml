"""Unit tests for the chunked file uploader."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.service import FileUploader  # noqa: E402


class FileUploaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = KeyValueStore(
            "test_uploader",
            persist_path=os.path.join(self.tmpdir, "up.json"),
        )
        self.svc = FileUploader(
            store=self.store,
            root=self.tmpdir,
            default_chunk_size=8,
        )

    # ---- validation ----------------------------------------------------

    def test_initiate_rejects_empty_filename(self):
        with self.assertRaises(ValueError):
            self.svc.initiate("", 10, "text/plain")

    def test_initiate_rejects_bad_size(self):
        with self.assertRaises(ValueError):
            self.svc.initiate("a.txt", 0, "text/plain")
        with self.assertRaises(ValueError):
            self.svc.initiate("a.txt", -1, "text/plain")

    def test_initiate_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            self.svc.initiate("../etc/passwd", 10, "text/plain")

    def test_initiate_rejects_bad_content_type(self):
        with self.assertRaises(ValueError):
            self.svc.initiate("a.txt", 10, "application/x-evil")

    def test_initiate_clamps_chunk_size(self):
        up = self.svc.initiate("a.txt", 10, "text/plain", chunk_size=10)
        self.assertGreaterEqual(up.chunk_size, 64 * 1024)
        up2 = self.svc.initiate("b.txt", 10, "text/plain", chunk_size=10**10)
        self.assertLessEqual(up2.chunk_size, 16 * 1024 * 1024)

    # ---- chunks --------------------------------------------------------

    def test_put_chunk_records_receipt(self):
        up = self.svc.initiate("a.txt", 16, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"01234567")
        again = self.svc.get_upload(up.upload_id)
        self.assertIn(0, again.received)
        self.assertEqual(again.status, "in_progress")

    def test_put_chunk_rejects_oversize(self):
        up = self.svc.initiate("a.txt", 1000, "text/plain", chunk_size=8)
        with self.assertRaises(ValueError):
            self.svc.put_chunk(up.upload_id, 0, b"x" * 64)

    # ---- missing chunks / status ---------------------------------------

    def test_missing_chunks(self):
        up = self.svc.initiate("a.txt", 24, "text/plain")  # 3 chunks
        self.svc.put_chunk(up.upload_id, 0, b"aaaaaaaa")
        self.svc.put_chunk(up.upload_id, 2, b"cccccccc")
        s = self.svc.status(up.upload_id)
        self.assertEqual(s["received"], 2)
        self.assertEqual(s["missing"], [1])

    # ---- complete ------------------------------------------------------

    def test_complete_stitches_and_downloads(self):
        up = self.svc.initiate("hello.txt", 12, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"hello ")
        self.svc.put_chunk(up.upload_id, 1, b"world!")
        rec = self.svc.complete(up.upload_id)
        self.assertEqual(rec.size, 12)
        self.assertEqual(rec.sha256, __import__("hashlib").sha256(b"hello world!").hexdigest())
        self.assertEqual(self.svc.download(rec.file_id), b"hello world!")
        # Idempotent.
        rec2 = self.svc.complete(up.upload_id)
        self.assertEqual(rec2.file_id, rec.file_id)

    def test_complete_rejects_missing(self):
        up = self.svc.initiate("a.txt", 16, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"01234567")
        with self.assertRaises(ValueError):
            self.svc.complete(up.upload_id)

    def test_complete_rejects_size_mismatch(self):
        up = self.svc.initiate("a.txt", 12, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"hello ")
        self.svc.put_chunk(up.upload_id, 1, b"world")  # 11 bytes, not 12
        with self.assertRaises(ValueError):
            self.svc.complete(up.upload_id)

    # ---- abort ---------------------------------------------------------

    def test_abort_removes_chunks(self):
        up = self.svc.initiate("a.txt", 16, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"01234567")
        ok = self.svc.abort(up.upload_id)
        self.assertTrue(ok)
        again = self.svc.get_upload(up.upload_id)
        self.assertEqual(again.status, "aborted")
        # Subsequent put should fail.
        with self.assertRaises(ValueError):
            self.svc.put_chunk(up.upload_id, 1, b"abcdefgh")

    def test_abort_missing_returns_false(self):
        self.assertFalse(self.svc.abort(999))

    # ---- list / get file ----------------------------------------------

    def test_list_files(self):
        up = self.svc.initiate("a.txt", 4, "text/plain")
        self.svc.put_chunk(up.upload_id, 0, b"data")
        rec = self.svc.complete(up.upload_id)
        files = self.svc.list_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].file_id, rec.file_id)
        self.assertEqual(self.svc.get_file(rec.file_id).file_id, rec.file_id)


if __name__ == "__main__":
    unittest.main()
