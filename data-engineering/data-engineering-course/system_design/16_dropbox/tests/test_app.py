"""HTTP-level tests for the file sync service (Flask test client)."""

from __future__ import annotations

import base64
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import FileSyncService, FixedSizeChunker  # noqa: E402


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


class FileSyncAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.svc = FileSyncService(
            base_dir=self.tmp,
            chunker=FixedSizeChunker(size=1024),
        )
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_upload_returns_id(self):
        r = self.client.post(
            "/api/files",
            json={"filename": "x.txt", "content_b64": _b64(b"hello world")},
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertIn("id", body)
        self.assertEqual(body["filename"], "x.txt")
        self.assertEqual(body["size"], 11)

    def test_upload_rejects_bad_base64(self):
        r = self.client.post(
            "/api/files",
            json={"filename": "x.txt", "content_b64": "!!not base64!!"},
        )
        self.assertEqual(r.status_code, 400)

    def test_upload_rejects_missing(self):
        r = self.client.post("/api/files", json={"filename": "x.txt"})
        self.assertEqual(r.status_code, 400)

    def test_list_files(self):
        self.client.post("/api/files", json={"filename": "a", "content_b64": _b64(b"data")})
        r = self.client.get("/api/files")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["files"]), 1)

    def test_download_roundtrip(self):
        data = b"the quick brown fox jumps over the lazy dog"
        r1 = self.client.post(
            "/api/files",
            json={"filename": "doc.txt", "content_b64": _b64(data)},
        )
        file_id = r1.get_json()["id"]
        r2 = self.client.get(f"/api/files/{file_id}/download")
        self.assertEqual(r2.status_code, 200)
        body = r2.get_json()
        self.assertEqual(base64.b64decode(body["content_b64"]), data)

    def test_download_missing(self):
        r = self.client.get("/api/files/9999/download")
        self.assertEqual(r.status_code, 404)

    def test_get_chunk(self):
        r1 = self.client.post(
            "/api/files",
            json={"filename": "a", "content_b64": _b64(b"some data here")},
        )
        chunks = r1.get_json()["chunks"]
        h = chunks[0]["hash"]
        r2 = self.client.get(f"/api/chunks/{h}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["size"], chunks[0]["size"])

    def test_get_chunk_missing(self):
        r = self.client.get("/api/chunks/deadbeef" * 8)
        self.assertEqual(r.status_code, 404)

    def test_metrics_endpoint(self):
        self.client.post(
            "/api/files",
            json={"filename": "a", "content_b64": _b64(b"x")},
        )
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("upload_total", r.get_data(as_text=True))

    def test_index(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("endpoints", r.get_json())


if __name__ == "__main__":
    unittest.main()
