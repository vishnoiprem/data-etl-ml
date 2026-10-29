"""Twitch-style live streaming + chat service — HTTP layer (Flask).

This is the thin wrapper around `TwitchService`. The HTTP layer
is intentionally small: parse, delegate, return JSON. All real
work lives in `service.py`. The one exception is the SSE endpoint
which streams chat fanout from in-process subscriber queues.

Run:
    PORT=8032 python3 32_twitch/code/app.py

Try:
    curl -X POST http://localhost:8032/api/users \
         -H 'Content-Type: application/json' \
         -d '{"name": "alice"}'

    curl -X POST http://localhost:8032/api/streams \
         -H 'Content-Type: application/json' \
         -d '{"user_id": <id>, "title": "playing zelda", "game": "zelda"}'

    curl -X POST http://localhost:8032/api/streams/<id>/chat \
         -H 'Content-Type: application/json' \
         -d '{"user_id": <id>, "body": "hi chat"}'

    curl "http://localhost:8032/api/streams/<id>/chat/sse?user_id=<id>"
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Make `common` importable when launched directly.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request, stream_with_context  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import TwitchService  # noqa: E402


def create_app(service: TwitchService | None = None) -> Flask:
    app = Flask("twitch_service")
    svc = service or TwitchService(
        store=KeyValueStore(
            "twitch_service",
            persist_path=str(HERE / "var" / "twitch_service.json"),
        ),
    )
    metrics = MetricsRegistry()
    user_count = metrics.counter("user_total", "users created")
    stream_start_count = metrics.counter(
        "stream_start_total", "streams started"
    )
    stream_end_count = metrics.counter("stream_end_total", "streams ended")
    chat_post_count = metrics.counter("chat_post_total", "chat messages")
    chat_get_count = metrics.counter("chat_get_total", "chat reads")
    hb_count = metrics.counter("heartbeat_total", "viewer heartbeats")
    sse_count = metrics.counter("sse_total", "SSE chat connections")

    sse_hist = metrics.histogram("sse_duration_ms", "SSE connection duration")
    chat_hist = metrics.histogram("chat_post_latency_ms", "POST chat")

    # ---- index + health + metrics ------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "service": "twitch_service",
            "endpoints": [
                "POST /api/users",
                "POST /api/streams",
                "POST /api/streams/<id>/end",
                "GET /api/streams/<id>",
                "GET /api/streams?game=",
                "GET /api/streams/<id>/chat",
                "POST /api/streams/<id>/chat",
                "GET /api/streams/<id>/chat/sse",
                "POST /api/streams/<id>/heartbeat",
                "GET /api/streams/<id>/viewers",
                "GET /metrics",
                "GET /health",
            ],
            "total_streams": svc.total_streams(),
            "live_streams": svc.live_streams(),
        })

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.get("/metrics")
    def metrics_endpoint():
        return (
            metrics.render(),
            200,
            {"Content-Type": "text/plain; version=0.0.4"},
        )

    # ---- users -------------------------------------------------------

    @app.post("/api/users")
    def create_user():
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        try:
            user = svc.create_user(name or "")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        user_count.inc()
        return jsonify(user.to_dict()), 201

    # ---- streams -----------------------------------------------------

    @app.post("/api/streams")
    def start_stream():
        body = request.get_json(force=True, silent=True) or {}
        user_id = body.get("user_id")
        title = body.get("title") or ""
        game = body.get("game") or ""
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id must be an int"}), 400
        try:
            stream = svc.start_stream(user_id, title, game)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        stream_start_count.inc()
        return jsonify(stream.to_dict()), 201

    @app.post("/api/streams/<int:stream_id>/end")
    def end_stream(stream_id: int):
        s = svc.end_stream(stream_id)
        if s is None:
            return jsonify({"error": "stream not found"}), 404
        stream_end_count.inc()
        return jsonify(s.to_dict())

    @app.get("/api/streams/<int:stream_id>")
    def get_stream(stream_id: int):
        s = svc.get_stream(stream_id)
        if s is None:
            return jsonify({"error": "not found"}), 404
        body = s.to_dict()
        body["viewers"] = svc.viewer_count(stream_id)
        return jsonify(body)

    @app.get("/api/streams")
    def list_streams():
        game = request.args.get("game")
        include_ended = request.args.get(
            "include_ended", default="false"
        ).lower() == "true"
        results = svc.list_streams(
            game=game, live_only=not include_ended
        )
        return jsonify({
            "game": game,
            "live_only": not include_ended,
            "results": [s.to_dict() for s in results],
        })

    # ---- chat --------------------------------------------------------

    @app.post("/api/streams/<int:stream_id>/chat")
    def post_chat(stream_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            text = body.get("body") or ""
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                return (
                    jsonify({"error": "user_id must be an int"}),
                    400,
                )
            try:
                msg = svc.post_chat(stream_id, user_id, text)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            chat_post_count.inc()
            return jsonify(msg.to_dict()), 201
        finally:
            chat_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/streams/<int:stream_id>/chat")
    def get_chat(stream_id: int):
        limit = request.args.get("limit", default=100, type=int) or 100
        results = svc.get_chat_log(stream_id, limit=limit)
        chat_get_count.inc()
        return jsonify({
            "stream_id": stream_id,
            "limit": limit,
            "results": results,
        })

    @app.get("/api/streams/<int:stream_id>/chat/sse")
    def chat_sse(stream_id: int):
        """Server-Sent Events stream of chat for a given stream.

        Sends an initial ``event: hello`` line, then one
        ``event: chat`` line per message until the stream ends
        (which sends an ``event: end`` sentinel). A 15-second
        keepalive comment is sent if no messages arrive.
        """
        sse_count.inc()
        s = svc.get_stream(stream_id)
        if s is None:
            return jsonify({"error": "stream not found"}), 404

        sub_id, q = svc.subscribe(stream_id)
        start = time.perf_counter()

        def gen():
            try:
                # Initial hello so the client knows we're connected.
                yield (
                    f"event: hello\n"
                    f"data: {json.dumps({'stream_id': stream_id, 'ts': time.time()})}\n\n"
                )
                last_keepalive = time.time()
                while True:
                    try:
                        payload = q.get(timeout=1.0)
                    except Exception:
                        payload = None
                    if payload is None:
                        # Keepalive comment (keeps proxies from
                        # closing the connection).
                        if time.time() - last_keepalive >= 15.0:
                            yield ": keepalive\n\n"
                            last_keepalive = time.time()
                        continue
                    if payload.get("__end__"):
                        yield (
                            f"event: end\n"
                            f"data: {json.dumps({'stream_id': stream_id})}\n\n"
                        )
                        return
                    yield (
                        f"event: chat\n"
                        f"data: {json.dumps(payload)}\n\n"
                    )
            finally:
                svc.unsubscribe(stream_id, sub_id)
                sse_hist.observe_ms(
                    (time.perf_counter() - start) * 1000
                )

        return Response(
            stream_with_context(gen()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # ---- viewer count ------------------------------------------------

    @app.post("/api/streams/<int:stream_id>/heartbeat")
    def heartbeat(stream_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            viewer_id = int(body.get("viewer_id") or body.get("user_id", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "viewer_id must be an int"}), 400
        try:
            result = svc.heartbeat(stream_id, viewer_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        hb_count.inc()
        return jsonify(result)

    @app.get("/api/streams/<int:stream_id>/viewers")
    def viewers(stream_id: int):
        return jsonify({
            "stream_id": stream_id,
            "viewers": svc.viewer_count(stream_id),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8032"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
