"""Metrics + Logging service.

Stores time-series samples in a KeyValueStore, bucketed by series key, and
log lines in a separate index. Range queries bucket samples on read and
apply `sum/avg/max/min/count` aggregations. Log search is a substring scan
over the message + label values.
"""

from __future__ import annotations

import re
import time
from typing import Any, Iterable, Optional

from common.storage import KeyValueStore

MAX_SAMPLES_PER_SERIES = 10_000
MAX_LOG_LINES = 50_000
AGG_FNS = {"sum", "avg", "max", "min", "count"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _series_key(name: str, labels: dict) -> str:
    """Compose a stable, normalized key for a metric series.

    Label keys are sorted to make `(a=1, b=2)` and `(b=2, a=1)` the same
    series — same convention as Prometheus.
    """
    if not labels:
        return f"series:{name}:"
    parts = ",".join(f"{k}={labels[k]}" for k in sorted(labels.keys()))
    return f"series:{name}:{parts}"


def _parse_ts(ts: Any) -> int:
    """Accept seconds (small) or ms (large) and return ms."""
    try:
        v = float(ts)
    except (TypeError, ValueError):
        return _now_ms()
    # Heuristic: < 10^12 means seconds.
    if v < 1e12:
        return int(v * 1000)
    return int(v)


class MetricsLoggingService:
    """In-process time-series metrics + log query."""

    def __init__(self, store: Optional[KeyValueStore] = None):
        self.store = store or KeyValueStore("metrics_logging", persist_path=None)
        self._log_seq = 0  # monotonic sequence for log keys

    # ------------------------------------------------------------------
    # Metric ingest
    # ------------------------------------------------------------------

    def ingest_metric(
        self, name: str, value: float, labels: Optional[dict] = None,
        ts: Optional[float] = None,
    ) -> dict:
        if not name:
            raise ValueError("name required")
        ts_ms = _parse_ts(ts) if ts is not None else _now_ms()
        key = _series_key(name, labels or {})
        rec = self.store.get(key) or {"samples": []}
        rec["samples"].append([ts_ms, float(value)])
        if len(rec["samples"]) > MAX_SAMPLES_PER_SERIES:
            rec["samples"] = rec["samples"][-MAX_SAMPLES_PER_SERIES:]
        rec["first_ts"] = rec["samples"][0][0]
        rec["last_ts"] = rec["samples"][-1][0]
        self.store.set(key, rec)
        return {"ok": True, "series": key, "ts": ts_ms, "value": value}

    def ingest_many(self, items: Iterable[dict]) -> int:
        n = 0
        for it in items:
            self.ingest_metric(
                it["name"],
                float(it["value"]),
                it.get("labels") or {},
                it.get("ts"),
            )
            n += 1
        return n

    # ------------------------------------------------------------------
    # Range query
    # ------------------------------------------------------------------

    def query(
        self,
        metric: str,
        ts_from: float,
        ts_to: float,
        step: float = 60.0,
        agg: str = "avg",
        label_filter: Optional[dict] = None,
    ) -> dict:
        if agg not in AGG_FNS:
            raise ValueError(f"agg must be one of {sorted(AGG_FNS)}")
        if step <= 0:
            step = 60.0
        from_ms = _parse_ts(ts_from)
        to_ms = _parse_ts(ts_to)
        if to_ms <= from_ms:
            return {"metric": metric, "step": step, "agg": agg, "points": []}

        prefix = f"series:{metric}:"
        # Aggregate across all matching series per bucket.
        bucket_vals: dict[int, list[float]] = {}
        for k, v in self.store.scan(prefix):
            if not isinstance(v, dict) or "samples" not in v:
                continue
            if label_filter and not _series_matches(k, label_filter):
                continue
            for ts, val in v["samples"]:
                if ts < from_ms or ts > to_ms:
                    continue
                b = (ts // int(step * 1000)) * int(step * 1000)
                bucket_vals.setdefault(b, []).append(float(val))

        points = []
        for b in sorted(bucket_vals):
            vals = bucket_vals[b]
            points.append({"t": b, "v": _apply_agg(agg, vals)})
        return {"metric": metric, "step": step, "agg": agg, "points": points}

    def list_series(self, metric: str) -> list[str]:
        prefix = f"series:{metric}:"
        return [k for k in self.store.keys_with_prefix(prefix)]

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def ingest_log(
        self, msg: str, level: str = "info",
        labels: Optional[dict] = None, ts: Optional[float] = None,
    ) -> dict:
        ts_ms = _parse_ts(ts) if ts is not None else _now_ms()
        bucket = ts_ms // 60_000
        idx_key = "logs:index"
        seq = self._log_seq
        self._log_seq += 1
        rec = {"ts": ts_ms, "level": level, "msg": msg, "labels": labels or {}}
        self.store.set(f"log:{bucket}:{seq}", rec)
        idx = self.store.get(idx_key) or []
        idx.append(seq)
        if len(idx) > MAX_LOG_LINES:
            # drop oldest indices to bound memory
            drop = len(idx) - MAX_LOG_LINES
            for old_seq in idx[:drop]:
                # find and drop the corresponding key
                self._drop_log_key_for_seq(old_seq)
            idx = idx[drop:]
        self.store.set(idx_key, idx)
        return {"ok": True, "ts": ts_ms, "seq": seq}

    def search_logs(self, q: str, limit: int = 100) -> list[dict]:
        idx = self.store.get("logs:index") or []
        if not q:
            # Return most recent `limit` lines.
            seqs = idx[-limit:]
        else:
            try:
                pattern = re.compile(re.escape(q), re.IGNORECASE)
            except re.error:
                pattern = re.compile(re.escape(q))
            seqs = [s for s in idx if self._log_matches(s, pattern)]
        out = []
        for seq in reversed(seqs):
            rec = self._get_log_by_seq(seq)
            if rec is not None:
                out.append(rec)
                if len(out) >= limit:
                    break
        return out

    def _log_matches(self, seq: int, pattern: re.Pattern) -> bool:
        rec = self._get_log_by_seq(seq)
        if not rec:
            return False
        haystack = rec.get("msg", "") + " " + " ".join(
            f"{k}={v}" for k, v in (rec.get("labels") or {}).items()
        )
        return pattern.search(haystack) is not None

    def _get_log_by_seq(self, seq: int) -> Optional[dict]:
        # We don't know the bucket, so scan keys.
        for k, v in self.store.scan("log:"):
            if not k.startswith("log:"):
                continue
            if k.endswith(f":{seq}"):
                v = dict(v)
                v["seq"] = seq
                return v
        return None

    def _drop_log_key_for_seq(self, seq: int) -> None:
        for k, _ in self.store.scan("log:"):
            if k.endswith(f":{seq}"):
                self.store.delete(k)
                return

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        series_count = len(self.store.keys_with_prefix("series:"))
        log_count = len(self.store.get("logs:index") or [])
        return {
            "series": series_count,
            "logs": log_count,
            "log_seq": self._log_seq,
        }


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _apply_agg(agg: str, vals: list[float]) -> float:
    if not vals:
        return 0.0
    if agg == "sum":
        return sum(vals)
    if agg == "avg":
        return sum(vals) / len(vals)
    if agg == "max":
        return max(vals)
    if agg == "min":
        return min(vals)
    if agg == "count":
        return float(len(vals))
    return 0.0


def _series_matches(series_key: str, label_filter: dict) -> bool:
    # series_key looks like "series:<name>:k1=v1,k2=v2"
    try:
        tail = series_key.split(":", 2)[2]
    except IndexError:
        return False
    pairs = {}
    if tail:
        for chunk in tail.split(","):
            if "=" in chunk:
                k, v = chunk.split("=", 1)
                pairs[k] = v
    for k, expected in label_filter.items():
        if str(pairs.get(k)) != str(expected):
            return False
    return True
