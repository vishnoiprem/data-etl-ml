"""LLM Query Batching — Flask HTTP service (port 8036).

Endpoints:

    POST /api/queries                 -> {query_id}
    GET  /api/queries/<id>            -> {status: "pending"|"done", response, ...}
    GET  /api/queries/<id>?wait=1     -> blocks until the query is done
    POST /api/queries/flush           -> force a flush of the current window
    GET  /api/queries                 -> list recent queries
    GET  /stats                       -> batching metrics
    GET  /metrics, /health
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import BatchingService  # noqa: E402


def create_app(service: BatchingService | None = None) -> Flask:
    app = Flask("llm_batching")
    svc = service or BatchingService(
        batch_size=int(os.environ.get("BATCH_SIZE", "8")),
        window_ms=float(os.environ.get("WINDOW_MS", "25")),
    )
    metrics = MetricsRegistry()
    submit_hist = metrics.histogram("submit_latency_ms", "submit latency")
    fetch_hist = metrics.histogram("fetch_latency_ms", "fetch latency")
    submit_count = metrics.counter("queries_submitted_total", "queries submitted")
    done_count = metrics.counter("queries_completed_total", "queries completed")
    batch_count = metrics.counter("batches_total", "batches flushed")

    # ---- routes -------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/queries")
    def submit():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            prompt = body.get("prompt", "")
            max_tokens = body.get("max_tokens")
            if not prompt:
                return jsonify({"error": "prompt is required"}), 400
            qid = svc.submit(prompt, max_tokens=int(max_tokens) if max_tokens else None)
            submit_count.inc()
            return jsonify({"query_id": qid, "status": "pending"}), 202
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            submit_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/queries")
    def list_queries():
        return jsonify([q.to_dict() for q in svc.list_queries()])

    @app.get("/api/queries/<int:qid>")
    def get_query(qid: int):
        start = time.perf_counter()
        try:
            wait = request.args.get("wait") in ("1", "true", "yes")
            timeout = float(request.args.get("timeout", "5.0")) if wait else None
            q = svc.get(qid, timeout=timeout)
            if q is None:
                return jsonify({"error": "not found"}), 404
            if q.response is not None:
                done_count.inc()
            return jsonify({
                "query_id": q.query_id,
                "status": "done" if q.response is not None else "pending",
                "response": q.response,
                "tokens": q.tokens,
                "batch_id": q.batch_id,
                "wait_ms": round(q.wait_ms, 2),
            })
        finally:
            fetch_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/queries/flush")
    def flush():
        n = svc.flush_now()
        if n > 0:
            batch_count.inc()
        return jsonify({"flushed": n})

    @app.get("/stats")
    def stats():
        return jsonify(svc.stats())

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "llm_batching",
            "endpoints": [
                "POST /api/queries",
                "GET  /api/queries",
                "GET  /api/queries/<id>?wait=1&timeout=5",
                "POST /api/queries/flush",
                "GET  /stats",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8036"))
    app = create_app()
    try:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    finally:
        # Best-effort shutdown of the flusher.
        try:
            app.config.get("BATCHING_SVC", None)
        except Exception:  # pragma: no cover
            pass
