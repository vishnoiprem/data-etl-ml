# Module 04 — System Design Interviews (cross-link)

> **0 lessons · Cross-link to `../system_design/`**

> **Author:** [Prem Vishnoi](https://medium.com/@premvishnoi) · <pvishnoi@avilx.com>

System Design is the largest single track in the course, and
it has its own complete curriculum: **71 lessons, 32
videos, ~18 hours of hands-on work**, organized into 11
modules covering every common system design problem an SA
candidate is likely to face.

This module is the **cross-link**. There are no new lessons
in `solutions_architect/04_system_design_crossref/`. The
content already exists, is complete, and is the right depth
for SA interviews. Use it.

---

## What the system design track covers

| # | Module | What it covers | SA relevance |
|---|---|---|---|
| [00](../system_design/00_overview/) | **Overview** | Interview framework, the 8 must-know patterns, whiteboard rubric | **Critical.** Read this first. |
| [01](../system_design/01_url_shortener/) | **Read-Heavy Systems** | URL Shortener, Typeahead, Instagram, Twitter, Newsfeed, YouTube/Netflix, Reddit | **High.** Read-heavy patterns are common in SA interviews. |
| 02 | **Event-Driven Systems** | Distributed Message Queue, Webhook Delivery, Uber Eats | **High.** Uber Eats is a worked example. |
| 03 | **Async Jobs & Workers** | Web Crawler, Job Scheduler, User Data Export | Medium. Useful for async patterns. |
| 04 | **Distributed Storage** | Key-Value Store, Rate Limiter, Distributed LRU, Dropbox, S3 Storage | **High.** Storage patterns are tested in SA interviews. |
| 05 | **Transactional Systems** | Ticketmaster, Hotel Booking, Parking Garage | **High.** Transactional patterns are tested. |
| 06 | **Batch Processing** | Metrics & Logging, APM, Doc Processing, Zillow, Weather App | **High.** Batch processing is the bread-and-butter of data SA roles. |
| 07 | **Real-Time & Collaborative** | Messenger, WhatsApp, Chess.com, Slack, Google Docs | Medium. Real-time is tested for streaming SA roles. |
| 08 | **Media Streaming** | YouTube, Netflix, TikTok, Twitch | Medium. Specialized for media SA roles. |
| 09 | **Agentic AI** | AI Support, ChatGPT, File Uploader, LLM Batching, Claude Code, Voice AI | **High.** AI workloads are increasingly tested. |
| [10](../system_design/99_appendix/) | **Appendix: Concepts** | Glossary, blogs, caching, CDN, protocols, APIs, LB, CAP, SQL vs NoSQL, sharding, replication, consistent hashing, async, encryption, auth, cloud, availability, reliability | **Critical.** The 18-concept appendix is the *reference* you'll use in every interview. |

**Total: 71 lessons.**

---

## How to use the system design track from this SA track

For an SA interview at AWS, GCP, Azure, Snowflake,
Databricks, Confluent, or similar:

### Step 1: Read the Overview (Module 00)

Start with `../system_design/00_overview/`. This is the
*framework* — the 8 must-know patterns, the whiteboard
rubric, the 4-step process from Module 03 Lesson 10 of
this track. Read this first; everything else builds on it.

### Step 2: Pick 3-5 system design problems

Pick 3-5 problems based on the SA role you're targeting:

- **Data-focused SA** (Snowflake, Databricks, Confluent,
  AWS data specialty) → Module 06 (Batch Processing)
  and Module 02 (Event-Driven Systems).
- **Real-time / streaming SA** → Module 07 (Real-Time)
  and Module 02 (Event-Driven).
- **AI / ML SA** → Module 09 (Agentic AI).
- **Cloud-platform SA** (AWS, GCP, Azure) → Modules 04
  (Distributed Storage), 05 (Transactional), and the
  Appendix (Concepts).

For each, work through the *design doc* (`design/README.md`),
read the *code* (`code/service.py` + `code/app.py`), and
run the *tests* (`tests/`). The hands-on practice is what
builds the muscle memory.

### Step 3: Skim the Appendix (Module 10)

The 18-concept Appendix is the *reference*. You don't
read it cover-to-cover; you skim it once, then refer
back to it as needed. Each concept has a 1-page summary
and a worked example.

### Step 4: Practice with a friend

Pick 2-3 problems from the modules above and run the
whiteboard demo from Module 03 Lesson 10. Practice the
4-step process:

1. Clarify (5-7 min).
2. Sketch (10-15 min).
3. Defend (15-20 min).
4. Adapt (5-10 min).

Run 3 different problems with 3 different friends. By
the 3rd, you'll have the 4-step process in muscle
memory. That's the system design round of the interview.

---

## What this track adds on top of `../system_design/`

This SA track adds 3 things on top of the system design
content:

1. **The customer-first framing.** Module 02 of this
   track covers the customer-interaction rounds that
   *precede* the system design round. The system design
   round is more likely to land when the customer
   interaction went well.
2. **The tradeoff frameworks.** Module 03 Lesson 06 of
   this track covers the latency-vs-cost-vs-consistency
   tradeoff in a way that's specific to the SA's
   "defend against a customer" interview format.
3. **The 30-second decision tree.** Module 03 Lesson 07
   of this track covers the decision tree for *quick*
   service choices during a system design round. The
   `../system_design/` content is the deep dive; the
   decision tree is the in-the-moment reference.

The 3 additions are the SA-specific layer on top of
the system design foundation. Use both.

---

## Where to go next

After working through `../system_design/`:

- **Module 05** of this track — Behavioral Interviews
  for SAs. The behavioral round is the second core SA
  round after customer interaction.
- **Module 06** of this track — Interview Tips &
  Frameworks. The 4 C's, the PREP framework, the 24-hour
  checklist.
- **`../behavioral_interviews/`** — The full behavioral
  track. 31 lessons, 19 videos, ~12 hours. The behavioral
  track is calibrated for *engineering* behavioral
  interviews; Module 05 of this track is calibrated for
  *SA* behavioral interviews. Use both.
