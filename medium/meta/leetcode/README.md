# Meta DE-PA interview prep — LeetCode question bank

> **A pointer file to the Meta-tagged LeetCode
> questions, plus a 4-step prep path.** This directory
> doesn't ship any code; it points to the canonical
> question bank and the prep sites that the Meta Data
> Engineer / Product Analytics loop actually tests on.

The interview loop for Meta DE-PA is **SQL + Python +
data modeling + product sense**, in roughly that
weighting. LeetCode is the volume-builder; the
Meta-specific tag filters the question set to what
Meta actually asks. The other prep sites add the
real-Meta style and the data-modeling depth.

---

## The question bank

The canonical source is the
[`liquidslr/leetcode-company-wise-problems`](https://github.com/liquidslr/leetcode-company-wise-problems)
repo. The Meta-tagged questions live in
[`Meta/`](https://github.com/liquidslr/leetcode-company-wise-problems/tree/main/Meta);
the curated 30-day sheet is in
[`Meta/1. Thirty Days.csv`](https://github.com/liquidslr/leetcode-company-wise-problems/blob/main/Meta/1.%20Thirty%20Days.csv).

Start with the 30-day CSV. It's the question set with
the highest signal density for Meta-tagged problems.

---

## The 4-step prep path

This is the order that worked. Volume first, then
style, then modeling depth, then mocks.

| Step | What | Where | Why |
|------|------|-------|-----|
| 1 | **Build SQL + Python volume and speed** | [DataLemur](https://datalemur.com/) (free, Meta-style SQL) + LeetCode Database tag | Meta tests SQL harder than any other skill; volume is the only way to hit the speed bar |
| 2 | **Switch to Meta-style real questions** | [StrataScratch](https://www.stratascratch.com/) | Real interview questions from real candidates, not textbook exercises |
| 3 | **Data modeling + pipeline thinking** | [DataDriven.io](https://www.datadriven.io/) or [Interview Query](https://www.interviewquery.com/) | The data-modeling round is the differentiator; LeetCode alone won't get you there |
| 4 | **2-4 paid mocks** | [Prepfully](https://prepfully.com/) or [Exponent](https://www.tryexponent.com/) | Simulate the real loop; the first mock is always the worst, the fourth is the calibration |

The order matters. **Volume before style, style
before depth, depth before mocks.** Skip a step and
you'll find it in the first mock anyway.

---

## What's in this directory

Just this README. The pointers above are the actual
content. The same pattern is used in
[`../internet_search/`](../internet_search/) — the
internet search turned up 0 first-hand Singapore
reports and 41 first-hand Other-region reports; that
directory is the 9-file writeup of the search.

---

## What this is NOT

- **Not a question bank.** The questions are at the
  links above; this directory is the *pointer* to
  them.
- **Not a guarantee of interview success.** The
  prep path is what worked for one candidate; the
  loop changes, the question style changes, and the
  weighting changes. Use this as a starting point,
  not a checklist.
- **Not a substitute for the structured search.** For
  the *first-hand* question reports (what candidates
  actually got asked, with dates and locations), see
  [`../internet_search/`](../internet_search/). That
  directory is the 9-file writeup of the actual
  search, with sources, confidence tags, and gap
  notes.

---

## Related directories

- [`../internet_search/`](../internet_search/) — the
  internet search for first-hand Meta DE-PA reports
  (41 first-hand Other-region questions, 48 guide
  questions, 15 behavioral questions, 65 sources).
- [`../../`](../..) — the parent `medium/` directory
  (40+ articles, interview prep, design deep-dives).
