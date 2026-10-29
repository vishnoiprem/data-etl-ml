# Try Experiments — content + code for "Read-Heavy Systems"

> **One system-design topic, shipped in three formats: a
> long-form essay, a Twitter/X thread, and a LinkedIn
> carousel, plus a worked code example.** Same content,
> different surfaces. The point is to test which surface
> gets the most engagement for the same underlying idea.

This directory is a small experiment in content-format
multiplication. The design problem is "read-heavy
systems" — the pattern that powers Instagram's feed,
Amazon's product page, Netflix's catalog. The same
explanation is told in five forms, each tuned to the
medium.

---

## What's in this directory

| File | What it is |
|------|------------|
| `read-heavy-system.md` | The long-form essay (the source of truth) |
| `read-heavy-systems-principal-engineer-guide.md` | The same content, rewritten for a Principal-Engineer audience (deeper, more references, more opinion) |
| `read-heavy-systems-part2-sizing-math-cost-tradeoffs.md` | The follow-up: the sizing math, the cost tradeoffs, the operational reality of running a read-heavy system at scale |
| `twitter-thread-read-heavy-systems.md` | A 14-tweet thread. Each tweet ≤ 280 chars. Post as replies to tweet 1 |
| `linkedin-carousel-read-heavy-systems.md` | A 14-slide LinkedIn carousel. 1080×1350 (4:5 portrait). One idea per slide |
| `02_news_feed_engagement_original.py` | The worked example: a data-model design for a Facebook-style News Feed engagement analytics fact table |

The five markdown files are the same content in five
voices. The Python file is the "show me the code" half
of the experiment.

---

## The design problem (one paragraph)

A viral post may be written once and read millions of
times. How do systems like Instagram or Amazon serve
that traffic without overwhelming the database? The
answer is read-heavy scaling: compute an answer once,
then serve copies instead of rebuilding it for every
reader.

We can cache popular data, spread reads across
replicas, and precompute expensive results. Each
technique improves throughput by storing another copy
of the data, which means accepting some amount of
staleness. The design work is deciding where stale
data is acceptable and how each copy gets refreshed.

---

## The five formats — when to use which

| Format | Where it lands | Best for |
|--------|----------------|----------|
| Long-form essay | Personal blog, Medium, dev.to | SEO, deep reading, citations |
| Principal-Engineer guide | Internal newsletter, conference talk prep | Authority signal, deeper technical audience |
| Sizing math follow-up | Personal blog (Part 2), conference talk | Operational audience, the "is it worth it" question |
| Twitter/X thread | Twitter / X | Top-of-funnel, virality, drive traffic to long-form |
| LinkedIn carousel | LinkedIn | B2B audience, save / share, hiring-manager signal |

The experiment is whether shipping the same idea in
five surfaces gets more reach than shipping it in
one. The honest answer so far: the long-form essay
and the LinkedIn carousel get the most engagement;
the Twitter thread gets the most impressions but
the least click-through. The PE guide gets the
highest-quality DMs.

---

## The code example

`02_news_feed_engagement_original.py` is a worked
data-model design for the Facebook News Feed
engagement analytics fact table. The interesting
bits:

- **Three events** on each story shown in feed:
  impression (render), reaction (like / love / ...),
  share. Each is its own grain.
- **A periodic snapshot fact** (`feed_engagement_daily`)
  for reach vs interaction metrics.
- **Conformed dimensions** that match the rest of the
  Meta-style warehouse: `dim_post`, `dim_user`,
  `dim_date`, `dim_time`, `dim_device`, `dim_placement`,
  `dim_share_destination`, `dim_reaction_type`.

The code is reference-quality but not executable —
it's the data-model design, not the SQL pipeline.
For the pipeline pattern, see
[`../../data-engineering/activity-volume-olap/`](../../data-engineering/activity-volume-olap/).

---

## How to use this directory

- **Pick the format that matches your audience.** The
  same idea in five voices means you don't have to
  rewrite from scratch when you go from a long-form
  blog to a Twitter thread.
- **Use the long-form essay as the source of truth.**
  The other formats are derived from it; if you change
  a fact, change it in the essay first, then propagate.
- **Use the code example as the interview talking
  point.** The data-model design is what you'd
  whiteboard in a Staff system-design loop. The
  thread and the carousel are the marketing; the
  schema is the substance.

---

## What this is NOT

- **Not a production system design.** The essay and
  the code are the *shape* of a read-heavy system.
  The actual production system has retry logic,
  backpressure handling, cache stampede prevention,
  and a cost model that varies per cloud. Those live
  in [`../../data-engineering/keystone-iceberg-ops/`](../../data-engineering/keystone-iceberg-ops/)
  and [`../../data-engineering/financial-reporting-platform/`](../../data-engineering/financial-reporting-platform/).
- **Not a content-marketing play.** This is an
  experiment, not a content calendar. The other
  content lives in [`../../../medium/`](../../../medium/).
- **Not a finished experiment.** The five formats
  exist; the engagement numbers are still being
  collected. When the data is in, it goes in the
  essay as an addendum.

---

## Related directories

- [`../../../medium/`](../../../medium/) — the broader
  long-form writing (40+ articles, interview prep,
  design deep-dives).
- [`../../data-engineering/activity-volume-olap/`](../../data-engineering/activity-volume-olap/) —
  the OLAP-on-clickstream reference that the
  `02_news_feed_engagement_original.py` schema is
  designed for.
- [`../../ai-engineering/`](../../ai-engineering/) —
  the parent AI-engineering directory. 40 projects;
  this one is the "show me how you'd talk about
  systems in public" example.
