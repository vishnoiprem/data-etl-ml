"""Distributed KV Store — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import KVCluster, KVStore  # noqa: E402


def create_app(service: KVStore | None = None) -> Flask:
    app = Flask("kv_store")
    persist_dir = str(HERE / "var" / "kv")
    svc = service or KVStore(
        cluster=KVCluster(
            servers=["s0", "s1", "s2"],
            replication=3,
            vnodes_per_server=128,
            persist_dir=persist_dir,
        )
    )
    metrics = MetricsRegistry()
    put_hist = metrics.histogram("put_latency_ms", "PUT latency")
    get_hist = metrics.histogram("get_latency_ms", "GET latency")
    put_count = metrics.counter("put_total", "PUT requests")
    get_count = metrics.counter("get_total", "GET requests")
    fallback = metrics.counter("replica_fallback_total", "Reads served by a replica")
    fail_count = metrics.counter("not_found_total", "Reads with no value")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/put")
    def put():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            key = body.get("key")
            value = body.get("value")
            if key is None:
                return jsonify({"error": "missing 'key'"}), 400
            if value is None:
                return jsonify({"error": "missing 'value'"}), 400
            require_acks = int(body.get("require_acks", 1))
            res = svc.put(key, value, require_acks=require_acks)
            put_count.inc()
            return jsonify({
                "key": res.key,
                "primary": res.primary,
                "replicas": res.replicas,
                "acks": res.acks,
                "total": res.total,
                "writes": [
                    {"server": w.server_id, "ok": w.ok, "error": w.error}
                    for w in res.writes
                ],
            }), 200
        finally:
            put_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/get/<key>")
    def get(key: str):
        start = time.perf_counter()
        try:
            quorum = int(request.args.get("quorum", "1"))
            res = svc.get(key, quorum=quorum)
            get_count.inc()
            if res.value is None:
                fail_count.inc()
                return jsonify({"error": "not found", "tried": res.tried}), 404
            if res.source and res.source != svc.cluster.primary_for(key):
                fallback.inc()
            return jsonify({
                "key": res.key,
                "value": res.value,
                "source": res.source,
                "replica_hits": res.replica_hits,
                "tried": res.tried,
            })
        finally:
            get_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/cluster/servers")
    def configure_servers():
        body = request.get_json(force=True, silent=True) or {}
        servers = body.get("servers") or ["s0", "s1", "s2"]
        replication = int(body.get("replication", 3))
        vnodes = int(body.get("vnodes", 128))
        # Rebuild cluster
        new_cluster = KVCluster(
            servers=servers, replication=replication, vnodes_per_server=vnodes,
            persist_dir=str(HERE / "var" / "kv"),
        )
        svc.cluster = new_cluster
        return jsonify(svc.cluster.stats())

    @app.post("/api/cluster/servers/<server_id>/fail")
    def fail_server(server_id: str):
        svc.cluster.fail(server_id)
        return jsonify(svc.cluster.stats())

    @app.post("/api/cluster/servers/<server_id>/revive")
    def revive_server(server_id: str):
        svc.cluster.revive(server_id)
        return jsonify(svc.cluster.stats())

    @app.get("/api/cluster")
    def cluster():
        return jsonify(svc.cluster.stats())

    @app.get("/api/ring")
    def ring():
        nodes = svc.cluster.ring.ring
        return jsonify({
            "size": len(nodes),
            "nodes": [{"position": n.position, "server": n.server_id} for n in nodes],
        })

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "kv_store",
            "endpoints": [
                "POST /api/put",
                "GET /api/get/<key>",
                "POST /api/cluster/servers",
                "POST /api/cluster/servers/<id>/fail",
                "POST /api/cluster/servers/<id>/revive",
                "GET /api/cluster",
                "GET /api/ring",
                "GET /metrics",
                "GET /health",
            ],
            "cluster": svc.cluster.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8013"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
