"""
Q21: Notification System   [Medium | Data Model — OLTP relational]

Design a relational schema for a multi-channel notification system: event-
triggered AND scheduled notifications, per-user preferences, delivery status
tracking, and read/unread state.

NOTE this is an OLTP schema, not a star schema. Normalise, use composite keys,
and let constraints enforce the rules. Q25 models the SAME domain dimensionally
for analytics — read them together, the contrast is the lesson.

THE GRAIN DECISIONS (state all three before drawing anything):
  1. notification          = one row per (user, logical notification)
  2. notification_delivery = one row per (notification, channel, ATTEMPT)
  3. notification_read     = one row per notification that was read

Why delivery is a separate table — this is the whole question:
  One notification fans out to several channels, and each channel succeeds or
  fails INDEPENDENTLY. Put `status` on `notification` and you cannot represent
  "push delivered, email bounced". Every candidate who collapses these two
  grains fails this question.

Why attempt_no is in the delivery key:
  Retries are append-only. "Current status" is the LATEST attempt per
  (notification, channel) — a window function, not an UPDATE. Overwriting the
  row destroys the retry history you need to debug a carrier outage.

Why read/unread is per NOTIFICATION, not per delivery:
  The user reads the thing once. If read state lived on delivery, a user who
  got both push and email would show 2 reads for 1 notification, and unread
  badge counts would be wrong.

Event-triggered vs scheduled — one table or two?
  ONE table with a `trigger_kind` discriminator and a nullable `scheduled_for`.
  They share every downstream concern (preferences, fan-out, delivery, read
  state), so splitting them doubles all of that logic. Two tables would only be
  right if scheduled notifications had genuinely different attributes.

Preferences are a THREE-way relationship:
  (user x notification_type x channel) -> enabled. That is a junction table with
  a composite PK, not columns like `email_enabled` on the users table. Adding a
  channel must not require an ALTER TABLE on users.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("21-model-notification-system")
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
-- Constraints are written as comments: Spark does not enforce PK/FK, but the
-- interviewer is grading the constraints, so say them out loud.

CREATE TABLE users (
  user_id        BIGINT,          -- PK
  handle         VARCHAR(40),     -- UNIQUE
  timezone       VARCHAR(40),     -- needed for quiet-hours logic
  created_at     TIMESTAMP
);

CREATE TABLE notification_type (
  type_id        INT,             -- PK
  code           VARCHAR(40),     -- UNIQUE: 'friend_request', 'comment_reply'
  category       VARCHAR(20),     -- social / system / marketing
  is_critical    BOOLEAN          -- critical types IGNORE preferences (security)
);

CREATE TABLE channel (
  channel_id     INT,             -- PK
  name           VARCHAR(20)      -- UNIQUE: push / email / sms
);

-- 3-way preference junction. PK (user_id, type_id, channel_id).
CREATE TABLE user_notification_preference (
  user_id        BIGINT,          -- FK users
  type_id        INT,             -- FK notification_type
  channel_id     INT,             -- FK channel
  is_enabled     BOOLEAN,
  quiet_from     TIME,            -- nullable
  quiet_to       TIME
);

-- Grain: one row per (user, logical notification).
CREATE TABLE notification (
  notification_id BIGINT,         -- PK
  user_id         BIGINT,         -- FK users  (the RECIPIENT)
  type_id         INT,            -- FK notification_type
  trigger_kind    VARCHAR(10),    -- CHECK IN ('event','scheduled')
  source_event_id BIGINT,         -- nullable; set when trigger_kind='event'
  scheduled_for   TIMESTAMP,      -- nullable; set when trigger_kind='scheduled'
  payload         STRING,         -- JSON: rendered title/body params
  created_at      TIMESTAMP
  -- CHECK (trigger_kind='scheduled' AND scheduled_for IS NOT NULL)
  --    OR (trigger_kind='event'     AND source_event_id IS NOT NULL)
);

-- Grain: one row per (notification, channel, attempt). APPEND ONLY.
CREATE TABLE notification_delivery (
  delivery_id     BIGINT,         -- PK
  notification_id BIGINT,         -- FK notification
  channel_id      INT,            -- FK channel
  attempt_no      INT,            -- 1,2,3...  UNIQUE(notification_id,channel_id,attempt_no)
  status          VARCHAR(20),    -- queued/sent/delivered/failed/bounced
  failure_reason  VARCHAR(100),   -- nullable
  attempted_at    TIMESTAMP
);

-- Grain: one row per notification that has been read. Absence = unread.
CREATE TABLE notification_read (
  notification_id BIGINT,         -- PK, FK notification
  read_at         TIMESTAMP
);
"""

