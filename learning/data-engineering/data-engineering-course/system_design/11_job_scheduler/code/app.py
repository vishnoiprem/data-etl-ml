"""Job scheduler HTTP service (Flask).

Run:
    PORT=8011 python3 11_job_scheduler/code/app.py

Try:
    curl -X POST http://localhost:8011/api/jobs \
         -H 'Content-Type: application/json' \
         -d '{"name":"ping","kind":"cron","interval_seconds":60}'

    curl http://localhost:8011/api/jobs
    curl -X POST http://localhost:8011/api/jobs/123/run
    curl http://localhost:8011/metrics
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.ids import Snowflake  # noqa: E402
from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import (  # noqa: E402
    DAGCycleError,
    FunctionJobRunner,
    InvalidJobError,
    JobNotFoundError,
    JobScheduler,
)


# A tiny registry of runnable functions for `payload.fn` jobs.
# These exist so that cron + manual runs have something concrete to
# invoke in this demo. In production you'd dispatch to subprocesses,
# containerised workers, or Airflow.
JOB_REGISTRY: Dict[str, Any] = {
    "ping": lambda payload: {"ok": True, "echo": payload},
    "noop": lambda payload: {"ok": True, "payload": payload},
    "fail": lambda payload: (_ for _ in ()).throw(RuntimeError("intentional")),
}


def create_app(service: JobScheduler | None = None) -> Flask:
    app = Flask("job_scheduler")
    if service is None:
        store = KeyValueStore(
            "job_scheduler",
            persist_path=str(HERE / "var" / "job_scheduler.json"),
        )
        runner = FunctionJobRunner(registry=JOB_REGISTRY)
        service = JobScheduler(
            store=store,
            idgen=Snowflake(machine_id=11),
            runner=runner,
        )
    svc = service
    metrics = MetricsRegistry()
    create_count = metrics.counter("jobs_created_total", "POST /api/jobs")
    run_count = metrics.counter("runs_total", "runs started")
    trigger_count = metrics.counter("triggers_total", "manual triggers")
    sched_latency = metrics.histogram("sched_tick_ms", "scheduler tick latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/jobs")
    def create():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            try:
                job = svc.create_job(body)
            except (InvalidJobError, DAGCycleError) as e:
                return jsonify({"error": str(e)}), 400
            create_count.inc()
            return jsonify(job), 201
        finally:
            sched_latency.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/jobs")
    def list_jobs():
        return jsonify({"jobs": svc.list_jobs()})

    @app.get("/api/jobs/<int:job_id>")
    def get_job(job_id: int):
        try:
            return jsonify(svc.get_job(job_id))
        except JobNotFoundError:
            return jsonify({"error": "not found"}), 404

    @app.post("/api/jobs/<int:job_id>/run")
    def run_now(job_id: int):
        try:
            run = svc.trigger_now(job_id)
        except JobNotFoundError:
            return jsonify({"error": "not found"}), 404
        run_count.inc()
        trigger_count.inc()
        return jsonify(run), 200

    @app.get("/api/runs")
    def list_runs():
        job_id = request.args.get("job_id")
        try:
            limit = int(request.args.get("limit", "50"))
        except ValueError:
            return jsonify({"error": "limit must be int"}), 400
        jid = int(job_id) if job_id is not None else None
        return jsonify({"runs": svc.list_runs(job_id=jid, limit=limit)})

    @app.get("/api/runs/<int:run_id>")
    def get_run(run_id: int):
        try:
            return jsonify(svc.get_run(run_id))
        except JobNotFoundError:
            return jsonify({"error": "not found"}), 404

    @app.get("/metrics")
    def metrics_endpoint():
        text = metrics.render()
        st = svc.status()
        text += f"# jobs {st['jobs']}\n# due {st['due']}\n# runs {st['runs']}\n"
        return text, 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "job_scheduler",
            "endpoints": [
                "POST /api/jobs",
                "GET /api/jobs",
                "GET /api/jobs/<id>",
                "POST /api/jobs/<id>/run",
                "GET /api/runs",
                "GET /api/runs/<id>",
                "GET /metrics",
                "GET /health",
            ],
            "status": svc.status(),
        })

    @app.errorhandler(404)
    def _nf(_e):
        return jsonify({"error": "not found"}), 404

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8011"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
