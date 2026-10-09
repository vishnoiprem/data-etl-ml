# Lesson 18 — Designing a Star Schema for Instagram

> **What you'll learn:** the event-grain fact for an Instagram-
> style product (post events: view, like, comment, share, save)
> and the trick of using *two* user keys on the fact to capture
> the actor-vs-author relationship.

---

## The prompt

> "Design a data warehouse for Instagram so the analytics team
> can answer questions about engagement, reach, and creator
> performance."

This is the third canonical question. The trick is the
*actor-vs-author* distinction: every event has a user who
*did* the action (the actor) and a user who *owns* the post
(the author). The two are different people, and you need
both to answer "engagement per post" and "engagement per
creator."

---

## The star schema

```
                ┌──────────────┐
                │  dim_users   │
                │  (SCD 2)     │
                └──────┬───────┘
                       │ user_key
                       │
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ dim_date │◄───┤ fact_post_   ├───►│  dim_posts   │
└──────────┘    │   events     │    └──────────────┘
                │              │
┌──────────────┐│ (no numeric  │
│dim_event_type│┤  measures —  │
│              │┤  just joins) │
└──────────────┘└──────────────┘
                       │
                       └──────► dim_users  (again, as the author)
```

Five tables. One fact, four dimensions. The fact has *two*
foreign keys to `dim_users` — one for the actor, one for the
author.

---

## Why two user keys

Every event on a post has:

- The **actor** — the user who did the action (liked,
  commented, viewed). For "view" events on a public post,
  the actor is anyone. For "like" and "comment," the actor
  is a logged-in user.
- The **author** — the user who created the post. Fixed
  per post.

To answer "engagement per post" we need the post. To answer
"engagement per creator" we need the author. To answer
"engagement per user" (i.e., what posts has this user
interacted with) we need the actor.

The two keys on the fact table are the *bridge* between
these three views. Both are FKs to `dim_users`. The dim is
*reused* — that's the definition of a conformed dimension.

```sql
CREATE TABLE fact_post_events (
    event_key        INTEGER PRIMARY KEY,
    post_key         INTEGER NOT NULL,
    actor_user_key   INTEGER NOT NULL,
    author_user_key  INTEGER NOT NULL,  -- for "per creator" queries
    event_type_key   INTEGER NOT NULL,
    date_key         INTEGER NOT NULL,
    minute_of_day    INTEGER,
    FOREIGN KEY (post_key)        REFERENCES dim_posts(post_key),
    FOREIGN KEY (actor_user_key)  REFERENCES dim_users(user_key),
    FOREIGN KEY (author_user_key) REFERENCES dim_users(user_key),
    FOREIGN KEY (event_type_key)  REFERENCES dim_event_type(event_type_key),
    FOREIGN KEY (date_key)        REFERENCES dim_date(date_key)
);
```

