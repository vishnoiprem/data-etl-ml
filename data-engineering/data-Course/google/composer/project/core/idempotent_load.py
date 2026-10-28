from __future__ import annotations
from typing import Iterable, Mapping

def apply_load(existing, incoming, *, mode="truncate", partitions=None):
    table = {region: dict(bucket) for region, bucket in existing.items()}
    if mode == "append":
        for region, bucket in incoming.items():
            current = table.setdefault(region, {"order_count": 0.0, "revenue_eur": 0.0})
            current["order_count"] += bucket["order_count"]
            current["revenue_eur"] = round(current["revenue_eur"] + bucket["revenue_eur"], 2)
        return table
    if mode == "truncate":
        scope = set(partitions) if partitions is not None else set(incoming)
        for region in scope:
            if region in incoming:
                table[region] = dict(incoming[region])
            else:
                table.pop(region, None)
        return table
    raise ValueError(f"unknown write mode: {mode!r}")
