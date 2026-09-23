# Dead-Letter Queue + Quarantine

## Problem
Handle poison-pill records (always-failing rows) without breaking the
pipeline.

## How to Think
1. **Detect** poison-pill records during process().
2. **Route** failures to a DLQ table with full error metadata.
3. **Continue** processing good records.
4. **Alert** on DLQ growth rate.
5. **Replay** fixed records back into prod.

## How to Remember
- **DLQ schema**: error_record + error_reason + source + ingest_ts.
- **Never let poison-pill break the pipeline.**

## DLQ Schema
- raw_record (JSON string of original)
- error_type
- error_message
- source_topic
- source_partition
- ingest_ts

## Code (Process with DLQ)
```python
import json
from datetime import datetime

def process_with_dlq(record, dlq_writer):
    try:
        validate(record); transform(record); load(record)
    except Exception as e:
        dlq_writer.write({
            "raw_record":      json.dumps(record),
            "error_type":      type(e).__name__,
            "error_message":   str(e),
            "source_topic":    record.get("_topic"),
            "source_partition":record.get("_partition"),
            "ingest_ts":       datetime.utcnow().isoformat(),
        })
```

## SQL (DLQ Growth Investigation)
```sql
SELECT error_type, source_topic,
       DATE_TRUNC('hour', ingest_ts) AS hr,
       COUNT(*) AS n_errors
FROM dlq.events
WHERE ingest_ts >= CURRENT_DATE - INTERVAL '24' HOUR
GROUP BY error_type, source_topic, hr
ORDER BY hr DESC, n_errors DESC;
```

## Common Mistakes
- No DLQ -> one bad record breaks the whole job.
- DLQ with no metadata -> can't debug.
- Never replaying DLQ -> permanent data loss.

## AI Use Cases
- Auto-classify DLQ rows by error type.
- Smart replay after upstream fix.
- Anomaly detection on DLQ growth rate.
