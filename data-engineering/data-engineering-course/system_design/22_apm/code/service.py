"""APM service: span ingest, trace lookup, per-service error rate + latency."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

MAX_SPANS_PER_SVC = 5_000
MAX_TRACES = 10_000


def _now_ms() -> int:
    return int(time.time() * 1000)


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = max(0, min(len(sorted_vals) - 1, int(q * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


class APMService:
    """Tiny distributed APM."""

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        snowflake: Optional[Snowflake] = None,
    ):
        self.store = store or KeyValueStore("apm", persist_path=None)
        self.id_gen = snowflake or Snowflake(machine_id=2)

    # ------------------------------------------------------------------
    # Span ingest
    # ------------------------------------------------------------------

    def ingest_span(
        self,
        trace_id: str,
        service: str,
        name: str,
        start_ms: Optional[int] = None,
        duration_ms: float = 0.0,
        span_id: Optional[int] = None,
        parent_span_id: Optional[int] = 0,
        status: str = "ok",
        tags: Optional[dict] = None,
    ) -> dict:
        if not trace_id or not service or not name:
            raise ValueError("trace_id, service, and name are required")
        sid = int(span_id) if span_id is not None else self.id_gen.next_id()
        psid = int(parent_span_id) if parent_span_id is not None else 0
        ts = int(start_ms) if start_ms is not None else _now_ms()
        span = {
            "trace_id": trace_id,
            "span_id": sid,
            "parent_span_id": psid,
            "service": service,
            "name": name,
            "start_ms": ts,
            "duration_ms": float(duration_ms),
            "status": status,
            "tags": tags or {},
        }

        trace_key = f"trace:{trace_id}"
        spans_for_trace = list(self.store.get(trace_key) or [])
        spans_for_trace.append(span)
        self.store.set(trace_key, spans_for_trace)

        svc_key = f"svc:{service}:spans"
        spans_for_svc = list(self.store.get(svc_key) or [])
        spans_for_svc.append(span)
        if len(spans_for_svc) > MAX_SPANS_PER_SVC:
            spans_for_svc = spans_for_svc[-MAX_SPANS_PER_SVC:]
        self.store.set(svc_key, spans_for_svc)

        # update services index
        services = dict(self.store.get("services") or {})
        services[service] = services.get(service, 0) + 1
        self.store.set("services", services)

        # update trace index
        idx = list(self.store.get("traces:index") or [])
        if trace_id not in idx:
            idx.append(trace_id)
            if len(idx) > MAX_TRACES:
                drop = len(idx) - MAX_TRACES
                for old in idx[:drop]:
                    self.store.delete(f"trace:{old}")
                idx = idx[drop:]
            self.store.set("traces:index", idx)

        return span

    # ------------------------------------------------------------------
    # Trace lookup
    # ------------------------------------------------------------------

    def get_trace(self, trace_id: str) -> dict:
        spans = list(self.store.get(f"trace:{trace_id}") or [])
        if not spans:
            return {"trace_id": trace_id, "spans": [], "roots": []}
        by_id: dict[int, dict] = {}
        for s in spans:
            by_id[s["span_id"]] = {**s, "children": []}
        roots = []
        for s in by_id.values():
            pid = s.get("parent_span_id", 0)
            if pid and pid in by_id:
                by_id[pid]["children"].append(s)
            else:
                roots.append(s)
        return {
            "trace_id": trace_id,
            "spans": list(by_id.values()),
            "roots": roots,
        }

    def list_traces(self) -> list[str]:
        return list(self.store.get("traces:index") or [])

    # ------------------------------------------------------------------
    # Services / error rate / latency
    # ------------------------------------------------------------------

    def list_services(self) -> list[dict]:
        services = self.store.get("services") or {}
        return [
            {"name": name, "span_count": count}
            for name, count in sorted(services.items())
        ]

    def service_error_rate(self, service: str, window_s: int = 300,
                           with_latency: bool = False) -> dict:
        spans = list(self.store.get(f"svc:{service}:spans") or [])
        cutoff = _now_ms() - window_s * 1000
        recent = [s for s in spans if int(s.get("start_ms", 0)) >= cutoff]
        if not recent:
            return {
                "service": service,
                "total": 0,
                "errors": 0,
                "error_rate": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
            }
        errors = sum(1 for s in recent if s.get("status") == "error")
        durations = sorted(float(s.get("duration_ms", 0.0)) for s in recent)
        out = {
            "service": service,
            "total": len(recent),
            "errors": errors,
            "error_rate": errors / len(recent),
        }
        if with_latency:
            out["p50_ms"] = _percentile(durations, 0.50)
            out["p95_ms"] = _percentile(durations, 0.95)
            out["p99_ms"] = _percentile(durations, 0.99)
        return out

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        services = self.store.get("services") or {}
        traces = self.store.get("traces:index") or []
        return {
            "services": len(services),
            "traces": len(traces),
        }
