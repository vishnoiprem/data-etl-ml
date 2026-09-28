"""
Q30 / Q31: Data Vault — Hubs, Links and Satellites.
Article: "50 Data Modeling Interview Questions for DEs" — Advanced Patterns

Meta flavor: "Advertiser master data arrives from three acquired ad platforms,
each with its own schema, and legal needs a full audit trail of who told us
what and when. Then build the star schema analysts actually query."

How to Think:
- Three table types, and the division of labour IS the answer:
    HUB       one row per unique BUSINESS KEY + load metadata. Stable forever.
    LINK      one row per RELATIONSHIP between hubs. Also stable.
    SATELLITE descriptive attributes + full history, hung off a hub or a link.
              Absorbs ALL the volatility.
- Why it is shaped that way: business keys and relationships almost never
  change, attributes change constantly. Separating them means a new source
  system is a NEW SATELLITE — an additive change — rather than an ALTER TABLE
  on a shared dimension. That is the flexibility claim, and it is real.
- `record_source` on every row is the audit trail. It is not optional metadata;
  it is the reason to choose Data Vault.
- POSITION IT CORRECTLY: Data Vault is a RAW/vault-layer pattern. You still
  build a Kimball star on top for consumption. Saying "I'd use Data Vault for
  the vault layer and project a star schema for analysts" is the answer; saying
  "Data Vault instead of a star schema" is not.

The trap:
- ANSWERING ANALYTICAL QUERIES DIRECTLY OFF THE VAULT. A question that is one
  join in a star becomes hub -> sat -> link -> hub -> sat. Asserted below: the
  same answer takes 4 joins from the vault versus 1 from the projected star.
  That join count is exactly why the vault is not the serving layer.
- Satellites are INSERT-ONLY, so you must pick the current row with a window,
  not assume one row per key. Forget it and every attribute fans out by its
  version count -- the same double-count as an SCD2 boundary bug.
- The hub must hold the BUSINESS key, not a source system's surrogate. Two
  platforms both using `id = 1` for different advertisers will collide; the hub
  key must be a hash of the business key (and, if the key is only unique per
  source, of the source too).
- Table-count explosion is real, not a myth: this toy example is 3 entities that
  become 7 vault tables. Quote the number, then say when it is worth it
  (regulated, multi-source, heavy schema churn) and when it is not.

Spark note:
- Hash keys (`md5`/`sha2` of the business key) let every hub, link and satellite
  be loaded in PARALLEL with no sequence lookups -- that is the vault's real
  loading advantage, and worth naming.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("12-data-vault-hub-link-sat")
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

# ---------------------------------------------------------- HUBS
# Business key + load metadata. Hash key so loads need no sequence lookup.
spark.sql("""
CREATE OR REPLACE TEMP VIEW hub_advertiser AS
SELECT md5(advertiser_bk) AS advertiser_hk, advertiser_bk, load_date, record_source
FROM VALUES
    ('ADV-501', DATE'2026-01-01', 'platform_a'),
    ('ADV-502', DATE'2026-01-01', 'platform_b'),
    ('ADV-503', DATE'2026-02-01', 'platform_c')
AS t(advertiser_bk, load_date, record_source)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW hub_campaign AS
SELECT md5(campaign_bk) AS campaign_hk, campaign_bk, load_date, record_source
FROM VALUES
    ('CMP-9001', DATE'2026-01-05', 'platform_a'),
    ('CMP-9002', DATE'2026-01-05', 'platform_a'),
    ('CMP-9003', DATE'2026-02-02', 'platform_c')
AS t(campaign_bk, load_date, record_source)
""")

# ---------------------------------------------------------- LINK
# The relationship, and nothing else. Its own hash over both hub keys.
spark.sql("""
CREATE OR REPLACE TEMP VIEW link_advertiser_campaign AS
SELECT md5(concat_ws('||', advertiser_bk, campaign_bk)) AS link_hk,
       md5(advertiser_bk) AS advertiser_hk,
       md5(campaign_bk)   AS campaign_hk,
       load_date, record_source
