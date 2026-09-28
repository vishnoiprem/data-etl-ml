"""
Q25: Notification Delivery Analytics   [Medium | Dim Model — star schema]
Tags: Star Schema

Dashboard for notification delivery effectiveness across channels (push, email,
SMS) and USER SEGMENTS.

READ THIS WITH Q21. Same domain, opposite discipline:
  Q21 = OLTP. Normalised, composite keys, constraints, append-only retries.
  Q25 = OLAP. Denormalised star, surrogate keys, SCD2 dims, pre-aggregation.
  Being able to model the same domain both ways, and say why they differ, is
  what a dedicated modeling round is actually testing.

GRAIN: one row per DELIVERY ATTEMPT (user x notification x channel x attempt).
  Not per notification — a notification fanned out to 3 channels is 3 deliveries
  and each has its own outcome. Same reasoning as Q21, carried into the star.

THE HARD PART, AND THE WHOLE POINT OF THIS QUESTION — "by user segment":
  Segment is a SLOWLY CHANGING attribute. A user who was 'new' in January is
  'engaged' in March. If you join the fact to the CURRENT dim row, you attribute
  January's deliveries to the segment the user is in TODAY, and your historical
  segment report silently rewrites itself every single day.

  The fix is SCD Type 2 on dim_user plus a POINT-IN-TIME join:
        ON  f.sent_date >= d.effective_from
        AND (f.sent_date <  d.effective_to OR d.effective_to IS NULL)

  This file asserts BOTH the correct point-in-time result and the wrong
  current-segment result, so the size of the error is visible: the wrong join
  moves 2 of 5 deliveries into the wrong segment and makes the 'new' segment
  vanish from the report entirely.

THE DELIVERY FUNNEL: sent -> delivered -> opened -> clicked.
  Each rate needs a DECLARED denominator, and mixing them is the classic bug:
      delivery rate = delivered / sent
      open rate     = opened / DELIVERED   (not / sent)
      click rate    = clicked / OPENED     (or / delivered — say which)
  Quoting an "open rate" over `sent` mixes a delivery problem into an engagement
  metric, and a carrier outage then looks like users losing interest.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("25-model-notification-delivery-analytics")
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



DDL = """
-- Grain: one row per delivery attempt.
CREATE TABLE fact_notification_delivery (
  delivery_key       BIGINT,    -- PK (surrogate)
  notification_id    BIGINT,    -- degenerate dimension (natural key from OLTP)
  user_key           BIGINT,    -- FK dim_user  (SCD2 -> join point-in-time!)
  channel_key        INT,       -- FK dim_channel
  type_key           INT,       -- FK dim_notification_type
  status_key         INT,       -- FK dim_delivery_status
  sent_date_key      INT,       -- FK dim_date (PARTITION KEY)
  sent_date          DATE,      -- kept for the point-in-time dim join
  attempt_no         INT,
  -- funnel milestone timestamps (accumulating-snapshot flavour on one row)
  delivered_ts       TIMESTAMP,
  opened_ts          TIMESTAMP,
  clicked_ts         TIMESTAMP,
  latency_ms         BIGINT     -- additive
);

-- PERIODIC SNAPSHOT for the dashboard: channel x segment x day.
CREATE TABLE fact_delivery_daily (
  date_key     INT,
  channel_key  INT,
  segment      VARCHAR(20),
  sent         BIGINT,
  delivered    BIGINT,
  opened       BIGINT,
  clicked      BIGINT
);

-- SCD2. Segment changes over time, so history must be versioned.
CREATE TABLE dim_user (
  user_key       BIGINT,        -- PK (surrogate, one per VERSION)
  user_id        VARCHAR(40),   -- natural key (stable across versions)
  segment        VARCHAR(20),   -- new / casual / engaged / dormant
  country        VARCHAR(60),
  effective_from DATE,
  effective_to   DATE,          -- NULL = current.  [from, to) half-open
  is_current     BOOLEAN
);

CREATE TABLE dim_channel         ( channel_key INT, channel_name VARCHAR(20) );
CREATE TABLE dim_notification_type ( type_key INT, type_code VARCHAR(40),
                                     category VARCHAR(20) );
