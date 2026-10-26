"""Claude Code — Flask HTTP service (port 8037).

Endpoints:

    POST /api/sessions                          -> {session_id, workspace}
    GET  /api/sessions/<id>                     -> Session
    POST /api/sessions/<id>/messages            -> runs the agent loop, returns new turns
    GET  /api/sessions/<id>/files               -> [{path, size, modified_at}]
    GET  /api/sessions/<id>/files/<path>        -> file contents (text)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import AgentService  # noqa: E402


def create_app(service: AgentService | None = None) -> Flask:
    app = Flask("claude_code")
    svc = service or AgentService(
        store=KeyValueStore(
            "claude_code",
            persist_path=str(HERE / "var" / "claude_code.json"),
        ),
        workspace_root=str(HERE / "var"),
    )
    metrics = MetricsRegistry()
    sess_hist = metrics.histogram("session_latency_ms", "create session latency")
    turn_hist = metrics.histogram("turn_latency_ms", "turn latency")
    sess_count = metrics.counter("sessions_created_total", "sessions created")
    turn_count = metrics.counter("turns_total", "agent turns run")
    tool_count = metrics.counter("tool_calls_total", "tool calls executed")
    tool_err = metrics.counter("tool_errors_total", "tool errors")

    # ---- routes -------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/sessions")
    def create_session():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id", "anonymous")
            workspace = body.get("workspace")
            s = svc.create_session(user_id, workspace=workspace)
            sess_count.inc()
            return jsonify(s.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            sess_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/sessions")
    def list_sessions():
        return jsonify([s.to_dict() for s in svc.list_sessions()])

    @app.get("/api/sessions/<int:sid>")
    def get_session(sid: int):
        s = svc.get_session(sid)
        if not s:
            return jsonify({"error": "not found"}), 404
        return jsonify(s.to_dict())

    @app.post("/api/sessions/<int:sid>/messages")
    def post_message(sid: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            content = body.get("content", "")
            if not content:
                return jsonify({"error": "content is required"}), 400
            new_turns = svc.run_turn(sid, content)
            turn_count.inc()
            for t in new_turns:
                if t.tool_call is not None:
                    tool_count.inc()
                    if t.tool_call.status == "error":
                        tool_err.inc()
            return jsonify({
                "session_id": sid,
                "new_turns": [t.to_dict() for t in new_turns],
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            turn_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/sessions/<int:sid>/files")
    def list_files(sid: int):
        try:
            return jsonify(svc.list_files(sid))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/sessions/<int:sid>/files/<path:filepath>")
    def read_file(sid: int, filepath: str):
        try:
            text = svc.read_file(sid, filepath)
            return Response(text, mimetype="text/plain")
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "claude_code",
            "endpoints": [
                "POST /api/sessions",
                "GET  /api/sessions",
                "GET  /api/sessions/<id>",
                "POST /api/sessions/<id>/messages",
                "GET  /api/sessions/<id>/files",
                "GET  /api/sessions/<id>/files/<path>",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8037"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
