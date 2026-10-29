"""Google-Docs HTTP service (Flask) with SSE stream for live ops."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request, stream_with_context  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import DocsService  # noqa: E402


def create_app(service: DocsService | None = None) -> Flask:
    app = Flask("docs")
    svc = service or DocsService()

    metrics = MetricsRegistry()
    metrics.histogram("op_latency_ms", "POST op latency")
    metrics.counter("ops_total", "ops applied")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/docs")
    def create_doc():
        body = request.get_json(force=True, silent=True) or {}
        try:
            d = svc.create_doc(str(body.get("title", "untitled")))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(d.to_dict()), 201

    @app.get("/api/docs/<int:doc_id>")
    def get_doc(doc_id: int):
        d = svc.get_doc(doc_id)
        if not d:
            return jsonify({"error": "not found"}), 404
        return jsonify(d.to_dict())

    @app.post("/api/docs/<int:doc_id>/ops")
    def apply_op(doc_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                r = svc.apply_op(
                    doc_id,
                    op=str(body["op"]),
                    pos=int(body["pos"]),
                    text=body.get("text"),
                    n=int(body.get("n", 0) or 0),
                    client_id=body.get("client_id"),
                    if_version=body.get("if_version"),
                )
            except (ValueError, KeyError) as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("ops_total").inc()
            return jsonify(r)
        finally:
            metrics.histogram("op_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/docs/<int:doc_id>/snapshot")
    def snapshot(doc_id: int):
        if not svc.get_doc(doc_id):
            return jsonify({"error": "not found"}), 404
        s = svc.snapshot(doc_id)
        return jsonify(s)

    @app.get("/api/docs/<int:doc_id>/ops")
    def list_ops(doc_id: int):
        if not svc.get_doc(doc_id):
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "doc_id": doc_id,
            "ops": [o.to_dict() for o in svc.get_ops(doc_id)],
        })

    @app.get("/api/docs/<int:doc_id>/stream")
    def stream(doc_id: int):
        q = svc.register_listener(doc_id)

        @stream_with_context
        def gen():
            try:
                yield "event: ready\ndata: {}\n\n"
                while True:
                    try:
                        evt = q.get(timeout=15.0)
                        yield f"event: op\ndata: {json.dumps(evt)}\n\n"
                    except Exception:
                        yield "event: ping\ndata: {}\n\n"
            finally:
                svc.unregister_listener(doc_id, q)

        return Response(gen(), mimetype="text/event-stream")

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "google-docs",
            "endpoints": [
                "POST /api/docs",
                "GET  /api/docs/<id>",
                "POST /api/docs/<id>/ops",
                "GET  /api/docs/<id>/snapshot",
                "GET  /api/docs/<id>/ops",
                "GET  /api/docs/<id>/stream   (SSE)",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8030"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
