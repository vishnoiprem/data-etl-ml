"""URL Shortener — HTTP service (Flask).

This is the "thin wrapper" the design doc mentions. All real work is in
service.py. The HTTP layer exists so you can curl the system and see the
caching / redirection behavior end-to-end.

Run:
    python3 01_url_shortener/code/app.py            # http://localhost:8001

Try:
    curl -X POST http://localhost:8001/api/shorten \
         -H 'Content-Type: application/json' \
         -d '{"url": "https://example.com/some/very/long/path"}'

    curl -i http://localhost:8001/<key>             # 302 redirect
    curl    http://localhost:8001/api/stats/<key>
    curl    http://localhost:8001/metrics
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make `common` importable when launched directly.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, redirect, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import URLShortener  # noqa: E402


def create_app(service: URLShortener | None = None) -> Flask:
    app = Flask("url_shortener")
    svc = service or URLShortener(
        store=KeyValueStore("url_shortener", persist_path=str(HERE / "var" / "url_shortener.json")),
    )
    metrics = MetricsRegistry()
    shorten_hist = metrics.histogram("shorten_latency_ms", "POST /api/shorten latency")
    resolve_hist = metrics.histogram("resolve_latency_ms", "GET /<key> latency")
    shorten_count = metrics.counter("shorten_total", "shorten requests")
    resolve_count = metrics.counter("resolve_total", "resolve requests")
    cache_hit_count = metrics.counter("cache_hits", "cache hits")
    cache_miss_count = metrics.counter("cache_misses", "cache misses")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/shorten")
    def shorten():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            url = body.get("url")
            alias = body.get("alias")
            if not url:
                return jsonify({"error": "missing 'url'"}), 400
            rec = svc.shorten(url, alias=alias)
            shorten_count.inc()
            return jsonify({
                "key": rec.key,
                "short_url": f"{request.host_url.rstrip('/')}/{rec.key}",
                "is_alias": rec.is_alias,
                "created_at": rec.created_at,
            }), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            shorten_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/<key>")
    def resolve(key: str):
        start = time.perf_counter()
        try:
            rec = svc.resolve(key)
            if rec is None:
                resolve_count.inc()
                return jsonify({"error": "not found"}), 404
            if svc.cache.get(f"url:{key}") is not None:
                cache_hit_count.inc()
            else:
                cache_miss_count.inc()
            svc.record_click(key)
            resolve_count.inc()
            return redirect(rec.long_url, code=302)
        finally:
            resolve_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/stats/<key>")
    def stats(key: str):
        data = svc.stats(key)
        if data is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(data)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "url_shortener",
            "endpoints": [
                "POST /api/shorten",
                "GET /<key>",
                "GET /api/stats/<key>",
                "GET /metrics",
                "GET /health",
            ],
            "cache": svc.cache_stats(),
            "total": svc.total(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8001"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
