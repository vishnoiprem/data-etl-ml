"""
Problem 09: Cross-region replication.

Meta flavor: Move data from primary region (us-east-1) to secondary
(eu-west-1) for DR / data-residency.

How to Think:
- S3 cross-region replication (CRR) for raw + curated tiers.
- Iceberg / Delta can replicate metadata via Glue catalog mirroring.
- For latency-sensitive: stream via Kafka MirrorMaker.
- For batch: distcp / s3-dist-cp.

How to Remember:
- "S3 CRR for files; Kafka MirrorMaker for streams; Iceberg/Delta metadata
  via catalog sync."
- "Always replicate encrypted + versioned buckets."

AI Use Cases:
- Auto-detect data-residency requirements from user geo.
- Smart replication policies (cost vs lag).
- Anomaly detection on replication lag.
"""
REPLICATION_PATTERNS = {
    "object_storage": {
        "tool":      "S3 Cross-Region Replication (CRR)",
        "use_when":  "raw + curated Parquet tables, RPO hours acceptable",
        "lag":       "minutes-hours",
        "cost":      "$ per GB replicated + storage",
    },
    "stream": {
        "tool":      "Kafka MirrorMaker 2 / MSK Replicator",
        "use_when":  "near-realtime replication, RPO seconds",
        "lag":       "seconds",
        "cost":      "EC2 / MSK hours",
    },
    "table_format": {
        "tool":      "Iceberg / Delta catalog sync (Glue / Polaris)",
        "use_when":  "ACID table metadata must also replicate",
        "lag":       "minutes",
        "cost":      "metadata + storage",
    },
}

CHECKLIST = [
    "1. Encrypt source + dest buckets.",
    "2. Enable versioning on both sides.",
    "3. Replicate IAM policies / bucket policies.",
    "4. Monitor replication lag with a watchdog metric.",
    "5. Test restore from secondary quarterly.",
    "6. Document RPO / RTO for each tier.",
]
