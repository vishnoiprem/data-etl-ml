"""
Discovery Service — find every place user data lives.

Combines:
  - Data catalog (table/column metadata)
  - Lineage graph (downstream transformations)
  - Search index lookup (Elasticsearch)
  - Key-value store lookup (Redis)
  - Object storage inventory (S3)

Returns a unified list of locations to delete from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class DataLocation:
    system: str             # 'iceberg' | 'warehouse' | 'redis' | 's3' | 'es' | 'ml'
    table_or_key: str
    delete_method: str      # 'direct' | 'crypto_shred' | 'soft_delete'
    estimated_rows: int = 0
    needs_propagation: bool = False    # has downstream tables


@dataclass
class DiscoveryResult:
    user_id: str
    locations: List[DataLocation] = field(default_factory=list)
    lineage_depth: int = 0


# In-memory mock of catalog + lineage
SAMPLE_LOCATIONS = {
    "user_42": [
        DataLocation("iceberg",    "local.bronze.events",        "direct",        1_000_000),
        DataLocation("iceberg",    "local.silver.events",        "direct",          500_000),
        DataLocation("iceberg",    "local.gold.user_features_daily","direct",       1_000),
        DataLocation("iceberg",    "local.gold.session_metrics", "direct",            200),
        DataLocation("warehouse",  "analytics.dwd.events",       "direct",          500_000),
        DataLocation("redis",      "user:42:session",            "direct",              1),
        DataLocation("es",         "events-2026-09",             "direct",          500_000),
        DataLocation("s3",         "exports/user_42/",           "direct",             50),
        DataLocation("ml",         "feast.user_features",        "soft_delete",    1_000),
        DataLocation("iceberg",    "local.gold.funnel_daily",    "soft_delete",    1_000),  # aggregated
    ],
}


def discover(user_id: str) -> DiscoveryResult:
    """Mock: in prod, query Hive metastore + DataHub + Elasticsearch + Redis."""
    return DiscoveryResult(
        user_id=user_id,
        locations=SAMPLE_LOCATIONS.get(user_id, []),
        lineage_depth=3,
    )


if __name__ == "__main__":
    import json
    r = discover("user_42")
    print(f"User {r.user_id}: found in {len(r.locations)} systems")
    for loc in r.locations:
        print(f"  {loc.system:12s} {loc.table_or_key:35s} "
              f"method={loc.delete_method:14s} rows≈{loc.estimated_rows}")
