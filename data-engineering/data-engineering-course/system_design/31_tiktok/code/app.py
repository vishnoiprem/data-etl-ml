"""TikTok-style short-form video service — HTTP layer (Flask).

This is the thin wrapper around `TikTokService`. The HTTP layer
is intentionally small: parse, delegate, return JSON. All real
work lives in `service.py`.

Run:
    PORT=8031 python3 31_tiktok/code/app.py

Try:
    curl -X POST http://localhost:8031/api/users \
         -H 'Content-Type: application/json' \
         -d '{"name": "alice"}'

    curl -X POST http://localhost:8031/api/videos \
         -H 'Content-Type: application/json' \
         -d '{"user_id": <id>, "caption": "hi", "duration_s": 15, "tags": ["cat"]}'

    curl -X POST http://localhost:8031/api/videos/<id>/view \
         -H 'Content-Type: application/json' \
         -d '{"user_id": <id>, "watch_pct": 95}'

    curl "http://localhost:8031/api/foryou/<user_id>?limit=20"
    curl "http://localhost:8031/api/videos/<id>"
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

from common.cache import TTLCache  # noqa: E402
from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import TikTokService  # noqa: E402


def create_app(service: TikTokService | None = None) -> Flask:
    app = Flask("tiktok_service")
    svc = service or TikTokService(
        store=KeyValueStore(
            "tiktok_service",
            persist_path=str(HERE / "var" / "tiktok_service.json"),
        ),
        foryou_cache=TTLCache(
            ttl_seconds=TikTokService.__init__.__defaults__[3]
            if TikTokService.__init__.__defaults__ else 60.0,
            max_entries=50_000,
        ),
    )
    metrics = MetricsRegistry()
    user_count = metrics.counter("user_total", "users created")
    post_count = metrics.counter("video_post_total", "videos posted")
    view_count = metrics.counter("view_total", "view events")
    like_count = metrics.counter("like_total", "likes")
    foryou_count = metrics.counter("foryou_total", "For You queries")
    cache_hits = metrics.counter("cache_hits", "TTLCache hits")
    cache_misses = metrics.counter("cache_misses", "TTLCache misses")
    foryou_cache_hits = metrics.counter("foryou_cache_hits", "For You cache hits")
    foryou_cache_misses = metrics.counter("foryou_cache_misses", "For You cache misses")

    get_hist = metrics.histogram("get_video_latency_ms", "GET /api/videos/<id>")
    foryou_hist = metrics.histogram("foryou_latency_ms", "GET /api/foryou/<user_id>")
    view_hist = metrics.histogram("view_latency_ms", "POST /api/videos/<id>/view")

    # ---- index + health + metrics ------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "service": "tiktok_service",
            "endpoints": [
                "POST /api/users",
                "POST /api/videos",
                "POST /api/videos/<id>/view",
                "POST /api/videos/<id>/like",
                "GET /api/foryou/<user_id>?limit=N",
                "GET /api/videos/<id>",
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

    # ---- videos ------------------------------------------------------

    @app.post("/api/videos")
    def post_video():
        body = request.get_json(force=True, silent=True) or {}
        user_id = body.get("user_id")
        caption = body.get("caption") or ""
        duration_s = body.get("duration_s")
        tags = body.get("tags") or []
        try:
            user_id = int(user_id)
            duration_s = int(duration_s)
        except (TypeError, ValueError):
            return (
                jsonify({"error": "user_id and duration_s must be ints"}),
                400,
            )
        if not isinstance(tags, list):
            return jsonify({"error": "tags must be a list of strings"}), 400
        try:
            video = svc.post_video(user_id, caption, duration_s, tags)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        post_count.inc()
        return jsonify(video.to_dict()), 201

    @app.get("/api/videos/<int:video_id>")
    def get_video(video_id: int):
        start = time.perf_counter()
        try:
            # Did the cache get hit? We check before/after.
            cache_key = svc._k_video(video_id)
            pre = svc.cache.get(cache_key)
            v = svc.get_video(video_id)
            if v is None:
                cache_misses.inc()
                return jsonify({"error": "not found"}), 404
            if pre is not None:
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
            watch_pct = body.get("watch_pct", 100.0)
            try:
                user_id = int(user_id)
                watch_pct = float(watch_pct)
            except (TypeError, ValueError):
                return (
                    jsonify({"error": "user_id must be int, watch_pct must be number"}),
                    400,
                )
            try:
                v = svc.record_view(video_id, user_id, watch_pct)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            if v is None:
                return jsonify({"error": "video not found"}), 404
            view_count.inc()
            return jsonify(
                {
                    "recorded": True,
                    "video_id": v.video_id,
                    "views": v.views,
                    "avg_watch_pct": (
                        (v.total_watch_s / v.views) / max(1, v.duration_s) * 100
                    ),
                }
            )
        finally:
            view_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.post("/api/videos/<int:video_id>/like")
    def like_video(video_id: int):
        body = request.get_json(force=True, silent=True) or {}
        try:
            user_id = int(body.get("user_id", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id must be an int"}), 400
        try:
            v = svc.like_video(video_id, user_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if v is None:
            return jsonify({"error": "video not found"}), 404
        like_count.inc()
        return jsonify({"video_id": v.video_id, "likes": v.likes})

    # ---- For You feed -----------------------------------------------

    @app.get("/api/foryou/<int:user_id>")
    def foryou(user_id: int):
        start = time.perf_counter()
        try:
            limit = request.args.get("limit", default=20, type=int) or 20
            cache_key = svc._k_foryou(user_id)
            cached = svc.foryou_cache.get(cache_key)
            if cached is not None:
                foryou_cache_hits.inc()
                return jsonify(
                    {
                        "user_id": user_id,
                        "limit": limit,
                        "cached": True,
                        "results": [
                            {"video_id": vid, "caption": cap, "score": score}
                            for vid, cap, score in cached[:limit]
                        ],
                    }
                )
            foryou_cache_misses.inc()
            results = svc.foryou(user_id, limit=limit)
            foryou_count.inc()
            return jsonify(
                {
                    "user_id": user_id,
                    "limit": limit,
                    "cached": False,
                    "results": [
                        {"video_id": vid, "caption": cap, "score": score}
                        for vid, cap, score in results
                    ],
                }
            )
        finally:
            foryou_hist.observe_ms((time.perf_counter() - start) * 1000)

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8031"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
