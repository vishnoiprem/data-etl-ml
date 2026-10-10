# Module 11 — Meta Data Engineer Technical Screen (2026 Format)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The 60-minute CoderPad screen that Meta's DE loop opens with.
**5 SQL + 5 Python. Pass bar 3 of 5 in each half. No DSA.**

This is the *one* screen that 80% of Meta DE candidates fail.
The shape is wrong for most: Meta's Python is **pandas / dict / string
handling**, not algorithms. The SQL is **funnel / cohort / sessionization
on social event data**, not "top-N-per-group with classic schema."

This module is 5 SQL + 5 Python screen problems + 6 deeper onsite-flavored
SQL problems, all with worked solutions, a runnable test suite, and 5
Jupyter notebooks you can execute end-to-end.

---

## What this module covers

| Section | Files | What it teaches |
|---|---|---|
| 1. Loop structure | `design/01_loop_structure.md` | The 60-min format, pass bar, what to do if you fail mid-problem |
| 2. SQL problems (5) | `design/02_sql_problems.md` + `code/meta_screen_sql.sql` | Funnel, retention, sessionization, top-N-with-threshold, gaps-and-islands |
| 3. Python problems (5) | `design/03_python_problems.md` + `code/meta_screen_python.py` | Pandas vectorization, dict ranking, groupby-agg, second-highest, exception handling |
| 4. Onsite-flavored SQL (6) | `design/04_onsite_flavoured_sql.md` + `code/meta_onsite_sql.sql` | Instagram Stories 7-day retention, WhatsApp power-user cohort, Messenger yesterday-active video-call % |
| 5. Sessionization pattern | `design/05_sessionization_pattern.md` + `notebooks/04_sessionization.ipynb` | The 30-min inactivity gap — the signature Meta pattern |
| 6. Meta DE 2026 walkthrough | `design/06_company_specific.md` | Loop, 5+5 format, what changes at L4 vs L5, sources |

**Notebooks** (`notebooks/`) are runnable Jupyter files that load the
schema, walk through each problem, and run the solutions. The
notebook is the *narrated* form; the `.py`/`.sql` files are the
*executable* form. Both should be in your repo.

## How to use this module

**Week 1** — read `01_loop_structure.md` + `02_sql_problems.md`.
Run the SQL notebook. Time yourself on each problem. The pass
bar is 3 of 5 in 25 minutes; if you can't hit that on your second
attempt, you need another week of practice.

**Week 2** — read `03_python_problems.md`. Run the Python
notebook. Pandas vectorization is the #1 thing that separates
a 3/5 from a 5/5. Iterative / loop-based solutions are
*rejected* at Meta — read the inline comments.

**Week 3** — read `04_onsite_flavoured_sql.md` and
`05_sessionization_pattern.md`. These are the patterns that
*also* show up in the onsite SQL rounds. The sessionization
notebook is the most-asked single pattern at Meta in 2026.

**Week 4** — read `06_company_specific.md` to see the full
2026 Meta DE loop with all 6 rounds. Then do 2 timed mock
interviews: 5 SQL + 5 Python in 60 min.

By week 4 you should be hitting 4/5 or 5/5 on each half.

## Why this module exists

The course's `07_easy_practice` and `08_medium_practice` modules
cover classic SQL problems (employee salaries, top-N, departments).
They do *not* cover the social-event-data patterns that Meta
asks. The two Instagram-Likes problems in `07_easy_practice`
are the *only* Meta-tagged SQL in the rest of the course, and
they're easy — not the screen-level pattern.

This module is the gap-filler. It does not replace the easy/medium
practice; it adds the 5+5+6 Meta-specific problems that the
canonical SQL practice modules don't have.

## The schema

All 5 SQL screen problems + 6 onsite problems use the same 5
social-event tables defined in `code/meta_schema.sql`:

- `instagram_post` — `(post_id, user_id, post_date, likes, comments)`
- `instagram_story_event` — `(event_id, user_id, event_ts, event_type, view_duration_ms)`
- `facebook_post` — `(post_id, page_id, post_ts, impressions, engagements)`
- `whatsapp_message` — `(msg_id, sender_id, receiver_id, sent_ts)`
- `messenger_call` — `(call_id, caller_id, callee_id, started_ts, duration_s, is_video)`

These are the canonical 2026 Meta SQL screen tables. The
problems in this module are exactly the kind of questions
the recruiter told you to "expect a Presto/Spark dialect
and a funnels/retention/time-series flavor" — the same five
tables, runnable in SQLite with minor syntax adjustments.

## Stats

- **5 SQL screen problems** + **5 Python screen problems** + **6 onsite SQL problems** = **16 problems**
- **5 Jupyter notebooks** (one per problem set)
- **~30 tests** (each problem has 1-3 tests; Python tests are deterministic)
- **0 new dependencies** (pure stdlib + SQLite, same as the rest of the course)
- **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
