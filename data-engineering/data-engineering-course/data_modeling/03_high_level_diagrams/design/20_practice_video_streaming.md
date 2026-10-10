# Lesson 20 — Practice: Video Streaming Service

> **What you'll learn:** the streaming star, with the
> content/creator/series hierarchy, a device-type dim, and
> watch-time as the headline measure. By the end of this
> lesson you'll be able to draw a video-streaming
> warehouse for YouTube, Netflix, Disney+, Twitch, or any
> "play" event product.

---

## Why this lesson

Video streaming is the prompt you get at Netflix, YouTube,
Disney+, HBO Max, Twitch, and any company that serves
long-form video to consumer devices. The schema looks
like Spotify on the surface — there's a play event, a
content hierarchy, a device type, a skip-or-completion
signal — but the *framing* is different: instead of
asking "skip rate by genre," you're asking "completion
rate by content by device by recommender," and instead
of "release-decade" you're asking "content freshness"
(how recently was this released). The trick is the
*content/creator/series hierarchy* (video replaces
song/artist/album) and the *recommender* dimension —
Netflix's home page and YouTube's sidebar are
recommenders, and the analyst needs to know which one
served the video. This lesson teaches the streaming
star with that broader content+recommender framing.

---

## The prompt

> "Design a data warehouse for a video streaming service
> (think YouTube / Netflix / Disney+) so the analytics
> team can answer questions about watch time, completion
> rate, content performance, and recommender
> effectiveness."

This is the canonical streaming question. The trick is
the *content/creator/series hierarchy* — three related
dimensions that have to be modeled carefully — and the
*recommender dim* that records which surface served
the video (home, search, "because you watched," etc.).

---

## The star schema

```
                ┌──────────────┐
                │ dim_users    │
                │ (SCD 2)      │
                └──────┬───────┘
                       │ user_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ dim_date │◄───┤ fact_streams ├───►│ dim_songs    │
└──────────┘    │              │    └──────┬───────┘
                │ measures:    │           │
                │  ms_played   │           │ artist_key
                │  was_skipped │           ▼
                └──────┬───────┘    ┌──────────────┐
                       │            │ dim_artists  │
                       │            └──────────────┘
                       │
                ┌──────┴───────┐    ┌──────────────┐
                │dim_device_   │    │ dim_albums   │
                │   type       │    │              │
                └──────────────┘    └──────────────┘
```

Seven tables. One fact, six dimensions. The fact has
*four* foreign keys to dimensions (user, song, device_type,
date), plus two denormalized FKs (artist_key, album_key) for
query speed.

---

## The grain: one row per stream

A "stream" is a single play event. The grain is **one row per
(user, song, minute) listen**. A user listening to a song for
5 minutes produces 1 row in this schema (with
`ms_played = 300000`), or 5 rows (one per minute) if you
model "every minute of listening" as a separate event.

The choice depends on the question:

- "How many songs were streamed today?" — both work, but
  one-row-per-stream is simpler.
- "How much time did users spend listening today?" —
  one-row-per-stream with `ms_played` is the right shape.
- "How long did the average user listen to song X?" —
  one-row-per-stream is fine.
- "What was the drop-off curve of song X?" — needs
  one-row-per-(user, song, second) or
  one-row-per-(user, song, listening_position).

The first three are the common ones. We go with
one-row-per-stream.

---

## The measures

| Measure | Type | Notes |
|---|---|---|
| `ms_played` | INT | How long the user actually listened. |
| `was_skipped` | INT | 0 / 1 — did the user skip before 30s? |

`ms_played` is the headline measure. It tells you "how much
listening" and "drop-off" at the row level. It's semi-additive
(can be summed per user, per song, per day, but the meaning
of "sum of ms_played" is "total listening time").

`was_skipped` is a boolean measure. It's *flag* — used for
the skip-rate calculation: `SUM(was_skipped) / COUNT(*)`.

---

## The dimensions

### `dim_users` (SCD Type 2)

User attributes change over time. Plan (free, premium,
family) is the most important — skip rate differs hugely
between free (ad-supported, more skips) and premium. SCD 2
so we can attribute historical streams to the right plan.

### `dim_songs`

A song has a title, duration, and `release_decade` (a
derived attribute used for "skip rate by decade"
queries). SCD 1 — songs don't change much after release.

### `dim_artists`

An artist is a small dim with name and genre. SCD 1.

### `dim_albums`

An album has a title, release_year, and a FK to the artist.
SCD 1.

### The song-artist-album hierarchy

A song belongs to one album; an album belongs to one
artist. The hierarchy is:

```
Artist 1──* Album 1──* Song
```

In the star, this is implemented as three flat dimensions
(`dim_songs`, `dim_albums`, `dim_artists`) joined by FKs
on each dim. The fact then has *denormalized* FKs to all
three (so you can query "skip rate by artist" without
joining through `dim_songs` → `dim_albums` → `dim_artists`).

The `dim_songs.artist_key` and `dim_songs.album_key` are
snowflaking-ish (you could go through them), but the
`fact_streams.artist_key` and `fact_streams.album_key` are
denormalized. The trade-off is query speed vs redundancy.

In a 30-minute interview, the right call is to denormalize
the artist_key and album_key onto the fact. The redundancy
is small (one INT per fact row), and the query speed gain
is large (no 3-hop join for "skip rate by artist").

### `dim_device_type`