CREATE TABLE dim_delivery_status ( status_key INT, status_name VARCHAR(20),
                                   is_terminal BOOLEAN );
CREATE TABLE dim_date            ( date_key INT, full_date DATE, week_of_year INT );
"""

# SCD2 dim: user 1 moved 'new' -> 'engaged' on 2026-01-15. User 2 always engaged.
spark.createDataFrame([
    (1, "u1", "new",     "2026-01-01", "2026-01-15", False),
    (2, "u1", "engaged", "2026-01-15", None,         True),
    (3, "u2", "engaged", "2026-01-01", None,         True),
], ["user_key", "user_id", "segment", "effective_from", "effective_to", "is_current"]
).createOrReplaceTempView("dim_user")

# Deliveries straddle u1's segment change: 01-10 and 01-12 are 'new',
# 01-20 is 'engaged'.
spark.createDataFrame([
    (1, "u1", "push",  "delivered", "2026-01-10"),
    (2, "u1", "push",  "opened",    "2026-01-20"),
    (3, "u2", "email", "delivered", "2026-01-10"),
    (4, "u1", "sms",   "failed",    "2026-01-12"),
    (5, "u2", "email", "opened",    "2026-01-20"),
], ["delivery_key", "user_id", "channel", "status", "sent_date"]
).createOrReplaceTempView("fact_notification_delivery")

# 1. Channel effectiveness. No dim join needed, so no SCD2 subtlety.
expect("Q25 delivery + open rate by channel", """
SELECT channel,
       COUNT(*) AS sent,
       SUM(CASE WHEN status IN ('delivered','opened') THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN status = 'opened' THEN 1 ELSE 0 END) AS opened,
       ROUND(100.0 * AVG(CASE WHEN status IN ('delivered','opened')
                              THEN 1.0 ELSE 0.0 END), 2) AS delivery_rate_pct
FROM fact_notification_delivery
GROUP BY channel
ORDER BY channel
""", [
    ("email", 2, 2, 1, 100.00),
    ("push",  2, 2, 1, 100.00),
    ("sms",   1, 0, 0, 0.00),
])

# 2. THE CORRECT point-in-time segment join.
expect("Q25 by segment — POINT-IN-TIME (correct)", """
SELECT d.segment,
       COUNT(*) AS sent,
       SUM(CASE WHEN f.status IN ('delivered','opened') THEN 1 ELSE 0 END) AS delivered,
       ROUND(100.0 * AVG(CASE WHEN f.status IN ('delivered','opened')
                              THEN 1.0 ELSE 0.0 END), 2) AS delivery_rate_pct
FROM fact_notification_delivery f
JOIN dim_user d
  ON d.user_id = f.user_id
 AND f.sent_date >= d.effective_from
 AND (f.sent_date < d.effective_to OR d.effective_to IS NULL)
GROUP BY d.segment
ORDER BY d.segment
""", [
    ("engaged", 3, 3, 100.00),
    ("new",     2, 1, 50.00),
])

# 3. The WRONG current-segment join, asserted. The 'new' segment disappears and
#    the engaged cohort's delivery rate is diluted from 100% to 80%.
expect("Q25 by segment — CURRENT ROW ONLY (wrong)", """
SELECT d.segment,
       COUNT(*) AS sent,
       SUM(CASE WHEN f.status IN ('delivered','opened') THEN 1 ELSE 0 END) AS delivered,
       ROUND(100.0 * AVG(CASE WHEN f.status IN ('delivered','opened')
                              THEN 1.0 ELSE 0.0 END), 2) AS delivery_rate_pct
