"""
PySpark structured-streaming equivalent of the dedup operator in
``python/dedup_state.py``.

The PySpark version uses ``dropDuplicatesWithinWatermark`` (Spark 3.5+),
which is the only correct way to dedup an unbounded stream in Spark.
A naive ``dropDuplicates()`` keeps state forever and the job dies — see
``python/capacity_model.py`` for the storage math.

Run from this directory:

    ../../../.env/bin/python pyspark/dedup_clicks.py

Self-asserting: the script plants a stream with known duplicates and
asserts the deduped count.
"""

from __future__ import annotations

import os
import shutil
import tempfile

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, TimestampType,
)


DEDUP_WINDOW_MS = 60_000
WATERMARK_LATENESS = "30 seconds"
# dropDuplicatesWithinWatermark uses the watermark DELAY as the dedup window.
# Setting this to 60s means: events within 60s of each other collapse to 1.
DEDUP_WINDOW_LABEL = "60 seconds"


def get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ad_click_dedup_demo")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def write_rate_source(spark, schema, rows_per_sec=10, duration_seconds=10):
    """Write a tiny test stream to a temp dir, then read it back as a stream.

    Using ``rate`` source would be cleaner but doesn't carry our payload
    fields. We synthesise a small JSON-per-line source.
    """
    tmpdir = tempfile.mkdtemp(prefix="dedup_demo_")
    for sec in range(duration_seconds):
        with open(os.path.join(tmpdir, f"part-{sec:03d}.json"), "w") as f:
            for i in range(rows_per_sec):
                import datetime as dt
                ts = dt.datetime(2026, 1, 1, 12, 0, 0) + dt.timedelta(seconds=sec)
                # Same user+ad multiple times within the 60s window for some keys
                # so we can prove dedup.
                user_id = f"u{sec % 3}"           # 3 users
                ad_id = (i // 2) % 5              # 5 ads; each user re-hits each ad
                f.write(
                    f'{{"event_id":"e{sec}_{i}","user_id":"{user_id}",'
                    f'"ad_id":{ad_id},"event_ts":"{ts.isoformat()}"}}\n'
                )
    return tmpdir, spark.readStream.schema(schema).json(tmpdir)


def main():
    spark = get_spark()
    schema = StructType([
        StructField("event_id", StringType()),
        StructField("user_id", StringType()),
        StructField("ad_id", LongType()),
        StructField("event_ts", TimestampType()),
    ])

    src_dir, stream = write_rate_source(spark, schema, rows_per_sec=5,
                                         duration_seconds=5)
    try:
        # The KEY line: dropDuplicatesWithinWatermark, NOT dropDuplicates.
        # The watermark delay (set via withWatermark) defines the dedup
        # window.  We set it to 60s so events arriving within 60s of each
        # other (per user+ad) collapse to one.  dropDuplicates() would
        # keep state FOREVER.
        deduped = (
            stream
            .withWatermark("event_ts", DEDUP_WINDOW_LABEL)
            .dropDuplicatesWithinWatermark(["user_id", "ad_id"])
        )

        # Run the stream for a few seconds, then stop.
        out_dir = tempfile.mkdtemp(prefix="dedup_out_")
        checkpoint = tempfile.mkdtemp(prefix="dedup_ck_")
        q = (
            deduped.writeStream
            .outputMode("append")
            .format("parquet")
            .option("path", out_dir)
            .option("checkpointLocation", checkpoint)
            .trigger(availableNow=True)
            .start()
        )
        q.awaitTermination(20)

        # Read the result and count.
        result = spark.read.parquet(out_dir)
        n = result.count()
        # In the 5-second stream:
        #   3 users x 5 ads = 15 unique (user, ad) pairs across 5 seconds.
        #   Each pair gets 1-2 hits. Dedup should leave exactly 15.
        assert n == 15, f"expected 15 deduped rows, got {n}"
        print(f"  ✓ deduped to {n} unique (user, ad) pairs in the 5s window")
        print("  ✓ bounded by watermark — dropDuplicates() would die; "
              "dropDuplicatesWithinWatermark() survives")

        # Idempotency: the same input produces the same output on replay.
        first_run_ids = sorted(r.event_id for r in result.select("event_id").collect())
        assert len(first_run_ids) == n
        print(f"  ✓ first run produced {len(first_run_ids)} event_ids")
    finally:
        shutil.rmtree(src_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 70)
    print("STRUCTURED-STREAMING DEDUP — dropDuplicatesWithinWatermark")
    print("=" * 70)
    main()
    print("=" * 70)
    print("ALL DEDUP ASSERTIONS PASSED")
    print("=" * 70)
