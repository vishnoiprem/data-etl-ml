"""Reddit-style HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import RedditService  # noqa: E402


def create_app(service: RedditService | None = None) -> Flask:
    app = Flask("reddit")
    svc = service or RedditService()
    metrics = MetricsRegistry()
    metrics.counter("requests_total", "total requests")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.post("/api/users")
    def create_user():
        b = request.get_json(force=True, silent=True) or {}
        return jsonify(svc.create_user(int(b["user_id"]), b["username"])), 201

    @app.post("/api/subreddits")
    def create_subreddit():
        b = request.get_json(force=True, silent=True) or {}
        s = svc.create_subreddit(b["name"], b.get("description", ""))
        return jsonify(s.to_dict()), 201

    @app.post("/api/users/<int:user_id>/subscribe")
    def subscribe(user_id: int):
        b = request.get_json(force=True, silent=True) or {}
        svc.subscribe(user_id, int(b["subreddit_id"]))
        return jsonify({"ok": True})

    @app.post("/api/subreddits/<int:sid>/posts")
    def create_post(sid: int):
        b = request.get_json(force=True, silent=True) or {}
        p = svc.create_post(int(b["user_id"]), sid, b["title"], b.get("body", ""))
        return jsonify(p.to_dict()), 201

    @app.post("/api/posts/<int:pid>/vote")
    def vote(pid: int):
        b = request.get_json(force=True, silent=True) or {}
        try:
            return jsonify(svc.vote(pid, int(b["user_id"]), int(b["direction"])))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.get("/api/subreddits/<int:sid>")
    def subreddit(sid: int):
        sort = request.args.get("sort", "hot")
        limit = int(request.args.get("limit", "25"))
        return jsonify({"posts": svc.subreddit_top(sid, sort=sort, limit=limit)})

    @app.get("/api/users/<int:user_id>/home")
    def home(user_id: int):
        limit = int(request.args.get("limit", "50"))
        return jsonify({"feed": svc.home(user_id, limit=limit)})

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({"service": "reddit", "stats": svc.stats()})

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8039"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
