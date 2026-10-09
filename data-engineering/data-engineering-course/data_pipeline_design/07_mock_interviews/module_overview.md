# Module 07 — Mock Interviews & Practice

> **3 lessons · 3 videos · ~4.5 hours**

The capstone. Three full 30-minute mock interviews with
transcripts, architecture diagrams, and post-interview
analysis. The lessons are written as the candidate is talking —
you should be able to read them aloud and feel like you're in
the room.

Author: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**

---

## Lessons

| # | Mock interview | What you'll learn |
|---|---|---|
| 28 | [Design Netflix's Clickstream Pipeline](design/28_mock_netflix_clickstream.md) | High-volume event ingestion, real-time + batch. |
| 29 | [Design a Document Processing Pipeline](design/29_mock_document_processing.md) | OCR, parsing, enrichment, search indexing. |
| 30 | [Design a CDC Pipeline for a Banking System](design/30_mock_banking_cdc.md) | CDC, exactly-once, schema evolution, regulatory. |

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
