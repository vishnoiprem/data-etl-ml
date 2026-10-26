"""Distributed Rate Limiter — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import RateLimiter, STRATEGIES  # noqa: E402


def create_app(limiter: RateLimiter | None = None) -> Flask:
    app = Flask("rate_limiter")
    limiter = limiter or RateLimiter(capacity=100_000)
    metrics = MetricsRegistry()
    check_hist = metrics.histogram("check_latency_ms", "POST /api/check latency")
    allow_count = metrics.counter("allow_total", "Allowed checks")
    deny_count = metrics.counter("deny_total", "Denied checks")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/check")
    def check():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            key = body.get("key")
            limit = body.get("limit")
            window = body.get("window_seconds")
            strategy = body.get("strategy", "token_bucket")
            cost = int(body.get("cost", 1))
            if key is None or limit is None or window is None:
                return jsonify({"error": "key, limit, window_seconds are required"}), 400
            d = limiter.check(
                key=key,
                limit=int(limit),
                window_seconds=float(window),
                strategy=strategy,
                cost=cost,
            )
            (allow_count if d.allowed else deny_count).inc()
            return jsonify({
                "allowed": d.allowed,
                "remaining": d.remaining,
                "reset_in": d.reset_in,
                "strategy": d.strategy,
                "limit": d.limit,
                "cost": d.cost,
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            check_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/keys/<key>")
    def inspect(key: str):
        strategy = request.args.get("strategy", "token_bucket")
        info = limiter.inspect(key, strategy=strategy)
        return jsonify(info)

    @app.delete("/api/keys/<key>")
    def reset(key: str):
        strategy = request.args.get("strategy")
        n = limiter.reset(key=key, strategy=strategy)
        return jsonify({"removed": n})

    @app.get("/api/strategies")
    def strategies():
        return jsonify({"available": sorted(STRATEGIES.keys())})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "rate_limiter",
            "endpoints": [
                "POST /api/check",
                "GET /api/keys/<key>?strategy=...",
                "DELETE /api/keys/<key>",
                "GET /api/strategies",
                "GET /metrics",
                "GET /health",
            ],
            "stats": limiter.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8014"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
