"""Flask HTTP service for the weather app."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import WeatherService  # noqa: E402


def create_app(service: WeatherService | None = None) -> Flask:
    app = Flask("weather")
    svc = service or WeatherService()

    metrics = MetricsRegistry()
    metrics.counter("weather_total", "weather calls")
    metrics.counter("cache_hit_total", "cache hits")
    metrics.counter("all_failed_total", "calls where all providers failed")
    lat_hist = metrics.histogram("weather_latency_ms", "GET /api/weather")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/api/weather")
    def weather():
        start = time.perf_counter()
        try:
            try:
                lat = float(request.args.get("lat", "0"))
                lng = float(request.args.get("lng", "0"))
            except ValueError:
                return jsonify({"error": "lat/lng must be numbers"}), 400
            nocache = request.args.get("nocache", "0") == "1"
            try:
                res = svc.get_weather(lat, lng, nocache=nocache)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            except RuntimeError as e:
                metrics.counter("all_failed_total").inc()
                return jsonify({"error": str(e)}), 503
            metrics.counter("weather_total").inc()
            if res.get("cache_hit"):
                metrics.counter("cache_hit_total").inc()
            return jsonify(res)
        finally:
            lat_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/providers")
    def providers():
        return jsonify({"providers": svc.provider_health()})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "weather",
            "endpoints": [
                "GET /api/weather?lat=&lng=",
                "GET /api/providers",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8025"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
