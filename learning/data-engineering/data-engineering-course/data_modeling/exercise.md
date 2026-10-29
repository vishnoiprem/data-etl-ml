# Capstone Exercise — Twitter/X Schema

> **Format:** end-to-end design exercise. Time-box:
> 2 hours. Produce a working SQLite schema, a SQL
> query, and a 1-page narrative.
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

## The prompt

Design a data warehouse for **Twitter (now X)**. The
system has:

- **Users** with profiles, follower/followee
  relationships, and verified status.
- **Tweets** (now "posts") with text, media
  attachments, and reply / retweet / quote
  relationships.
- **Engagement** events: impressions, likes,
  reposts, replies, bookmarks, profile clicks,
  link clicks.
- **Timelines** that show a user a ranked list of
  tweets.

The warehouse must support:

1. **DAU / MAU** with a "logged in" definition.
2. **Tweet impressions** (how many timelines showed
   a given tweet).
3. **Engagement rate** (likes + reposts + replies
   ÷ impressions).
4. **Follower growth** (new followers per day, per
   user).
5. **Top tweets** by engagement in a time window.
6. **Search** by hashtag, mentions, and full-text.

---

## What to produce

1. **Discovery questions** — at least ten.
2. **Requirements doc** — consumers, use cases,
   sources, key facts.
3. **Star schema** — fact tables, dimensions, grain,
   SCD type, all foreign keys.
4. **Indexes and partitions** — at least one
   indexing decision and one partitioning decision,
   with reasoning.
5. **Five SQL queries** — DAU, engagement rate,
   follower growth, top tweets, and one of your
   choice.
6. **Materialized view** — for at least one of the
   five queries.
7. **Tradeoffs** — at least four, one per fact table
   if you have multiple.

---

## Hints

- A tweet is *one row per tweet* — but the engagement
  events (impressions, likes, etc.) are separate
  facts. Don't put them all on the tweet.
- An *impression* is "this tweet appeared on this
  user's timeline at this time." That's a
  transactional fact. So is each like, repost,
  reply.
- The user dim is SCD 2 — verified status changes,
  bio changes, account suspensions, all need
  historical attribution.
- The "follow" relationship is a *factless fact*
  with `follower_key`, `followee_key`, and
  `follow_date_key`. The follower growth report is
  a count of new fact rows per day.
- Timelines are *generated* — they're a function of
  who you follow, what they tweeted, and the
  ranking algorithm. The warehouse doesn't store
  timelines; it stores the engagement events that
  result from them.
- The text of the tweet is a slowly changing dim
  (edits). Each edit creates a new version of the
  dim row.
- Hashtags and mentions are *many-to-many* between
  tweets and tags/users. Use bridge tables.

---

## Sample discovery questions

1. Is "engagement" defined as impressions, or
   interactions? Or both?
2. Are impressions measured per *timeline render*
   or per *unique viewer*?
3. Is "tweet" now called a "post"? Are replies
   separate posts or attributes of the parent?
4. What is the cardinality of users? 500M+? 1B+?
5. What is the daily volume of tweets? 500M?
6. What is the daily volume of engagement events?
7. Are reposts / quote tweets tracked separately?
8. How are retweets-with-comment (quote tweets)
   modeled? Are they new posts or modifications of
   the original?
9. Is there a "view count" for video posts, separate
   from impressions?
10. What is the SLA for the analytics warehouse? Are
    operational dashboards real-time?
11. Are deleted tweets / accounts reflected in the
    warehouse? GDPR right-to-be-forgotten?
12. Are bookmarks (private saves) tracked in
    engagement metrics?

---

## Sample star schema (one possible answer)

```
fact_tweets (transactional)
   grain: one row per tweet (post)
   measures: has_media_flag, num_media, char_count
   dimensions:
     dim_user (SCD 2, role-played for author_key)
     dim_date (role-played for tweet_date_key)
   degenerate: tweet_id, in_reply_to_tweet_id

fact_impressions (transactional)
   grain: one row per (user, tweet) pair, per day
   measures: impression_count
   dimensions:
     dim_user (viewer), dim_tweet, dim_date

fact_engagements (transactional)
   grain: one row per engagement event
   measures: count (always 1)
   dimensions:
     dim_user, dim_tweet, dim_engagement_type,
     dim_date

fact_follows (factless)
   grain: one row per (follower, followee) pair
   measures: none (or 1)
   dimensions:
     dim_user (role-played for follower_key, followee_key),
     dim_date
```

