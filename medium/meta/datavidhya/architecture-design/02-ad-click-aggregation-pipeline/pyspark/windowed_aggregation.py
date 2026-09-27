"""
Windowed aggregation in PySpark with two-stage salted aggregation.

The hot-key problem: a Super Bowl campaign generates 10x the volume of
any other, and naively partitioning by ``campaign_id`` puts all of that
load on one task while the others idle. The fix is two-stage salted
aggregation:

  Stage 1: aggregate per (campaign_id, salt) where salt = hash(event_id) % 64
  Stage 2: SUM the salts to get the per-campaign aggregate

This script demonstrates both stages on a synthetic stream with one
"hot" campaign and several "normal" campaigns. The hot campaign's
parallelism goes from 1 to 64.

Run from this directory:

    ../../../.env/bin/python pyspark/windowed_aggregation.py
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


NUM_SALT_BUCKETS = 64


def get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ad_click_windowed_agg")
        .master("local[4]")
        .config("spark.sql.shuffle.partitions", "16")
        .getOrCreate()
    )


def synth_clicks(spark):
    """Synthetic click stream.

    Hot campaign: campaign_id=42 receives 10,000 clicks.
    Normal campaigns: 1..40 each receive 100 clicks.
    """
    import random
    random.seed(0)
    rows = []
    eid = 0
    # Hot campaign
    for _ in range(10_000):
        rows.append((f"e{eid}", 42, 100 + (eid % 50)))   # ad_id varies
        eid += 1
    # Normal campaigns
    for c in range(1, 41):
        if c == 42:
            continue
        for _ in range(100):
            rows.append((f"e{eid}", c, 100 + (eid % 50)))
            eid += 1
    return spark.createDataFrame(rows, ["event_id", "campaign_id", "ad_id"])


def stage1_per_salt(df):
    """Stage 1: aggregate per (campaign_id, salt).

    Salt is deterministic from event_id so retries land in the same bucket.
    64 buckets => up to 64-way parallelism on the hot key.

    ``pmod`` (not ``%``) is important: ``F.hash`` returns a 64-bit signed
    long, so ``hash % 64`` produces negative values in roughly half the
    cases. ``pmod(x, 64)`` returns a non-negative remainder in [0, 64).
    Without this fix the bucket cardinality is 127 and the parallelism
    claim is half-true at best.
    """
    salted = df.withColumn(
        "salt", F.pmod(F.hash("event_id"), F.lit(NUM_SALT_BUCKETS)).cast("int")
    )
    return (
        salted
        .groupBy("campaign_id", "salt")
        .agg(F.count("*").alias("clicks"))
    )


def stage2_rollup(stage1_df):
    """Stage 2: SUM the salts per campaign_id."""
    return (
        stage1_df
        .groupBy("campaign_id")
        .agg(F.sum("clicks").alias("clicks"))
        .orderBy(F.col("clicks").desc())
    )


def naive_agg(df):
    """Naive: aggregate per campaign_id without salting. The hot key
    collapses to a single task."""
    return (
        df
        .groupBy("campaign_id")
        .agg(F.count("*").alias("clicks"))
        .orderBy(F.col("clicks").desc())
    )


def main():
    spark = get_spark()
    clicks = synth_clicks(spark)

    # Naive: no salting. The hot campaign 42 will land on one task.
    naive = naive_agg(clicks).collect()
    hot_naive = next(r.clicks for r in naive if r.campaign_id == 42)
    print(f"  naive aggregation: campaign 42 -> {hot_naive} clicks")

    # Salted: two-stage. Should give the same total but spread across 64 salts.
    s1 = stage1_per_salt(clicks)
    salt_distribution = (
        s1.filter(F.col("campaign_id") == 42)
          .groupBy().agg(
              F.count("*").alias("buckets_used"),
              F.min("clicks").alias("min_bucket"),
              F.max("clicks").alias("max_bucket"),
          ).collect()[0]
    )
    print(f"  salted: campaign 42 spread across {salt_distribution.buckets_used} salt buckets "
          f"(of {NUM_SALT_BUCKETS}), bucket sizes {salt_distribution.min_bucket}.."
          f"{salt_distribution.max_bucket}")
    assert salt_distribution.buckets_used > 1, \
        "salting should spread the hot key across multiple buckets"
    print(f"  ✓ hot key parallelised: {salt_distribution.buckets_used} buckets "
          f"vs 1 without salting")

    # The rollup must equal the naive total.
    s2 = stage2_rollup(s1).collect()
    hot_salted = next(r.clicks for r in s2 if r.campaign_id == 42)
    assert hot_salted == hot_naive, \
        f"salted total {hot_salted} != naive total {hot_naive}"
    print(f"  ✓ salted rollup equals naive: {hot_salted} clicks for campaign 42")

    # Normal campaigns unaffected.
    normal_total = sum(r.clicks for r in s2 if r.campaign_id != 42)
    assert normal_total == 40 * 100, f"normal total {normal_total} != 4000"
    print(f"  ✓ 40 normal campaigns each show 100 clicks (total {normal_total})")

    print("=" * 70)
    print("ALL WINDOWED-AGGREGATION ASSERTIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("TWO-STAGE SALTED WINDOWED AGGREGATION")
    print("=" * 70)
    main()