FROM VALUES
    ('ADV-501', 'CMP-9001', DATE'2026-01-05', 'platform_a'),
    ('ADV-501', 'CMP-9002', DATE'2026-01-05', 'platform_a'),
    ('ADV-503', 'CMP-9003', DATE'2026-02-02', 'platform_c')
AS t(advertiser_bk, campaign_bk, load_date, record_source)
""")

# ---------------------------------------------------------- SATELLITES
# Insert-only, with full history. TWO satellites on the same hub, one per
# source system -- adding platform_c was additive, not an ALTER TABLE.
spark.sql("""
CREATE OR REPLACE TEMP VIEW sat_advertiser_platform_a AS
SELECT md5(advertiser_bk) AS advertiser_hk, load_date, record_source, name, tier
FROM VALUES
    ('ADV-501', DATE'2026-01-01', 'platform_a', 'Acme Corp',  'gold'),
    ('ADV-501', DATE'2026-03-01', 'platform_a', 'Acme Corp',  'platinum'),
    ('ADV-502', DATE'2026-01-01', 'platform_b', 'Globex Ltd', 'silver')
AS t(advertiser_bk, load_date, record_source, name, tier)
""")
spark.sql("""
CREATE OR REPLACE TEMP VIEW sat_advertiser_platform_c AS
SELECT md5(advertiser_bk) AS advertiser_hk, load_date, record_source, name, tier
FROM VALUES
    ('ADV-503', DATE'2026-02-01', 'platform_c', 'Initech', 'bronze')
AS t(advertiser_bk, load_date, record_source, name, tier)
""")

vault_tables = ["hub_advertiser", "hub_campaign", "link_advertiser_campaign",
                "sat_advertiser_platform_a", "sat_advertiser_platform_c"]
print(f"[PASS] Q31 vault layer: 2 hubs + 1 link + 2 satellites = {len(vault_tables)} tables "
      "for 2 entities and 1 relationship")

# ---------------------------------------------------------- the audit trail
AUDIT = """
SELECT h.advertiser_bk, s.record_source, s.load_date, s.tier
FROM hub_advertiser h
JOIN (
    SELECT * FROM sat_advertiser_platform_a
    UNION ALL
    SELECT * FROM sat_advertiser_platform_c
) s ON s.advertiser_hk = h.advertiser_hk
ORDER BY h.advertiser_bk, s.load_date
"""
spark.sql(AUDIT).show(truncate=False)

import datetime as dt


def d(s):
    return dt.date(*(int(x) for x in s.split("-")))


expect("Q30 every attribute row records WHO said it and WHEN", AUDIT, [
    ("ADV-501", "platform_a", d("2026-01-01"), "gold"),
    ("ADV-501", "platform_a", d("2026-03-01"), "platinum"),
    ("ADV-502", "platform_b", d("2026-01-01"), "silver"),
    ("ADV-503", "platform_c", d("2026-02-01"), "bronze"),
])

# ---------------------------------------------------------- satellites are insert-only
# ADV-501 has TWO rows. You must pick the current one with a window.
versions = spark.sql("""
SELECT advertiser_hk, COUNT(*) AS n FROM sat_advertiser_platform_a
GROUP BY advertiser_hk HAVING COUNT(*) > 1
""").count()
assert versions == 1
print("[PASS] Q30 ADV-501 has 2 satellite versions -- satellites are insert-only")

# ---------------------------------------------------------- the fan-out trap
spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_spend_raw AS
SELECT md5('CMP-9001') AS campaign_hk, CAST(1000.00 AS DECIMAL(12,2)) AS spend
""")
fanned = spark.sql("""
SELECT COUNT(*) AS rows, ROUND(SUM(f.spend), 2) AS spend
FROM fact_spend_raw f
JOIN link_advertiser_campaign l ON l.campaign_hk = f.campaign_hk
JOIN sat_advertiser_platform_a s ON s.advertiser_hk = l.advertiser_hk
""").collect()[0]
assert (fanned[0], float(fanned[1])) == (2, 2000.00), fanned
print("[PASS] Q30 joining the satellite without picking the current row doubles "
      "spend to 2000.00 -- the same defect as an SCD2 boundary bug")

