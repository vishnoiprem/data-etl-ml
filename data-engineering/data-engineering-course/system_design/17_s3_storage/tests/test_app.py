"""HTTP-level tests for the S3-style object store (Flask test client)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import ObjectStoreService  # noqa: E402


class S3AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.svc = ObjectStoreService(base_dir=self.tmp)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_put_get_roundtrip(self):
        r = self.client.put("/mybucket/file.txt", data=b"hello world")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertIn("version_id", body)
        self.assertIn("etag", body)
        self.assertEqual(body["size"], 11)

        r2 = self.client.get("/mybucket/file.txt")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data, b"hello world")
        self.assertIn("ETag", r2.headers)
        self.assertIn("x-version-id", r2.headers)

    def test_head(self):
        self.client.put("/b/k", data=b"abcd")
        r = self.client.head("/b/k")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Length"], "4")
        self.assertEqual(r.headers["x-deleted"], "0")

    def test_head_missing(self):
        r = self.client.head("/b/missing")
        self.assertEqual(r.status_code, 404)

    def test_delete(self):
        self.client.put("/b/k", data=b"x")
        r = self.client.delete("/b/k")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["deleted"])
        # Subsequent get → 404
        r2 = self.client.get("/b/k")
        self.assertEqual(r2.status_code, 404)

    def test_listing_with_prefix(self):
        self.client.put("/b/a/1.png", data=b"x")
        self.client.put("/b/a/2.png", data=b"x")
        self.client.put("/b/b/1.png", data=b"x")
        r = self.client.get("/b/?prefix=a/")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["key_count"], 2)

    def test_listing_no_prefix(self):
        self.client.put("/b/a.txt", data=b"x")
        self.client.put("/b/b.txt", data=b"x")
        r = self.client.get("/b/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["key_count"], 2)

    def test_versioning_roundtrip(self):
        r1 = self.client.put("/b/k", data=b"v1")
        v1 = r1.get_json()["version_id"]
        r2 = self.client.put("/b/k", data=b"v2")
        v2 = r2.get_json()["version_id"]
        self.assertNotEqual(v1, v2)
        # Read each version explicitly
        rd1 = self.client.get(f"/b/k?versionId={v1}")
        self.assertEqual(rd1.data, b"v1")
        rd2 = self.client.get(f"/b/k?versionId={v2}")
        self.assertEqual(rd2.data, b"v2")

    def test_multipart_flow(self):
        # Init
        r = self.client.post("/b/big.bin?uploads")
        self.assertEqual(r.status_code, 200)
        upload_id = r.get_json()["upload_id"]
        # Parts
        r = self.client.put(
            f"/b/big.bin?uploadId={upload_id}&partNumber=1",
            data=b"hello ",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["etag"], __import__("hashlib").md5(b"hello ").hexdigest())
        r = self.client.put(
            f"/b/big.bin?uploadId={upload_id}&partNumber=2",
            data=b"world",
        )
        self.assertEqual(r.status_code, 200)
        # Complete
        r = self.client.post(f"/b/big.bin?uploadId={upload_id}&complete")
        self.assertEqual(r.status_code, 200)
        # Read back
        r = self.client.get("/b/big.bin")
        self.assertEqual(r.data, b"hello world")
        self.assertEqual(r.headers["Content-Length"], "11")

    def test_metrics_endpoint(self):
        self.client.put("/b/k", data=b"x")
        self.client.get("/b/k")
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        text = r.get_data(as_text=True)
        self.assertIn("put_total", text)
        self.assertIn("get_total", text)

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("endpoints", r.get_json())

    def test_invalid_bucket_name(self):
        r = self.client.put("/BAD_NAME/k", data=b"x")
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
