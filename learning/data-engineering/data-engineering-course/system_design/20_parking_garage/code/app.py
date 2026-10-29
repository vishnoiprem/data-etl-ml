"""Parking Garage HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import (  # noqa: E402
    GarageFull,
    ParkingError,
    ParkingGarageService,
    TicketAlreadyClosed,
    TicketNotFound,
)


def create_app(service: ParkingGarageService | None = None) -> Flask:
    app = Flask("parking_garage")
    svc = service or ParkingGarageService()

    metrics = MetricsRegistry()
    metrics.histogram("checkin_latency_ms", "POST /api/checkin latency")
    metrics.histogram("checkout_latency_ms", "POST /api/checkout latency")
    metrics.histogram("availability_latency_ms", "GET availability latency")
    metrics.counter("checkin_total", "check-ins")
    metrics.counter("checkout_total", "check-outs")
    metrics.counter("garage_full_total", "garage-full rejections")

    def _error(exc: ParkingError):
        return jsonify({"error": exc.code, "message": exc.message}), exc.http_status

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/checkin")
    def checkin():
        start = time.perf_counter()
        body = request.get_json(force=True, silent=True) or {}
        try:
            vehicle_id = int(body["vehicle_id"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "vehicle_id required"}), 400
        preferred = body.get("preferred_type")
        try:
            s = svc.checkin(vehicle_id, preferred_type=preferred)
            metrics.counter("checkin_total").inc()
            return jsonify(s), 201
        except GarageFull as e:
            metrics.counter("garage_full_total").inc()
            return _error(e)
        finally:
            metrics.histogram("checkin_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/checkout")
    def checkout():
        start = time.perf_counter()
        body = request.get_json(force=True, silent=True) or {}
        try:
            ticket_id = int(body["ticket_id"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "ticket_id required"}), 400
        try:
            s = svc.checkout(ticket_id)
            metrics.counter("checkout_total").inc()
            return jsonify(s)
        except (TicketNotFound, TicketAlreadyClosed) as e:
            return _error(e)
        finally:
            metrics.histogram("checkout_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/availability")
    def availability():
        start = time.perf_counter()
        try:
            return jsonify(svc.availability())
        finally:
            metrics.histogram("availability_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/tickets/<int:ticket_id>")
    def get_ticket(ticket_id: int):
        try:
            return jsonify(svc.get_ticket(ticket_id))
        except TicketNotFound as e:
            return _error(e)

    @app.get("/api/tickets")
    def list_tickets():
        return jsonify({"active_sessions": svc.list_active_sessions()})

    @app.get("/api/spots")
    def list_spots():
        return jsonify({"spots": svc.list_spots()})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "parking_garage",
            "endpoints": [
                "POST /api/checkin",
                "POST /api/checkout",
                "GET  /api/availability",
                "GET  /api/tickets",
                "GET  /api/tickets/<id>",
                "GET  /api/spots",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8020"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
