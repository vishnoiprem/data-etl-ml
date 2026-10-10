# SQL Interviews

> **11 modules · 108 lessons · 6 videos · ~34 hours**
>
> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

A focused track for the SQL portion of data engineering interviews.
The course is designed to be done start-to-finish in roughly a
month of part-time study. By the end you'll have solved 59 working
SQL problems (14 easy + 31 medium + 14 hard) with passing tests
against a real SQLite database, plus the conceptual background to
explain *why* each answer is correct.

## How the track is laid out

```
sql_interviews/
├── 01_overview/              3 lessons, concepts + history + answer format
├── 02_fast_track/            9 lessons, the syntax you must know cold
├── 03_basic_querying/        8 lessons, filtering, strings, dates, DDL/DML
├── 04_aggregations/          7 lessons, COUNT/SUM/AVG, GROUP BY, ROLLUP
├── 05_joins/                 8 lessons, INNER/LEFT/SELF/ANTI/CROSS
├── 06_window_functions/      4 lessons, ROW_NUMBER/RANK/LAG/frames
├── 07_easy_practice/         14 lessons + 14 passing tests
├── 08_medium_practice/       31 lessons + 31 passing tests
├── 09_hard_practice/         14 lessons + 14 passing tests
├── 10_query_performance/     4 lessons, EXPLAIN, indexes, joins, rewrites
├── 11_meta_screen/           6 lessons + 5 Jupyter notebooks, 2026 Meta DE CoderPad (60-min: 5 SQL + 5 Python + 6 onsite SQL)
└── exercise.md               capstone: 5 interview-style questions
```

The first six modules (M01–M06) are pure reading. They teach
concepts. The last three (M07–M09) are pure code. Each problem in
M07–M09 has a solution in `code/solutions.sql` and a test in
`tests/test_*.py` that runs the solution against a seeded SQLite
database and asserts the output.

## 4-week study plan

| Week | Focus | Modules | Hours |
|---|---|---|---|
| **1** | Foundations + Fast Track | M01 (Overview), M02 (Fast Track) | 6 |
| **2** | Core SQL skills | M03 (Basic), M04 (Aggregations), M05 (Joins) | 10 |
| **3** | Advanced + easy/medium practice | M06 (Window), M07 (Easy), first 15 of M08 (Medium) | 12 |
| **4** | Hard practice + query performance | M08 (Medium remainder), M09 (Hard), M10 (Query Performance) | 14 |

If you only have 2 weeks, skip M10 (Query Performance) and the last 7 of M09 (Hard). If you have 6 weeks, do M10 twice and redo every M09 problem until you can solve in 20 minutes.

## Running the tests

```bash
# Run all 59 practice tests
python3 -m unittest discover -s sql_interviews -p "test_*.py" -v

# Run just one module
python3 -m unittest sql_interviews.07_easy_practice.tests.test_easy -v
```

The shared `common/` library at the top of the course provides
`QueryRunner`, `Table`, and `Column` — every practice module
imports from it. The tests are deterministic; the seed data is
hand-crafted and never randomized.

## What you will be able to do

By the end of the track you will:

1. Read any SQL interview problem and pick the right pattern
   (window, CTE, anti-join, conditional aggregation).
2. Write `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, and
   `NTILE` queries on the first try.
3. Build a recursive CTE for hierarchical data (org charts,
   tree nodes, bill-of-materials).
4. Compute percentiles and medians in SQLite (with the usual
   workarounds) and explain the difference between exact and
   approximate answers.
5. Read execution plans at a high level and call out where a
   query is doing unnecessary work.
