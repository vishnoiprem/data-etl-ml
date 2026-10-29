"""Newsfeed HTTP service (Flask).

PORT env var, default 8005. Exposes a ranked feed read path plus the
write endpoints (post, follow, engage) and a /metrics endpoint for
Prometheus-style scraping.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import NewsfeedService, ScoredPost  # noqa: E402


def create_app(service: NewsfeedService | None = None) -> Flask:
    app = Flask("newsfeed")
    svc = service or NewsfeedService()

    metrics = MetricsRegistry()
    metrics.counter("posts_total", "posts created")
    metrics.counter("engage_total", "engagement events")
    metrics.counter("feed_total", "feed reads")
    metrics.counter("follow_total", "follow events")
    metrics.counter("ranker_fallback_total", "ranker fallbacks to chrono")
    metrics.histogram("post_latency_ms", "POST /api/posts latency")
    metrics.histogram("engage_latency_ms", "engage latency")
    metrics.histogram("feed_latency_ms", "GET /api/feed latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/")
    def index():
        return jsonify({
            "service": "newsfeed",
            "endpoints": [
                "POST /api/users",
                "POST /api/follow",
                "POST /api/unfollow",
                "POST /api/posts",
                "POST /api/posts/<id>/engage",
                "GET  /api/posts/<id>",
                "GET  /api/feed/<user_id>?limit=",
                "GET  /api/users/<user_id>/posts",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    @app.post("/api/users")
    def create_user():
        body = request.get_json(force=True, silent=True) or {}
        u = svc.create_user(
            int(body["user_id"]),
            str(body.get("username", "")),
            str(body.get("name", "")),
        )
        return jsonify(u.to_dict()), 201

    @app.post("/api/follow")
    def follow():
        body = request.get_json(force=True, silent=True) or {}
        metrics.counter("follow_total").inc()
        svc.follow(int(body["follower_id"]), int(body["followee_id"]))
        return jsonify({"ok": True})

    @app.post("/api/unfollow")
    def unfollow():
        body = request.get_json(force=True, silent=True) or {}
        svc.unfollow(int(body["follower_id"]), int(body["followee_id"]))
        return jsonify({"ok": True})

    @app.post("/api/posts")
    def create_post():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            p = svc.create_post(int(body["user_id"]), str(body.get("text", "")))
            metrics.counter("posts_total").inc()
            return jsonify(p.to_dict()), 201
        finally:
            metrics.histogram("post_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/posts/<int:post_id>")
    def get_post(post_id: int):
        p = svc.get_post(post_id)
        if not p:
            return jsonify({"error": "not found"}), 404
        return jsonify(p.to_dict())

    @app.get("/api/users/<int:user_id>/posts")
    def user_posts(user_id: int):
        return jsonify({
            "user_id": user_id,
            "posts": [p.to_dict() for p in svc.posts_by_author(user_id)],
        })

    @app.post("/api/posts/<int:post_id>/engage")
    def engage(post_id: int):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            kind = str(body.get("kind", "")).lower()
            counts = svc.engage(post_id, kind)
            metrics.counter("engage_total").inc()
            return jsonify(counts)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            metrics.histogram("engage_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/feed/<int:user_id>")
    def feed(user_id: int):
        start = time.perf_counter()
        try:
            limit = int(request.args.get("limit", "20"))
            ranked: list[ScoredPost] = svc.rank_feed(user_id, limit=limit)
            metrics.counter("feed_total").inc()
            return jsonify({
                "user_id": user_id,
                "ranked": [s.to_dict() for s in ranked],
                "posts": [s.post.to_dict() for s in ranked],
            })
        finally:
            metrics.histogram("feed_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8005"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
