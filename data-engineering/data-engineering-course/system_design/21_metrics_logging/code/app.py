"""Flask HTTP service for the Metrics + Logging backend."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import MetricsLoggingService  # noqa: E402


def create_app(service: MetricsLoggingService | None = None) -> Flask:
    app = Flask("metrics_logging")
    svc = service or MetricsLoggingService()

    metrics = MetricsRegistry()
    metrics.counter("ingest_total", "metric ingest calls")
    metrics.counter("log_ingest_total", "log ingest calls")
    metrics.histogram("query_latency_ms", "GET /api/query latency")
    metrics.histogram("log_search_latency_ms", "GET /api/logs latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/metrics")
    def ingest_metrics():
        body = request.get_json(force=True, silent=True) or {}
        metrics.counter("ingest_total").inc()
        if isinstance(body, list):
            n = svc.ingest_many(body)
            return jsonify({"ok": True, "ingested": n})
        try:
            res = svc.ingest_metric(
                body["name"],
                float(body["value"]),
                body.get("labels") or {},
                body.get("ts"),
            )
            return jsonify(res), 201
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/query")
    def query():
        start = time.perf_counter()
        try:
            metric = request.args.get("metric", "")
            if not metric:
                return jsonify({"error": "metric required"}), 400
            agg = request.args.get("agg", "avg")
            try:
                step = float(request.args.get("step", "60"))
                ts_from = float(request.args["from"])
                ts_to = float(request.args["to"])
            except (KeyError, ValueError):
                return jsonify({"error": "from/to/step must be numbers"}), 400
            label_filter = {
                k[len("label."):]: v
                for k, v in request.args.items()
                if k.startswith("label.")
            }
            return jsonify(svc.query(
                metric, ts_from, ts_to, step=step, agg=agg,
                label_filter=label_filter or None,
            ))
        finally:
            metrics.histogram("query_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/series")
    def list_series():
        metric = request.args.get("metric", "")
        if not metric:
            return jsonify({"error": "metric required"}), 400
        return jsonify({"metric": metric, "series": svc.list_series(metric)})

    @app.post("/api/logs")
    def ingest_log():
        body = request.get_json(force=True, silent=True) or {}
        metrics.counter("log_ingest_total").inc()
        try:
            res = svc.ingest_log(
                body["msg"],
                level=body.get("level", "info"),
                labels=body.get("labels") or {},
                ts=body.get("ts"),
            )
            return jsonify(res), 201
        except KeyError as e:
            return jsonify({"error": f"missing field: {e}"}), 400

    @app.get("/api/logs")
    def search_logs():
        start = time.perf_counter()
        try:
            q = request.args.get("q", "")
            try:
                limit = int(request.args.get("limit", "100"))
            except ValueError:
                limit = 100
            return jsonify({
                "q": q,
                "results": svc.search_logs(q, limit=limit),
            })
        finally:
            metrics.histogram("log_search_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "metrics_logging",
            "endpoints": [
                "POST /api/metrics",
                "GET  /api/query",
                "GET  /api/series",
                "POST /api/logs",
                "GET  /api/logs",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8021"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
