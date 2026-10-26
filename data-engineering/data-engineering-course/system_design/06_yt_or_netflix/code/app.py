"""YouTube / Netflix-style video service — HTTP layer (Flask).

This is the thin wrapper around `VideoService`. The HTTP layer is
intentionally small: parse, delegate, return JSON. All real work
lives in `service.py`.

Run:
    python3 06_yt_or_netflix/code/app.py            # http://localhost:8006

Try:
    curl -X POST http://localhost:8006/api/users \
         -H 'Content-Type: application/json' \
         -d '{"name": "alice"}'

    curl -X POST http://localhost:8006/api/videos \
         -H 'Content-Type: application/json' \
         -d '{"user_id": <id>, "title": "lesson 1", "duration_s": 600}'

    curl    http://localhost:8006/api/videos/<id>
    curl    "http://localhost:8006/api/trending?limit=10"
    curl    "http://localhost:8006/api/recommend/<user_id>?limit=10"
    curl    http://localhost:8006/metrics
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make `common` importable when launched directly.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import VideoService  # noqa: E402


def create_app(service: VideoService | None = None) -> Flask:
    app = Flask("video_service")
    svc = service or VideoService(
        store=KeyValueStore(
            "video_service",
            persist_path=str(HERE / "var" / "video_service.json"),
        ),
    )
    metrics = MetricsRegistry()
    upload_count = metrics.counter("upload_total", "videos uploaded")
    view_count = metrics.counter("view_total", "view events")
    trending_count = metrics.counter("trending_total", "trending queries")
    recommend_count = metrics.counter("recommend_total", "recommend queries")
    cache_hits = metrics.counter("cache_hits", "TTLCache hits")
    cache_misses = metrics.counter("cache_misses", "TTLCache misses")
    get_hist = metrics.histogram("get_video_latency_ms", "GET /api/videos/<id>")
    upload_hist = metrics.histogram("upload_latency_ms", "POST /api/videos")
    view_hist = metrics.histogram("view_latency_ms", "POST /api/videos/<id>/view")

    # ---- index + health + metrics ------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "service": "video_service",
            "endpoints": [
                "POST /api/users",
                "POST /api/videos",
                "GET /api/videos/<id>",
                "POST /api/videos/<id>/view",
                "GET /api/trending?limit=N",
                "GET /api/recommend/<user_id>?limit=N",
                "GET /metrics",
                "GET /health",
            ],
            "cache": svc.cache_stats(),
            "total_videos": svc.total_videos(),
        })

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    # ---- users -------------------------------------------------------

    @app.post("/api/users")
    def create_user():
        body = request.get_json(force=True, silent=True) or {}
        name = body.get("name")
        try:
            user = svc.create_user(name or "")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(user.to_dict()), 201

    # ---- videos ------------------------------------------------------

    @app.post("/api/videos")
    def upload_video():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            title = body.get("title")
            duration_s = body.get("duration_s")
            try:
                user_id = int(user_id)
                duration_s = int(duration_s)
            except (TypeError, ValueError):
                return jsonify({"error": "user_id and duration_s must be ints"}), 400
            try:
                video = svc.upload_video(user_id, title or "", duration_s)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            upload_count.inc()
            return jsonify(video.to_dict()), 201
        finally:
            upload_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/videos/<int:video_id>")
    def get_video(video_id: int):
        start = time.perf_counter()
        try:
            v = svc.get_video(video_id)
            if v is None:
                cache_misses.inc()
                return jsonify({"error": "not found"}), 404
            # Did the cache get hit? We re-check after the call.
            if svc.cache.get(svc._k_video(video_id)) is not None:
                cache_hits.inc()
            else:
                cache_misses.inc()
            return jsonify(v.to_dict())
        finally:
            get_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/videos/<int:video_id>/view")
    def record_view(video_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                return jsonify({"error": "user_id must be an int"}), 400
            v = svc.record_view(video_id, user_id)
            if v is None:
                return jsonify({"error": "video not found"}), 404
            view_count.inc()
            return jsonify({
                "recorded": True,
                "video_id": v.video_id,
                "views": v.views,
            })
        finally:
            view_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/videos/<int:video_id>/comments")
    def add_comment(video_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body.get("user_id", 0))
            text = body.get("text") or ""
            svc.add_comment(video_id, user_id, text)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"recorded": True}), 201

    # ---- trending + recommend ---------------------------------------

    @app.get("/api/trending")
    def trending():
        limit = request.args.get("limit", default=10, type=int)
        results = svc.trending(limit or 10)
        trending_count.inc()
        return jsonify({
            "limit": limit or 10,
            "window_seconds": svc.window_seconds,
            "results": [
                {"video_id": vid, "title": title, "views_in_window": n}
                for vid, n, title in results
            ],
        })

    @app.get("/api/recommend/<int:user_id>")
    def recommend(user_id: int):
        limit = request.args.get("limit", default=10, type=int)
        results = svc.recommend(user_id, limit or 10)
        recommend_count.inc()
        return jsonify({
            "user_id": user_id,
            "limit": limit or 10,
            "results": [
                {"video_id": vid, "title": title, "score": score}
                for vid, title, score in results
            ],
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8006"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
