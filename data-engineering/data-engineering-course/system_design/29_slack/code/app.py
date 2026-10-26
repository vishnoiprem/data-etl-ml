"""Slack HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import SlackService  # noqa: E402


def create_app(service: SlackService | None = None) -> Flask:
    app = Flask("slack")
    svc = service or SlackService()

    metrics = MetricsRegistry()
    metrics.histogram("post_latency_ms", "POST message latency")
    metrics.histogram("search_latency_ms", "GET search latency")
    metrics.counter("messages_total", "messages posted")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/workspaces")
    def create_workspace():
        body = request.get_json(force=True, silent=True) or {}
        try:
            w = svc.create_workspace(str(body.get("name", "")))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(w.to_dict()), 201

    @app.post("/api/workspaces/<int:workspace_id>/channels")
    def create_channel(workspace_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            ch = svc.create_channel(
                workspace_id, str(body.get("name", "")), int(body["creator_id"])
            )
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(ch.to_dict()), 201

    @app.get("/api/workspaces/<int:workspace_id>/channels")
    def list_channels(workspace_id: int):
        chs = svc.channels_in(workspace_id)
        return jsonify({"workspace_id": workspace_id, "channels": [c.to_dict() for c in chs]})

    @app.post("/api/channels/<int:channel_id>/messages")
    def post(channel_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                m = svc.post_message(
                    channel_id,
                    int(body["user_id"]),
                    str(body.get("body", "")),
                    thread_to=body.get("thread_to"),
                )
            except (ValueError, KeyError) as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("messages_total").inc()
            return jsonify(m.to_dict()), 201
        finally:
            metrics.histogram("post_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/channels/<int:channel_id>/messages")
    def list_messages(channel_id: int):
        since_ts = float(request.args.get("since_ts", "0") or 0)
        limit = int(request.args.get("limit", "100"))
        msgs = svc.fetch_messages(channel_id, since_ts=since_ts, limit=limit)
        return jsonify({
            "channel_id": channel_id,
            "messages": [m.to_dict() for m in msgs],
        })

    @app.get("/api/channels/<int:channel_id>/threads/<int:msg_id>")
    def thread(channel_id: int, msg_id: int):
        parent = svc.get_message(msg_id)
        if not parent or parent.channel_id != channel_id:
            return jsonify({"error": "parent not found in channel"}), 404
        replies = svc.fetch_thread(msg_id)
        return jsonify({
            "parent": parent.to_dict(),
            "replies": [r.to_dict() for r in replies],
        })

    @app.get("/api/users/<int:user_id>/mentions")
    def mentions(user_id: int):
        limit = int(request.args.get("limit", "100"))
        msgs = svc.fetch_mentions(user_id, limit=limit)
        return jsonify({
            "user_id": user_id,
            "mentions": [m.to_dict() for m in msgs],
        })

    @app.get("/api/search")
    def search():
        start = time.perf_counter()
        try:
            q = str(request.args.get("q", ""))
            limit = int(request.args.get("limit", "50"))
            results = svc.search(q, limit=limit)
            return jsonify({
                "q": q,
                "results": [m.to_dict() for m in results],
            })
        finally:
            metrics.histogram("search_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "slack",
            "endpoints": [
                "POST /api/workspaces",
                "POST /api/workspaces/<id>/channels",
                "GET  /api/workspaces/<id>/channels",
                "POST /api/channels/<id>/messages",
                "GET  /api/channels/<id>/messages",
                "GET  /api/channels/<id>/threads/<msg_id>",
                "GET  /api/users/<id>/mentions",
                "GET  /api/search?q=",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8029"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
