"""Unit tests for the S3-style object store service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    MultipartPart,
    ObjectStoreService,
    ObjectVersion,
    _is_safe_key,
)


class SafeKeyTests(unittest.TestCase):
    def test_safe_keys(self):
        for k in ["a.txt", "path/to/file.png", "2024/01/img.jpg"]:
            self.assertTrue(_is_safe_key(k), k)

    def test_unsafe_keys(self):
        for k in ["", "../etc/passwd", "key with space", "key\nwith\nnewline"]:
            self.assertFalse(_is_safe_key(k), k)


class ObjectStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.svc = ObjectStoreService(base_dir=self.tmp)

    def test_put_creates_bucket(self):
        self.svc.put("mybucket", "k", b"hello")
        self.assertIn("mybucket", self.svc.list_buckets())

    def test_put_get_roundtrip(self):
        self.svc.put("b", "file.txt", b"hello world")
        res = self.svc.get("b", "file.txt")
        self.assertIsNotNone(res)
        data, ver = res
        self.assertEqual(data, b"hello world")
        self.assertEqual(ver.size, 11)

    def test_etag_is_md5(self):
        import hashlib
        body = b"some body content"
        self.svc.put("b", "k", body)
        res = self.svc.get("b", "k")
        _, ver = res
        self.assertEqual(ver.etag, hashlib.md5(body).hexdigest())

    def test_versioning_preserves_old(self):
        v1 = self.svc.put("b", "k", b"v1")
        v2 = self.svc.put("b", "k", b"v2")
        self.assertNotEqual(v1["version_id"], v2["version_id"])
        # Both versions should be readable.
        d1, _ = self.svc.get("b", "k", version_id=v1["version_id"])
        d2, _ = self.svc.get("b", "k", version_id=v2["version_id"])
        self.assertEqual(d1, b"v1")
        self.assertEqual(d2, b"v2")

    def test_head(self):
        self.svc.put("b", "k", b"x")
        v = self.svc.head("b", "k")
        self.assertIsNotNone(v)
        self.assertEqual(v.size, 1)

    def test_delete_creates_tombstone(self):
        self.svc.put("b", "k", b"x")
        ver = self.svc.delete("b", "k")
        self.assertIsNotNone(ver)
        # get returns None since current version is a delete marker
        self.assertIsNone(self.svc.get("b", "k"))
        # head on the prior version still works
        all_v = self.svc._load_object("b", "k")
        live = [vid for vid, v in all_v.versions.items() if not v.deleted]
        self.assertEqual(len(live), 1)

    def test_list_objects_with_prefix(self):
        self.svc.put("b", "a/1.png", b"x")
        self.svc.put("b", "a/2.png", b"x")
        self.svc.put("b", "b/1.png", b"x")
        keys = self.svc.list_objects("b", prefix="a/")
        self.assertEqual(len(keys), 2)
        keys = self.svc.list_objects("b", prefix="b/")
        self.assertEqual(len(keys), 1)

    def test_multipart_upload(self):
        upload_id = self.svc.init_multipart("b", "big.bin")
        self.svc.upload_part(upload_id, 1, b"hello ")
        self.svc.upload_part(upload_id, 2, b"world")
        res = self.svc.complete_multipart(upload_id)
        self.assertEqual(res["size"], 11)
        d, _ = self.svc.get("b", "big.bin")
        self.assertEqual(d, b"hello world")

    def test_multipart_abort(self):
        upload_id = self.svc.init_multipart("b", "abort.bin")
        self.svc.upload_part(upload_id, 1, b"x")
        ok = self.svc.abort_multipart(upload_id)
        self.assertTrue(ok)
        # Should be gone
        self.assertIsNone(self.svc.list_multipart(upload_id))

    def test_multipart_invalid_part_number(self):
        upload_id = self.svc.init_multipart("b", "x")
        with self.assertRaises(ValueError):
            self.svc.upload_part(upload_id, 0, b"x")
        with self.assertRaises(ValueError):
            self.svc.upload_part(upload_id, 10_001, b"x")

    def test_get_missing(self):
        self.assertIsNone(self.svc.get("b", "nope"))

    def test_invalid_bucket_name(self):
        with self.assertRaises(ValueError):
            self.svc.put("BAD_BUCKET", "k", b"x")

    def test_invalid_key_rejected(self):
        with self.assertRaises(ValueError):
            self.svc.put("ok", "", b"x")


if __name__ == "__main__":
    unittest.main()