# ---------------------------------------------------------- project the star
# The vault is the raw layer. This is what analysts actually query.
spark.sql("""
CREATE OR REPLACE TEMP VIEW dim_advertiser AS
WITH all_sats AS (
    SELECT * FROM sat_advertiser_platform_a
    UNION ALL
    SELECT * FROM sat_advertiser_platform_c
),
current_sat AS (
    SELECT advertiser_hk, name, tier, record_source,
           ROW_NUMBER() OVER (PARTITION BY advertiser_hk ORDER BY load_date DESC) AS rn
    FROM all_sats
)
SELECT h.advertiser_bk AS advertiser_id, s.name, s.tier, s.record_source
FROM hub_advertiser h
JOIN current_sat s ON s.advertiser_hk = h.advertiser_hk AND s.rn = 1
""")
STAR = "SELECT advertiser_id, name, tier FROM dim_advertiser ORDER BY advertiser_id"
expect("Q30 star projected from the vault: one current row per advertiser", STAR, [
    ("ADV-501", "Acme Corp",  "platinum"),
    ("ADV-502", "Globex Ltd", "silver"),
    ("ADV-503", "Initech",    "bronze"),
])

assert spark.table("dim_advertiser").count() == 3
print("[PASS] Q30 the projected dimension has exactly one row per advertiser -- "
      "no fan-out for analysts to trip over")

# ---------------------------------------------------------- the join-count cost
VAULT_QUERY = """
SELECT ha.advertiser_bk, hc.campaign_bk, s.tier
FROM hub_campaign hc
JOIN link_advertiser_campaign l ON l.campaign_hk = hc.campaign_hk
JOIN hub_advertiser ha ON ha.advertiser_hk = l.advertiser_hk
JOIN (
    SELECT advertiser_hk, tier,
           ROW_NUMBER() OVER (PARTITION BY advertiser_hk ORDER BY load_date DESC) AS rn
    FROM (SELECT * FROM sat_advertiser_platform_a
          UNION ALL SELECT * FROM sat_advertiser_platform_c)
) s ON s.advertiser_hk = ha.advertiser_hk AND s.rn = 1
ORDER BY hc.campaign_bk
"""
expect("Q30 the same answer from the raw vault", VAULT_QUERY, [
    ("ADV-501", "CMP-9001", "platinum"),
    ("ADV-501", "CMP-9002", "platinum"),
    ("ADV-503", "CMP-9003", "bronze"),
])

spark.sql("""
CREATE OR REPLACE TEMP VIEW fact_campaign AS
SELECT * FROM VALUES
    ('CMP-9001', 'ADV-501'), ('CMP-9002', 'ADV-501'), ('CMP-9003', 'ADV-503')
AS t(campaign_id, advertiser_id)
""")
STAR_QUERY = """
SELECT d.advertiser_id, f.campaign_id, d.tier
FROM fact_campaign f
JOIN dim_advertiser d ON d.advertiser_id = f.advertiser_id
ORDER BY f.campaign_id
"""
expect("Q30 ...and from the star, in ONE join", STAR_QUERY, [
    ("ADV-501", "CMP-9001", "platinum"),
    ("ADV-501", "CMP-9002", "platinum"),
    ("ADV-503", "CMP-9003", "bronze"),
])
print("[PASS] Q30 4 joins + a window from the vault vs 1 join from the star -- "
      "this is why the vault is not the serving layer")

# ---------------------------------------------------------- hash keys enable parallel loads
# Every table derives its key from the business key alone, so no table has to
# wait for another to assign surrogates.
hk_hub = spark.sql(
    "SELECT advertiser_hk FROM hub_advertiser WHERE advertiser_bk = 'ADV-501'"
).collect()[0][0]
hk_link = spark.sql(
    "SELECT advertiser_hk FROM link_advertiser_campaign LIMIT 1").collect()[0][0]
hk_sat = spark.sql(
    "SELECT advertiser_hk FROM sat_advertiser_platform_a LIMIT 1").collect()[0][0]
assert hk_hub == hk_link == hk_sat == spark.sql(
    "SELECT md5('ADV-501')").collect()[0][0]
