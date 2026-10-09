"""HTTP-level tests for the chunked file uploader."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from common.storage import KeyValueStore  # noqa: E402
from code.app import create_app  # noqa: E402
from code.service import FileUploader  # noqa: E402


class FileUploaderAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        store = KeyValueStore(
            "test_uploader_app",
            persist_path=os.path.join(self.tmpdir, "up.json"),
        )
        self.svc = FileUploader(store=store, root=self.tmpdir, default_chunk_size=8)
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_initiate(self):
        r = self.client.post(
            "/api/uploads/initiate",
            json={"filename": "a.txt", "size": 16, "content_type": "text/plain"},
        )
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertIn("upload_id", body)
        self.assertIn("chunk_size", body)

    def test_initiate_rejects_missing(self):
        r = self.client.post("/api/uploads/initiate", json={"filename": "a.txt"})
        self.assertEqual(r.status_code, 400)

    def test_full_flow(self):
        r = self.client.post(
            "/api/uploads/initiate",
            json={"filename": "a.txt", "size": 12, "content_type": "text/plain"},
        )
        up_id = r.get_json()["upload_id"]
        r1 = self.client.put(f"/api/uploads/{up_id}/chunks/0", data=b"hello ")
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.put(f"/api/uploads/{up_id}/chunks/1", data=b"world!")
        self.assertEqual(r2.status_code, 200)
        rc = self.client.post(f"/api/uploads/{up_id}/complete")
        self.assertEqual(rc.status_code, 201)
        rec = rc.get_json()
        self.assertEqual(rec["size"], 12)
        # Download roundtrip.
        rd = self.client.get(f"/api/files/{rec['file_id']}/download")
        self.assertEqual(rd.status_code, 200)
        self.assertEqual(rd.data, b"hello world!")

    def test_status_for_resume(self):
        r = self.client.post(
            "/api/uploads/initiate",
            json={"filename": "a.txt", "size": 24, "content_type": "text/plain"},
        )
        up_id = r.get_json()["upload_id"]
        self.client.put(f"/api/uploads/{up_id}/chunks/0", data=b"aaaaaaaa")
        self.client.put(f"/api/uploads/{up_id}/chunks/2", data=b"cccccccc")
        s = self.client.get(f"/api/uploads/{up_id}/status")
        self.assertEqual(s.status_code, 200)
        body = s.get_json()
        self.assertEqual(body["received"], 2)
        self.assertEqual(body["missing"], [1])

    def test_complete_rejects_missing_chunks(self):
        r = self.client.post(
            "/api/uploads/initiate",
            json={"filename": "a.txt", "size": 16, "content_type": "text/plain"},
        )
        up_id = r.get_json()["upload_id"]
        self.client.put(f"/api/uploads/{up_id}/chunks/0", data=b"01234567")
        rc = self.client.post(f"/api/uploads/{up_id}/complete")
        self.assertEqual(rc.status_code, 400)

    def test_abort(self):
        r = self.client.post(
            "/api/uploads/initiate",
            json={"filename": "a.txt", "size": 8, "content_type": "text/plain"},
        )
        up_id = r.get_json()["upload_id"]
        ra = self.client.post(f"/api/uploads/{up_id}/abort")
        self.assertEqual(ra.status_code, 200)
        s = self.client.get(f"/api/uploads/{up_id}/status")
        self.assertEqual(s.get_json()["status"], "aborted")

    def test_metrics_endpoint(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("uploads_initiated_total", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
