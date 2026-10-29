"""Flask HTTP service for the APM backend."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import APMService  # noqa: E402


def create_app(service: APMService | None = None) -> Flask:
    app = Flask("apm")
    svc = service or APMService()

    metrics = MetricsRegistry()
    metrics.counter("span_ingest_total", "spans ingested")
    metrics.histogram("trace_lookup_ms", "GET /api/traces latency")
    ingest_lat = metrics.histogram("span_ingest_latency_ms",
                                   "POST /api/spans latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/spans")
    def ingest_span():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                span = svc.ingest_span(
                    trace_id=body["trace_id"],
                    service=body["service"],
                    name=body["name"],
                    start_ms=body.get("start_ms"),
                    duration_ms=body.get("duration_ms", 0.0),
                    span_id=body.get("span_id"),
                    parent_span_id=body.get("parent_span_id", 0),
                    status=body.get("status", "ok"),
                    tags=body.get("tags") or {},
                )
            except (KeyError, ValueError) as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("span_ingest_total").inc()
            return jsonify(span), 201
        finally:
            ingest_lat.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/traces/<trace_id>")
    def get_trace(trace_id: str):
        start = time.perf_counter()
        try:
            return jsonify(svc.get_trace(trace_id))
        finally:
            metrics.histogram("trace_lookup_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/traces")
    def list_traces():
        return jsonify({"traces": svc.list_traces()})

    @app.get("/api/services")
    def list_services():
        return jsonify({"services": svc.list_services()})

    @app.get("/api/services/<name>/error_rate")
    def error_rate(name: str):
        try:
            window_s = int(request.args.get("window_s", "300"))
        except ValueError:
            window_s = 300
        with_lat = request.args.get("latency", "false").lower() == "true"
        return jsonify(svc.service_error_rate(name, window_s=window_s,
                                              with_latency=with_lat))

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "apm",
            "endpoints": [
                "POST /api/spans",
                "GET  /api/traces/<id>",
                "GET  /api/services",
                "GET  /api/services/<name>/error_rate",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8022"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
