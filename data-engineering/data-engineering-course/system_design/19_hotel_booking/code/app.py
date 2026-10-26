"""Hotel Booking HTTP service (Flask)."""

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
    BookingNotFound,
    HotelBookingError,
    HotelBookingService,
    HotelNotFound,
    InvalidDateRange,
    NotAuthorized,
    RoomNotFound,
    RoomUnavailable,
)


def create_app(service: HotelBookingService | None = None) -> Flask:
    app = Flask("hotel_booking")
    svc = service or HotelBookingService()

    metrics = MetricsRegistry()
    metrics.histogram("book_latency_ms", "POST /api/rooms/<id>/book latency")
    metrics.histogram("availability_latency_ms", "GET availability latency")
    metrics.counter("book_total", "booking attempts")
    metrics.counter("book_success_total", "successful bookings")
    metrics.counter("conflict_total", "room conflicts")

    def _error(exc: HotelBookingError):
        body = {"error": exc.code, "message": exc.message}
        if isinstance(exc, RoomUnavailable):
            body["conflicts"] = exc.conflicts
        return jsonify(body), exc.http_status

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/hotels")
    def create_hotel():
        body = request.get_json(force=True, silent=True) or {}
        try:
            h = svc.create_hotel(body["name"], body["city"])
            return jsonify(h), 201
        except (KeyError, ValueError) as e:
            return jsonify({"error": "bad_request", "message": str(e)}), 400

    @app.get("/api/hotels")
    def list_hotels():
        return jsonify({"hotels": svc.list_hotels()})

    @app.get("/api/hotels/<int:hotel_id>")
    def get_hotel(hotel_id: int):
        try:
            return jsonify(svc.get_hotel(hotel_id))
        except HotelNotFound as e:
            return _error(e)

    @app.post("/api/hotels/<int:hotel_id>/rooms")
    def create_room(hotel_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            r = svc.create_room(
                hotel_id=hotel_id,
                room_number=body["room_number"],
                capacity=int(body.get("capacity", 2)),
                price_cents=int(body.get("price_cents", 10_000)),
            )
            return jsonify(r), 201
        except HotelNotFound as e:
            return _error(e)
        except (KeyError, ValueError) as e:
            return jsonify({"error": "bad_request", "message": str(e)}), 400

    @app.get("/api/hotels/<int:hotel_id>/rooms")
    def list_rooms(hotel_id: int):
        try:
            return jsonify({"hotel_id": hotel_id, "rooms": svc.list_rooms(hotel_id)})
        except HotelNotFound as e:
            return _error(e)

    @app.post("/api/rooms/<int:room_id>/book")
    def book(room_id: int):
        start = time.perf_counter()
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body["user_id"])
            check_in = body["check_in"]
            check_out = body["check_out"]
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "user_id, check_in, check_out required"}), 400
        metrics.counter("book_total").inc()
        try:
            b = svc.book(room_id, user_id, check_in, check_out)
            metrics.counter("book_success_total").inc()
            return jsonify(b), 201
        except (RoomNotFound, RoomUnavailable, InvalidDateRange) as e:
            if isinstance(e, RoomUnavailable):
                metrics.counter("conflict_total").inc()
            return _error(e)
        finally:
            metrics.histogram("book_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/rooms/<int:room_id>/availability")
    def availability(room_id: int):
        start = time.perf_counter()
        frm = request.args.get("from", "")
        to = request.args.get("to", "")
        if not frm or not to:
            return jsonify({"error": "bad_request", "message": "from and to required"}), 400
        try:
            res = svc.availability(room_id, frm, to)
            return jsonify(res)
        except (RoomNotFound, InvalidDateRange) as e:
            return _error(e)
        finally:
            metrics.histogram("availability_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/bookings/<int:booking_id>/cancel")
    def cancel(booking_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body["user_id"])
        except (KeyError, ValueError, TypeError):
            return jsonify({"error": "bad_request", "message": "user_id required"}), 400
        try:
            res = svc.cancel(booking_id, user_id)
            return jsonify(res)
        except (BookingNotFound, NotAuthorized) as e:
            return _error(e)

    @app.get("/api/bookings/<int:booking_id>")
    def get_booking(booking_id: int):
        try:
            return jsonify(svc.get_booking(booking_id))
        except BookingNotFound as e:
            return _error(e)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "hotel_booking",
            "endpoints": [
                "POST /api/hotels",
                "GET  /api/hotels",
                "GET  /api/hotels/<id>",
                "POST /api/hotels/<id>/rooms",
                "GET  /api/hotels/<id>/rooms",
                "POST /api/rooms/<id>/book",
                "GET  /api/rooms/<id>/availability?from=&to=",
                "POST /api/bookings/<id>/cancel",
                "GET  /api/bookings/<id>",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8019"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
