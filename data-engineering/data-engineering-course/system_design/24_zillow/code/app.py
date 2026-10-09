"""Flask HTTP service for the Zillow-style listings backend."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import ZillowService  # noqa: E402


def _f(name: str, default: float) -> float:
    v = request.args.get(name)
    if v is None or v == "":
        return default
    return float(v)


def _i(name: str, default: int) -> int:
    v = request.args.get(name)
    if v is None or v == "":
        return default
    return int(v)


def _fopt(name: str) -> float | None:
    v = request.args.get(name)
    return None if v is None or v == "" else float(v)


def _iopt(name: str) -> int | None:
    v = request.args.get(name)
    return None if v is None or v == "" else int(v)


def create_app(service: ZillowService | None = None) -> Flask:
    app = Flask("zillow")
    svc = service or ZillowService()

    metrics = MetricsRegistry()
    metrics.counter("create_listing_total", "listings created")
    metrics.counter("search_total", "search calls")
    search_lat = metrics.histogram("search_latency_ms", "GET /api/search")
    create_lat = metrics.histogram("create_latency_ms", "POST /api/listings")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/listings")
    def create_listing():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                rec = svc.create_listing(
                    lat=float(body["lat"]),
                    lng=float(body["lng"]),
                    price=float(body["price"]),
                    beds=int(body.get("beds", 0)),
                    baths=float(body.get("baths", 0.0)),
                    sqft=int(body.get("sqft", 0)),
                    address=body.get("address", ""),
                )
            except (KeyError, ValueError) as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("create_listing_total").inc()
            return jsonify(rec), 201
        finally:
            create_lat.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/listings/<listing_id>")
    def get_listing(listing_id: str):
        rec = svc.get_listing(listing_id)
        if not rec:
            return jsonify({"error": "not found"}), 404
        return jsonify(rec)

    @app.get("/api/search")
    def search():
        start = time.perf_counter()
        try:
            try:
                lat = _f("lat", 0.0)
                lng = _f("lng", 0.0)
            except ValueError:
                return jsonify({"error": "lat/lng must be numbers"}), 400
            try:
                res = svc.search(
                    lat=lat,
                    lng=lng,
                    radius_km=_f("radius_km", 5.0),
                    max_price=_fopt("max_price"),
                    min_beds=_iopt("min_beds"),
                    min_baths=_fopt("min_baths"),
                    min_sqft=_iopt("min_sqft"),
                    limit=_i("limit", 50),
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("search_total").inc()
            return jsonify(res)
        finally:
            search_lat.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "zillow",
            "endpoints": [
                "POST /api/listings",
                "GET  /api/listings/<id>",
                "GET  /api/search",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8024"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
