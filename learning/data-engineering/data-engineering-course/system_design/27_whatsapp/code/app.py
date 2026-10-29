"""WhatsApp HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import WhatsAppService  # noqa: E402


def create_app(service: WhatsAppService | None = None) -> Flask:
    app = Flask("whatsapp")
    svc = service or WhatsAppService()

    metrics = MetricsRegistry()
    metrics.histogram("send_latency_ms", "POST message latency")
    metrics.histogram("fetch_latency_ms", "GET history latency")
    metrics.counter("messages_total", "messages sent")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/groups")
    def create_group():
        body = request.get_json(force=True, silent=True) or {}
        try:
            g = svc.create_group(
                name=str(body.get("name", "")),
                creator_id=int(body["creator_id"]),
                members=list(body.get("members", []) or []),
            )
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(g.to_dict()), 201

    @app.get("/api/groups/<int:group_id>")
    def get_group(group_id: int):
        g = svc.get_group(group_id)
        if not g:
            return jsonify({"error": "not found"}), 404
        return jsonify(g.to_dict())

    @app.post("/api/groups/<int:group_id>/members")
    def add_member(group_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            g = svc.add_member(group_id, int(body["user_id"]))
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(g.to_dict())

    @app.delete("/api/groups/<int:group_id>/members/<int:user_id>")
    def remove_member(group_id: int, user_id: int):
        try:
            g = svc.remove_member(group_id, user_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(g.to_dict())

    @app.post("/api/groups/<int:group_id>/messages")
    def send_message(group_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                m = svc.send_message(
                    group_id=group_id,
                    sender_id=int(body["sender_id"]),
                    body=str(body.get("body", "") or ""),
                    media_url=body.get("media_url"),
                    media_b64=body.get("media_b64"),
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("messages_total").inc()
            return jsonify(m.to_dict()), 201
        finally:
            metrics.histogram("send_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/groups/<int:group_id>/messages")
    def fetch(group_id: int):
        start = time.perf_counter()
        try:
            since_ts = float(request.args.get("since_ts", "0") or 0)
            limit = int(request.args.get("limit", "200"))
            msgs = svc.fetch_messages(group_id, since_ts=since_ts, limit=limit)
            return jsonify({
                "group_id": group_id,
                "messages": [m.to_dict() for m in msgs],
            })
        finally:
            metrics.histogram("fetch_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/users/<int:user_id>/groups")
    def user_groups(user_id: int):
        groups = svc.groups_for(user_id)
        return jsonify({
            "user_id": user_id,
            "groups": [g.to_dict() for g in groups],
        })

    @app.get("/api/users/<int:user_id>/inbox")
    def inbox(user_id: int):
        since_ts = float(request.args.get("since_ts", "0") or 0)
        limit = int(request.args.get("limit", "200"))
        msgs = svc.fetch_inbox(user_id, since_ts=since_ts, limit=limit)
        return jsonify({
            "user_id": user_id,
            "messages": [m.to_dict() for m in msgs],
        })

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "whatsapp",
            "endpoints": [
                "POST /api/groups",
                "GET  /api/groups/<id>",
                "POST /api/groups/<id>/members",
                "DELETE /api/groups/<id>/members/<user_id>",
                "POST /api/groups/<id>/messages",
                "GET  /api/groups/<id>/messages?since_ts=",
                "GET  /api/users/<id>/groups",
                "GET  /api/users/<id>/inbox",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8027"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
