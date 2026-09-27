"""
Problem 02: Define success for Facebook Groups, then compute it.

Meta flavor: "How would you measure the success of Facebook Groups?"

The model answer, in the spine from problem 01:
  USER VALUE  - "Success means people find groups worth RETURNING to."
  BEHAVIOUR   - repeat PARTICIPATION, not joins. Joins are a one-time vanity
                event; a group with 10,000 members and no posts is dead.
  METRIC      - primary:   weekly active participants per group
                secondary: contributor-to-lurker ratio
  GRAIN       - one row per (user, group, day) activity fact.
  QUERY       - below.

Why "participants" and not "members": membership is monotonic and only ever
grows, so it cannot detect decline. Any metric that cannot go down is not a
health metric. That sentence is worth memorising.

Contributor vs lurker:
  contributor = posted or commented; lurker = viewed only.
  A healthy group needs lurkers (most members always are), so the ratio is a
  balance indicator, not a number to maximise.

Spark note:
- Grain is (user, group, day); dedup to that grain before counting or an
  active-user count silently becomes an event count.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _common import spark, expect

# One row per (user, group, day, action). g1 is healthy, g2 is a lurker-only
# group with no contributors at all — exactly the "dead group" case the metric
# has to be able to surface.
spark.createDataFrame([
    ("g1", 1, "2026-01-05", "post"),
    ("g1", 2, "2026-01-05", "comment"),
    ("g1", 3, "2026-01-06", "view"),
    ("g1", 1, "2026-01-07", "comment"),
    ("g1", 4, "2026-01-07", "view"),
    ("g2", 5, "2026-01-05", "view"),
    ("g2", 6, "2026-01-06", "view"),
], ["group_id", "user_id", "activity_date", "action"]).createOrReplaceTempView("group_activity")

expect("weekly active participants per group", """
SELECT group_id,
       COUNT(DISTINCT user_id) AS weekly_active_participants,
       COUNT(DISTINCT CASE WHEN action IN ('post', 'comment') THEN user_id END)
           AS contributors,
       COUNT(DISTINCT CASE WHEN action = 'view' THEN user_id END) AS viewers
FROM group_activity
GROUP BY group_id
ORDER BY group_id
""", [
    ("g1", 4, 2, 2),
    ("g2", 2, 0, 2),
])

# Contributor ratio. g2 scores 0.0 -> the group is pure lurkers and, by the
# definition we committed to, not succeeding regardless of its member count.
expect("contributor-to-participant ratio", """
SELECT group_id,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN action IN ('post','comment')
                                         THEN user_id END)
                   / COUNT(DISTINCT user_id), 2) AS contributor_pct
FROM group_activity
GROUP BY group_id
ORDER BY group_id
""", [("g1", 50.00), ("g2", 0.00)])
