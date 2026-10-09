"""Webhook delivery HTTP service (Flask).

A thin HTTP layer over :class:`code.service.WebhookService`.
The delivery loop is started in-process by ``create_app``; for tests,
the app is created with ``start_loop=False`` and ``dispatch_pending_now``
is invoked manually.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the `common` package importable when running as `python3 code/app.py`.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import SimulatedTransport, WebhookService  # noqa: E402


def create_app(
    service: WebhookService | None = None,
    start_loop: bool = True,
) -> Flask:
    """Build the Flask app. ``service`` is injectable for tests."""
    app = Flask("webhook_delivery")
    svc = service or WebhookService(transport=SimulatedTransport())
    if start_loop:
        svc.start()

    # ---- metrics --------------------------------------------------------
    metrics = MetricsRegistry()
    metrics.counter("subs_total", "subscriptions created")
    metrics.counter("deliveries_total", "deliveries enqueued")
    metrics.counter("delivered_total", "deliveries completed 2xx")
    metrics.counter("retried_total", "retries scheduled")
    metrics.counter("dlq_total", "deliveries moved to DLQ")
    metrics.counter("replays_total", "DLQ replays")
    metrics.histogram("dispatch_latency_ms", "transport send latency")

    # ---- health & index --------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/")
    def index():
        return jsonify({
            "service": "webhook_delivery",
            "design": "system_design/08_webhook_delivery/design/README.md",
            "endpoints": [
                "POST /api/subscriptions",
                "GET  /api/subscriptions",
                "GET  /api/subscriptions/<id>",
                "POST /api/subscriptions/<id>/deliver",
                "GET  /api/subscriptions/<id>/deliveries",
                "GET  /api/deliveries/<id>",
                "POST /api/subscriptions/<id>/replay/<delivery_id>",
                "GET  /api/dlq",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    # ---- subscriptions ---------------------------------------------------
    @app.post("/api/subscriptions")
    def create_sub():
        body = request.get_json(force=True, silent=True) or {}
        try:
            s = svc.create_subscription(
                url=body["url"],
                secret=body["secret"],
                event_types=body.get("event_types") or [],
            )
        except (KeyError, ValueError) as e:
            return jsonify({"error": str(e)}), 400
        metrics.counter("subs_total").inc()
        return jsonify(s.to_dict()), 201

    @app.get("/api/subscriptions")
    def list_subs():
        return jsonify({
            "subscriptions": [s.to_dict() for s in svc.list_subscriptions()]
        })

    @app.get("/api/subscriptions/<sid>")
    def get_sub(sid: str):
        s = svc.get_subscription(sid)
        if not s:
            return jsonify({"error": "not found"}), 404
        return jsonify(s.to_dict())

    # ---- deliveries ------------------------------------------------------
    @app.post("/api/subscriptions/<sid>/deliver")
    def deliver(sid: str):
        body = request.get_json(force=True, silent=True) or {}
        try:
            d = svc.deliver(
                subscription_id=sid,
                event=body.get("event", ""),
                payload=body.get("payload", {}),
                max_attempts=body.get("max_attempts"),
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        metrics.counter("deliveries_total").inc()
        return jsonify(d.to_dict()), 202

    @app.get("/api/subscriptions/<sid>/deliveries")
    def list_sub_deliveries(sid: str):
        items = [d.to_dict() for d in svc.list_deliveries(sid)]
        return jsonify({"subscription_id": sid, "deliveries": items})

    @app.get("/api/deliveries/<did>")
    def get_delivery(did: str):
        d = svc.get_delivery(did)
        if not d:
            return jsonify({"error": "not found"}), 404
        d_dict = d.to_dict()
        d_dict["attempts_detail"] = [
            a.to_dict() for a in svc.attempts_for(did)
        ]
        return jsonify(d_dict)

    @app.post("/api/subscriptions/<sid>/replay/<did>")
    def replay(sid: str, did: str):
        try:
            d = svc.replay(sid, did)
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        metrics.counter("replays_total").inc()
        return jsonify(d.to_dict())

    @app.get("/api/dlq")
    def dlq():
        return jsonify({
            "dlq": [d.to_dict() for d in svc.list_dlq()]
        })

    # ---- metrics endpoint -----------------------------------------------
    @app.get("/metrics")
    def metrics_endpoint():
        # Refresh the few "lifetime" counters that the service
        # maintains — so a /metrics scrape right after creation
        # shows zero. The service owns the truth; the metrics
        # registry just renders.
        snap = svc.stats()
        c = metrics.counter("delivered_total")
        c._value = snap["delivered"]
        c = metrics.counter("dlq_total")
        c._value = snap["dlq"]
        return metrics.render(), 200, {
            "Content-Type": "text/plain; version=0.0.4"
        }

    return app


if __name__ == "__main__":
    # Module 08 port — default 8008.
    port = int(os.environ.get("PORT", "8008"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
