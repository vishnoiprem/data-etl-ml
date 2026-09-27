"""
Capacity model for the ad click aggregation pipeline — every number in the
README is DERIVED here, not asserted.

Run it. If a number in the README disagrees with this file, this file is right.

The point of doing this in code rather than in prose: in an interview you will be
asked "how many partitions?" and "how much storage?" and the only credible answer
is one you can derive on the whiteboard in three lines. These are those three
lines, with the assumptions named so the interviewer can push on them.
"""

# ---------------------------------------------------------------- assumptions
# Stated in the problem
EVENTS_PER_SEC_SUSTAINED = 1_000_000
EVENTS_PER_SEC_PEAK = 10_000_000
CLICKS_PER_DAY = 1_000_000_000
FRAUD_RATE_LOW, FRAUD_RATE_HIGH = 0.10, 0.20
FRESHNESS_SLO_SEC = 10
RAW_RETENTION_DAYS = 365
AGG_RETENTION_DAYS = 90

# Engineering assumptions — SAY THESE OUT LOUD, they are where the numbers
# come from and where an interviewer will probe.
BYTES_PER_EVENT = 500          # JSON-ish envelope; ~150 B in Parquet+zstd
PARQUET_COMPRESSION = 5.0      # columnar + zstd on repetitive ad events
KAFKA_REPLAY_DAYS = 7          # enough to survive a long weekend outage
KAFKA_REPLICAS = 3
MB_PER_SEC_PER_PARTITION = 10  # conservative; keeps rebalance times sane
AVG_CPC_USD = 0.50             # order-of-magnitude, for the money math
ACTIVE_ADS = 10_000_000        # ads receiving traffic in a day

SEC_PER_DAY = 86_400
TB = 1024 ** 4
GB = 1024 ** 3
MB = 1024 ** 2


def check(label, value, expected, unit="", tol=0.02):
    """Assert a derived number, then print it. Tolerance is fractional."""
    ok = abs(value - expected) <= abs(expected) * tol
    if not ok:
        raise AssertionError(f"{label}: derived {value:,.2f} != expected {expected:,.2f}")
    print(f"  {label:<44} {value:>16,.2f} {unit}")


print("=" * 78)
print("THROUGHPUT")
print("=" * 78)

bytes_per_sec = EVENTS_PER_SEC_SUSTAINED * BYTES_PER_EVENT
mb_per_sec = bytes_per_sec / MB
check("sustained ingest", mb_per_sec, 476.84, "MB/s")

peak_mb_per_sec = EVENTS_PER_SEC_PEAK * BYTES_PER_EVENT / MB
check("peak ingest (10x)", peak_mb_per_sec, 4768.37, "MB/s")
print(f"  -> ~{peak_mb_per_sec / 1024:.1f} GB/s at peak. This is the number that "
      "decides your\n     broker count and your NIC budget.")

events_per_day = EVENTS_PER_SEC_SUSTAINED * SEC_PER_DAY
check("events/day (all types)", events_per_day / 1e9, 86.40, "billion")
print(f"  -> clicks are {CLICKS_PER_DAY / events_per_day:.1%} of all events; the rest "
      "are impressions\n     and conversions. Impressions dominate volume, clicks "
      "dominate MONEY.")

print()
print("=" * 78)
print("KAFKA PARTITIONS")
print("=" * 78)

min_partitions_sustained = mb_per_sec / MB_PER_SEC_PER_PARTITION
min_partitions_peak = peak_mb_per_sec / MB_PER_SEC_PER_PARTITION
check("min partitions (sustained)", min_partitions_sustained, 47.68)
check("min partitions (peak)", min_partitions_peak, 476.84)

# Round UP to a power of two: makes hash(key) % n distribute evenly and lets you
# double consumers without re-partitioning.
chosen = 1024
print(f"  -> choose {chosen} (power of 2, ~2x peak headroom).")
print(f"     At peak that is {peak_mb_per_sec / chosen:.2f} MB/s per partition, "
      "well inside limits.")
assert chosen >= min_partitions_peak * 2, "chosen partitions leave <2x headroom"
print("  -> WHY power of two: even hash distribution, and you can scale consumers")
print("     by halving/doubling without a re-key.")

print()
print("=" * 78)
print("STORAGE")
print("=" * 78)

kafka_raw_tb = bytes_per_sec * SEC_PER_DAY * KAFKA_REPLAY_DAYS / TB
check("Kafka replay buffer (1 copy)", kafka_raw_tb, 275.03, "TiB")
check("Kafka replay buffer (3x repl)", kafka_raw_tb * KAFKA_REPLICAS, 825.09, "TiB")

raw_uncompressed_pb = bytes_per_sec * SEC_PER_DAY * RAW_RETENTION_DAYS / TB / 1024
check("raw events, 1yr uncompressed", raw_uncompressed_pb, 14.00, "PiB")
raw_compressed_pb = raw_uncompressed_pb / PARQUET_COMPRESSION
check("raw events, 1yr Parquet+zstd", raw_compressed_pb, 2.80, "PiB")
print(f"  -> {PARQUET_COMPRESSION:.0f}:1 is realistic for ad events: high-cardinality")
print("     ids compress poorly, but timestamps/enums/booleans compress hard.")

