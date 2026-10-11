# Data Modeling Interview Track

> **36 lessons · 6 videos · ~14 hours of focused practice**
>
> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion articles:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

A practical, working guide to the data modeling interview — the round
where senior data engineers are most often downleveled. Not because they
can't write a window function, but because they can't tell the story of
*why* a fact table should be at one-grain-not-another, or *why* an
SCD Type 2 dimension is the right call for a slowly changing user
attribute.

This track fixes that. Every lesson pairs a short, opinionated design
write-up with runnable SQLite code and a unit test that exercises the
schema. Read the lesson, run the code, read the test, and you'll
internalize the patterns.

---

## What's in this track

**Pattern-based.** Every data modeling question reduces to four moves:
clarify the business, pick a grain, choose fact vs dimension, decide how
things change over time. The seven modules drill each move, then layer
the optimization concerns on top.

**Working code.** The 7 star-schema lessons in Module 03 are real,
runnable SQLite schemas with sample data, not pseudo-DDL. The
dimension, fact, and performance lessons all have code that runs and
tests that pass.

**Spine: canonical questions.** The questions in
[`docs/reference/de_interview_canonical_questions.md`](../docs/reference/de_interview_canonical_questions.md)
are the source of truth. We don't invent problem statements; we work
the list.

---

## The 7 modules

| # | Module | Lessons | What you'll get out of it |
|---|---|---|---|
| [01](01_overview/) | **Overview** | 4 | A shared vocabulary: fact vs dim, grain, ER vs dimensional, the rubric. Read first. |
| [02](02_requirements/) | **Gathering Business Requirements** | 8 | The discovery questions and the requirements doc that you produce *before* drawing anything. |
| [03](03_high_level_diagrams/) | **High-Level Model Diagrams** | 8 | ER → star schema. Five working star schemas (e-commerce, ride-sharing, Instagram, support, Spotify). |
| [04](04_dimension_design/) | **Dimension Design** | 3 | SCD 1/2/3, conformed dimensions, role-playing dimensions, junk & degenerate dims. |
| [05](05_fact_modeling/) | **Fact Data Modeling** | 4 | Transactional, periodic snapshot, accumulating snapshot, and factless fact tables. |
| [06](06_performance/) | **Performance Optimization** | 3 | Indexing, partitioning, materialized views — with benchmarks. |
| [07](07_mock_interviews/) | **Mock Interviews & Practice** | 6 | Three full 30-min mock transcripts (fitness, Uber, Amazon) plus three practice problems with full solutions. |

---

## How to use this track

1. **Read 01_overview first.** The vocabulary in Module 01 is reused in
   every later module. Skim it once; refer back to it forever.
2. **Treat the requirements doc as a deliverable.** Module 02 produces a
   `requirements_doc.py` helper. The actual output of your interview is
   *the document*, not the diagram. Many candidates skip this and lose
   easy points.
3. **Run every code module.** Each is a working SQLite schema. Open the
   Python file, copy the `if __name__ == "__main__"` block, and watch
   it execute. Reading alone is not enough.
4. **Read the tests.** The tests in `tests/test_*.py` document the
   *invariants* of each schema. If a test surprises you, that's a gap
   in your mental model.
5. **Do the practice problems in Module 07 cold.** Set a timer for 30
   minutes. Draw the diagram on paper. Then read the solution and the
   mock interview to see how a senior candidate narrates the same
   work.

---

## What "data modeling" actually tests

Interviewers want to know four things:

1. **Can you clarify the business first?** The candidate who asks
   "what does 'engagement' mean — daily, weekly, monthly?" before
   drawing a star schema immediately outranks the candidate who draws
   five tables and hopes for the best.
2. **Can you pick a grain?** "One row per workout session" or "one row
   per user-day"? The grain is the single most important decision in a
   dimensional model. Get it right and the rest follows.
3. **Can you make and defend tradeoffs?** Star vs snowflake. SCD 1 vs
   2 vs 3. Snapshot vs transactional fact. Every choice has a cost.
4. **Can you talk while you draw?** The whiteboard round is *narrated*.
   The candidate who says "I'm picking Type 2 here because the user
   fitness level changes over time and we want historical attribution"
   scores higher than the candidate who silently draws a box.

---

## Companion tracks

This track assumes you can write SQL. The
[`sql_interviews/`](../sql_interviews/) track covers window functions,
CTEs, and the rest of the SQL toolkit. The
[`data_pipeline_design/`](../data_pipeline_design/) track covers how
the schemas you design here actually get loaded, transformed, and
served.

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
