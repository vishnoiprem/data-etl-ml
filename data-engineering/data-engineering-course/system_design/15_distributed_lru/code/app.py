"""Distributed LRU Cache — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import DistributedLRU  # noqa: E402


def create_app(cache: DistributedLRU | None = None) -> Flask:
    app = Flask("distributed_lru")
    cache = cache or DistributedLRU(
        nodes=["n0", "n1", "n2", "n3"],
        capacity_per_node=10_000,
        vnodes_per_node=64,
    )
    metrics = MetricsRegistry()
    put_hist = metrics.histogram("put_latency_ms", "PUT /api/cache/<key> latency")
    get_hist = metrics.histogram("get_latency_ms", "GET /api/cache/<key> latency")
    put_count = metrics.counter("put_total", "PUT requests")
    get_count = metrics.counter("get_total", "GET requests")
    local_hit = metrics.counter("local_hits", "Local LRU hits")
    peer_miss = metrics.counter("peer_misses", "Misses (simulated peer fetch)")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.put("/api/cache/<key>")
    def put(key: str):
        start = time.perf_counter()
        try:
            # Accept either JSON body or plain text
            data = request.get_json(force=True, silent=True)
            if data is None:
                data = request.get_data(as_text=True) or ""
            res = cache.put(key, data)
            put_count.inc()
            if not res["stored"]:
                return jsonify(res), 503
            return jsonify(res), 200
        finally:
            put_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/cache/<key>")
    def get(key: str):
        start = time.perf_counter()
        try:
            res = cache.get(key)
            get_count.inc()
            if res.hit:
                local_hit.inc()
                return jsonify(res.to_dict()), 200
            peer_miss.inc()
            return jsonify(res.to_dict()), 404
        finally:
            get_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.delete("/api/cache/<key>")
    def delete(key: str):
        ok = cache.delete(key)
        return jsonify({"key": key, "removed": ok}), 200

    @app.get("/api/nodes")
    def nodes():
        return jsonify(cache.cluster_stats())

    @app.get("/api/ring")
    def ring():
        return jsonify({"ring": cache.ring(), "size": len(cache.ring())})

    @app.get("/api/locate/<key>")
    def locate(key: str):
        owner = cache.locate(key)
        return jsonify({"key": key, "owner": owner})

    @app.post("/api/nodes/<node_id>/fail")
    def fail_node(node_id: str):
        cache.fail_node(node_id)
        return jsonify(cache.cluster_stats())

    @app.post("/api/nodes/<node_id>/revive")
    def revive_node(node_id: str):
        cache.revive_node(node_id)
        return jsonify(cache.cluster_stats())

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "distributed_lru",
            "endpoints": [
                "PUT /api/cache/<key>",
                "GET /api/cache/<key>",
                "DELETE /api/cache/<key>",
                "GET /api/nodes",
                "GET /api/ring",
                "GET /api/locate/<key>",
                "POST /api/nodes/<id>/fail",
                "POST /api/nodes/<id>/revive",
                "GET /metrics",
                "GET /health",
            ],
            "cluster": cache.cluster_stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8015"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
