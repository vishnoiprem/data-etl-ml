"""Flask HTTP service for the document processing pipeline."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import DocumentService  # noqa: E402


def create_app(service: DocumentService | None = None) -> Flask:
    app = Flask("docproc")
    svc = service or DocumentService()

    metrics = MetricsRegistry()
    metrics.counter("upload_total", "documents uploaded")
    metrics.counter("search_total", "search queries")
    upload_lat = metrics.histogram("upload_latency_ms", "POST /api/documents")
    search_lat = metrics.histogram("search_latency_ms", "GET /api/search")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/documents")
    def upload():
        import time
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                rec = svc.upload(body.get("content", ""),
                                 doc_type=body.get("type", "text"))
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("upload_total").inc()
            return jsonify(rec), 201
        finally:
            upload_lat.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/documents/<doc_id>")
    def get_doc(doc_id: str):
        rec = svc.get(doc_id)
        if not rec:
            return jsonify({"error": "not found"}), 404
        # Don't echo content back at full size.
        out = {k: v for k, v in rec.items() if k != "content"}
        out["content_length"] = len(rec.get("content", ""))
        return jsonify(out)

    @app.get("/api/documents/<doc_id>/entities")
    def get_entities(doc_id: str):
        return jsonify({"id": doc_id, "entities": svc.entities(doc_id)})

    @app.get("/api/search")
    def search():
        import time
        start = time.perf_counter()
        try:
            q = request.args.get("q", "")
            try:
                limit = int(request.args.get("limit", "25"))
            except ValueError:
                limit = 25
            metrics.counter("search_total").inc()
            return jsonify({"q": q, "results": svc.search(q, limit=limit)})
        finally:
            search_lat.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "docproc",
            "endpoints": [
                "POST /api/documents",
                "GET  /api/documents/<id>",
                "GET  /api/documents/<id>/entities",
                "GET  /api/search",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8023"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
