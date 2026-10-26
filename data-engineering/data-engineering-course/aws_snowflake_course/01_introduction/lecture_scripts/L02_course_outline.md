---
l_id: L02
title: Course Outline
duration: "7:00"
prereqs: ["L01"]
downloads: []
---

# L02 — Course Outline

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 1 — Introduction
> **Duration:** ~7:00

## Prereqs

L01 — Welcome!. This is the second of four orientation lectures.

## Lecture

In L01 I gave you the elevator pitch. In this lecture I'll walk
you through every section of the curriculum at a high level so you
can decide whether to take the course linearly or jump straight to
the topic you need.

### The section arc

The course is organized so each section builds on the previous one,
but every section is also designed to stand on its own for
reference.

| # | Section | Lectures | What you'll do |
|---|---|---|---|
| 1 | Introduction | L01–L04 | Course orientation, resources, slides |
| 2 | Getting started | L05–L14 | Free trial, UI, warehouses, scaling |
| 3 | Snowflake architecture | L15–L23 | Editions, pricing, storage cost, resource monitors |
| 4 | Loading data | L24–L32 | Roles, stages, COPY INTO, transformations |
| 5 | Copy options | L33–L40 | File formats, ON_ERROR, VALIDATION_MODE, history |
| 6 | Loading unstructured data | L41–L49 | JSON, nested data, FLATTEN, arrays |
| 7 | Performance optimization | L50–L58 | Warehouses, caching, scaling up/out |
| 8 | Loading from AWS | L59–L65 | Clustering, S3, storage integration |
| 9 | Loading from Azure | L66–L72 | Azure Blob, SAS tokens, integrations |
| 10 | Loading from GCP | L73–L78 | GCS, service accounts, integrations |
| 11 | Snowpipe | L79–L85 | Auto-ingest, cloud event notifications |
| 12 | Cortex AI & ML | L86–L99 | AI SQL, Cortex Search, Snowflake ML, Streamlit |
| 13 | Snowpipe for Azure | L100–L103 | Azure-specific pipe setup |
| 14 | Time Travel | L104–L109 | Query past states, UNDROP, retention |
| 15 | Fail Safe | L110–L111 | Snowflake's 7-day disaster recovery window |
| 16 | Types of tables | L112–L115 | Permanent / Transient / Temporary |
| 17 | Zero-Copy Cloning | L116–L121 | Clone tables, schemas, databases |
| 18 | Data Sharing | L122–L132 | Shares, secure views, reader accounts |
| 19 | Data Sampling | L133–L135 | SAMPLE / TABLESAMPLE, Bernoulli vs system |
| 20 | Extra topics | L136–L192 | Tasks, streams, MVs, masking, roles, BI, best practices |

### How to navigate the course

There are three common paths through the material:

1. **Linear (recommended for first-timers).** Sections 1–8 give you
   the full data engineer foundation; sections 9–19 deepen each
   topic; section 20 is the advanced grab-bag.
2. **Project-driven.** If you already have a specific use case (e.g.
   "load Parquet from S3 and join it with a Kafka stream"), jump
   straight to the relevant section, then come back for gaps.
3. **Reference-driven.** Use the section READMEs as a table of
   contents; each README has a "Key concepts you'll need later"
   block you can scan in 30 seconds.

### Where to spend the most time

If you only have 3 hours for the course, watch:

- **L08–L09** (Snowflake architecture — the mental model you'll use
  every day)
- **L28–L32** (the `COPY INTO` command, end to end)
- **L52–L58** (performance — warehouses, caching, scaling)

Those ~45 minutes give you 80% of the value.

## Hands-on

No lab. The "homework" is to bookmark
[`../../SYLLABUS.md`](../../SYLLABUS.md) and skim the table of
contents to plan your route.

## Quiz prep

For this lecture, focus on the **navigation** questions:

- Which section covers the `COPY INTO` command? (Section 4)
- Which section covers zero-copy cloning? (Section 17)
- Which section covers time travel and UNDROP? (Section 14)

## What's next

Next up is **L03 — How to benefit best from the course?**, where
I share the study strategies that work for this material.
