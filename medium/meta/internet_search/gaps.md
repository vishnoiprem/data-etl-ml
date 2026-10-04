# Gaps and what to check manually

## Biggest gap: no first-hand Singapore or APAC report

Nothing fetched says "Singapore" or names any APAC city in a candidate's own account of a Meta DE-PA interview. Singapore DE-PA job listings exist (search snippets), so the loop is probably the standard one, but that is unconfirmed.

## Pages that could not be read (check these by hand in a browser)

| Page | Why it matters | Problem |
|---|---|---|
| Glassdoor, Meta Singapore interview questions: https://www.glassdoor.com/Interview/Meta-Singapore-Interview-Questions-EI_IE40772.0,4_IL.5,14_IM1123_IP2.htm | Best chance of Singapore-labelled reports (filter job title to Data Engineer) | HTTP 403 |
| Glassdoor Singapore, Meta Data Engineer: https://www.glassdoor.sg/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm | Same, localized site | HTTP 403 |
| Glassdoor, Meta Data Engineer (430 questions, 371 reviews per snippet): https://www.glassdoor.com/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm | Largest pool of dated, located reports | HTTP 403 |
| 1Point3Acres DE-PA threads: https://www.1point3acres.com/interview/thread/1157192 , /1131591 , /1148877 (IC6 phone screen), /1020381 (virtual onsite), and https://www.1point3acres.com/bbs/thread-1112159-1-1.html | Detailed Chinese and English reports, often with locations | HTTP 403 |
| LeetCode Discuss: https://leetcode.com/discuss/interview-experience/5681814/Meta-Data-Engineer-Onsite-Interview/ , https://leetcode.com/discuss/post/1832158/meta-data-engineer-phone-interview/ , https://leetcode.com/discuss/post/7264613/state-of-data-engineer-interviews-europe-6zh6/ , https://leetcode.com/discuss/interview-experience/1765664/facebook-data-engineer-feb-2022-meta-usa-waiting-for-result/ | Named first-hand onsite and phone-screen reports | HTTP 403 |
| Medium: https://medium.com/@rasterroo/meta-data-engineer-interview-experience-2025-c26d23f995ce , https://medium.com/@jarianroselline/meta-data-engineer-interview-nov-2025-experience-0f6419fb214a , https://medium.com/@rohitverma_87831/my-interview-experience-at-meta-ad7eb22dd220 , https://palakdatascientist.medium.com/how-to-crack-the-data-engineer-interview-at-facebook-7e16ae65e0be | Candidate write-ups (Nov 2025 one is the most recent) | connection refused, 2 tries each on the first two |
| Blind: https://www.teamblind.com/post/Meta-Data-Engineer-Interview-YDQ4FXk8 | DE interview thread | removed ("content isn't available anymore") |
| Reddit (r/dataengineering, r/cscareerquestions, r/leetcode, r/singaporejobs) | Possible Singapore-specific threads | fetch tool refuses reddit.com; WebSearch also returned no Reddit URLs |
| IGotAnOffer: https://igotanoffer.com/blogs/tech/facebook-data-engineer-interview | Guide with sample questions | HTTP 403 |
| Interview Query, DataInterview, Dataford guides | Guides | HTTP 429 (rate limited), retry later |

## Not searched or not reachable by this tool

- LinkedIn posts, YouTube video descriptions and transcripts: no usable result came back for Singapore or DE-PA.
- Blind's own company page and search results (https://www.teamblind.com/company/Meta/posts/meta-interview) were seen only as search results, not fetched. Searching Blind for "Singapore" inside the Meta channel by hand is worth doing.
- Hello Interview, DataLemur (the DataLemur Meta guide is for Data Science, not DE) and Educative were not fetched for DE-PA.

## Quality limits of what is in the files

- WebFetch summarises pages with a small model, so even `verbatim` tags mean "rendered inside quotation marks in the fetch output", not guaranteed character-for-character. Re-check any question you plan to rely on against the source URL.
- Blind post bodies were fetched without full comment trees in some cases; questions hidden in comments may be missing.
- The Aced experience has no absolute date ("a year ago", "submitted 6 months ago" relative to the fetch).
- Guide sites that say "candidate-reported" give no way to verify; several pages share identical books/authors/sales questions that probably trace back to one 2025 report.
- The SQLPad "Jake" case study is a vendor-written candidate account (Menlo Park, E5), not a direct post.
- Interview rounds changed over time (2021 onsite had streaming and ETL as separate areas; 2024 to 2026 loops blend product sense, modeling, SQL and Python). Older entries (2021, 2022) may not match the current loop.
- One search snippet claimed a January 2026 candidate had a take-home assessment and a stats-and-pipeline-monitoring round; the page behind it was not identified, so this is not used.
- Search snippets for tumbling-window and 10/15/15/15-minute splits came from unidentified pages and were not used as facts.

## Suggested manual checks (in priority order)

1. Glassdoor with the Singapore location filter and "Data Engineer" title.
2. Blind: Meta channel, search "Singapore" plus "data engineer".
3. Reddit searches in a browser for "Meta data engineer Singapore" and "Meta DE product analytics APAC".
4. 1Point3Acres company page https://www.1point3acres.com/interview/company/META filtered to data engineer.
5. Ask the recruiter whether the Singapore loop matches the US loop (technical screen format and the 30 min Ownership round).
