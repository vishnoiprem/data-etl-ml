"""Web crawler HTTP service (Flask).

Run:
    PORT=8010 python3 10_web_crawler/code/app.py

Try:
    curl -X POST http://localhost:8010/api/crawl \
         -H 'Content-Type: application/json' \
         -d '{"seed": "https://example.com/", "max_pages": 10, "max_depth": 2}'

    curl http://localhost:8010/api/crawl/status
    curl 'http://localhost:8010/api/pages/https:%2F%2Fexample.com%2F'
    curl http://localhost:8010/metrics
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.cache import TTLCache  # noqa: E402
from common.ids import Snowflake  # noqa: E402
from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import (  # noqa: E402
    DEFAULT_HOST_DELAY_MS,
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_PAGES,
    InvalidURLError,
    WebCrawler,
    normalise_url,
)


def create_app(service: WebCrawler | None = None) -> Flask:
    app = Flask("web_crawler")
    if service is None:
        store = KeyValueStore(
            "web_crawler",
            persist_path=str(HERE / "var" / "web_crawler.json"),
        )
        cache = TTLCache(ttl_seconds=300.0, max_entries=2_000)
        service = WebCrawler(
            store=store,
            cache=cache,
            idgen=Snowflake(machine_id=10),
            host_delay_ms=DEFAULT_HOST_DELAY_MS,
        )
    svc = service
    metrics = MetricsRegistry()
    crawl_count = metrics.counter("crawl_total", "POST /api/crawl requests")
    fetch_count = metrics.counter("fetch_total", "pages fetched by the worker")
    page_lookup_count = metrics.counter("page_lookup_total", "GET /api/pages requests")
    fetch_latency = metrics.histogram("fetch_latency_ms", "page fetch latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/crawl")
    def start_crawl():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            seed = body.get("seed")
            if not seed:
                return jsonify({"error": "missing 'seed'"}), 400
            try:
                max_pages = int(body.get("max_pages", DEFAULT_MAX_PAGES))
                max_depth = int(body.get("max_depth", DEFAULT_MAX_DEPTH))
            except (TypeError, ValueError):
                return jsonify({"error": "max_pages/max_depth must be int"}), 400
            try:
                crawl = svc.start_crawl(seed, max_pages=max_pages, max_depth=max_depth)
            except InvalidURLError as e:
                return jsonify({"error": str(e)}), 400
            crawl_count.inc()
            return jsonify({
                "crawl_id": crawl.crawl_id,
                "seed": crawl.seed,
                "max_pages": crawl.max_pages,
                "max_depth": crawl.max_depth,
                "status": crawl.status,
            }), 201
        finally:
            fetch_latency.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/crawl/status")
    def crawl_status():
        return jsonify({
            "totals": svc.status(),
            "crawls": svc.list_crawls(),
        })

    @app.get("/api/crawl/<int:crawl_id>")
    def crawl_detail(crawl_id: int):
        data = svc.get_crawl(crawl_id)
        if data is None:
            return jsonify({"error": "not found"}), 404
        data["pages_list"] = svc.list_pages(crawl_id)
        return jsonify(data)

    @app.get("/api/pages/<path:url>")
    def get_page(url: str):
        page_lookup_count.inc()
        # Flask's <path:url> decodes %2F -> /. Re-parse.
        # The original request URL gives us the raw path.
        raw = request.path
        if raw.startswith("/api/pages/"):
            raw = raw[len("/api/pages/"):]
        # URL-decode.
        from urllib.parse import unquote
        candidate = unquote(raw)
        data = svc.get_page(candidate)
        if data is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(data)

    @app.get("/metrics")
    def metrics_endpoint():
        # Roll fetch count into the metrics surface each call.
        metrics_text = metrics.render()
        # Append the service's view of the frontier as a comment line.
        status = svc.status()
        metrics_text += f"# frontier_size {status['frontier']}\n"
        return metrics_text, 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "web_crawler",
            "endpoints": [
                "POST /api/crawl",
                "GET /api/crawl/status",
                "GET /api/crawl/<id>",
                "GET /api/pages/<url>",
                "GET /metrics",
                "GET /health",
            ],
            "status": svc.status(),
        })

    @app.errorhandler(404)
    def _nf(_e):
        return jsonify({"error": "not found"}), 404

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8010"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
