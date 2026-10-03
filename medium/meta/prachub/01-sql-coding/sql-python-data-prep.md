# Write SQL and Python for Data Prep (DAU/WAU/MAU, Retention, Funnel)

## 1. Simple way to think
- Clickstream: `events(user_id, event_type, ts, properties)`. Users: `users(user_id, signup_ts, plan)`.
- DAU = distinct users with at least one event that day. WAU = 7-day rolling distinct. MAU = 30-day rolling distinct.
- Retention D1 = users who came back exactly 1 day after signup. W1 = came back within 7 days after signup.
- Funnel: count distinct users at each step, compute conversion = step_n / step_1.
- Always normalize timezones to UTC and treat the user as a unit, not an event.

## 2. Interview write-up (how to solve it)

```sql
-- DAU
SELECT event_date, COUNT(DISTINCT user_id) AS dau
FROM (SELECT user_id, DATE_TRUNC('day', ts) AS event_date FROM events) t
GROUP BY 1 ORDER BY 1;

-- D1 retention
WITH first_day AS (
    SELECT user_id, DATE_TRUNC('day', signup_ts) AS d0 FROM users
),
next_day AS (
    SELECT user_id, DATE_TRUNC('day', MIN(ts)) AS d1 FROM events GROUP BY user_id
)
SELECT fd.d0,
       COUNT(*)                            AS cohort,
       COUNT(*) FILTER (WHERE nd.d1 = fd.d0 + INTERVAL '1 day') AS retained_d1,
       COUNT(*) FILTER (WHERE nd.d1 = fd.d0 + INTERVAL '1 day') * 1.0
            / NULLIF(COUNT(*), 0)         AS d1_retention
FROM first_day fd LEFT JOIN next_day nd USING (user_id)
GROUP BY 1 ORDER BY 1;
```

```python
# Python / pandas
import pandas as pd

events = pd.DataFrame(events_raw, columns=["user_id", "event_type", "ts", "properties"])
events["event_date"] = events["ts"].dt.normalize()

# DAU
dau = events.groupby("event_date")["user_id"].nunique().rename("dau")

# Funnel
funnel = (events[events["event_type"].isin(["view", "click", "purchase"])]
          .groupby("event_date")["user_id"]
          .apply(lambda s: pd.Series({
              "view":     (s.values == "view").sum() if False else
                          events.loc[s.index][events.loc[s.index, "event_type"] == "view"]["user_id"].nunique(),
              "click":    events.loc[s.index][events.loc[s.index, "event_type"] == "click"]["user_id"].nunique(),
              "purchase": events.loc[s.index][events.loc[s.index, "event_type"] == "purchase"]["user_id"].nunique(),
          })))
```

## 3. Best optimized solution
A single pandas pipeline keeps it vectorized and clean.

```python
import pandas as pd

def engagement_metrics(events_df, users_df, lookback_days=30):
    e = events_df.assign(day=events_df["ts"].dt.normalize())
    u = users_df.assign(signup_day=users_df["signup_ts"].dt.normalize())

    dau = e.groupby("day")["user_id"].nunique().rename("dau").to_frame()

    # WAU / MAU via rolling distinct (approximate via min/max trick is fine for interview)
    wau = (e.set_index("ts").groupby("user_id").resample("D")["user_id"]
              .nunique().rolling(7).sum().groupby(level=0).max())
    # for simplicity in interview, return DAU and document the WAU/MAU approach

    # D1 retention
    next_event = e.groupby("user_id")["day"].min().rename("next_day")
    cohort = u.merge(next_event, on="user_id", how="left")
    cohort["retained_d1"] = (cohort["next_day"] == cohort["signup_day"] + pd.Timedelta(days=1))
    d1 = cohort.groupby("signup_day")["retained_d1"].mean().rename("d1")

    # Funnel per day
    funnel = (e[e["event_type"].isin(["view", "click", "purchase"])]
              .groupby(["day", "event_type"])["user_id"].nunique()
              .unstack(fill_value=0))
    funnel["view_to_click"]    = funnel["click"]    / funnel["view"]
    funnel["click_to_purchase"]= funnel["purchase"] / funnel["click"]
    return dau, d1, funnel
```

### Why it's optimal
- Vectorized: no Python loops over users.
- `groupby` + `nunique` uses C-hashed sets.
- Single `assign` keeps the dataframe immutable and chainable.
- Index on `events(user_id, ts)` makes day-truncation an index range scan.

### Common mistakes & interviewer tips
- Counting events instead of users (DAU = distinct users, not rows).
- Mixing timezones (clamp all timestamps to UTC first).
- Tip: clarify "retention" definition. New-user D1 is more standard than all-user D1, but the question matters.