A tiny dim with 5 rows: ios, android, web, speaker, tv.
We could leave this as a TEXT column on the fact, but a
dim lets us attach attributes (`is_mobile`, `is_paid_tier`)
later.

### `dim_date`

The standard conformed dim.

---

## Why denormalize the artist and album onto the fact

Three options for "skip rate by genre":

1. **Snowflake:** `fact_streams → dim_songs → dim_albums →
   dim_artists`. Three joins, but no redundancy.
2. **Star with bridge:** `fact_streams → dim_songs` (with
   `dim_songs.artist_key`) and `dim_artists` joined to
   `dim_songs`. Two hops.
3. **Denormalized star:** `fact_streams` has both
   `song_key` and `artist_key` directly. One hop.

Option 3 is the right call for the same reason e-commerce
denormalizes: hot path, fast queries, small redundancy.

If the question is "skip rate by *decade*", the same logic
applies — denormalize `release_decade` onto the fact.

---

## Tradeoffs to call out

1. **Why denormalize artist_key and album_key onto the
   fact?** "The most common query is 'skip rate by genre /
   artist / decade.' A 3-hop join is too slow. The
   redundancy is one INT per row, which is cheap."
2. **Why is `dim_users` SCD 2?** "User plan (free vs
   premium) changes over time and skip rate differs
   hugely. We need historical attribution."
3. **Why is `dim_songs` SCD 1?** "Songs don't change much
   after release. The only attribute that could change
   is the `release_decade` (if someone re-releases a song),
   and that's rare."
4. **Why a `dim_device_type` and not a TEXT column?**
   "A dim lets us attach attributes (e.g.,
   `is_mobile`, `is_paid_tier`) that the analyst can use
   for filtering without re-typing the values."
5. **Why is `release_decade` on the dim, not the fact?**
   "It's a *characteristic of the song*, not of the
   stream. The decade doesn't change per stream."

---

## The DDL — running it

The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_spotify_schema(q)` (the function backs the
video-streaming lesson; the schema is the same
streaming shape). Run the demo:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

Output (truncated):

```
[spotify]  tables: ['dim_users', 'dim_artists', 'dim_albums',
                    'dim_songs', 'dim_device_type', 'dim_date',
                    'fact_streams']
   fact_streams sample row: {
     'stream_key': 1, 'user_key': 1, 'song_key': 1,
     'artist_key': 1, 'album_key': 1, 'device_type_key': 1,
     'date_key': 20240501, 'ms_played': 215000, 'was_skipped': 0
   }
```

---

## Sample queries

### Skip rate by genre

```sql
SELECT
    a.genre,
    SUM(f.was_skipped) AS skipped,
    COUNT(*) AS total,
    ROUND(1.0 * SUM(f.was_skipped) / COUNT(*), 3) AS skip_rate
FROM fact_streams f
JOIN dim_artists a ON f.artist_key = a.artist_key
GROUP BY a.genre
ORDER BY skip_rate DESC;
```

### Listening time by release decade and plan

```sql
SELECT
    s.release_decade,
    u.plan,
    SUM(f.ms_played) / 1000.0 AS total_seconds
FROM fact_streams f
JOIN dim_songs s ON f.song_key = s.song_key
JOIN dim_users u ON f.user_key = u.user_key
WHERE u.is_current = 1
GROUP BY s.release_decade, u.plan
ORDER BY s.release_decade, u.plan;
```

### Skip rate by device

```sql
SELECT
    d.device_type,
    ROUND(1.0 * SUM(f.was_skipped) / COUNT(*), 3) AS skip_rate
FROM fact_streams f
JOIN dim_device_type d ON f.device_type_key = d.device_type_key
GROUP BY d.device_type
ORDER BY skip_rate DESC;
```

---

## Try it

Open
[`code/star_schemas.py`](../code/star_schemas.py) and read
`build_spotify_schema` (the function backs the
video-streaming lesson). Then:

1. State the grain out loud: "one row per watch
   session" (or per stream — the schema is the same
   shape).
2. Identify which dimensions are denormalized onto
   the fact (creator_key, series_key) and explain
   why — every dashboard joins all three content
   levels, so denormalizing the FKs avoids a 3-hop
   join.
3. Run the test and verify the 10 sample streams
   aggregate to 2 decades of skip data.

For the video-streaming framing, the questions the
analytics team asks are:

- **Watch time:** "average watch minutes per
  session per device per content type."
- **Completion rate:** "% of session that reaches
  95% of the video, by content length and
  recommender surface."
- **Content performance:** "top creators by total
  watch hours, top series by completion rate."
- **Recommender effectiveness:** "which surface
  (home, search, 'because you watched') produces
  the highest completion rate."

The recommender surface becomes a `dim_recommender`
in the production schema — the same star, with one
more dim.

---

## In the interview, you would say...

> "Video streaming is one event-grain fact, with the
> content/creator/series hierarchy denormalized onto
> the fact (creator_key, series_key) for query speed
> — every dashboard joins all three, so a 3-hop join
> would be too slow. The headline measure is
> `ms_played` (or `seconds_watched`); the headline
> ratio is completion rate, computed as
> `SUM(was_completed) / COUNT(*)`. `dim_users` is SCD
> 2 (subscription tier — free vs premium — drives
> completion rate). The recommender surface
> (home, search, "because you watched") is its own
> dim; a `dim_recommender` with 5–10 rows makes
> 'which surface drives the best completion' a
> one-line query."

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
