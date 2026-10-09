"""Uber Eats HTTP service (Flask).

A thin HTTP layer over :class:`code.service.UberEatsService`. The
endpoints follow ``design/README.md`` §4. State-transition errors
are mapped to HTTP 409.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make the `common` package importable when running as `python3 code/app.py`.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import (  # noqa: E402
    ACCEPTED,
    CANCELLED,
    DELIVERED,
    InvalidTransitionError,
    PICKED_UP,
    PLACED,
    UberEatsService,
)


def create_app(service: UberEatsService | None = None) -> Flask:
    """Build the Flask app. ``service`` is injectable for tests."""
    app = Flask("uber_eats")
    svc = service or UberEatsService()

    # ---- metrics --------------------------------------------------------
    metrics = MetricsRegistry()
    metrics.histogram("transition_latency_ms", "state transition latency")
    metrics.counter("restaurants_total", "restaurants created")
    metrics.counter("drivers_total", "drivers created")
    metrics.counter("orders_total", "orders placed")
    metrics.counter("accepts_total", "orders accepted")
    metrics.counter("pickups_total", "orders picked up")
    metrics.counter("deliveries_total", "orders delivered")
    metrics.counter("cancellations_total", "orders cancelled")
    metrics.counter("invalid_transitions_total", "illegal state moves rejected")

    # ---- health & index --------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/")
    def index():
        return jsonify({
            "service": "uber_eats",
            "design": "system_design/09_uber_eats/design/README.md",
            "endpoints": [
                "POST /api/restaurants",
                "GET  /api/restaurants",
                "GET  /api/restaurants/<id>",
                "POST /api/restaurants/<id>/menu",
                "POST /api/drivers",
                "GET  /api/drivers",
                "POST /api/orders",
                "GET  /api/orders?state=",
                "GET  /api/orders/<id>",
                "POST /api/orders/<id>/accept",
                "POST /api/orders/<id>/status",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    # ---- restaurants -----------------------------------------------------
    @app.post("/api/restaurants")
    def create_restaurant():
        body = request.get_json(force=True, silent=True) or {}
        try:
            r = svc.create_restaurant(
                name=body["name"],
                address=body["address"],
                lat=body["lat"],
                lng=body["lng"],
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400
        metrics.counter("restaurants_total").inc()
        return jsonify(r.to_dict()), 201

    @app.get("/api/restaurants")
    def list_restaurants():
        return jsonify({
            "restaurants": [r.to_dict() for r in svc.list_restaurants()]
        })

    @app.get("/api/restaurants/<int:rid>")
    def get_restaurant(rid: int):
        r = svc.get_restaurant(rid)
        if not r:
            return jsonify({"error": "not found"}), 404
        return jsonify(r.to_dict())

    @app.post("/api/restaurants/<int:rid>/menu")
    def add_menu_item(rid: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            item = svc.add_menu_item(
                restaurant_id=rid,
                name=body["name"],
                price_cents=int(body["price_cents"]),
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(item.to_dict()), 201

    # ---- drivers ---------------------------------------------------------
    @app.post("/api/drivers")
    def create_driver():
        body = request.get_json(force=True, silent=True) or {}
        try:
            d = svc.create_driver(
                name=body["name"],
                lat=body["lat"],
                lng=body["lng"],
                available=body.get("available", True),
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400
        metrics.counter("drivers_total").inc()
        return jsonify(d.to_dict()), 201

    @app.get("/api/drivers")
    def list_drivers():
        return jsonify({
            "drivers": [d.to_dict() for d in svc.list_drivers()]
        })

    # ---- orders ----------------------------------------------------------
    @app.post("/api/orders")
    def place_order():
        body = request.get_json(force=True, silent=True) or {}
        try:
            o = svc.place_order(
                eater_id=int(body["eater_id"]),
                restaurant_id=int(body["restaurant_id"]),
                items=body.get("items", []),
                address=body["address"],
                lat=body["lat"],
                lng=body["lng"],
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400
        metrics.counter("orders_total").inc()
        return jsonify(o.to_dict()), 201

    @app.get("/api/orders")
    def list_orders():
        state = request.args.get("state")
        return jsonify({
            "orders": [o.to_dict() for o in svc.list_orders(status=state)]
        })

    @app.get("/api/orders/<int:oid>")
    def get_order(oid: int):
        o = svc.get_order(oid)
        if not o:
            return jsonify({"error": "not found"}), 404
        return jsonify(o.to_dict())

    @app.post("/api/orders/<int:oid>/accept")
    def accept(oid: int):
        body = request.get_json(force=True, silent=True) or {}
        start = time.perf_counter()
        try:
            try:
                o = svc.accept_order(oid, int(body["driver_id"]))
            except InvalidTransitionError as e:
                metrics.counter("invalid_transitions_total").inc()
                return jsonify({"error": str(e)}), 409
            metrics.counter("accepts_total").inc()
            return jsonify(o.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            metrics.histogram("transition_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/orders/<int:oid>/status")
    def transition(oid: int):
        body = request.get_json(force=True, silent=True) or {}
        new_status = body.get("status", "")
        by = str(body.get("by", ""))
        note = str(body.get("note", ""))
        start = time.perf_counter()
        try:
            try:
                o = svc.transition(oid, new_status, by=by, note=note)
            except InvalidTransitionError as e:
                metrics.counter("invalid_transitions_total").inc()
                return jsonify({"error": str(e)}), 409
            # Counters
            if new_status == PICKED_UP:
                metrics.counter("pickups_total").inc()
            elif new_status == DELIVERED:
                metrics.counter("deliveries_total").inc()
            elif new_status == CANCELLED:
                metrics.counter("cancellations_total").inc()
            return jsonify(o.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            metrics.histogram("transition_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    # ---- metrics endpoint -----------------------------------------------
    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {
            "Content-Type": "text/plain; version=0.0.4"
        }

    return app


if __name__ == "__main__":
    # Module 09 port — default 8009.
    port = int(os.environ.get("PORT", "8009"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
