"""
Delete Coordinator — orchestrates deletion across all systems.

Uses plug-in adapters. Each adapter returns a signed receipt.
Workflow is idempotent and resumable.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Awaitable, Callable, Dict, List

from discovery import DiscoveryResult, DataLocation


@dataclass
class Receipt:
    system: str
    table_or_key: str
    rows_deleted: int
    objects_deleted: int
    method: str
    started_at: float
    completed_at: float
    status: str              # OK | FAILED
    error: str = ""

    def hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()


# Adapter protocol: (user_id, location) -> Receipt
Adapter = Callable[[str, DataLocation], Awaitable[Receipt]]


class DeleteCoordinator:
    def __init__(self, adapters: Dict[str, Adapter]):
        self.adapters = adapters

    async def execute(self, user_id: str, discovery: DiscoveryResult) -> List[Receipt]:
        receipts: List[Receipt] = []
        # Run independent deletes in parallel
        tasks = []
        for loc in discovery.locations:
            adapter = self.adapters.get(loc.system)
            if adapter is None:
                receipts.append(Receipt(
                    system=loc.system, table_or_key=loc.table_or_key,
                    rows_deleted=0, objects_deleted=0, method=loc.delete_method,
                    started_at=time.time(), completed_at=time.time(),
                    status="FAILED", error=f"no_adapter:{loc.system}",
                ))
                continue
            tasks.append(self._run_with_retry(user_id, loc, adapter))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                receipts.append(Receipt(
                    system="unknown", table_or_key="",
                    rows_deleted=0, objects_deleted=0, method="",
                    started_at=time.time(), completed_at=time.time(),
                    status="FAILED", error=str(r),
                ))
            else:
                receipts.append(r)
        return receipts

    async def _run_with_retry(self, user_id: str, loc: DataLocation,
                              adapter: Adapter, max_retries: int = 3) -> Receipt:
        for attempt in range(max_retries):
            try:
                return await adapter(user_id, loc)
            except Exception as e:
                if attempt == max_retries - 1:
                    return Receipt(
                        system=loc.system, table_or_key=loc.table_or_key,
                        rows_deleted=0, objects_deleted=0, method=loc.delete_method,
                        started_at=time.time(), completed_at=time.time(),
                        status="FAILED", error=str(e),
                    )
                await asyncio.sleep(2 ** attempt)


# --------------------------------------------------------------------- #
# Sample adapters (real prod would call into actual systems)
# --------------------------------------------------------------------- #

async def iceberg_adapter(user_id: str, loc: DataLocation) -> Receipt:
    """Trino/Spark: DELETE FROM table WHERE user_id = ?"""
    started = time.time()
    await asyncio.sleep(0.01)
    return Receipt(
        system="iceberg", table_or_key=loc.table_or_key,
        rows_deleted=loc.estimated_rows, objects_deleted=0,
        method=loc.delete_method,
        started_at=started, completed_at=time.time(),
        status="OK",
    )


async def warehouse_adapter(user_id: str, loc: DataLocation) -> Receipt:
    started = time.time()
    await asyncio.sleep(0.02)
    return Receipt(
        system="warehouse", table_or_key=loc.table_or_key,
        rows_deleted=loc.estimated_rows, objects_deleted=0,
        method=loc.delete_method,
        started_at=started, completed_at=time.time(),
        status="OK",
    )


async def elasticsearch_adapter(user_id: str, loc: DataLocation) -> Receipt:
    started = time.time()
    await asyncio.sleep(0.015)
    return Receipt(
        system="es", table_or_key=loc.table_or_key,
        rows_deleted=loc.estimated_rows, objects_deleted=0,
        method=loc.delete_method,
        started_at=started, completed_at=time.time(),
        status="OK",
    )


async def redis_adapter(user_id: str, loc: DataLocation) -> Receipt:
    started = time.time()
    await asyncio.sleep(0.005)
    return Receipt(
        system="redis", table_or_key=loc.table_or_key,
        rows_deleted=1, objects_deleted=0,
        method="direct",
        started_at=started, completed_at=time.time(),
        status="OK",
    )


async def s3_adapter(user_id: str, loc: DataLocation) -> Receipt:
    started = time.time()
    await asyncio.sleep(0.02)
    return Receipt(
        system="s3", table_or_key=loc.table_or_key,
        rows_deleted=0, objects_deleted=loc.estimated_rows,
        method="direct",
        started_at=started, completed_at=time.time(),
        status="OK",
    )


async def ml_adapter(user_id: str, loc: DataLocation) -> Receipt:
    """Mark features as deleted; ML models don't need retraining."""
    started = time.time()
    await asyncio.sleep(0.01)
    return Receipt(
        system="ml", table_or_key=loc.table_or_key,
        rows_deleted=loc.estimated_rows, objects_deleted=0,
        method="soft_delete",
        started_at=started, completed_at=time.time(),
        status="OK",
    )


# --------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------- #

async def demo():
    from discovery import discover
    coord = DeleteCoordinator({
        "iceberg":   iceberg_adapter,
        "warehouse": warehouse_adapter,
        "redis":     redis_adapter,
        "s3":        s3_adapter,
        "es":        elasticsearch_adapter,
        "ml":        ml_adapter,
    })
    d = discover("user_42")
    receipts = await coord.execute("user_42", d)
    print(f"\nGot {len(receipts)} receipts:")
    for r in receipts:
        print(f"  {r.system:10s} {r.table_or_key:35s} status={r.status} "
              f"rows={r.rows_deleted} method={r.method}")


if __name__ == "__main__":
    asyncio.run(demo())