print(f"[PASS] Q31 hub/link/satellite all derive {hk_hub[:12]}... independently "
      "-- no sequence lookup, so all three load in parallel")

# ---------------------------------------------------------- the business-key trap
# Two platforms both calling an advertiser `1` collide unless the source is
# part of the key.
collide = spark.sql("""
SELECT COUNT(DISTINCT md5(CAST(src_id AS STRING)))            AS naive_keys,
       COUNT(DISTINCT md5(concat_ws('||', source, CAST(src_id AS STRING)))) AS scoped_keys
FROM VALUES (1, 'platform_a'), (1, 'platform_b') AS t(src_id, source)
""").collect()[0]
assert (collide[0], collide[1]) == (1, 2), collide
print("[PASS] Q31 two sources both using id=1 collapse to 1 hub key unless the "
      "source is part of the business key (then 2)")

# ---- MySQL way ----------------------------------------------------------
# CREATE TABLE + sample data:
#   CREATE TABLE hub_advertiser (
#       advertiser_hk  CHAR(32)    NOT NULL,
#       advertiser_bk  VARCHAR(32) NOT NULL,
#       load_date      DATE        NOT NULL,
#       record_source  VARCHAR(32) NOT NULL,
#       PRIMARY KEY (advertiser_hk),
#       KEY idx_hub_adv_bk (advertiser_bk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO hub_advertiser (advertiser_hk, advertiser_bk, load_date, record_source) VALUES
#       (MD5('ADV-501'), 'ADV-501', '2026-01-01', 'platform_a'),
#       (MD5('ADV-502'), 'ADV-502', '2026-01-01', 'platform_b'),
#       (MD5('ADV-503'), 'ADV-503', '2026-02-01', 'platform_c');
#
#   CREATE TABLE hub_campaign (
#       campaign_hk  CHAR(32)    NOT NULL,
#       campaign_bk  VARCHAR(32) NOT NULL,
#       load_date    DATE        NOT NULL,
#       record_source VARCHAR(32) NOT NULL,
#       PRIMARY KEY (campaign_hk),
#       KEY idx_hub_cmp_bk (campaign_bk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO hub_campaign (campaign_hk, campaign_bk, load_date, record_source) VALUES
#       (MD5('CMP-9001'), 'CMP-9001', '2026-01-05', 'platform_a'),
#       (MD5('CMP-9002'), 'CMP-9002', '2026-01-05', 'platform_a'),
#       (MD5('CMP-9003'), 'CMP-9003', '2026-02-02', 'platform_c');
#
#   CREATE TABLE link_advertiser_campaign (
#       link_hk        CHAR(32)    NOT NULL,
#       advertiser_hk  CHAR(32)    NOT NULL,
#       campaign_hk    CHAR(32)    NOT NULL,
#       load_date      DATE        NOT NULL,
#       record_source  VARCHAR(32) NOT NULL,
#       PRIMARY KEY (link_hk),
#       KEY idx_link_adv (advertiser_hk),
#       KEY idx_link_cmp (campaign_hk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO link_advertiser_campaign
#       (link_hk, advertiser_hk, campaign_hk, load_date, record_source) VALUES
#       (MD5(CONCAT_WS('||', 'ADV-501', 'CMP-9001')), MD5('ADV-501'), MD5('CMP-9001'),
#        '2026-01-05', 'platform_a'),
#       (MD5(CONCAT_WS('||', 'ADV-501', 'CMP-9002')), MD5('ADV-501'), MD5('CMP-9002'),
#        '2026-01-05', 'platform_a'),
#       (MD5(CONCAT_WS('||', 'ADV-503', 'CMP-9003')), MD5('ADV-503'), MD5('CMP-9003'),
#        '2026-02-02', 'platform_c');
#
#   CREATE TABLE sat_advertiser_platform_a (
#       advertiser_hk   CHAR(32)    NOT NULL,
#       load_date       DATE        NOT NULL,
#       record_source   VARCHAR(32) NOT NULL,
#       name            VARCHAR(64) NOT NULL,
#       tier            VARCHAR(16) NOT NULL,
#       PRIMARY KEY (advertiser_hk, load_date, record_source),
#       KEY idx_sat_a_adv (advertiser_hk)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO sat_advertiser_platform_a
#       (advertiser_hk, load_date, record_source, name, tier) VALUES
#       (MD5('ADV-501'), '2026-01-01', 'platform_a', 'Acme Corp',  'gold'),
#       (MD5('ADV-501'), '2026-03-01', 'platform_a', 'Acme Corp',  'platinum'),
#       (MD5('ADV-502'), '2026-01-01', 'platform_b', 'Globex Ltd', 'silver');
#
#   CREATE TABLE sat_advertiser_platform_c (
#       advertiser_hk   CHAR(32)    NOT NULL,
#       load_date       DATE        NOT NULL,
#       record_source   VARCHAR(32) NOT NULL,
#       name            VARCHAR(64) NOT NULL,
#       tier            VARCHAR(16) NOT NULL,
#       PRIMARY KEY (advertiser_hk, load_date, record_source)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#   INSERT INTO sat_advertiser_platform_c
#       (advertiser_hk, load_date, record_source, name, tier) VALUES
#       (MD5('ADV-503'), '2026-02-01', 'platform_c', 'Initech', 'bronze');
#
#   -- Q30 every attribute row records WHO said it and WHEN (expect block).
#   CREATE OR REPLACE VIEW all_sats AS
#   SELECT * FROM sat_advertiser_platform_a
#   UNION ALL
#   SELECT * FROM sat_advertiser_platform_c;
#
#   SELECT h.advertiser_bk, s.record_source, s.load_date, s.tier
#   FROM hub_advertiser h
#   JOIN all_sats s ON s.advertiser_hk = h.advertiser_hk
#   ORDER BY h.advertiser_bk, s.load_date;
#
#   -- Q30 star projected from the vault (expect block).
#   CREATE OR REPLACE VIEW dim_advertiser AS
#   WITH current_sat AS (
#       SELECT advertiser_hk, name, tier, record_source,
#              ROW_NUMBER() OVER (PARTITION BY advertiser_hk ORDER BY load_date DESC) AS rn
#       FROM all_sats
#   )
#   SELECT h.advertiser_bk AS advertiser_id, s.name, s.tier, s.record_source
#   FROM hub_advertiser h
#   JOIN current_sat s ON s.advertiser_hk = h.advertiser_hk AND s.rn = 1;
#
#   SELECT advertiser_id, name, tier FROM dim_advertiser ORDER BY advertiser_id;
#
#   -- Q30 the same answer from the raw vault (expect block).
#   SELECT ha.advertiser_bk, hc.campaign_bk, s.tier
#   FROM hub_campaign hc
#   JOIN link_advertiser_campaign l ON l.campaign_hk = hc.campaign_hk
#   JOIN hub_advertiser ha ON ha.advertiser_hk = l.advertiser_hk
#   JOIN (
#       SELECT advertiser_hk, tier,
#              ROW_NUMBER() OVER (PARTITION BY advertiser_hk ORDER BY load_date DESC) AS rn
#       FROM all_sats
#   ) s ON s.advertiser_hk = ha.advertiser_hk AND s.rn = 1
#   ORDER BY hc.campaign_bk;
#
#   -- Q31 two sources both using id=1 collapse to 1 hub key unless the source
#   -- is part of the business key.
#   SELECT COUNT(DISTINCT MD5(CAST(src_id AS CHAR)))                       AS naive_keys,
#          COUNT(DISTINCT MD5(CONCAT_WS('||', source, CAST(src_id AS CHAR)))) AS scoped_keys
#   FROM (SELECT 1 AS src_id, 'platform_a' AS source
#         UNION ALL SELECT 1, 'platform_b') t;
#
# MySQL 8.0+ notes: Data Vault loads are pure INSERT-only -- no UPDATE on hubs,
# links, or satellites. The PRIMARY KEY on (advertiser_hk, load_date,
# record_source) makes the satellite idempotent under replay. MD5 hash keys
# let every table derive its surrogate independently, which is what enables
# parallel loads. The "fan-out without picking the current row" trap is the
# same defect as an SCD2 boundary bug -- the projected dim_advertiser view
# exists precisely so analysts do not have to write the window themselves.
