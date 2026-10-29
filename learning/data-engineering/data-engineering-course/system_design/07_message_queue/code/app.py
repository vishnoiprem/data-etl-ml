"""Message queue HTTP service (Flask).

A thin HTTP layer over :class:`code.service.MessageQueueService`.
Endpoints follow ``design/README.md`` §4.
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

from .service import MessageQueueService  # noqa: E402


def create_app(service: MessageQueueService | None = None) -> Flask:
    """Build the Flask app. ``service`` is injectable for tests."""
    app = Flask("message_queue")
    svc = service or MessageQueueService()

    # ---- metrics --------------------------------------------------------
    metrics = MetricsRegistry()
    metrics.histogram("produce_latency_ms", "POST /api/topics/<name>/produce latency")
    metrics.histogram("consume_latency_ms", "GET  /api/topics/<name>/consume latency")
    metrics.counter("topics_total", "topics created")
    metrics.counter("produces_total", "records produced")
    metrics.counter("consumes_total", "consume calls")
    metrics.counter("groups_total", "consumer groups created")
    metrics.counter("records_consumed_total", "records returned to consumers")

    # ---- health & index --------------------------------------------------
    @app.get("/health")
    def health():
        return jsonify({"ok": True, "stats": svc.stats()})

    @app.get("/")
    def index():
        return jsonify({
            "service": "message_queue",
            "design": "system_design/07_message_queue/design/README.md",
            "endpoints": [
                "POST /api/topics",
                "GET  /api/topics",
                "GET  /api/topics/<name>",
                "DELETE /api/topics/<name>",
                "POST /api/topics/<name>/produce",
                "GET  /api/topics/<name>/consume?group=&max=&commit=&reset=",
                "POST /api/groups",
                "GET  /api/groups",
                "GET  /api/groups/<name>/offsets?topic=",
                "POST /api/groups/<name>/commit",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    # ---- topics (design §4) --------------------------------------------
    @app.post("/api/topics")
    def create_topic():
        body = request.get_json(force=True, silent=True) or {}
        t = svc.create_topic(
            body["name"], int(body.get("partitions", 4))
        )
        metrics.counter("topics_total").inc()
        return jsonify(t.to_dict()), 201

    @app.get("/api/topics")
    def list_topics():
        return jsonify({"topics": [t.to_dict() for t in svc.list_topics()]})

    @app.get("/api/topics/<name>")
    def get_topic(name: str):
        t = svc.get_topic(name)
        if not t:
            return jsonify({"error": "not found"}), 404
        d = t.to_dict()
        # Augment with per-partition log sizes — handy for /debug-style
        # inspection. The size field is what real Kafka's `kafka-topics
        # --describe` would show you.
        d["partitions_detail"] = [
            {"partition": p, "size": svc.topic_log_size(name, p)}
            for p in range(t.partitions)
        ]
        return jsonify(d)

    @app.delete("/api/topics/<name>")
    def delete_topic(name: str):
        if not svc.delete_topic(name):
            return jsonify({"error": "not found"}), 404
        return jsonify({"ok": True})

    # ---- produce (design §6) -------------------------------------------
    @app.post("/api/topics/<name>/produce")
    def produce(name: str):
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            r = svc.produce(
                topic=name,
                key=body.get("key"),
                value=body.get("value", ""),
                headers=body.get("headers"),
            )
            metrics.counter("produces_total").inc()
            return jsonify({
                "message_id": r.message_id,
                "partition": r.partition,
                "offset": r.offset,
            }), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        finally:
            metrics.histogram("produce_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    # ---- consume (design §7) -------------------------------------------
    @app.get("/api/topics/<name>/consume")
    def consume(name: str):
        start = time.perf_counter()
        try:
            group = request.args.get("group")
            if not group:
                return jsonify({"error": "group is required"}), 400
            max_records = int(request.args.get("max", "10"))
            commit = request.args.get("commit", "true").lower() == "true"
            reset = request.args.get("reset")
            records = svc.consume(
                topic=name,
                group=group,
                max_records=max_records,
                commit=commit,
                reset=reset,
            )
            metrics.counter("consumes_total").inc()
            metrics.counter("records_consumed_total").inc(len(records))
            # Compute next_offset per the records we returned.
            next_offset: dict[int, int] = {}
            for r in records:
                next_offset[r.partition] = r.offset + 1
            return jsonify({
                "topic": name,
                "group": group,
                "records": [r.to_dict() for r in records],
                "next_offset": next_offset,
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        finally:
            metrics.histogram("consume_latency_ms").observe_ms(
                (time.perf_counter() - start) * 1000
            )

    # ---- groups (design §4) --------------------------------------------
    @app.post("/api/groups")
    def create_group():
        body = request.get_json(force=True, silent=True) or {}
        g = svc.create_group(
            body["name"], reset=body.get("reset", "earliest")
        )
        metrics.counter("groups_total").inc()
        return jsonify(g.to_dict()), 201

    @app.get("/api/groups")
    def list_groups():
        return jsonify({
            "groups": [g.to_dict() for g in svc.list_groups()]
        })

    @app.get("/api/groups/<name>/offsets")
    def group_offsets(name: str):
        topic = request.args.get("topic")
        g = svc.get_group(name)
        if not g:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "group": name,
            "topic": topic,
            "offsets": svc.group_offsets(name, topic=topic),
        })

    @app.post("/api/groups/<name>/commit")
    def commit(name: str):
        body = request.get_json(force=True, silent=True) or {}
        try:
            off = svc.commit(
                name,
                body["topic"],
                int(body["partition"]),
                int(body["offset"]),
            )
            return jsonify({"committed": off})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    # ---- metrics endpoint -----------------------------------------------
    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    return app


if __name__ == "__main__":
    # Module 07 port — default 8007.
    port = int(os.environ.get("PORT", "8007"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
