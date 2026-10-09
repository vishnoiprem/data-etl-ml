"""User data export HTTP service (Flask).

Run:
    PORT=8012 python3 12_user_data_export/code/app.py

Try:
    curl -X POST http://localhost:8012/api/exports \
         -H 'Content-Type: application/json' \
         -d '{"user_id": "u-1"}'

    curl http://localhost:8012/api/exports/<id>
    curl http://localhost:8012/api/exports/<id>/download
    curl http://localhost:8012/metrics
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.ids import Snowflake  # noqa: E402
from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    ExportError,
    ExportNotFoundError,
    ExportService,
    InvalidUserError,
)


# Sample data so the demo is interesting out of the box.
SAMPLE_PROFILES = {
    "u-1": {"name": "Alice", "email": "alice@example.com", "joined": "2022-03-01"},
    "u-2": {"name": "Bob", "email": "bob@example.com", "joined": "2023-07-15"},
}
SAMPLE_ORDERS = {
    "u-1": [
        {"order_id": "o-100", "amount": 19.99, "sku": "BOOK-1"},
        {"order_id": "o-101", "amount": 5.50, "sku": "PEN-2"},
    ],
    "u-2": [{"order_id": "o-200", "amount": 99.00, "sku": "DESK-1"}],
}
SAMPLE_ACTIVITY = {
    "u-1": [
        {"event": "login", "at": "2025-01-15T08:00:00Z"},
        {"event": "view_item", "at": "2025-01-15T08:05:00Z", "sku": "BOOK-1"},
    ],
}
SAMPLE_PREFS = {
    "u-1": {"newsletter": True, "theme": "dark"},
    "u-2": {"newsletter": False, "theme": "light"},
}


def _build_default_service(persist_root: Path) -> ExportService:
    from service import (  # noqa: WPS433
        ActivityCollection,
        BlobStore,
        OrdersCollection,
        PreferencesCollection,
        UserProfileCollection,
    )
    store = KeyValueStore(
        "user_data_export",
        persist_path=str(persist_root / "user_data_export.json"),
    )
    blob_store = BlobStore(root=str(persist_root / "blobs"))
    return ExportService(
        store=store,
        blob_store=blob_store,
        idgen=Snowflake(machine_id=12),
        collections=[
            UserProfileCollection(profiles=SAMPLE_PROFILES),
            OrdersCollection(orders=SAMPLE_ORDERS),
            ActivityCollection(activity=SAMPLE_ACTIVITY),
            PreferencesCollection(prefs=SAMPLE_PREFS),
        ],
        ttl_seconds=DEFAULT_TTL_SECONDS,
    )


def create_app(service: ExportService | None = None) -> Flask:
    app = Flask("user_data_export")
    if service is None:
        persist_root = HERE / "var"
        service = _build_default_service(persist_root)
    svc = service
    metrics = MetricsRegistry()
    create_count = metrics.counter("exports_created_total", "POST /api/exports")
    download_count = metrics.counter("downloads_total", "GET /api/exports/<id>/download")
    failure_count = metrics.counter("export_failures_total", "exports that failed")
    export_latency = metrics.histogram("export_latency_ms", "compile + write latency")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/exports")
    def create():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            try:
                export = svc.create_export(user_id)
            except InvalidUserError as e:
                return jsonify({"error": str(e)}), 400
            create_count.inc()
            return jsonify(export.to_dict()), 202
        finally:
            export_latency.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/exports")
    def list_exports():
        user_id = request.args.get("user_id")
        return jsonify({"exports": svc.list_exports(user_id=user_id)})

    @app.get("/api/exports/<int:export_id>")
    def get_export(export_id: int):
        try:
            return jsonify(svc.get_export(export_id))
        except ExportNotFoundError:
            return jsonify({"error": "not found"}), 404

    @app.get("/api/exports/<int:export_id>/download")
    def download(export_id: int):
        try:
            blob = svc.download(export_id)
        except ExportNotFoundError:
            return jsonify({"error": "expired or missing"}), 410
        except ExportError as e:
            return jsonify({"error": str(e)}), 409
        download_count.inc()
        return jsonify(blob)

    @app.get("/metrics")
    def metrics_endpoint():
        text = metrics.render()
        st = svc.status()
        text += "# queue_size {qs}\n".format(qs=st["queue_size"])
        for k, v in st["counts"].items():
            text += f"# export_status_{k} {v}\n"
        return text, 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "user_data_export",
            "endpoints": [
                "POST /api/exports",
                "GET /api/exports",
                "GET /api/exports/<id>",
                "GET /api/exports/<id>/download",
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
    port = int(os.environ.get("PORT", "8012"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)