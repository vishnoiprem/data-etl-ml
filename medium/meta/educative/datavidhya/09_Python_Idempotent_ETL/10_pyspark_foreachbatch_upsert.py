"""
Problem 10: PySpark foreachBatch upsert into Delta/Iceberg table
Meta flavor: "Streaming conversion events must end up in a Delta table keyed
by (user_id, event_id). Every micro-batch may overlap with prior batches; the
sink must dedupe via MERGE so re-running any batch yields the same rows."

How to Think:
- Use `foreachBatch` to run a Python function per micro-batch on the streaming
  DataFrame.
- Inside, build a MERGE (Delta) or `upsert` (Iceberg) keyed by the business
  identity. Source rows win by ordering; tie-break with a stable tie-breaker.
- Re-runs of the same batch are idempotent because MERGE is keyed; duplicate
  rows are absorbed.
- Use `processingTime` or `availableNow` triggers for batch-style replay.

How to Remember:
- `foreachBatch` is your transaction boundary inside a stream.

AI Use Cases
- Streaming ad conversions into a Delta table for near-real-time dashboards.
- Online feature-store writes from a Kafka stream with replay-safe semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class SinkPlan:
    """
    Plan a batch's upserts. Used in unit tests and in dry-runs; in production
    swap `execute()` for a real `delta_table.merge(...)` call.
    """
    matched: list[dict]
    inserted: list[dict]
    updated: list[dict]

    @classmethod
    def from_batch(cls, batch: Iterable[dict],
                   target_index: dict[tuple, dict]) -> "SinkPlan":
        matched, inserted, updated = [], [], []
        # Dedup within the batch first (deterministic order by key fields).
        seen: dict[tuple, dict] = {}
        for r in batch:
            k = (r.get("user_id"), r.get("event_id"))
            if k in seen:
                # keep the LATER occurrence -- explicit, not input order
                if r.get("ts", "") >= seen[k].get("ts", ""):
                    seen[k] = r
            else:
                seen[k] = r
        for k, r in seen.items():
            if k in target_index:
                matched.append(r)
                if target_index[k] != r:
                    updated.append(r)
            else:
                inserted.append(r)
        return cls(matched=matched, inserted=inserted, updated=updated)

    def execute(self, delta_or_iceberg_table) -> None:
        """
        Production version would do:
            from delta.tables import DeltaTable
            dt = DeltaTable.forName(spark, "conversions")
            (dt.alias("t")
              .merge(self._as_df(spark), "t.user_id = s.user_id AND t.event_id = s.event_id")
              .whenMatchedUpdateAll()
              .whenNotMatchedInsertAll()
              .execute())
        """
        # Stubbed: just print the plan for the demo.
        print(f"matched={len(self.matched)} "
              f"inserted={len(self.inserted)} "
              f"updated={len(self.updated)}")


def transform(batch: Iterable[dict],
              target_index: dict[tuple, dict] | None = None) -> SinkPlan:
    return SinkPlan.from_batch(batch, target_index or {})


if __name__ == "__main__":
    target = {("u1", "e1"): {"user_id": "u1", "event_id": "e1", "v": 1}}
    batch = [
        {"user_id": "u1", "event_id": "e1", "v": 99, "ts": "2026-01-10"},
        {"user_id": "u1", "event_id": "e1", "v": 1,  "ts": "2026-01-05"},  # older
        {"user_id": "u2", "event_id": "e2", "v": 5,  "ts": "2026-01-09"},
    ]
    plan = transform(batch, target)
    print("plan:", plan)
    plan.execute(target)  # would call Delta MERGE in production
    print("FOREACHBATCH_PLAN_OK")
