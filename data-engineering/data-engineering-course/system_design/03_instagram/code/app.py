"""Instagram HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import InstagramService  # noqa: E402


def create_app(service: InstagramService | None = None) -> Flask:
    app = Flask("instagram")
    svc = service or InstagramService()

    metrics = MetricsRegistry()
    metrics.histogram("upload_latency_ms", "POST /api/photos latency")
    metrics.histogram("feed_latency_ms", "GET /api/feed latency")
    upload_count = metrics.counter("upload_total", "uploads")
    feed_count = metrics.counter("feed_total", "feed reads")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/users")
    def create_user():
        body = request.get_json(force=True, silent=True) or {}
        u = svc.create_user(int(body["user_id"]), body["username"], body["name"])
        return jsonify(u.to_dict()), 201

    @app.post("/api/photos")
    def upload():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            p = svc.upload(int(body["user_id"]), body.get("caption", ""))
            upload_count.inc()
            return jsonify(p.to_dict()), 201
        finally:
            metrics.histogram("upload_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/photos/<int:photo_id>")
    def get_photo(photo_id: int):
        p = svc.get_photo(photo_id)
        if not p:
            return jsonify({"error": "not found"}), 404
        return jsonify(p.to_dict())

    @app.post("/api/follow")
    def follow():
        body = request.get_json(force=True, silent=True) or {}
        svc.follow(int(body["follower_id"]), int(body["followee_id"]))
        return jsonify({"ok": True})

    @app.post("/api/unfollow")
    def unfollow():
        body = request.get_json(force=True, silent=True) or {}
        svc.unfollow(int(body["follower_id"]), int(body["followee_id"]))
        return jsonify({"ok": True})

    @app.get("/api/feed/<int:user_id>")
    def feed(user_id: int):
        start = time.perf_counter()
        try:
            limit = int(request.args.get("limit", "20"))
            feed_count.inc()
            return jsonify({
                "user_id": user_id,
                "photos": [p.to_dict() for p in svc.feed(user_id, limit=limit)],
            })
        finally:
            metrics.histogram("feed_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/users/<int:user_id>/photos")
    def user_photos(user_id: int):
        return jsonify({
            "user_id": user_id,
            "photos": [p.to_dict() for p in svc.photos_by(user_id)],
        })

    @app.post("/api/photos/<int:photo_id>/like")
    def like(photo_id: int):
        try:
            count = svc.like(photo_id)
            return jsonify({"photo_id": photo_id, "likes": count})
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "instagram",
            "endpoints": [
                "POST /api/users",
                "POST /api/photos",
                "GET  /api/photos/<id>",
                "POST /api/follow",
                "POST /api/unfollow",
                "GET  /api/feed/<user_id>",
                "GET  /api/users/<user_id>/photos",
                "POST /api/photos/<id>/like",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8003"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
