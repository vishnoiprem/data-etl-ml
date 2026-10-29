"""Messenger HTTP service (Flask) with SSE stream for delivery."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request, stream_with_context  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import MessengerService  # noqa: E402


def create_app(service: MessengerService | None = None) -> Flask:
    app = Flask("messenger")
    svc = service or MessengerService()

    metrics = MetricsRegistry()
    send_hist = metrics.histogram("send_latency_ms", "POST message latency")
    fetch_hist = metrics.histogram("fetch_latency_ms", "GET history latency")
    send_count = metrics.counter("messages_total", "messages sent")
    presence_count = metrics.counter("heartbeat_total", "heartbeats")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/conversations")
    def create_conv():
        body = request.get_json(force=True, silent=True) or {}
        try:
            c = svc.create_conversation(int(body["user_a"]), int(body["user_b"]))
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(c.to_dict()), 201

    @app.get("/api/conversations/<int:conv_id>")
    def get_conv(conv_id: int):
        c = svc.get_conversation(conv_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        return jsonify(c.to_dict())

    @app.post("/api/conversations/<int:conv_id>/messages")
    def send(conv_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                m = svc.send_message(
                    conv_id, int(body["sender_id"]), str(body.get("body", ""))
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            send_count.inc()
            return jsonify(m.to_dict()), 201
        finally:
            send_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/conversations/<int:conv_id>/messages")
    def fetch(conv_id: int):
        start = time.perf_counter()
        try:
            since_ts = float(request.args.get("since_ts", "0") or 0)
            limit = int(request.args.get("limit", "200"))
            msgs = svc.fetch_messages(conv_id, since_ts=since_ts, limit=limit)
            return jsonify({
                "conversation_id": conv_id,
                "messages": [m.to_dict() for m in msgs],
            })
        finally:
            fetch_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/users/<int:user_id>/inbox")
    def inbox(user_id: int):
        since_ts = float(request.args.get("since_ts", "0") or 0)
        limit = int(request.args.get("limit", "200"))
        msgs = svc.fetch_inbox(user_id, since_ts=since_ts, limit=limit)
        return jsonify({
            "user_id": user_id,
            "messages": [m.to_dict() for m in msgs],
        })

    @app.post("/api/users/<int:user_id>/heartbeat")
    def heartbeat(user_id: int):
        svc.heartbeat(user_id)
        presence_count.inc()
        return jsonify({"user_id": user_id, "online": True, "ttl": 30})

    @app.get("/api/users/<int:user_id>/presence")
    def presence(user_id: int):
        online = svc.is_online(user_id)
        return jsonify({
            "user_id": user_id,
            "online": online,
            "last_seen": svc.last_seen(user_id),
        })

    @app.get("/api/users/<int:user_id>/stream")
    def stream(user_id: int):
        """Server-Sent Events stream of new messages for this user."""
        q = svc.register_listener(user_id)
        last_beat = time.time()

        @stream_with_context
        def gen():
            nonlocal last_beat
            try:
                # Initial event so the client knows we're alive.
                yield "event: ready\ndata: {}\n\n"
                while True:
                    try:
                        evt = q.get(timeout=15.0)
                        yield f"event: message\ndata: {json.dumps(evt)}\n\n"
                    except Exception:
                        # Keep-alive ping every ~15s.
                        yield "event: ping\ndata: {}\n\n"
                        if time.time() - last_beat > 90:
                            break
            finally:
                svc.unregister_listener(user_id, q)

        return Response(gen(), mimetype="text/event-stream")

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "messenger",
            "endpoints": [
                "POST /api/conversations",
                "GET  /api/conversations/<id>",
                "POST /api/conversations/<id>/messages",
                "GET  /api/conversations/<id>/messages?since_ts=",
                "GET  /api/users/<id>/inbox?since_ts=",
                "POST /api/users/<id>/heartbeat",
                "GET  /api/users/<id>/presence",
                "GET  /api/users/<id>/stream   (SSE)",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8026"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
