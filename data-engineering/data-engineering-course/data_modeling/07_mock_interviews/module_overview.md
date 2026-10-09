# Module 07 — Mock Interviews and Practice

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

This module is the *practical exam* for the data modeling
track. Three full mock interviews, narrated start to
finish, followed by three practice problems with full
solutions.

The mock interviews are written as a script between the
interviewer and a senior candidate. Read them aloud. The
goal is to internalize how a strong candidate *thinks out
loud* — not what they draw, but what they say while
they draw.

The practice problems are unscored problem statements.
Time-box yourself to 30 minutes per problem. Then read
the solution and the test. The test asserts the
*invariants* a senior solution would have.

---

## Lessons

| # | Title | What it is |
|---|---|---|
| [31](design/31_fitness_mock.md) | Mock interview: fitness app | Full 30-min transcript, narrated. |
| [32](design/32_uber_mock.md) | Mock interview: ride-sharing | Full 30-min transcript, narrated. |
| [33](design/33_amazon_mock.md) | Mock interview: Amazon marketplace | Full 30-min transcript, narrated. |
| [34](design/34_library_problem.md) | Practice: library management | Problem statement. |
| [35](design/35_hospital_problem.md) | Practice: hospital patient records | Problem statement. |
| [36](design/36_hotel_problem.md) | Practice: hotel booking | Problem statement. |

---

## Code

The three practice problems (lessons 34, 35, 36) have
full working solutions in
[`code/solutions.py`](code/solutions.py). The tests in
[`tests/test_solutions.py`](tests/test_solutions.py)
assert the invariants of each solution.

To run:

```bash
python3 -m unittest data_modeling/07_mock_interviews/tests/test_solutions.py
```

---

## How to use this module

1. **Read the rubric in Module 01 first.** The mock
   interview scoring is built on the 4-bucket rubric.
2. **For each mock interview**, read the problem
   statement in the lesson header, then read the
   transcript. Don't read the solution first.
3. **For each practice problem**, close the lesson, set
   a 30-minute timer, draw the diagram on paper, and
   narrate out loud. Then read the solution.
4. **Run the tests.** If you wrote a solution that the
   tests pass, you have a correct answer.

---

## What "narrate" means

The whiteboard round is *spoken*. The interviewer is
grading your *reasoning*, not your handwriting. The
mock interviews show what narration sounds like:

- "Before I draw anything, I want to clarify the use
  case. Are we reporting on engagement, retention, or
  revenue?"
- "I'm picking the workout session as the grain because
  it's the smallest unit that still has the measures
  the analyst needs."
- "I'm using SCD 2 on `dim_user` because fitness level
  changes and we want to attribute Q1 workouts to the
  user's Q1 fitness level, not today's."

If you can rehearse three or four of those phrases per
mock, you'll be ahead of 80% of candidates.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