`dim_user` is the *conformed* dim across all four
facts. It's SCD 2 with `effective_date` and
`expiry_date`. The temporal join pattern is
explained in Lesson 22.

---

## Sample SQL queries

**DAU (users who tweeted OR engaged in the day):**

```sql
WITH active_users AS (
  SELECT user_key FROM fact_tweets
  WHERE tweet_date_key = 20240301
  UNION
  SELECT user_key FROM fact_engagements
  WHERE engagement_date_key = 20240301
)
SELECT COUNT(DISTINCT user_key) AS dau
FROM active_users;
```

**Engagement rate for a tweet:**

```sql
SELECT t.tweet_id,
       SUM(CASE WHEN e.engagement_type_key IN
                   (SELECT engagement_type_key
                    FROM dim_engagement_type
                    WHERE name IN ('like','repost','reply'))
                THEN 1 ELSE 0 END) AS engaged,
       i.impression_count AS impressions,
       1.0 * engaged / i.impression_count AS eng_rate
FROM fact_tweets t
JOIN fact_impressions i ON t.tweet_key = i.tweet_key
LEFT JOIN fact_engagements e
  ON t.tweet_key = e.tweet_key
 AND i.user_key = e.user_key
WHERE t.tweet_id = 12345
GROUP BY t.tweet_id, i.impression_count;
```

**Follower growth (new followers per day, per user):**

```sql
SELECT followee_key, follow_date_key,
       COUNT(*) AS new_followers
FROM fact_follows
WHERE follow_date_key BETWEEN 20240101 AND 20240131
GROUP BY followee_key, follow_date_key;
```

**Top tweets by engagement in a window:**

```sql
SELECT t.tweet_id, t.author_key, COUNT(*) AS eng
FROM fact_engagements e
JOIN fact_tweets t ON e.tweet_key = t.tweet_key
WHERE e.engagement_date_key BETWEEN 20240101 AND 20240131
GROUP BY t.tweet_id, t.author_key
ORDER BY eng DESC
LIMIT 10;
```

---

## Tradeoffs to call out

1. **One engagement fact vs separate facts per
   engagement type.** I picked one fact with a
   `dim_engagement_type` because the events share
   the same shape and joining the same dim across
   them is cheaper.
2. **Impressions as a daily fact vs per-event.**
   Daily grain is enough for engagement-rate
   reporting and 30x smaller.
3. **Follow as a factless fact vs a dim attribute.**
   A factless fact because the relationship has
   history (unfollows) and we want to report on
   growth, not just current state.
4. **SCD 2 on user.** Required for historical
   attribution of tweets to the user's verified
   status at the time.
5. **Tweet text as a dim, not a fact attribute.**
   Because the text is edited and we want to
   preserve the version that was visible at the
   time of an engagement.

---

## What a senior candidate does differently

- **Asks about cardinality first.** "How many
  users? How many tweets per day? How many
  impressions per tweet?" — these numbers drive
  every other decision.
- **Names the conformed dim.** "The user dim is
  shared across tweets, impressions, engagements,
  and follows. That's why SCD 2 is worth the
  cost."
- **Distinguishes "tweet" from "engagement."** A
  tweet is *content*; an engagement is an
  *event*. Putting them in the same fact
  conflates the two grains.
- **Names the freshness tradeoff.** "Operational
  dashboards need minute-level freshness;
  executive reports need daily. I'd build a
  streaming pipeline for the engagement events
  and a daily batch pipeline for the
  conformed-dim updates."

---

## How to submit

Write your solution as a single Markdown file with
embedded SQL. Aim for ~5 pages. The rubric is the
4-bucket from Module 01:

1. Clarifies the business.
2. Picks a grain.
3. Makes and defends tradeoffs.
4. Talks while drawing (i.e., the narrative is
   on-paper, not just the diagram).

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
