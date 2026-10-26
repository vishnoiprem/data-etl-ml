# Module 07 — Mock Interviews & Practice

> **7 lessons · 7 videos · ~10.5 hours**

The capstone. Seven full 30-minute mock interviews with
transcripts, architecture diagrams, and post-interview
analysis. The lessons are written as the candidate is talking —
you should be able to read them aloud and feel like you're in
the room.

Lessons 28-30 are the original 3 mocks (high-volume events,
document processing, CDC for banking) — solid for L4 / L5
candidates. Lessons 31-34 are 4 advanced mocks (feature
stores, multi-tenant analytics, data observability, real-time
ad dedup) that target senior+ / L6 candidates and the
harder "open-ended architecture" rounds at FAANG, ad-tech,
and ML-platform companies. If you're interviewing for a Staff
or Principal role, start at 31.

Author: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**

---

## Lessons

| # | Mock interview | What you'll learn |
|---|---|---|
| 28 | [Design Netflix's Clickstream Pipeline](design/28_mock_netflix_clickstream.md) | High-volume event ingestion, real-time + batch. |
| 29 | [Design a Document Processing Pipeline](design/29_mock_document_processing.md) | OCR, parsing, enrichment, search indexing. |
| 30 | [Design a CDC Pipeline for a Banking System](design/30_mock_banking_cdc.md) | CDC, exactly-once, schema evolution, regulatory. |
| 31 | [Design a Feature Store for an ML Platform](design/31_mock_feature_store.md) | Training/serving skew, point-in-time joins, feature versioning. |
| 32 | [Design a Multi-Tenant SaaS Analytics Platform](design/32_mock_multi_tenant_analytics.md) | Row-level security, query routing, noisy neighbors, cost attribution. |
| 33 | [Design a Data Observability / Monitoring Platform](design/33_mock_data_observability.md) | The 5 detection layers; alert fatigue; the on-call burden. |
| 34 | [Design a Real-Time Ad Impression Dedup Pipeline](design/34_mock_realtime_streaming.md) | Dedup at scale, late events, exactly-once at 100K events/sec. |

---

## Code

- [`code/full_solutions.py`](code/full_solutions.py) — three
  end-to-end pipeline implementations in a single file,
  building on the abstractions from earlier modules.
- [`tests/test_solutions.py`](tests/test_solutions.py) — 10
  unit tests verifying the three solutions run.

---

## How to use these lessons

Each lesson is a full mock interview:

1. **Setup** — the question, the company, the level.
2. **Transcript** — what the candidate says, with whiteboard
   annotations.
3. **Architecture diagram** — the boxes and arrows drawn on
   the whiteboard.
4. **Post-interview analysis** — what was good, what was
   missing, what to add.

Read the transcript *aloud*. Compare to your own answer to
the same question. The transcripts are 1500+ words each;
that's the depth you need on interview day.