FROM fact_notification_delivery f
JOIN dim_user d ON d.user_id = f.user_id AND d.is_current
GROUP BY d.segment
ORDER BY d.segment
""", [("engaged", 5, 4, 80.00)])

# 4. Open rate over the RIGHT denominator (delivered), not sent.
expect("Q25 open rate over delivered, by segment", """
WITH pit AS (
    SELECT f.*, d.segment
    FROM fact_notification_delivery f
    JOIN dim_user d
      ON d.user_id = f.user_id
     AND f.sent_date >= d.effective_from
     AND (f.sent_date < d.effective_to OR d.effective_to IS NULL)
)
SELECT segment,
       SUM(CASE WHEN status IN ('delivered','opened') THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN status = 'opened' THEN 1 ELSE 0 END) AS opened,
       ROUND(100.0 * SUM(CASE WHEN status = 'opened' THEN 1 ELSE 0 END)
                   / NULLIF(SUM(CASE WHEN status IN ('delivered','opened')
                                     THEN 1 ELSE 0 END), 0), 2) AS open_rate_pct
FROM pit GROUP BY segment ORDER BY segment
""", [
    ("engaged", 3, 2, 66.67),
    ("new",     1, 0, 0.00),
])

# ---- MySQL way ----------------------------------------------------------
# DDL-only. The same notification domain as Q21, modeled dimensionally here:
# fact_notification has one row per logical notification; a per-channel
# delivery sub-fact is a separate table for retry history; dim_channel and
# dim_user provide context. Booleans -> TINYINT(1). Two example dimension
# inserts:
#
# CREATE TABLE dim_user (
#     user_key  BIGINT      NOT NULL AUTO_INCREMENT,
#     user_id   BIGINT      NOT NULL,
#     country   VARCHAR(8)  NOT NULL,
#     PRIMARY KEY (user_key),
#     UNIQUE KEY uq_dim_user_nk (user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE dim_channel (
#     channel_key INT         NOT NULL AUTO_INCREMENT,
#     name        VARCHAR(16) NOT NULL,
#     PRIMARY KEY (channel_key),
#     UNIQUE KEY uq_dim_channel_name (name)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE dim_notification_type (
#     type_key      INT         NOT NULL AUTO_INCREMENT,
#     code          VARCHAR(32) NOT NULL,
#     category      VARCHAR(16) NOT NULL,
#     is_critical   TINYINT(1)  NOT NULL DEFAULT 0,
#     PRIMARY KEY (type_key),
#     UNIQUE KEY uq_dim_nt_code (code)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE fact_notification (
#     notification_key BIGINT    NOT NULL AUTO_INCREMENT,
#     user_key         BIGINT    NOT NULL,
#     type_key         INT       NOT NULL,
#     trigger_kind     VARCHAR(10) NOT NULL,
#     created_at       TIMESTAMP NOT NULL,
#     read_at          TIMESTAMP NULL,
#     is_read          TINYINT(1) NOT NULL DEFAULT 0,
#     PRIMARY KEY (notification_key),
#     KEY ix_fn_user (user_key, created_at),
#     KEY ix_fn_type (type_key, created_at),
#     CONSTRAINT fk_fn_user FOREIGN KEY (user_key) REFERENCES dim_user(user_key),
#     CONSTRAINT fk_fn_type FOREIGN KEY (type_key) REFERENCES dim_notification_type(type_key)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE fact_notification_delivery (
#     delivery_key     BIGINT    NOT NULL AUTO_INCREMENT,
#     notification_key BIGINT    NOT NULL,
#     channel_key      INT       NOT NULL,
#     attempt_no       INT       NOT NULL,
#     status           VARCHAR(16) NOT NULL,
#     attempted_at     TIMESTAMP NOT NULL,
#     PRIMARY KEY (delivery_key),
#     UNIQUE KEY uq_fnd_attempt (notification_key, channel_key, attempt_no),
#     KEY ix_fnd_channel_status (channel_key, status),
#     CONSTRAINT fk_fnd_notif   FOREIGN KEY (notification_key) REFERENCES fact_notification(notification_key),
#     CONSTRAINT fk_fnd_channel FOREIGN KEY (channel_key)      REFERENCES dim_channel(channel_key)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# INSERT INTO dim_channel (name) VALUES ('push'), ('email'), ('sms');
# INSERT INTO dim_notification_type (code, category, is_critical) VALUES
#     ('friend_request', 'social', 0),
#     ('comment_reply',  'social', 0),
#     ('security_alert', 'system', 1);
