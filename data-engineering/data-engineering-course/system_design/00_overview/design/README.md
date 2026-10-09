# Module 00 — System Design Interview Overview

> **Lesson 1 of 71 — Overview track** · 5 lessons · 1 video · ~30 min

The System Design interview is not a trivia test. It is a **structured
conversation** that probes how you think about real engineering tradeoffs
under ambiguity. This module teaches you the playbook every interviewer
is looking for.

---

## 1. What "System Design" actually tests

Interviewers want to know four things, in order of importance:

1. **Can you clarify a vague problem?** Real systems start ambiguous.
   Good candidates ask questions before drawing boxes.
2. **Can you reason about scale?** How much data, what QPS, how that
   changes the design.
3. **Can you make and defend tradeoffs?** Every choice has a cost.
   Articulate it.
4. **Can you drive a design deep on a critical area?** Don't go wide;
   go deep on the hot path.

There are no right answers. There are well-reasoned answers.

---

## 2. The 4-step framework

```
┌──────────────────────────────────────────────────────┐
│ Step 1: Clarify requirements (5 min)                 │
│   - Functional: features, actors, use cases          │
│   - Non-functional: scale, latency, consistency      │
│                                                      │
│ Step 2: Back-of-envelope estimation (5 min)          │
│   - QPS, storage, bandwidth                          │
│   - Pick numbers; back-of-envelope is enough         │
│                                                      │
│ Step 3: High-level design (10 min)                   │
│   - Boxes and arrows: client, app, cache, DB         │
│   - Identify the "hot path"                          │
│                                                      │
│ Step 4: Deep dive on hot path (15-20 min)            │
│   - API, data model, algorithm, failure modes        │
│   - This is where senior candidates shine            │
└──────────────────────────────────────────────────────┘
```

---

## 3. The must-know patterns

These 8 patterns appear in 80%+ of system design questions. Every module
in this course is a worked example of one or more of them:

| # | Pattern | Modules that demonstrate it |
|---|---|---|
| 1 | **Caching** | URL Shortener, Typeahead, Instagram, YouTube, Rate Limiter |
| 2 | **Sharding / partitioning** | KV Store, S3 Storage, Message Queue, Distributed LRU |
| 3 | **Replication** | KV Store, Message Queue, Distributed Storage |
| 4 | **Consistent hashing** | Distributed LRU, KV Store, Dropbox |
| 5 | **Pub/Sub / message queue** | Message Queue, Webhooks, Async Jobs, Notification fanout |
| 6 | **Fanout (write vs read)** | Twitter, Instagram, Newsfeed, Slack |
| 7 | **CDN + edge cache** | YouTube, Netflix, TikTok, Twitch |
| 8 | **Async processing / queues** | Web Crawler, Job Scheduler, Export, Doc Processing |

Other patterns you'll meet: **rate limiting**, **idempotency**,
**exactly-once / at-least-once**, **leader election**, **bloom filters**,
**CRDTs**, **vector search**, **batching**, **circuit breaker**,
**two-phase commit / saga**, **RAG**, **agentic tool use**.

---

## 4. The whiteboard rubric

Interviewers grade you on a 4-bucket rubric. Know what each bucket means:

| Bucket | What they're looking for |
|---|---|
| **Problem framing** | Did you ask clarifying questions? Did you identify the right non-functionals? |
| **Estimation** | QPS, storage, bandwidth. Are your numbers in the right ballpark? |
| **High-level architecture** | Are the components named correctly? Is the data flow sensible? |
| **Hot-path deep dive** | Did you go deep on the 1 thing that matters? Did you discuss failure modes? |

A common failure mode: spending 25 min on the high-level diagram and 5
min on the deep dive. **Invert it.** The deep dive is what separates
senior from junior.

---

## 5. How to use a whiteboard (or Excalidraw)

Tips that have saved candidates repeatedly:

- **Start with the user.** Draw a stick figure on the left. Then boxes
  on the right. Never start with a database in the middle.
- **Label every arrow.** "HTTPS", "gRPC", "async", "batch".
- **Use the corners.** "CDN", "Object store", "Search index" — these
  are the *integration points* interviewers want to see you bring up.
- **Number your boxes** so you can refer back: "DB1", "Cache2".
- **Cross things out instead of erasing.** Erasing makes the interviewer
  lose track. Crossing out is honest iteration.

---

## 6. How this course is organized

71 lessons, 11 modules, ~18 hours of work.

```
00 Overview  (this module)  ← 5 lessons
01 Read-Heavy Systems        ← 6 lessons
02 Event-Driven Systems      ← 3 lessons
03 Async Jobs & Workers      ← 3 lessons
04 Distributed Storage       ← 5 lessons
05 Transactional Systems     ← 3 lessons
06 Batch Processing          ← 5 lessons
07 Real-Time & Collaborative ← 5 lessons
08 Media Streaming           ← 4 lessons
09 Agentic AI                ← 6 lessons
10 Appendix (concepts)       ← 18 lessons
```

Each module:

- Has a `design/README.md` that **is** the interview answer.
- Has a `code/` directory with a **working** Python implementation.
- Has `tests/` you can actually run.

---

## 7. How to use this course

- **First pass (1× speed)**: read the design doc, run the code, read
  the code. Move on.
- **Second pass (2× speed)**: re-read the design doc, this time
  out loud, as if the interviewer just asked "design X". Pause at every
  diagram and explain it.
- **Third pass (3× speed)**: close the doc, open a blank editor, and
  re-derive the design from the requirements. Compare.

By the third pass, you'll be able to produce each design in 30-45 min
on a whiteboard. That's the target.

---

## 8. Code map

This module has no service. It's a meta-lesson. But the rest of the
course does. Start with the **Read-Heavy** track — it's the
foundation everything else builds on.
