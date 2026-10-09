"""Real-Time Voice AI — Flask HTTP service (port 8038).

Endpoints:

    POST /api/sessions
    POST /api/sessions/<id>/audio                  (binary body, runs pipeline)
    GET  /api/sessions/<id>/transcript
    GET  /api/sessions/<id>/audio/stream           (SSE of audio chunk metadata)
    GET  /api/sessions/<id>/audio/outbox           (list pending audio chunks)
    POST /api/sessions/<id>/outbox/clear
    GET  /metrics, /health
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

from service import VoiceService  # noqa: E402


def create_app(service: VoiceService | None = None) -> Flask:
    app = Flask("voice_ai")
    svc = service or VoiceService(
        store=KeyValueStore("voice_ai", persist_path=str(HERE / "var" / "voice_ai.json")),
    )
    metrics = MetricsRegistry()
    sess_hist = metrics.histogram("session_latency_ms", "create session latency")
    audio_hist = metrics.histogram("audio_latency_ms", "audio push latency")
    stream_hist = metrics.histogram("stream_latency_ms", "stream latency")
    sess_count = metrics.counter("sessions_created_total", "sessions created")
    audio_count = metrics.counter("audio_chunks_in_total", "audio chunks received")
    turn_count = metrics.counter("turns_total", "turns run")
    bytes_in = metrics.counter("bytes_in_total", "audio bytes received")
    bytes_out = metrics.counter("bytes_out_total", "audio bytes synthesized")

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
            s = svc.create_session(user_id)
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

    @app.post("/api/sessions/<int:sid>/audio")
    def push_audio(sid: int):
        start = time.perf_counter()
        try:
            data = request.get_data(cache=False, as_text=False)
            chunks = svc.push_audio(sid, data)
            audio_count.inc()
            bytes_in.inc(len(data))
            turn_count.inc()
            for c in chunks:
                bytes_out.inc(len(c.data))
            return jsonify({
                "session_id": sid,
                "state": svc.get_session(sid).state,
                "audio_chunks": [c.to_dict() for c in chunks],
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            audio_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/sessions/<int:sid>/transcript")
    def get_transcript(sid: int):
        s = svc.get_session(sid)
        if not s:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "session_id": sid,
            "transcript": [t.to_dict() for t in s.transcript],
        })

    @app.get("/api/sessions/<int:sid>/audio/outbox")
    def get_outbox(sid: int):
        s = svc.get_session(sid)
        if not s:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "session_id": sid,
            "state": s.state,
            "outbox": [c.to_dict() for c in s.outbox],
        })

    @app.post("/api/sessions/<int:sid>/outbox/clear")
    def clear_outbox(sid: int):
        n = svc.clear_outbox(sid)
        return jsonify({"cleared": n})

    @app.get("/api/sessions/<int:sid>/audio/stream")
    def stream_audio(sid: int):
        """SSE stream of pending outbox chunks.

        Each event has the audio chunk metadata. Clients can then fetch
        the binary over a separate channel or use the JSON to drive
        playback in a web worker.
        """
        start = time.perf_counter()
        s = svc.get_session(sid)
        if not s:
            return jsonify({"error": "not found"}), 404

        def _events():
            try:
                for c in svc.iter_outbox(sid):
                    payload = json.dumps(c.to_dict())
                    yield f"data: {payload}\n\n"
                    time.sleep(0.01)
                yield "data: [DONE]\n\n"
            except Exception as e:  # pragma: no cover
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        resp = Response(stream_with_context(_events()), mimetype="text/event-stream")
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
            "service": "voice_ai",
            "endpoints": [
                "POST /api/sessions",
                "GET  /api/sessions",
                "GET  /api/sessions/<id>",
                "POST /api/sessions/<id>/audio",
                "GET  /api/sessions/<id>/transcript",
                "GET  /api/sessions/<id>/audio/outbox",
                "GET  /api/sessions/<id>/audio/stream (SSE)",
                "POST /api/sessions/<id>/outbox/clear",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8038"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