# ---- Seed data ------------------------------------------------------------
spark.createDataFrame(
    [(1, "push"), (2, "email"), (3, "sms")], ["channel_id", "name"]
).createOrReplaceTempView("channel")

# u1 wants push+email for type 1 but NOT sms. u2 refuses push.
spark.createDataFrame([
    (1, 1, 1, True), (1, 1, 2, True), (1, 1, 3, False),
    (2, 1, 1, False), (2, 1, 2, True),
    (3, 2, 1, True),
], ["user_id", "type_id", "channel_id", "is_enabled"]
).createOrReplaceTempView("user_notification_preference")

spark.createDataFrame([
    (101, 1, 1, "event",     "2026-01-10 10:00:00"),
    (102, 2, 1, "event",     "2026-01-10 10:01:00"),
    (103, 3, 2, "scheduled", "2026-01-10 12:00:00"),
    (104, 1, 1, "event",     "2026-01-10 10:05:00"),
], ["notification_id", "user_id", "type_id", "trigger_kind", "created_at"]
).createOrReplaceTempView("notification")

# Note 101/email failed then succeeded on retry; 103/push failed twice.
spark.createDataFrame([
    (1, 101, 1, 1, "delivered", None),
    (2, 101, 2, 1, "failed",    "smtp timeout"),
    (3, 101, 2, 2, "delivered", None),
    (4, 102, 2, 1, "delivered", None),
    (5, 103, 1, 1, "failed",    "invalid token"),
    (6, 103, 1, 2, "failed",    "invalid token"),
    (7, 104, 1, 1, "delivered", None),
    (8, 104, 2, 1, "delivered", None),
], ["delivery_id", "notification_id", "channel_id", "attempt_no",
    "status", "failure_reason"]).createOrReplaceTempView("notification_delivery")

spark.createDataFrame([
    (101, "2026-01-10 10:30:00"), (102, "2026-01-10 11:00:00"),
], ["notification_id", "read_at"]).createOrReplaceTempView("notification_read")

# ---- Prove the model answers the questions it exists for -----------------

# 1. Fan-out: which channels may we actually use for this user+type?
expect("Q21 enabled channels for user 1 / type 1", """
SELECT c.name
FROM user_notification_preference p
JOIN channel c ON c.channel_id = p.channel_id
WHERE p.user_id = 1 AND p.type_id = 1 AND p.is_enabled
ORDER BY c.name
""", [("email",), ("push",)])

# 2. Current status = LATEST attempt per (notification, channel). This is why
#    delivery is append-only with attempt_no.
expect("Q21 delivery success rate by channel (latest attempt)", """
WITH latest AS (
    SELECT notification_id, channel_id, status,
           ROW_NUMBER() OVER (PARTITION BY notification_id, channel_id
                              ORDER BY attempt_no DESC) AS rn
    FROM notification_delivery
)
SELECT c.name AS channel,
       COUNT(*) AS attempted,
       SUM(CASE WHEN l.status = 'delivered' THEN 1 ELSE 0 END) AS delivered,
       ROUND(100.0 * AVG(CASE WHEN l.status = 'delivered' THEN 1.0 ELSE 0.0 END), 2)
           AS success_pct
FROM latest l
JOIN channel c ON c.channel_id = l.channel_id
WHERE l.rn = 1
GROUP BY c.name
ORDER BY c.name
""", [("email", 3, 3, 100.00), ("push", 3, 2, 66.67)])

# 3. Unread badge count. LEFT ANTI on the read table — absence means unread.
expect("Q21 unread count per user", """
SELECT n.user_id, COUNT(*) AS unread
FROM notification n
LEFT JOIN notification_read r ON r.notification_id = n.notification_id
WHERE r.notification_id IS NULL
GROUP BY n.user_id
ORDER BY n.user_id
""", [(1, 1), (3, 1)])

# 4. Total failure: failed on EVERY channel we tried. This is the alerting
#    query, and it is only expressible because delivery has its own grain.
expect("Q21 notifications that failed on all channels", """
WITH latest AS (
    SELECT notification_id, channel_id, status,
           ROW_NUMBER() OVER (PARTITION BY notification_id, channel_id
                              ORDER BY attempt_no DESC) AS rn
    FROM notification_delivery
)
SELECT notification_id
FROM latest WHERE rn = 1
GROUP BY notification_id
HAVING SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) = 0
ORDER BY notification_id
""", [(103,)])

# 5. Retry history survives — the property an UPDATE-in-place model destroys.
expect("Q21 retry history is preserved", """
SELECT notification_id, channel_id, COUNT(*) AS attempts
FROM notification_delivery
GROUP BY notification_id, channel_id
HAVING COUNT(*) > 1
ORDER BY notification_id, channel_id
""", [(101, 2, 2), (103, 1, 2)])
