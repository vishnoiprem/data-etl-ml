"""Quick scaffolder: prints a working service+app+tests skeleton for a topic.

Usage:
    python3 scripts/scaffold.py --module 41_key_value_store "KeyValueStore service"

This is a *helper* for the author of the course, not for the learner.
"""

from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path


TEMPLATE_SERVICE = '''\
"""{title} — core service.

Documented in design/README.md.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


@dataclass
class {ClassName}Record:
    id: int
    created_at: float
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class {ClassName}Service:
    """A working {title}.

    >>> svc = {ClassName}Service()
    >>> r = svc.create({{"k": "v"}})
    >>> svc.get(r.id) is not None
    True
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=42)
        self.store = KeyValueStore("{store_name}")
        self.cache = TTLCache(ttl_seconds=60)

    def create(self, payload: dict) -> {ClassName}Record:
        rid = self.snow.next_id()
        rec = {ClassName}Record(id=rid, created_at=time.time(), payload=payload)
        self.store.set(f"rec:{{rid}}", rec.to_dict())
        return rec

    def get(self, rid: int) -> Optional[{ClassName}Record]:
        cached = self.cache.get(f"rec:{{rid}}")
        if cached:
            return {ClassName}Record(**cached)
        d = self.store.get(f"rec:{{rid}}")
        if not d:
            return None
        self.cache.set(f"rec:{{rid}}", d)
        return {ClassName}Record(**d)

    def stats(self) -> dict:
        return {{"items": self.store.size(), "cache": self.cache.stats()}}
'''

TEMPLATE_APP = '''\
"""{title} — HTTP service (Flask)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402

from .service import {ClassName}Service  # noqa: E402


def create_app(service: {ClassName}Service | None = None) -> Flask:
    app = Flask("{module_name}")
    svc = service or {ClassName}Service()
    metrics = MetricsRegistry()
    hist = metrics.histogram("latency_ms", "generic latency")
    count = metrics.counter("requests_total", "total requests")

    @app.get("/health")
    def health():
        return jsonify({{"ok": True, "stats": svc.stats()}})

    @app.post("/api/items")
    def create():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {{}}
            rec = svc.create(body)
            count.inc()
            return jsonify(rec.to_dict()), 201
        finally:
            hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/items/<int:rid>")
    def get(rid: int):
        rec = svc.get(rid)
        if not rec:
            return jsonify({{"error": "not found"}}), 404
        return jsonify(rec.to_dict())

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {{"Content-Type": "text/plain; version=0.0.4"}}

    @app.get("/")
    def index():
        return jsonify({{"service": "{module_name}", "stats": svc.stats()}})

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "{port}"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
'''

TEMPLATE_TEST_SERVICE = '''\
"""{title} — service tests."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import {ClassName}Service  # noqa: E402


class {ClassName}ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = {ClassName}Service()

    def test_create_and_get(self):
        rec = self.svc.create({{"k": "v"}})
        self.assertIsNotNone(self.svc.get(rec.id))

    def test_get_missing(self):
        self.assertIsNone(self.svc.get(99999))


if __name__ == "__main__":
    unittest.main()
'''

TEMPLATE_TEST_APP = '''\
"""{title} — HTTP tests."""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import {ClassName}Service  # noqa: E402


class {ClassName}AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.svc = {ClassName}Service()
        self.app = create_app(self.svc)
        self.client = self.app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)

    def test_create_and_get(self):
        r = self.client.post("/api/items", json={{"k": "v"}})
        self.assertEqual(r.status_code, 201)
        rid = r.get_json()["id"]
        r2 = self.client.get(f"/api/items/{{rid}}")
        self.assertEqual(r2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
'''


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--module", required=True, help="e.g. 41_kvstore")
    p.add_argument("title", help="Service title, e.g. Key-Value Store")
    p.add_argument("--port", default="8100")
    p.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = p.parse_args()

    cls = "".join(part.capitalize() for part in args.module.split("_") if not part.isdigit())
    module_name = args.module
    port = args.port
    out = Path(args.root) / module_name
    out.mkdir(parents=True, exist_ok=True)
    (out / "code").mkdir(exist_ok=True)
    (out / "tests").mkdir(exist_ok=True)
    (out / "design").mkdir(exist_ok=True)

    store_name = module_name.replace(".", "_")
    (out / "code" / "__init__.py").write_text("")
    (out / "tests" / "__init__.py").write_text("")
    (out / "code" / "service.py").write_text(
        TEMPLATE_SERVICE.format(title=args.title, ClassName=cls, store_name=store_name)
    )
    (out / "code" / "app.py").write_text(
        TEMPLATE_APP.format(title=args.title, ClassName=cls, module_name=module_name, port=port)
    )
    (out / "tests" / "test_service.py").write_text(
        TEMPLATE_TEST_SERVICE.format(title=args.title, ClassName=cls)
    )
    (out / "tests" / "test_app.py").write_text(
        TEMPLATE_TEST_APP.format(title=args.title, ClassName=cls)
    )
    print(f"Scaffolded {out}")


if __name__ == "__main__":
    main()
