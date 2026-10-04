# Meta Data Engineer, Product Analytics: internet search

Run date: 2026-10-04. Scope: real questions reported for Meta DE-PA, Singapore and APAC first, then other locations.

## Headline

- First-hand Singapore reports found: **0**. First-hand APAC reports found: **0**. See `02_real_questions_singapore.md` and `gaps.md`.
- The closest material is first-hand reports with US or unstated locations. They describe the same DE-PA loop, but nothing confirms the Singapore loop is identical.
- 46 first-hand entries (41 technical in file 03, 5 behavioral in file 05), 48 guide entries (file 04) and 10 guide behavioral entries (file 05). Seven of these entries bundle several questions (G35, G36, G44, G46, G47, G48, B15), so the question count is higher than the entry count.
- About 99 entries remain after merging repeated questions (ride-sharing model, Instagram metric drop, e-commerce model and so on, listed in `06_by_topic.md`).

## Files

| File | Contents | Entries |
|---|---|---|
| `01_round_structure.md` | Round-by-round structure, per Meta's own PDF and per candidates, with contradictions flagged | none |
| `02_real_questions_singapore.md` | States plainly that there are zero SG/APAC first-hand reports; lists the closest non-SG reports | 0 |
| `03_real_questions_other_locations.md` | First-hand questions (Blind, Aced, SQLPad case study), all Region: Other | 41 (R01-R41) |
| `04_prep_site_questions.md` | Guide and question-bank questions, clearly not first-hand | 48 (G01-G48) |
| `05_behavioral_leadership.md` | Ownership / behavioral questions, first-hand and guide | 15 (B01-B15) |
| `06_by_topic.md` | Everything grouped SQL / Python / data modeling / architecture / product sense / behavioral | index |
| `sources.md` | Every URL visited: site, title, date, location, usable or not | 65 URLs |
| `gaps.md` | Blocked or unreadable pages and manual checks | none |

## Sources and method

- About 40 distinct searches and about 75 page fetches. The last two batches of searches added no new first-hand question.
- 42 pages were read; 23 were blocked (Glassdoor, LeetCode Discuss, 1Point3Acres, several Medium posts, Reddit, some guide sites). The blocked list is in `sources.md` and `gaps.md`.
- Meta's own DE onsite prep PDF was fetched and read; it is the basis for the structure in `01_round_structure.md`.

## Confidence tags used

`verbatim` (candidate's words rendered in quotation marks by the fetch tool), `paraphrased` (summary of a candidate's account), `guide` (prep-site content, not first-hand), `snippet-only` (search snippet or card title, no full text).

## Coverage gaps

- No Singapore or APAC first-hand report. Glassdoor (including the Singapore pages), 1Point3Acres, LeetCode Discuss and Reddit are where they most likely sit and were all unreadable by this tool.
- Many first-hand sources are Blind threads that talk about format and prep rather than listing questions; several list only topics.
- Verbatim question text is rare; the fetch tool summarises pages, so re-check any question you rely on against its source URL.
- Older entries (2021, 2022) may not reflect the current blended product sense / data modeling / SQL / Python loop.

This is a public repo: no personal data about any reader is stored here, and quotes are limited to question text with attribution.
