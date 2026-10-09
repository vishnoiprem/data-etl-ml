"""Typeahead HTTP service (Flask).

Run:
    python3 02_typeahead/code/app.py            # http://localhost:8002

Try:
    curl 'http://localhost:8002/suggest?q=fla&k=5'
    curl -X POST http://localhost:8002/api/reload
    curl    http://localhost:8002/metrics
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

from .service import TypeaheadService  # noqa: E402


def create_app(service: TypeaheadService | None = None) -> Flask:
    app = Flask("typeahead")
    svc = service or TypeaheadService()
    if not svc.stats().get("trie_nodes", 0):
        svc.load_default()

    metrics = MetricsRegistry()
    hist = metrics.histogram("suggest_latency_ms", "GET /suggest latency")
    count = metrics.counter("suggest_total", "suggest requests")

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/suggest")
    def suggest():
        start = time.perf_counter()
        try:
            q = request.args.get("q", "")
            k = int(request.args.get("k", "10"))
            out = svc.suggest(q, k=k)
            count.inc()
            return jsonify({
                "q": q,
                "k": k,
                "suggestions": [{"word": w, "freq": f} for w, f in out],
            })
        finally:
            hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/reload")
    def reload():
        t0 = time.time()
        ok = svc.load_default()
        return jsonify({"loaded": ok, "ms": int((time.time() - t0) * 1000),
                        "stats": svc.stats()})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "typeahead",
            "stats": svc.stats(),
            "endpoints": ["/suggest", "/api/reload", "/metrics", "/health"],
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8002"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
