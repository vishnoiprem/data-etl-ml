"""Chunked File Uploader — Flask HTTP service (port 8035).

Endpoints:

    POST   /api/uploads/initiate                       -> {upload_id, chunk_size, ...}
    PUT    /api/uploads/<id>/chunks/<idx>              (binary body)
    GET    /api/uploads/<id>/status                    -> resumability info
    POST   /api/uploads/<id>/complete                  -> {file_id, ...}
    POST   /api/uploads/<id>/abort
    GET    /api/files                                  -> list files
    GET    /api/files/<file_id>/download               (binary stream)
    GET    /api/files/<file_id>                        -> metadata
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import FileUploader  # noqa: E402


def create_app(service: FileUploader | None = None) -> Flask:
    app = Flask("file_uploader")
    svc = service or FileUploader(
        store=KeyValueStore(
            "file_uploader",
            persist_path=str(HERE / "var" / "file_uploader.json"),
        ),
        root=str(HERE / "var"),
    )
    metrics = MetricsRegistry()
    init_hist = metrics.histogram("initiate_latency_ms", "initiate latency")
    chunk_hist = metrics.histogram("chunk_latency_ms", "PUT chunk latency")
    complete_hist = metrics.histogram("complete_latency_ms", "complete latency")
    init_count = metrics.counter("uploads_initiated_total", "uploads initiated")
    chunk_count = metrics.counter("chunks_received_total", "chunks received")
    complete_count = metrics.counter("uploads_completed_total", "uploads completed")
    abort_count = metrics.counter("uploads_aborted_total", "uploads aborted")
    bytes_count = metrics.counter("bytes_received_total", "bytes received")

    # ---- routes -------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/uploads/initiate")
    def initiate():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            filename = body.get("filename")
            size = body.get("size")
            content_type = body.get("content_type", "application/octet-stream")
            user_id = body.get("user_id", "anonymous")
            chunk_size = body.get("chunk_size")
            if not filename or size is None:
                return jsonify({"error": "filename and size are required"}), 400
            up = svc.initiate(
                filename=filename,
                size=int(size),
                content_type=content_type,
                user_id=user_id,
                chunk_size=int(chunk_size) if chunk_size else None,
            )
            init_count.inc()
            return jsonify(up.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            init_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.put("/api/uploads/<int:upload_id>/chunks/<int:idx>")
    def put_chunk(upload_id: int, idx: int):
        start = time.perf_counter()
        try:
            data = request.get_data(cache=False, as_text=False)
            svc.put_chunk(upload_id, idx, data)
            chunk_count.inc()
            bytes_count.inc(len(data))
            return jsonify({"ok": True, "idx": idx, "bytes": len(data)})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            chunk_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/uploads/<int:upload_id>/status")
    def status(upload_id: int):
        s = svc.status(upload_id)
        if s is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(s)

    @app.post("/api/uploads/<int:upload_id>/complete")
    def complete(upload_id: int):
        start = time.perf_counter()
        try:
            rec = svc.complete(upload_id)
            complete_count.inc()
            return jsonify(rec.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            complete_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/uploads/<int:upload_id>/abort")
    def abort(upload_id: int):
        ok = svc.abort(upload_id)
        if not ok:
            return jsonify({"error": "not found"}), 404
        abort_count.inc()
        return jsonify({"ok": True, "status": "aborted"})

    @app.get("/api/files")
    def list_files():
        user_id = request.args.get("user_id")
        return jsonify([f.to_dict() for f in svc.list_files(user_id=user_id)])

    @app.get("/api/files/<file_id>")
    def get_file(file_id: str):
        rec = svc.get_file(file_id)
        if not rec:
            return jsonify({"error": "not found"}), 404
        return jsonify(rec.to_dict())

    @app.get("/api/files/<file_id>/download")
    def download(file_id: str):
        try:
            data = svc.download(file_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        rec = svc.get_file(file_id)
        return Response(
            data,
            mimetype=rec.content_type if rec else "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{rec.filename if rec else file_id}"',
                "Content-Length": str(len(data)),
            },
        )

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "file_uploader",
            "endpoints": [
                "POST /api/uploads/initiate",
                "PUT  /api/uploads/<id>/chunks/<idx>",
                "GET  /api/uploads/<id>/status",
                "POST /api/uploads/<id>/complete",
                "POST /api/uploads/<id>/abort",
                "GET  /api/files",
                "GET  /api/files/<file_id>",
                "GET  /api/files/<file_id>/download",
                "GET  /metrics",
                "GET  /health",
            ],
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8035"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
