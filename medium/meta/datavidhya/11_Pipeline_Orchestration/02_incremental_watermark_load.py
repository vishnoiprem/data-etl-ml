"""
Problem 02: Incremental load driven by a watermark.

Meta flavor: "The table has 10 billion rows. You are not reprocessing it nightly.
How do you load only what changed?"

How to Think:
- Keep a WATERMARK: the high-water mark of what you have already ingested.
  Each run reads source rows strictly above it, then advances it.
- The boundary is the whole question. Use `>` on the stored watermark, not `>=`,
  or you re-ingest the boundary row every single run. Use a half-open interval
  (last_wm, new_wm] and the arithmetic is unambiguous.
- LATE-ARRIVING DATA is the failure mode nobody mentions: if a row's
  updated_at is older than the watermark when it finally shows up, a strict
  watermark skips it forever. Mitigations, in order of cost:
    a) a lookback window (re-read the last N hours and MERGE) — cheap, standard
    b) MERGE on key instead of append — handles updates as well as inserts
    c) CDC/streaming with event-time watermarks and allowed lateness
- Never derive the watermark from wall-clock time. Derive it from the DATA
  (MAX(updated_at) of what you actually read), or a crash between "read" and
  "commit watermark" loses rows silently.

This file runs three loads and asserts: no duplicates, nothing skipped, and that
a re-run with no new data is a no-op.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("02-incremental-watermark-load")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got


from pyspark.sql import functions as F

# Source with an updated_at watermark column.
spark.createDataFrame([
    (1, "a", "2026-01-01 10:00:00"),
    (2, "b", "2026-01-01 11:00:00"),
    (3, "c", "2026-01-02 09:00:00"),
], ["id", "val", "updated_at"]).createOrReplaceTempView("src")

target = []          # stands in for the destination table
watermark = "1970-01-01 00:00:00"


def incremental_load():
    """Read strictly above the watermark, then advance it from the DATA."""
    global watermark
    batch = spark.sql(f"""
        SELECT id, val, updated_at FROM src
        WHERE updated_at > '{watermark}'
        ORDER BY updated_at
    """).collect()
    if not batch:
        return 0
    target.extend((r["id"], r["val"]) for r in batch)
    watermark = max(r["updated_at"] for r in batch)   # from data, not clock
    return len(batch)


n1 = incremental_load()
assert n1 == 3 and watermark == "2026-01-02 09:00:00", (n1, watermark)
print(f"[PASS] initial load took {n1} rows, watermark -> {watermark}")

# Re-run with no new data must be a no-op — this is the `>` vs `>=` test.
n2 = incremental_load()
assert n2 == 0, f"re-ran and re-ingested {n2} rows — watermark uses >= not >"
assert len(target) == 3, target
print("[PASS] re-run with no new data ingested 0 rows (strict > boundary)")

# New row arrives above the watermark.
spark.createDataFrame([
    (1, "a", "2026-01-01 10:00:00"),
    (2, "b", "2026-01-01 11:00:00"),
    (3, "c", "2026-01-02 09:00:00"),
    (4, "d", "2026-01-03 08:00:00"),
], ["id", "val", "updated_at"]).createOrReplaceTempView("src")

n3 = incremental_load()
assert n3 == 1 and len(target) == 4, (n3, target)
print(f"[PASS] picked up only the {n3} new row; target has {len(target)} rows")

# --- The late-arriving-data failure, demonstrated -------------------------
# Row 5 has updated_at BELOW the current watermark. A strict watermark loses it.
spark.createDataFrame([
    (1, "a", "2026-01-01 10:00:00"),
    (2, "b", "2026-01-01 11:00:00"),
    (3, "c", "2026-01-02 09:00:00"),
    (4, "d", "2026-01-03 08:00:00"),
    (5, "late", "2026-01-02 12:00:00"),      # arrives late, timestamped early
], ["id", "val", "updated_at"]).createOrReplaceTempView("src")

n4 = incremental_load()
assert n4 == 0, n4
assert 5 not in [t[0] for t in target], "expected the late row to be skipped"
print("[PASS] late-arriving row was SKIPPED — this is the bug a lookback fixes")

# Mitigation (a): re-read a lookback window and merge by key.
LOOKBACK_HOURS = 48
recovered = spark.sql(f"""
    SELECT id, val, updated_at FROM src
    WHERE updated_at > CAST(CAST('{watermark}' AS TIMESTAMP)
                            - INTERVAL {LOOKBACK_HOURS} HOURS AS STRING)