The `author_user_key` is denormalized — it could be derived
from `dim_posts.user_key` via a join, but storing it on the
fact saves a join for the most common query ("engagement per
creator"). This is a *deliberate denormalization* for query
performance.

---

## The grain: one row per event

The grain is **one row per (post, actor, event_type, minute)**.
Why this and not "one row per view" or "one row per post"?

- "One row per view" would inflate the table to billions of
  rows for a busy post.
- "One row per post" loses the per-actor data; you can't
  answer "what did this user like last week."

The right grain captures the *event* — every time a user did
something to a post, a row. Aggregations roll up
(`COUNT(*)` gives "engagement per post", "engagement per
creator", etc.).

If the same user likes the same post twice in the same
minute (e.g., they un-liked and re-liked), you get two rows.
If the interviewer cares, you can de-dupe at load time
(keeping only the latest event per actor+post) or add a
`is_first_in_minute` flag.

---

## The measures

This fact is a **factless fact table** — there are no numeric
measures. The fact exists to record *that an event happened*,
not to measure its magnitude. The measures are at the
aggregate level (computed by the analyst):

- `engagement_rate` = COUNT(engagement events) / COUNT(views)
- `avg_likes_per_post` = SUM(likes) / COUNT(posts)
- `daily_active_users` = COUNT(DISTINCT actor_user_key)

See Lesson 27 for the full treatment of factless facts.

---

## The dimensions

### `dim_users` (SCD Type 2)

User attributes change over time. SCD 2 is the right call
when you need "what was this user's country when they
posted this comment?" The SCD 2 fields are the same as
in the e-commerce schema.

### `dim_posts`

A post is mostly static once created. The dim has the
caption, media type, and the user_key of the author. We
do *not* make `dim_posts` SCD 2 — once a post is created,
its attributes don't change. (If the user edits the
caption, the post_id stays the same but the caption
column updates — SCD 1 is fine for that.)

### `dim_event_type`

A tiny dim with 5 rows: view, like, comment, share, save.
We could have left the event type as a TEXT column on the
fact, but a dim lets us attach attributes (e.g.,
`is_engagement` to filter views out of the "engagement"
denominator).

### `dim_date`

The standard conformed date dim.

---

## Why is `dim_posts` not SCD 2?

A common question. The reasoning:

- A post's `caption` and `media_type` are mostly fixed.
  Edits are rare and don't usually need historical
  attribution.
- A post's *engagement* (likes, comments) is in the fact
  table, not the dim. The dim just describes the post.
- A post's `posted_at` is fixed.

The SCD 2 cost (extra rows, complex joins) is not worth
it for a post. SCD 1 (overwrite on edit) is the right
call.

The exception: if the product has a "delete post" feature
and you need to track when it was deleted, the
`is_deleted` flag needs SCD 2 to record the delete
event. But that's a rare requirement.

---

## Tradeoffs to call out

1. **Why two user keys on the fact?** "The actor and the
   author are different people. The actor is who did the
   action; the author is who owns the post. Storing both
   avoids a join to `dim_posts` for the most common
   'engagement per creator' query."
2. **Why is this a factless fact?** "The event has no
   numeric measure. The fact exists to record the
   occurrence; aggregates are computed at query time."
3. **Why not aggregate events at load time?** "Aggregating
   at load loses the per-actor data. We need the event
   grain for 'what did this user like last week' queries."
4. **Why is `dim_users` SCD 2?** "User country and
   `is_creator` flag change over time and we need
   historical attribution for accurate creator analytics."

---

## The DDL — running it

The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_instagram_schema(q)`. Run the demo:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

Output (truncated):

```
[instagram]  tables: ['dim_users', 'dim_posts', 'dim_event_type',
                     'dim_date', 'fact_post_events']
   fact_post_events sample row: {
     'event_key': 1, 'post_key': 1, 'actor_user_key': 2,
     'author_user_key': 1, 'event_type_key': 1,
     'date_key': 20240115, 'minute_of_day': 1100
   }
```

---

## Sample queries

### Engagement rate per post

```sql
SELECT
    p.post_id,
    p.caption,
    SUM(CASE WHEN et.is_engagement = 1 THEN 1 ELSE 0 END) AS engagements,
    COUNT(*) AS total_events,
    ROUND(
        1.0 * SUM(CASE WHEN et.is_engagement = 1 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        3
    ) AS engagement_rate
FROM fact_post_events f
JOIN dim_posts p ON f.post_key = p.post_key
JOIN dim_event_type et ON f.event_type_key = et.event_type_key
GROUP BY p.post_id, p.caption
ORDER BY engagement_rate DESC;
```

### Top 5 creators by total engagement

```sql
SELECT
    u.username,
    COUNT(*) AS n_engagements
FROM fact_post_events f
JOIN dim_event_type et ON f.event_type_key = et.event_type_key
JOIN dim_users u ON f.author_user_key = u.user_key
WHERE et.is_engagement = 1
GROUP BY u.username
ORDER BY n_engagements DESC
LIMIT 5;
```

---

## Try it

Open
[`code/star_schemas.py`](../code/star_schemas.py) and read
`build_instagram_schema`. Then:

1. State the grain out loud: "one row per (post, actor,
   event_type, minute)."
2. Identify the two foreign keys to `dim_users` and explain
   why each is there.
3. Run the test and watch the 10 sample events aggregate
   correctly.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
