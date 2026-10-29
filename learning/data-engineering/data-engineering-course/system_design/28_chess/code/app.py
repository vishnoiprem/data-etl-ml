"""Chess HTTP service (Flask) with SSE stream for live moves."""

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

from .service import ChessService  # noqa: E402


def create_app(service: ChessService | None = None) -> Flask:
    app = Flask("chess")
    svc = service or ChessService()

    metrics = MetricsRegistry()
    metrics.histogram("move_latency_ms", "POST move latency")
    metrics.counter("moves_total", "moves played")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/games")
    def create_game():
        body = request.get_json(force=True, silent=True) or {}
        g = svc.create_game(
            white_id=body.get("white_id"),
            black_id=body.get("black_id"),
        )
        return jsonify(g.to_dict()), 201

    @app.get("/api/games/<int:game_id>")
    def get_game(game_id: int):
        g = svc.get_game(game_id)
        if not g:
            return jsonify({"error": "not found"}), 404
        return jsonify(g.to_dict())

    @app.post("/api/games/<int:game_id>/join")
    def join(game_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            g = svc.join(game_id, int(body["user_id"]), body.get("color", "any"))
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(g.to_dict())

    @app.post("/api/games/<int:game_id>/moves")
    def move(game_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                r = svc.submit_move(
                    game_id,
                    int(body["user_id"]),
                    str(body["from_sq"]),
                    str(body["to_sq"]),
                    body.get("promotion"),
                )
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            metrics.counter("moves_total").inc()
            return jsonify(r)
        finally:
            metrics.histogram("move_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.post("/api/games/<int:game_id>/resign")
    def resign(game_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            g = svc.resign(game_id, int(body["user_id"]))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(g.to_dict())

    @app.get("/api/matchmaking")
    def matchmaking():
        uid = int(request.args.get("user_id", "0"))
        if uid == 0:
            return jsonify({"error": "user_id required"}), 400
        return jsonify(svc.enqueue(uid))

    @app.get("/api/games/<int:game_id>/stream")
    def stream(game_id: int):
        q = svc.register_listener(game_id)

        @stream_with_context
        def gen():
            try:
                yield "event: ready\ndata: {}\n\n"
                while True:
                    try:
                        evt = q.get(timeout=15.0)
                        yield f"event: state\ndata: {json.dumps(evt)}\n\n"
                    except Exception:
                        yield "event: ping\ndata: {}\n\n"
            finally:
                svc.unregister_listener(game_id, q)

        return Response(gen(), mimetype="text/event-stream")

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "chess",
            "endpoints": [
                "POST /api/games",
                "GET  /api/games/<id>",
                "POST /api/games/<id>/join",
                "POST /api/games/<id>/moves",
                "POST /api/games/<id>/resign",
                "GET  /api/matchmaking?user_id=",
                "GET  /api/games/<id>/stream   (SSE)",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8028"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
