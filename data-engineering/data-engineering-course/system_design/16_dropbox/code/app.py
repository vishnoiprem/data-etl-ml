"""Dropbox-style file sync — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import (  # noqa: E402
    DEFAULT_CHUNK_SIZE,
    FileSyncService,
    FixedSizeChunker,
    RabinKarpChunker,
)


def create_app(service: FileSyncService | None = None) -> Flask:
    app = Flask("dropbox")
    service = service or FileSyncService(
        base_dir=str(HERE / "var" / "dropbox"),
        chunker=FixedSizeChunker(DEFAULT_CHUNK_SIZE),
    )
    metrics = MetricsRegistry()
    up_hist = metrics.histogram("upload_latency_ms", "POST /api/files latency")
    dl_hist = metrics.histogram("download_latency_ms", "GET /api/files/<id>/download latency")
    up_count = metrics.counter("upload_total", "Uploads")
    dl_count = metrics.counter("download_total", "Downloads")
    dedup_count = metrics.counter("deduped_chunks_total", "Chunks deduped on upload")
    new_count = metrics.counter("new_chunks_total", "New chunks written")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/files")
    def upload():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            filename = body.get("filename")
            content_b64 = body.get("content_b64")
            if not filename or content_b64 is None:
                return jsonify({"error": "filename and content_b64 are required"}), 400
            try:
                data = FileSyncService.decode_b64(content_b64)
            except Exception:
                return jsonify({"error": "content_b64 is not valid base64"}), 400
            rec = service.upload(filename, data)
            up_count.inc()
            # Count new vs deduped chunks
            for c in rec.chunks:
                rc = service.chunk_store.refcount(c["hash"])
                if rc > 1:
                    dedup_count.inc()
                else:
                    new_count.inc()
            return jsonify({
                "id": rec.id,
                "filename": rec.filename,
                "size": rec.size,
                "version": rec.version,
                "chunk_count": len(rec.chunks),
                "mtime": rec.mtime,
                "chunks": rec.chunks,
            }), 201
        finally:
            up_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/files")
    def list_files():
        return jsonify({"files": service.list_files()})

    @app.get("/api/files/<file_id>")
    def get_file(file_id: str):
        rec = service.get_file(file_id)
        if rec is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(rec.to_dict())

    @app.get("/api/files/<file_id>/download")
    def download(file_id: str):
        start = time.perf_counter()
        try:
            res = service.download(file_id)
            if res is None:
                return jsonify({"error": "not found"}), 404
            filename, data = res
            dl_count.inc()
            return jsonify({
                "filename": filename,
                "content_b64": FileSyncService.encode_b64(data),
                "size": len(data),
            })
        finally:
            dl_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/chunks/<h>")
    def get_chunk(h: str):
        data = service.get_chunk(h)
        if data is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "hash": h,
            "size": len(data),
            "content_b64": FileSyncService.encode_b64(data),
        })

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "dropbox",
            "endpoints": [
                "POST /api/files",
                "GET /api/files",
                "GET /api/files/<id>",
                "GET /api/files/<id>/download",
                "GET /api/chunks/<hash>",
                "GET /metrics",
                "GET /health",
            ],
            "stats": service.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8016"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
