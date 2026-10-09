"""Twitter / X HTTP service (Flask).

A thin HTTP layer over :class:`code.service.TwitterService`. Maps the
endpoints in `design/README.md` §4 to handler functions and wires up
metrics (counters + histograms) so they surface at ``/metrics``.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make the `common` package importable when running as `python3 code/app.py`.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import TwitterService  # noqa: E402


def create_app(service: TwitterService | None = None) -> Flask:
    """Build the Flask app. ``service`` is injectable for tests."""
    app = Flask("twitter")
    svc = service or TwitterService()

    # ---- metrics (design §4 GET /metrics) --------------------------------
    metrics = MetricsRegistry()
    metrics.histogram("tweet_latency_ms", "POST /api/tweets latency")
    metrics.histogram("timeline_latency_ms", "GET /api/timeline latency")
    tweet_count = metrics.counter("tweet_total", "tweets posted")
    timeline_count = metrics.counter("timeline_total", "timeline reads")
    follow_count = metrics.counter("follow_total", "follow edges added")
    like_count = metrics.counter("like_total", "tweet likes")
    celeb_count = metrics.counter("celeb_tweet_total", "celebrity tweets (no fanout)")
    fanout_count = metrics.counter("fanout_total", "fanned-out tweets (normal path)")

    # ---- health & index --------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/")
    def index():
        return jsonify({
            "service": "twitter",
            "design": "system_design/04_twitter/design/README.md",
            "endpoints": [
                "POST /api/users",
                "POST /api/follow",
                "POST /api/unfollow",
                "POST /api/tweets",
                "GET  /api/tweets/<id>",
                "POST /api/tweets/<id>/like",
                "GET  /api/timeline/<user_id>?limit=",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    # ---- users (design §4) -----------------------------------------------
    @app.post("/api/users")
    def create_user():
        body = request.get_json(force=True, silent=True) or {}
        u = svc.create_user(
            int(body["user_id"]), body["username"], body["name"]
        )
        return jsonify(u.to_dict()), 201

    # ---- follows (design §4) --------------------------------------------
    @app.post("/api/follow")
    def follow():
        body = request.get_json(force=True, silent=True) or {}
        svc.follow(int(body["follower_id"]), int(body["followee_id"]))
        follow_count.inc()
        return jsonify({"ok": True})

    @app.post("/api/unfollow")
    def unfollow():
        body = request.get_json(force=True, silent=True) or {}
        svc.unfollow(int(body["follower_id"]), int(body["followee_id"]))
        return jsonify({"ok": True})

    # ---- tweets (design §7) ---------------------------------------------
    @app.post("/api/tweets")
    def post_tweet():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            retweet_of = body.get("retweet_of")
            t = svc.post_tweet(
                int(body["user_id"]),
                body.get("text", ""),
                retweet_of=int(retweet_of) if retweet_of is not None else None,
            )
            tweet_count.inc()
            if svc.is_celeb(int(body["user_id"])):
                celeb_count.inc()
            else:
                fanout_count.inc()
            return jsonify(t.to_dict()), 201
        finally:
            metrics.histogram("tweet_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    @app.get("/api/tweets/<int:tweet_id>")
    def get_tweet(tweet_id: int):
        t = svc.get_tweet(tweet_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        return jsonify(t.to_dict())

    @app.post("/api/tweets/<int:tweet_id>/like")
    def like(tweet_id: int):
        try:
            count = svc.like_tweet(tweet_id)
            like_count.inc()
            return jsonify({"tweet_id": tweet_id, "likes": count})
        except ValueError as e:
            return jsonify({"error": str(e)}), 404

    # ---- timeline (design §6) -------------------------------------------
    @app.get("/api/timeline/<int:user_id>")
    def timeline(user_id: int):
        start = time.perf_counter()
        try:
            limit = int(request.args.get("limit", "20"))
            timeline_count.inc()
            tweets = svc.timeline(user_id, limit=limit)
            return jsonify({
                "user_id": user_id,
                "tweets": [t.to_dict() for t in tweets],
            })
        finally:
            metrics.histogram("timeline_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    # ---- metrics endpoint (design §4) -----------------------------------
    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    return app


if __name__ == "__main__":
    # Module 04 port — default 8004.
    port = int(os.environ.get("PORT", "8004"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)