"""
Billing reconciliation in PySpark — speed vs. batch, idempotent vs. append.

The billable-click count is determined by THREE independent decisions:
  1. dedup at 60s (handled upstream, see dedup_clicks.py)
  2. tier-2 fraud signal (async, arrives minutes/hours after the click)
  3. campaign CPC from the dim

The speed layer can't wait for (2), so it ships a provisional count.
The batch layer reruns once (2) settles and produces the authoritative
ledger. Reconciliation then publishes an ADJUSTMENT row for every
(advertiser_id, campaign_id, period) whose billable count changed.

This script demonstrates the four invariants the reconciliation has to
hold or billing diverges from product reality:

  - speed and batch produce DIFFERENT provisional counts (the bug)
  - the idempotent OVERWRITE produces a STABLE ledger across reruns
  - the APPEND-mode sink produces a DIFFERENT ledger on every rerun
  - speed + adjustment == batch  (delta is what the advertiser sees)

Run from this directory:

    ../../../.env/bin/python pyspark/billing_reconciliation.py
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("ad_click_billing_recon")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def synth_clicks(spark):
    """30 deduped clicks across 2 campaigns + 1 user_id with a double.

    After dedup (which we skip here — see dedup_clicks.py), the speed layer
    sees them all. The fraud model invalidates 4 of campaign 1's clicks 2
    hours later; the batch rerun sees the smaller number.
    """
    rows = []
    eid = 0
    # Campaign c1: 20 clicks, 4 later flagged as fraud.
    for _ in range(20):
        rows.append((f"e{eid}", "c1", 100, f"2026-03-01 10:00:{eid % 60:02d}"))
        eid += 1
    # Campaign c2: 10 clicks, no fraud. Control case.
    for _ in range(10):
        rows.append((f"e{eid}", "c2", 200, f"2026-03-01 10:01:{eid % 60:02d}"))
        eid += 1
    return spark.createDataFrame(
        rows, ["event_id", "campaign_id", "user_id", "event_ts"]
    )


def synth_fraud_verdicts(spark):
    """4 events tier-2-flagged 2 hours after the click. The speed layer
    did NOT see these when it shipped its provisional aggregate."""
    return spark.createDataFrame(
        [("e0", "bot"), ("e1", "bot"), ("e2", "bot",), ("e3", "bot")],
        ["event_id", "verdict"],
    )


def synth_campaign_dim(spark):
    return spark.createDataFrame(
        [("c1", "adv-A", 1.00), ("c2", "adv-B", 2.50)],
        ["campaign_id", "advertiser_id", "cpc_usd"],
    )


# ------------------------------------------------------------- billable (shared)
def billable(clicks, fraud, dim):
    """Speed and batch layers compute billable clicks with the SAME shape;
    the difference between them is purely WHICH fraud verdicts are
    visible at compute time. Speed passes an empty fraud set; batch
    passes the full set. The function collapses those into one because
    their bodies are byte-identical and any divergence here would be a
    bug, not a feature.
    """
    return (
        clicks.alias("c")
        .join(fraud.alias("f"), F.col("c.event_id") == F.col("f.event_id"), "left_anti")
        .join(dim, "campaign_id")
        .groupBy("advertiser_id", "campaign_id")
        .agg(
            F.count("*").alias("billable_clicks"),
            F.first("cpc_usd").alias("cpc_usd"),
        )
        .withColumn("billable_clicks", F.col("billable_clicks").cast("long"))
        .orderBy("campaign_id")
    )


# ------------------------------------------------- idempotent vs. append-mode sink
def idempotent_sink(batch_df, deterministic_key_col="ledger_id"):
    """OVERWRITE-style sink keyed on a HASH. Reruns replace, never append.

    This is the sink the production system uses. Demonstrated here by
    building the hash, simulating two reruns, and asserting the row count
    is stable.
    """
    return (
        batch_df
        .withColumn(
            "ledger_id",
            F.hash(F.concat_ws("|", F.col("advertiser_id"), F.col("campaign_id"),
                                F.lit("2026-03"))),
        )
        .select(
            "ledger_id", "advertiser_id", "campaign_id",
            "billable_clicks", "cpc_usd",
        )
    )


def append_sink(batch_df):
    """The trap. Append-mode with no natural key double-counts on rerun.

    We DON'T actually emit it as production code; we simulate it here to
    show the divergence so the interview answer is grounded in a number.
    """
    # No ledger_id, no deterministic key. Each "emit" is a brand new row.
    return batch_df.select("advertiser_id", "campaign_id", "billable_clicks", "cpc_usd")


# ----------------------------------------------------------- adjustment_records
def adjustment_records(speed_df, batch_df):
    """Publish the delta, never mutate history.

    positive delta = batch saw MORE billable clicks (speed under-counted
        because a fraud verdict hadn't arrived yet)
    negative delta = batch saw FEWER (speed over-counted; tier-2 fraud
        invalidated clicks already billed)
    """
    s = (speed_df
         .withColumnRenamed("billable_clicks", "s_billable")
         .withColumnRenamed("cpc_usd", "s_cpc"))
    b = (batch_df
         .withColumnRenamed("billable_clicks", "b_billable")
         .withColumnRenamed("cpc_usd", "b_cpc"))
    joined = (
        s.join(b, ["advertiser_id", "campaign_id"])
         .withColumn("delta_clicks", F.col("b_billable") - F.col("s_billable"))
         .withColumn("delta_usd", F.col("delta_clicks") * F.col("b_cpc"))
    )
    return joined.select(
        "advertiser_id", "campaign_id", "s_billable", "b_billable",
        "delta_clicks", "delta_usd",
    ).orderBy("campaign_id")


# ====================================================================== main
def main():
    spark = get_spark()
    clicks = synth_clicks(spark)
    fraud = synth_fraud_verdicts(spark)
    dim = synth_campaign_dim(spark)

    # -- 1. speed and batch SHOULD disagree --------------------------------
    # In this seed, fraud_verdicts is the SAME at speed-time and
    # batch-time (we model the moment the batch rerun computes — after
    # all fraud has settled). To prove the mechanism, simulate the speed
    # layer having a PARTIAL view: empty fraud set.
    speed = billable(clicks, fraud.limit(0), dim)               # sees no fraud
    batch = billable(clicks, fraud, dim)                        # sees all 4

    speed_rows = {r.campaign_id: r.billable_clicks for r in speed.collect()}
    batch_rows = {r.campaign_id: r.billable_clicks for r in batch.collect()}
    print(f"  speed-layer provisional: {speed_rows}")
    print(f"  batch-layer authoritative: {batch_rows}")
    assert speed_rows["c1"] != batch_rows["c1"], \
        f"speed and batch must differ for c1; got {speed_rows['c1']} == {batch_rows['c1']}"
    assert speed_rows["c1"] - batch_rows["c1"] == 4, \
        f"c1 delta should equal the 4 fraud verdicts; got {speed_rows['c1'] - batch_rows['c1']}"
    assert speed_rows["c2"] == batch_rows["c2"], \
        "c2 had no fraud; speed and batch must agree"
    print(f"  ✓ speed/batch divergence is mechanical: {speed_rows['c1'] - batch_rows['c1']} "
          "clicks differ on c1 (the 4 fraud verdicts); c2 unaffected")

    # -- 2. adjustment row is the public delta ------------------------------
    adj = adjustment_records(speed, batch).collect()
    print(f"  adjustment row: {[(r.campaign_id, r.delta_clicks, r.delta_usd) for r in adj]}")
    c1_adj = next(r for r in adj if r.campaign_id == "c1")
    assert c1_adj.delta_clicks == -4, c1_adj.delta_clicks
    assert c1_adj.delta_usd == -4 * 1.00, c1_adj.delta_usd    # c1 cpc = 1.00
    c2_adj = next(r for r in adj if r.campaign_id == "c2")
    assert c2_adj.delta_clicks == 0, c2_adj.delta_clicks
    print(f"  ✓ adjustment: c1 delta={c1_adj.delta_clicks} clicks, "
          f"{c1_adj.delta_usd} USD (refund); c2 delta=0 (no fraud)")

    # -- 3. IDEMPOTENT sink: reruns don't double-count -----------------------
    # Hash key is (advertiser_id, campaign_id, period) -- distinct per row.
    # Two reruns union to 2N rows but DROP DISTINCT to N (the natural keys
    # collapse). The advertiser is billed once per (advertiser, campaign,
    # period) regardless of how many times the pipeline reruns.
    one_run = idempotent_sink(batch).cache()
    n_one = one_run.count()
    two_runs = idempotent_sink(batch).unionByName(idempotent_sink(batch))
    n_total = two_runs.count()
    n_distinct = two_runs.dropDuplicates(["ledger_id"]).count()
    assert n_total == 2 * n_one, (n_total, n_one)
    assert n_distinct == n_one, (n_distinct, n_one)
    print(f"  ✓ idempotent sink: 2 reruns -> {n_total} rows collapse via "
          f"ledger_id hash to {n_distinct} unique ledger_ids (one per campaign)")

    # -- 4. APPEND-mode sink: the bug, with a number -------------------------
    one_run_a = append_sink(batch)
    two_runs_a = append_sink(batch).unionByName(append_sink(batch))
    n_a = two_runs_a.count()
    n_a_distinct = two_runs_a.dropDuplicates(["advertiser_id", "campaign_id"]).count()
    assert n_a == 2 * one_run_a.count(), (n_a, one_run_a.count())
    assert n_a_distinct < n_a, (n_a_distinct, n_a)
    print(f"  ✗ append-mode sink: 2 reruns -> {n_a} rows of which {n_a_distinct} are real;"
          f"\n       the advertiser is DOUBLE-billed every retry, which is the bug")

    # -- 5. conservation: billable + rejected + raw consistency check -------
    raw_clicks = clicks.count()
    total_billable_batch = sum(batch_rows.values())
    fraud_count = fraud.count()
    assert total_billable_batch + fraud_count == raw_clicks, \
        (total_billable_batch, fraud_count, raw_clicks)
    print(f"  ✓ conservation: {total_billable_batch} billable + {fraud_count} "
          f"fraud-invalidated = {raw_clicks} raw -> nothing vanished")

    # -- 6. spend calculation is per-campaign, not just per-row --------------
    spend = (
        batch.withColumn("spend_usd", F.col("billable_clicks") * F.col("cpc_usd"))
             .select("campaign_id", "billable_clicks", "cpc_usd", "spend_usd")
             .orderBy("campaign_id")
             .collect()
    )
    for r in spend:
        print(f"     campaign={r.campaign_id}: {r.billable_clicks} billable @ "
              f"${r.cpc_usd} = ${r.spend_usd}")
    c1_spend = next(r for r in spend if r.campaign_id == "c1")
    assert c1_spend.spend_usd == c1_spend.billable_clicks * 1.00
    print(f"  ✓ spend computed per-campaign from CPC dim, not hard-coded")

    print("=" * 70)
    print("ALL BILLING-RECONCILIATION ASSERTIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("BILLING RECONCILIATION: speed vs batch, idempotent vs append")
    print("=" * 70)
    main()
