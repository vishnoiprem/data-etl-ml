"""S3-style Object Store — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, Response, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from service import ObjectStoreService  # noqa: E402


def create_app(service: ObjectStoreService | None = None) -> Flask:
    app = Flask("s3_storage")
    base_dir = str(HERE / "var" / "s3")
    service = service or ObjectStoreService(base_dir=base_dir)
    metrics = MetricsRegistry()
    put_hist = metrics.histogram("put_latency_ms", "PUT latency")
    get_hist = metrics.histogram("get_latency_ms", "GET latency")
    put_count = metrics.counter("put_total", "PUT requests")
    get_count = metrics.counter("get_total", "GET requests")
    delete_count = metrics.counter("delete_total", "DELETE requests")
    list_count = metrics.counter("list_total", "LIST requests")
    mp_count = metrics.counter("multipart_total", "Multipart operations")

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    # ---- bucket + key routing ------------------------------------------
    # Path forms we handle:
    #   /<bucket>/          (list)
    #   /<bucket>/<key>...  (object ops)

    @app.route("/<bucket>/", methods=["GET"])
    def list_endpoint(bucket: str):
        prefix = request.args.get("prefix", "")
        max_keys = int(request.args.get("max_keys", "1000"))
        try:
            keys = service.list_objects(bucket, prefix=prefix, max_keys=max_keys)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        list_count.inc()
        return jsonify({
            "bucket": bucket,
            "prefix": prefix,
            "key_count": len(keys),
            "keys": keys,
        })

    @app.route("/<bucket>/<path:key>", methods=["PUT"])
    def put_endpoint(bucket: str, key: str):
        start = time.perf_counter()
        try:
            upload_id = request.args.get("uploadId")
            part_number = request.args.get("partNumber")
            data = request.get_data() or b""
            if upload_id and part_number:
                # Multipart part upload
                try:
                    pn = int(part_number)
                    res = service.upload_part(upload_id, pn, data)
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
                mp_count.inc()
                return jsonify(res)
            if upload_id and request.args.get("complete"):
                try:
                    res = service.complete_multipart(upload_id)
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
                mp_count.inc()
                return jsonify(res), 200
            try:
                res = service.put(bucket, key, data)
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            put_count.inc()
            return jsonify(res), 200
        finally:
            put_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.route("/<bucket>/<path:key>", methods=["GET"])
    def get_endpoint(bucket: str, key: str):
        start = time.perf_counter()
        try:
            version_id = request.args.get("versionId")
            res = service.get(bucket, key, version_id=version_id)
            get_count.inc()
            if res is None:
                return jsonify({"error": "not found"}), 404
            data, version = res
            resp = Response(data, mimetype="application/octet-stream")
            resp.headers["ETag"] = version.etag
            resp.headers["x-version-id"] = version.version_id
            resp.headers["Content-Length"] = str(version.size)
            return resp
        finally:
            get_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.route("/<bucket>/<path:key>", methods=["HEAD"])
    def head_endpoint(bucket: str, key: str):
        version_id = request.args.get("versionId")
        v = service.head(bucket, key, version_id=version_id)
        if v is None:
            return Response(status=404)
        resp = Response(status=200)
        resp.headers["ETag"] = v.etag
        resp.headers["x-version-id"] = v.version_id
        resp.headers["Content-Length"] = str(v.size)
        resp.headers["x-deleted"] = "1" if v.deleted else "0"
        return resp

    @app.route("/<bucket>/<path:key>", methods=["DELETE"])
    def delete_endpoint(bucket: str, key: str):
        version_id = service.delete(bucket, key)
        delete_count.inc()
        if version_id is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"bucket": bucket, "key": key, "version_id": version_id, "deleted": True})

    # ---- multipart init (POST /<bucket>/<path:key>?uploads) -----------

    @app.route("/<bucket>/<path:key>", methods=["POST"])
    def post_endpoint(bucket: str, key: str):
        if request.args.get("uploads"):
            try:
                upload_id = service.init_multipart(bucket, key)
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            mp_count.inc()
            return jsonify({"bucket": bucket, "key": key, "upload_id": upload_id}), 200
        return jsonify({"error": "unsupported POST"}), 400

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "s3_storage",
            "endpoints": [
                "PUT /<bucket>/<key>",
                "GET /<bucket>/<key>",
                "HEAD /<bucket>/<key>",
                "DELETE /<bucket>/<key>",
                "GET /<bucket>/?prefix=...",
                "POST /<bucket>/<key>?uploads",
                "POST /<bucket>/<key>?uploadId=...&partNumber=N",
                "POST /<bucket>/<key>?uploadId=...&complete",
                "GET /metrics",
                "GET /health",
            ],
            "buckets": service.list_buckets(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8017"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
