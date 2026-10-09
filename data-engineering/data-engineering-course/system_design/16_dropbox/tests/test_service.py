"""Unit tests for the file sync service."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    DEFAULT_CHUNK_SIZE,
    FixedSizeChunker,
    FileSyncService,
    RabinKarpChunker,
)


class FixedSizeChunkerTests(unittest.TestCase):
    def test_chunks_small_data(self):
        c = FixedSizeChunker(size=10)
        out = list(c.chunks(b"abc"))
        self.assertEqual(out, [(0, 3)])

    def test_chunks_exact(self):
        c = FixedSizeChunker(size=4)
        out = list(c.chunks(b"0123456789"))
        # 0-3, 4-7, 8-9
        self.assertEqual(out, [(0, 4), (4, 4), (8, 2)])

    def test_chunks_empty(self):
        c = FixedSizeChunker(size=10)
        self.assertEqual(list(c.chunks(b"")), [])


class RabinKarpChunkerTests(unittest.TestCase):
    def test_smaller_than_min(self):
        c = RabinKarpChunker(min_size=100, max_size=200, mask=0)
        out = list(c.chunks(b"x" * 50))
        self.assertEqual(out, [(0, 50)])

    def test_splits_at_boundaries(self):
        c = RabinKarpChunker(min_size=10, max_size=50, mask=0xF)
        data = bytes(range(256)) * 4  # 1024 bytes
        out = list(c.chunks(data))
        # Verify partition: chunks cover all bytes, no overlap, contiguous.
        pos = 0
        for off, length in out:
            self.assertEqual(off, pos)
            pos += length
        self.assertEqual(pos, len(data))


class FileSyncServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.svc = FileSyncService(
            base_dir=self.tmp,
            chunker=FixedSizeChunker(size=1024),  # small for tests
        )

    def test_upload_creates_record(self):
        data = b"hello world"
        rec = self.svc.upload("hello.txt", data)
        self.assertEqual(rec.filename, "hello.txt")
        self.assertEqual(rec.size, len(data))
        self.assertGreater(len(rec.chunks), 0)

    def test_download_roundtrip(self):
        data = b"the quick brown fox" * 10
        rec = self.svc.upload("fox.txt", data)
        out = self.svc.download(rec.id)
        self.assertIsNotNone(out)
        filename, payload = out
        self.assertEqual(filename, "fox.txt")
        self.assertEqual(payload, data)

    def test_dedup_reduces_storage(self):
        # Upload the same content under two filenames.
        a = self.svc.upload("a.txt", b"a" * 5000)
        b = self.svc.upload("b.txt", b"a" * 5000)
        # The chunks should match exactly.
        hashes_a = {c["hash"] for c in a.chunks}
        hashes_b = {c["hash"] for c in b.chunks}
        self.assertEqual(hashes_a, hashes_b)
        # The chunk store refcount should be > 1 for each chunk.
        for h in hashes_a:
            self.assertGreaterEqual(self.svc.chunk_store.refcount(h), 2)

    def test_versioning(self):
        self.svc.upload("v.txt", b"first")
        rec2 = self.svc.upload("v.txt", b"second")
        self.assertEqual(rec2.version, 2)
        # Listing shows latest
        all_files = self.svc.list_files()
        self.assertEqual(len(all_files), 1)
        self.assertEqual(all_files[0]["version"], 2)

    def test_get_chunk(self):
        rec = self.svc.upload("c.bin", b"chunkable data")
        h = rec.chunks[0]["hash"]
        data = self.svc.get_chunk(h)
        self.assertIsNotNone(data)
        self.assertEqual(len(data), rec.chunks[0]["size"])

    def test_get_missing(self):
        self.assertIsNone(self.svc.get_file("9999"))
        self.assertIsNone(self.svc.download("9999"))

    def test_large_file(self):
        # 1 MB file with 16 KB chunks
        data = os.urandom(1024 * 1024)
        rec = self.svc.upload("big.bin", data)
        out = self.svc.download(rec.id)
        self.assertEqual(out[1], data)

    def test_get_by_name(self):
        rec = self.svc.upload("name.txt", b"hi")
        rec2 = self.svc.get_by_name("name.txt")
        self.assertIsNotNone(rec2)
        self.assertEqual(rec2.id, rec.id)

    def test_stats(self):
        self.svc.upload("x", b"data1")
        self.svc.upload("y", b"data2")
        s = self.svc.stats()
        self.assertEqual(s["files"], 2)
        self.assertGreaterEqual(s["chunks"]["unique_chunks"], 1)


if __name__ == "__main__":
    unittest.main()
