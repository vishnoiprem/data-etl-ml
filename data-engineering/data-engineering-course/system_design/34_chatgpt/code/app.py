"""Conversational Chat — Flask HTTP service (port 8034).

Exposes a /api/conversations/<id>/stream SSE endpoint that simulates
token-by-token streaming from the (mock) LLM.
"""

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
from common.storage import KeyValueStore  # noqa: E402

from service import ChatService  # noqa: E402


def create_app(service: ChatService | None = None) -> Flask:
    app = Flask("chatgpt")
    svc = service or ChatService(
        store=KeyValueStore("chatgpt", persist_path=str(HERE / "var" / "chatgpt.json")),
    )
    metrics = MetricsRegistry()
    create_hist = metrics.histogram("create_conv_latency_ms", "POST /api/conversations latency")
    msg_hist = metrics.histogram("message_latency_ms", "POST message latency")
    stream_hist = metrics.histogram("stream_latency_ms", "stream latency")
    create_count = metrics.counter("conversations_created_total", "conversations created")
    msg_count = metrics.counter("messages_total", "messages appended")
    stream_count = metrics.counter("streams_total", "streams initiated")

    # ---- routes -------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/conversations")
    def create_conversation():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            model = body.get("model", "mock-fast")
            system_prompt = body.get("system_prompt")
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400
            kwargs = {"user_id": user_id, "model": model}
            if system_prompt:
                kwargs["system_prompt"] = system_prompt
            c = svc.create_conversation(**kwargs)
            create_count.inc()
            return jsonify(c.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            create_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/conversations")
    def list_conversations():
        user_id = request.args.get("user_id")
        return jsonify([c.to_dict() for c in svc.list_conversations(user_id=user_id)])

    @app.get("/api/conversations/<int:conv_id>")
    def get_conversation(conv_id: int):
        c = svc.get_conversation(conv_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        return jsonify(c.to_dict())

    @app.post("/api/conversations/<int:conv_id>/messages")
    def post_message(conv_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            role = body.get("role", "user")
            content = body.get("content", "")
            if not content:
                return jsonify({"error": "content is required"}), 400
            m = svc.add_message(conv_id, role, content)
            msg_count.inc()
            return jsonify(m.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            msg_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/conversations/<int:conv_id>/complete")
    def complete(conv_id: int):
        """Non-streamed completion — returns the full reply at once."""
        try:
            m = svc.complete(conv_id)
            return jsonify(m.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.post("/api/conversations/<int:conv_id>/stream")
    def stream(conv_id: int):
        """SSE stream of growing reply chunks from the mock LLM."""
        start = time.perf_counter()
        try:
            stream_count.inc()
            gen = svc.stream(conv_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        def _events():
            try:
                # A small per-chunk delay simulates token latency.
                for chunk in gen:
                    payload = json.dumps({
                        "role": chunk.role,
                        "content": chunk.content,
                        "tokens": chunk.tokens,
                    })
                    yield f"data: {payload}\n\n"
                    time.sleep(0.02)
                yield "data: [DONE]\n\n"
            except Exception as e:  # pragma: no cover
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        resp = Response(
            stream_with_context(_events()),
            mimetype="text/event-stream",
        )
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["X-Accel-Buffering"] = "no"
        stream_hist.observe_ms((time.perf_counter() - start) * 1000)
        return resp

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "chatgpt",
            "endpoints": [
                "POST /api/conversations",
                "GET  /api/conversations",
                "GET  /api/conversations/<id>",
                "POST /api/conversations/<id>/messages",
                "POST /api/conversations/<id>/complete",
                "POST /api/conversations/<id>/stream (SSE)",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8034"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
