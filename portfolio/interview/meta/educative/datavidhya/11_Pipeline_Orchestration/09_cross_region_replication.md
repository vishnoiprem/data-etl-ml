# Cross-Region Replication

## Problem
Replicate data from primary region (us-east-1) to secondary (eu-west-1) for
DR and data-residency.

## How to Think
1. **Object storage** – S3 Cross-Region Replication (CRR).
2. **Streams** – Kafka MirrorMaker 2 / MSK Replicator.
3. **Table formats** – Iceberg/Delta catalog sync.
4. **Always encrypt + version** both sides.
5. **Test restore** quarterly.

## How to Remember
- **"S3 CRR for files; MirrorMaker for streams; Iceberg/Delta for ACID."**
- **"RPO drives the choice: hours vs seconds."**

## Pattern Matrix
| Tier | Tool | Use when | Lag |
|---|---|---|---|
| Object storage | S3 CRR | Raw + curated Parquet | min-hours |
| Stream | Kafka MirrorMaker 2 | Near-realtime | seconds |
| Table format | Iceberg/Delta catalog sync | ACID metadata must replicate | minutes |

## Checklist
1. Encrypt source + dest buckets.
2. Enable versioning on both sides.
3. Replicate IAM policies.
4. Monitor replication lag with a watchdog metric.
5. Test restore from secondary quarterly.
6. Document RPO / RTO for each tier.

## Common Mistakes
- No versioning -> deletes don't replicate.
- Forgetting IAM / bucket policies.
- No lag monitoring -> silent DR failure.

## AI Use Cases
- Auto-detect data-residency requirements from user geo.
- Smart replication policies (cost vs lag trade-off).
- Anomaly detection on replication lag.