print()
print("=" * 78)
print("AGGREGATE GRAIN — the retention decision")
print("=" * 78)

# This is the calculation that forces the rollup, and it is worth showing.
minute_rows_per_day = ACTIVE_ADS * 1440
check("1-min rows/day", minute_rows_per_day / 1e9, 14.40, "billion")

minute_rows_90d = minute_rows_per_day * AGG_RETENTION_DAYS
check("1-min rows if kept 90 days", minute_rows_90d / 1e12, 1.296, "trillion")
print("  -> 1.3 TRILLION rows at 1-min grain. Not viable. This is why you roll up.")

hourly_rows_90d = ACTIVE_ADS * 24 * AGG_RETENTION_DAYS
check("1-hour rows, 90 days", hourly_rows_90d / 1e9, 21.60, "billion")
print("  -> 21.6B rows is a large but ordinary Druid/Pinot table.")

reduction = minute_rows_90d / hourly_rows_90d
check("rollup reduction factor", reduction, 60.00, "x")
print("  -> DECISION: 1-min grain retained 7 days (incident debugging),")
print("     1-hour grain for the full 90, daily beyond that.")

minute_rows_7d = minute_rows_per_day * 7
check("1-min rows, 7 days only", minute_rows_7d / 1e9, 100.80, "billion")

print()
print("=" * 78)
print("DEDUP STATE — why it must be RocksDB, not heap")
print("=" * 78)

# State is bounded by the 60s window, which is the whole reason it is tractable.
DEDUP_WINDOW_SEC = 60
STATE_BYTES_PER_KEY = 64        # (user_id, ad_id) + timestamp + overhead

clicks_per_sec = CLICKS_PER_DAY / SEC_PER_DAY
check("clicks/sec (sustained avg)", clicks_per_sec, 11_574.07, "clicks/s")

keys_in_window = clicks_per_sec * DEDUP_WINDOW_SEC
check("distinct keys in 60s window", keys_in_window / 1e3, 694.44, "thousand")
state_gb = keys_in_window * STATE_BYTES_PER_KEY / GB
check("dedup state (sustained)", state_gb * 1024, 42.39, "MiB")

peak_clicks_per_sec = clicks_per_sec * 10
peak_state_gb = peak_clicks_per_sec * DEDUP_WINDOW_SEC * STATE_BYTES_PER_KEY / GB
check("dedup state (10x peak)", peak_state_gb * 1024, 423.86, "MiB")
print("  -> Modest! The 60s bound is doing all the work.")
print("  -> Contrast: UNBOUNDED DISTINCT over a year of clicks would be")
unbounded_tb = CLICKS_PER_DAY * RAW_RETENTION_DAYS * STATE_BYTES_PER_KEY / TB
check("  unbounded DISTINCT state", unbounded_tb, 21.25, "TiB")
print("     21 TB of streaming state -> the job dies. THAT is why dedup needs a")
print("     watermark/TTL and not SELECT DISTINCT.")

print()
print("=" * 78)
print("THE MONEY MATH — why fraud sits upstream of counting")
print("=" * 78)

gross_rev = CLICKS_PER_DAY * AVG_CPC_USD
check("gross billable if unfiltered", gross_rev / 1e6, 500.00, "$M/day")

for rate in (FRAUD_RATE_LOW, FRAUD_RATE_HIGH):
    risk = CLICKS_PER_DAY * rate * AVG_CPC_USD
    print(f"  mis-billing risk at {rate:.0%} fraud                  "
          f"{risk / 1e6:>16,.2f} $M/day")

mid_risk = CLICKS_PER_DAY * 0.15 * AVG_CPC_USD
check("mis-billing risk at 15% fraud", mid_risk / 1e6, 75.00, "$M/day")
check("  ... annualised", mid_risk * 365 / 1e9, 27.38, "$B/year")
print("  -> $27B/yr of exposure is the answer to 'why not just clean it up later'.")
print("  -> It also justifies holding invoices when the fraud scorer is down:")
print("     a day of delayed billing costs far less than a day of billing fraud.")

print()
print("=" * 78)
print("FRESHNESS BUDGET — where the 10 seconds goes")
print("=" * 78)

budget = [
    ("edge collector + tier-1 fraud", 0.05),
    ("Kafka produce + replicate (acks=all)", 0.20),
    ("dedup consume + state lookup", 0.50),
    ("re-key hop through deduped_clicks", 0.30),
    ("window aggregation (1-min tumbling)", 2.00),
    ("emit + idempotent upsert to Druid", 1.00),
    ("dashboard query + render", 0.50),
]
total = sum(v for _, v in budget)
for label, v in budget:
    print(f"  {label:<44} {v:>16,.2f} s")
print(f"  {'-' * 44} {'-' * 16}")
check("total pipeline latency", total, 4.55, "s")
headroom = FRESHNESS_SLO_SEC - total
check("headroom against 10s SLO", headroom, 5.45, "s")
print("  -> The 1-min tumbling window is the dominant term. If you needed <2s you")
print("     would emit incremental updates mid-window rather than shrink the SLO.")
print("  -> Headroom absorbs GC pauses, rebalances and checkpoint stalls. Budget")
print("     it deliberately; do not spend it.")

print()
print("=" * 78)
print("ALL DERIVED NUMBERS CHECKED — README figures are reproducible")
print("=" * 78)
