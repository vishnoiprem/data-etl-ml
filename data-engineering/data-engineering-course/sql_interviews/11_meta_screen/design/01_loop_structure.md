# 01 — The 60-Minute CoderPad Format

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The Meta Data Engineer technical screen, as of 2026:

```
0:00-0:05   Intros + confirm SQL/Python preference
0:05-0:30   5 SQL problems (Presto/Spark dialect; SQLite-compatible here)
0:30-0:55   5 Python problems (pandas, dict, string — NOT DSA)
0:55-1:00   Wrap-up
```

**Pass bar**: 3 of 5 in each half. **No partial credit.**
You'll get a real CoderPad with a real test-case suite
running against your code.

## What the interviewer is grading (Meta 2026)

From the [Aced.io 2026 Meta DE guide](https://www.aced.io/guides/meta-data-engineer-interview)
and [Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer):

- **Speed with precision.** 5 problems in 25 minutes is 5
  minutes per problem. You don't have time to think for
  2 minutes and code for 3. You think while you type.
- **Narrating in real time.** The interviewer hears your
  inner monologue. "I'm going to use a window function
  here, partition by user_id, order by event_ts" — that
  narration is half the signal.
- **Asking clarifiers.** "Do you want distinct users or
  total events?" is a 10-second question that doubles
  your chance of getting the right answer.
- **Recovering on failed test cases.** You'll get a
  red-light/red-X 30% of the time. The right move is
  to debug out loud, not to silently rewrite.
- **Switching between SQL and Python fluidly.** The two
  halves test different skills. The transition is a
  signal too.

## The 4 things that fail candidates

1. **Treating Python as DSA.** FizzBuzz + parens-with-wildcards
   is the *Google* phone screen. Meta's Python is
   *pandas* — `quantile`, `groupby`, vectorized boolean
   indexing. If you write a loop on a million-row DataFrame,
   the interviewer interrupts.
2. **Top-N after filter vs. before filter.** A classic
   5-minute SQL bug. The right answer is *filter first,
   then window* — and the right answer is *named* in your
   narration, not just done in code.
3. **No sessionization pattern.** "Find users with 3+
   sessions" is the Meta signature question. The
   30-minute-inactivity-gap pattern is in `design/05_*.md`.
   If you don't have it cold, you fail.
4. **Not narrating the *scale* trade-off.** "If this table
   were 10x bigger, what would you do?" — the question
   comes at minute 50. If your answer is "the same
   thing," you don't get the L5 signal.

## The 5+5 problem set in this module

The 5 SQL + 5 Python problems in `code/meta_screen_sql.sql`
and `code/meta_screen_python.py` are calibrated to the
2026 format. They are:

| # | SQL problem | Pattern tested |
|---|---|---|
| 1 | 7-day rolling retention by country | Window function + cohort |
| 2 | Peak-engagement-in-first-hour | Time-series + percentile |
| 3 | Top-N posts per page (with threshold) | Top-N-per-group after filter |
| 4 | Sessionize events (30-min gap) | Sessionization pattern |
| 5 | Gaps-and-islands (3+ consecutive days) | Gaps-and-islands |

| # | Python problem | Pattern tested |
|---|---|---|
| 1 | Top 5 pages by statistically-significant upward 30-day impression trend | Pandas groupby + boolean masking + vectorized |
| 2 | Second-highest salary per department | Dict + groupby, no DataFrame |
| 3 | Read CSV, handle exception, summarize by category | File I/O + exception handling |
| 4 | Find users with 3+ calls in the last week from a stream | Streaming / sliding window |
| 5 | Compute 15-min tumbling-window counts from a ride-request stream | Tumbling window |

The 6 onsite-flavored SQL problems in `code/meta_onsite_sql.sql`
are deeper (multiple CTEs, recursive window functions, time-travel
on a fact table). They show up in the 60-min onsite SQL round,
not the 60-min screen, but the patterns are the same.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