""").collect()
by_key = {t[0]: t for t in target}
for r in recovered:
    by_key[r["id"]] = (r["id"], r["val"])       # MERGE semantics, not append
target = sorted(by_key.values())

assert len(target) == 5 and (5, "late") in target, target
print(f"[PASS] {LOOKBACK_HOURS}h lookback + merge recovered the late row "
      f"-> {len(target)} rows, no duplicates")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE src (
#       id         INT PRIMARY KEY,
#       val        VARCHAR(20),
#       updated_at DATETIME NOT NULL
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO src VALUES
#       (1, 'a', '2026-01-01 10:00:00'),
#       (2, 'b', '2026-01-01 11:00:00'),
#       (3, 'c', '2026-01-02 09:00:00');
#
#   CREATE TABLE target (
#       id  INT PRIMARY KEY,
#       val VARCHAR(20)
#   ) ENGINE=InnoDB;
#
#   CREATE TABLE watermark_kv (
#       wm_name VARCHAR(40) PRIMARY KEY,
#       wm_ts   DATETIME NOT NULL
#   ) ENGINE=InnoDB;
#   INSERT INTO watermark_kv (wm_name, wm_ts) VALUES ('src_to_target', '1970-01-01 00:00:00');
#
# Per-run procedure: read strictly ABOVE watermark, MERGE into target, then
# advance watermark from the DATA (not wall-clock):
#   DELIMITER $$
#   CREATE PROCEDURE incremental_load()
#   BEGIN
#       START TRANSACTION;
#
#       SELECT wm_ts INTO @wm FROM watermark_kv WHERE wm_name = 'src_to_target'
#           FOR UPDATE;
#
#       -- 1) read strictly above the watermark
#       CREATE TEMPORARY TABLE _batch AS
#       SELECT id, val, updated_at
#       FROM src
#       WHERE updated_at > @wm;
#
#       -- 2) MERGE into target (upsert, MERGE semantics)
#       INSERT INTO target (id, val)
#       SELECT id, val FROM _batch
#       ON DUPLICATE KEY UPDATE val = VALUES(val);
#
#       -- 3) advance the watermark from the DATA, not wall-clock
#       UPDATE watermark_kv SET wm_ts = (SELECT MAX(updated_at) FROM _batch)
#       WHERE wm_name = 'src_to_target';
#
#       DROP TEMPORARY TABLE _batch;
#       COMMIT;
#   END$$
#   DELIMITER ;
#
# Late-arriving-data mitigation: lookback + MERGE. Re-read the last N hours
# and let ON DUPLICATE KEY UPDATE collapse updates:
#   DELIMITER $$
#   CREATE PROCEDURE merge_lookback(IN p_lookback_hours INT)
#   BEGIN
#       SELECT wm_ts INTO @wm FROM watermark_kv WHERE wm_name = 'src_to_target';
#       SET @cutoff = DATE_SUB(@wm, INTERVAL p_lookback_hours HOUR);
#
#       INSERT INTO target (id, val)
#       SELECT id, val FROM src
#       WHERE updated_at > @cutoff
#       ON DUPLICATE KEY UPDATE val = VALUES(val);
#   END$$
#   DELIMITER ;
#
# Critical invariants:
#   - Boundary is strict `>` (not `>=`) — re-running with no new data is a no-op.
#   - Advance the watermark from the DATA (`MAX(updated_at)` of what you read),
#     NEVER wall-clock time — a crash between "read" and "commit watermark"
#     would otherwise lose rows silently.
#   - For late-arriving data: lookback + MERGE, not append-only.
