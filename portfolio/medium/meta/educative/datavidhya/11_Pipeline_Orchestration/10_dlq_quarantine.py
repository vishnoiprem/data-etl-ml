"""
Problem 10: Dead-letter queue + quarantine for poison-pill data.

Meta flavor: Some records will always fail (bad schema, NULL where NOT
NULL, business-rule violation). Don't break the whole pipeline.

How to Think:
- Detect poison-pill records.
- Quarantine them in a separate DLQ table with error metadata.
- Continue processing good records.
- Alert on DLQ growth (poison-pill flood).

How to Remember:
- "DLQ = error_record + error_reason + source_partition + ingest_ts."
- "Never let poison-pill break the pipeline."

AI Use Cases:
- Auto-classify DLQ rows by error type.
- Smart re-processing after upstream fix.
- Anomaly detection on DLQ growth rate.
"""
import json
from datetime import datetime

DLQ_SCHEMA = [
    "raw_record", "error_type", "error_message",
    "source_topic", "source_partition", "ingest_ts",
]

def process_with_dlq(record, dlq_writer):
    """Process a record; route failures to DLQ instead of crashing."""
    try:
        validate(record)
        transform(record)
        load(record)
    except Exception as e:
        dlq_writer.write({
            "raw_record":      json.dumps(record),
            "error_type":      type(e).__name__,
            "error_message":   str(e),
            "source_topic":    record.get("_topic"),
            "source_partition":record.get("_partition"),
            "ingest_ts":       datetime.utcnow().isoformat(),
        })

# SQL: investigate DLQ growth
SQL_DLQ_INVESTIGATE = """
SELECT error_type, source_topic,
       DATE_TRUNC('hour', ingest_ts) AS hr,
       COUNT(*) AS n_errors
FROM dlq.events
WHERE ingest_ts >= CURRENT_DATE - INTERVAL '24' HOUR
GROUP BY error_type, source_topic, hr
ORDER BY hr DESC, n_errors DESC;
"""

# Replay fixed records back into prod
def replay_dlq(error_type, fixed_after):
    spark.sql(f"""
        INSERT INTO prod.events
        SELECT from_json(raw_record, '...') AS r,
               current_timestamp() AS replayed_at
        FROM dlq.events
        WHERE error_type = '{error_type}'
          AND ingest_ts >= '{fixed_after}'
    """)
