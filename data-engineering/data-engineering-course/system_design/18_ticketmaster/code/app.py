"""Ticketmaster HTTP service (Flask)."""

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
    EventNotFound,
    HoldExpired,
    HoldTokenMismatch,
    SeatNotFound,
    SeatUnavailable,
    TicketmasterService,
    TicketmasterError,
)


def create_app(service: TicketmasterService | None = None) -> Flask:
    app = Flask("ticketmaster")
    svc = service or TicketmasterService()

    metrics = MetricsRegistry()
    metrics.histogram("hold_latency_ms", "POST hold latency")
    metrics.histogram("purchase_latency_ms", "POST purchase latency")
    metrics.histogram("seats_latency_ms", "GET seats latency")
    metrics.counter("hold_total", "hold attempts")
    metrics.counter("purchase_total", "purchases")
    metrics.counter("conflict_total", "seat conflicts")

    def _error(exc: TicketmasterError):
        return jsonify({"error": exc.code, "message": exc.message}), exc.http_status

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/events")
    def create_event():
        body = request.get_json(force=True, silent=True) or {}
        try:
            ev = svc.create_event(
                body["name"], int(body["rows"]), int(body["cols"])
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": "bad_request", "message": str(e)}), 400
        return jsonify(ev), 201

    @app.get("/api/events/<int:event_id>")
    def get_event(event_id: int):
        try:
            return jsonify(svc.get_event(event_id))
        except EventNotFound as e:
            return _error(e)

    @app.get("/api/events/<int:event_id>/seats")
    def list_seats(event_id: int):
        start = time.perf_counter()
        try:
            seats = svc.list_seats(event_id)
            return jsonify({"event_id": event_id, "seats": seats})
        except EventNotFound as e:
            return _error(e)
        finally:
            metrics.histogram("seats_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/events/<int:event_id>/seats/<seat_id>/hold")
    def hold(event_id: int, seat_id: str):
        start = time.perf_counter()
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body["user_id"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "user_id required"}), 400
        metrics.counter("hold_total").inc()
        try:
            res = svc.hold(event_id, seat_id, user_id)
            return jsonify(res), 201
        except (SeatNotFound, SeatUnavailable) as e:
            if isinstance(e, SeatUnavailable):
                metrics.counter("conflict_total").inc()
            return _error(e)
        finally:
            metrics.histogram("hold_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/events/<int:event_id>/seats/<seat_id>/purchase")
    def purchase(event_id: int, seat_id: str):
        start = time.perf_counter()
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body["user_id"])
            hold_token = int(body["hold_token"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "user_id and hold_token required"}), 400
        try:
            res = svc.purchase(event_id, seat_id, user_id, hold_token)
            metrics.counter("purchase_total").inc()
            return jsonify(res), 201
        except (SeatNotFound, SeatUnavailable, HoldExpired, HoldTokenMismatch) as e:
            if isinstance(e, SeatUnavailable):
                metrics.counter("conflict_total").inc()
            return _error(e)
        finally:
            metrics.histogram("purchase_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/events/<int:event_id>/seats/<seat_id>/release")
    def release(event_id: int, seat_id: str):
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body["user_id"])
            hold_token = int(body["hold_token"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "user_id and hold_token required"}), 400
        try:
            res = svc.release(event_id, seat_id, user_id, hold_token)
            return jsonify(res)
        except (SeatNotFound, SeatUnavailable, HoldTokenMismatch) as e:
            return _error(e)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "ticketmaster",
            "endpoints": [
                "POST /api/events",
                "GET  /api/events/<id>",
                "GET  /api/events/<id>/seats",
                "POST /api/events/<id>/seats/<seat_id>/hold",
                "POST /api/events/<id>/seats/<seat_id>/purchase",
                "POST /api/events/<id>/seats/<seat_id>/release",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8018"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
