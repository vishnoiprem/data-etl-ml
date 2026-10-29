# Google Data Engineer — Interview Question Bank (Compiled from Candidate Reports, ~2015–2026)

> Sources: questions reported by real candidates on Glassdoor, Blind, Interview Query, IGotAnOffer, and Prepfully analyses. Google rotates questions, so treat these as the *patterns* you must master — variations of these appear every year. Focus area for your round: **Role Related Knowledge — Code Comprehension & Programming** (Sections 1–3 are most critical).

---

## SECTION 1 — SQL QUESTIONS (most frequently reported topic)

### Joins, Filtering & Anti-Joins
1. Find customers who placed an order in January but not in February.
2. Find all employees who earn more than their manager (self-join).
3. Given `users` and `transactions` tables, find users who have never made a transaction.
4. Explain the difference between INNER, LEFT, RIGHT, FULL OUTER, and CROSS JOIN — and what happens to row counts when there are duplicate keys.
5. Why can `NOT IN` give wrong results when the subquery contains NULLs? How do you fix it (NOT EXISTS / anti-join)?
6. Join two tables on a date range rather than an exact key (e.g., price valid between start_date and end_date).

### Window Functions
7. Find the top 3 products by revenue in each region (RANK vs DENSE_RANK vs ROW_NUMBER — explain the difference).
8. Find each employee's salary rank within their department.
9. Compute a 7-day moving average of daily sales.
10. Compute a running (cumulative) total of revenue by month.
11. For each user, find the time difference between consecutive logins (LAG/LEAD).
12. Find the second-highest salary — (a) with a window function, (b) without one.
13. Compute month-over-month % growth in revenue.
14. For each customer, flag their first and most recent purchase.

### Deduplication & Data Cleaning
15. Remove duplicate rows from a table keeping only the latest record per user (ROW_NUMBER + QUALIFY / CTE delete).
16. A pipeline double-loaded yesterday's data. Write SQL to detect and remove the duplicates safely.
17. Find records where the same email maps to multiple user_ids.

### Aggregation & Percentages (very commonly reported)
18. Calculate the percentage of total revenue contributed by each product category.
19. What % of users who signed up in a given month made a purchase within 30 days? (conversion)
20. Write a query to get the distribution of the number of conversations created by each user per day in a given year (reported Google question — group by user+day, then group by the count).
21. Pivot rows to columns using conditional aggregation (COUNT(CASE WHEN ...)).
22. Compute click-through rate (clicks/impressions) per ad, handling division by zero.

### Sessionization / Gaps & Islands (favorite senior-level pattern)
23. Given event logs (user_id, timestamp), sessionize events with a 30-minute inactivity timeout.
24. Find users active for 3+ consecutive days.
25. Find the longest streak of consecutive daily logins per user.
26. Identify gaps in a sequence of IDs or dates.

### Retention / Cohorts / Funnels
27. Build a monthly cohort retention table (signup month × months since signup).
28. Day-1 / Day-7 / Day-30 retention for new users.
29. Funnel analysis: of users who viewed a page, how many added to cart, how many purchased?

### SQL Theory & Optimization
30. A query on a trillion-row table is slow — how do you optimize it? (partitioning, clustering, predicate pushdown, avoiding SELECT *)
31. Difference between WHERE and HAVING; when does each execute?
32. Difference between UNION and UNION ALL (and performance implications).
33. Explain query execution order (FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY).
34. What are indexes? When do they hurt performance? Why does BigQuery not use traditional indexes?
35. Correlated vs non-correlated subqueries — performance impact.
36. CTEs vs temp tables vs subqueries — when to use which.
37. How would you find and handle data skew in a JOIN on a distributed engine?

---

## SECTION 2 — PYTHON / PROGRAMMING QUESTIONS (reported verbatim or near-verbatim)

### Reported Google questions
38. **Friends count:** Given a 2-D array of friend pairs like `[[A,B],[A,C],[B,D],[B,C],[R,M],[S],[P],[A]]`, write a function that returns a dictionary of how many friends each person has (people can have 0 to many friends). *(actual reported question)*
39. **Forward-fill:** Replace every `None` in a list with the previous non-None value. Handle edge cases: list starts with None, empty list, input is None. *(actual reported question)*
40. **Nth highest in dict:** Given a dictionary, print the key for the nth-highest value; if ties exist, sort keys and return the first. *(actual reported question)*
41. **Uncommon words:** Given two sentences, print words that appear in one sentence but not the other (a word appearing twice in sentence 1 but absent from sentence 2 still counts). *(actual reported question)*
42. **Letter frequency:** Count occurrences of each letter in a string.
43. **Fill-in-the-blank code:** Complete a partially written function and make it pass all edge cases (None input, empty list). *(reported format)*

### Common data-flavored coding patterns
44. Parse a log file and return the top N most frequent IPs / URLs / error codes.
45. Flatten an arbitrarily nested JSON/dictionary into dot-notation keys.
46. Flatten a nested list of lists.
47. Merge overlapping intervals; merge two sorted lists.
48. Find duplicates in a list; dedupe while preserving order.
49. Two-sum / pair-with-target-sum using a hashmap.
50. Group anagrams; check if two strings are anagrams.
51. Reverse words in a sentence; check palindrome ignoring punctuation.
52. Implement a word-count over a large text (dictionary aggregation).
53. Given a CSV as a list of dicts, group by a column and aggregate (a "mini groupby" without pandas).
54. FizzBuzz-style warmups (yes, still occasionally asked as an opener).
55. Generate the Fibonacci sequence (iterative vs recursive; discuss complexity).
56. Find the first non-repeating character in a string.
57. Validate and transform timestamps between formats; compute time deltas.
58. How would you process a 100 GB file that doesn't fit in memory? (generators, chunking, streaming)
59. Difference between list and tuple; dict vs set; when to use each.
60. What are Python generators and `yield`? Why do they matter for data pipelines?
61. Explain the mutable default argument bug (`def f(x, acc=[])`).
62. Shallow vs deep copy.
63. List/dict comprehensions — rewrite a loop as a comprehension.
64. (Sometimes) pandas: groupby + agg, merge two DataFrames, handle NaNs, drop duplicates.

---

## SECTION 3 — CODE COMPREHENSION (the defining part of your RRK round)

Interviewers paste a snippet and ask you to reason about it aloud. Reported formats:

65. "Walk me through this code line by line. What does it do?"
66. "What is the output of this code for input X?" — typically traps include:
    - mutable default arguments
    - integer vs float division
    - variable scoping / late binding in closures and lambdas
    - off-by-one errors in range() loops
    - modifying a list while iterating over it
    - is vs == comparisons
67. "There's a bug in this function — find it and fix it." (often the bug is an edge case: empty input, single element, all duplicates)
68. "What happens if the input is None / empty / 1000× larger?" (complexity + robustness)
69. "Refactor this code to be more readable / Pythonic / efficient."
70. "What's the time and space complexity of this function?"
71. SQL comprehension: "Here's a query — explain what result set it produces" (usually involving a tricky join + window function + filter ordering).
72. "This query returns wrong/duplicate rows — why?" (fan-out from a one-to-many join, or filtering a LEFT JOIN in WHERE instead of ON).

**How to practice:** read code aloud, predict output BEFORE running it, then verify. Use snippets from real codebases or generated buggy code.

---

## SECTION 4 — DATA MODELING & WAREHOUSING (reported across onsite loops)

73. Design a star schema for an e-commerce business (orders, products, customers). Identify fact vs dimension tables.
74. Star vs snowflake schema — trade-offs.
75. Normalization vs denormalization — when do you denormalize for analytics?
76. What are Slowly Changing Dimensions? Implement SCD Type 2 (effective dates, current flag).
77. Design a data mart for a ride-sharing app / YouTube watch-history analytics.
78. Fact table grain — what is it and why does it matter?
79. How do you model many-to-many relationships in a warehouse (bridge tables)?
80. Surrogate keys vs natural keys.
81. OLTP vs OLAP — differences in design and workload.

---

## SECTION 5 — ETL / PIPELINES / BIG DATA (reported)

82. Design an end-to-end ETL pipeline: source → transformation → sink. Where do you validate? Where can it fail?
83. How do you handle late-arriving data in a daily batch pipeline?
84. How do you make a pipeline idempotent so reruns/backfills don't duplicate data?
85. Batch vs streaming — trade-offs; when would you choose each?
86. ETL vs ELT — why has the industry shifted to ELT?
87. How do you implement deduplication and error handling in an ingestion pipeline?
88. How do you detect and handle schema drift from an upstream source?
89. How would you backfill 2 years of historical data without breaking the daily pipeline?
90. Explain how MapReduce works conceptually; what replaced it and why (Spark — in-memory DAG execution)?
91. What is data skew in distributed processing and how do you mitigate it (salting, broadcast joins)?
92. Airflow/Cloud Composer: what is a DAG? How do retries, SLAs, sensors, and backfills work?
93. How do you monitor data quality in production (freshness, volume, null-rate, uniqueness checks)?
94. Exactly-once vs at-least-once processing semantics.

---

## SECTION 6 — GCP / BIGQUERY (asked when on your resume or for GCP-aligned teams)

95. Explain BigQuery's architecture: separation of storage and compute, columnar storage, slots.
96. Partitioning vs clustering in BigQuery — when to use each, and limits.
97. How do you reduce BigQuery cost for a query scanning huge tables?
98. Streaming inserts vs batch loads into BigQuery.
99. When would you use Dataflow vs Dataproc vs BigQuery for a transformation?
100. Pub/Sub: how does it guarantee delivery? How do you handle duplicates downstream?
101. Cloud Storage → BigQuery ingestion patterns; external tables vs native tables.
102. How does BigQuery handle JOIN execution across distributed slots?

---

## SECTION 7 — SYSTEM / PIPELINE DESIGN (senior-level follow-ups)

103. Design a pipeline to ingest clickstream events at 1M events/second and make them queryable within minutes.
104. Design YouTube's daily watch-time aggregation pipeline.
105. Design a real-time fraud-detection data flow.
106. You're given a trillion-row table and an analyst's query takes hours — walk through your full optimization approach.
107. Design a system to deduplicate events arriving from an at-least-once message queue.
108. How would you migrate an on-prem warehouse to GCP with zero downtime?

(Interviewers often start with a modeling question, then layer on scale/streaming constraints — be ready for the pivot.)

---

## SECTION 8 — BEHAVIORAL / GOOGLEYNESS (separate round, but prep anyway)

109. Tell me about a time a pipeline you owned failed in production. What did you do?
110. Describe a time you disagreed with a teammate on a technical design.
111. Tell me about the most complex data problem you've solved.
112. A stakeholder reports your numbers are wrong — how do you respond?
113. Tell me about a time you had to deliver with ambiguous requirements.
114. Why Google? Why this role?

Use STAR format; for a Senior role, emphasize ownership, cross-team influence, and decisions with trade-offs.

---

## PREP CHECKLIST FOR YOUR SPECIFIC ROUND (Code Comprehension & Programming)

- [ ] Solve Sections 1 & 2 by writing code in a plain Google Doc (no autocomplete, no syntax highlighting) — this mirrors the real environment
- [ ] For every solution, state assumptions first, then code, then test with an edge case yourself before declaring done
- [ ] Practice tracing code output aloud (Section 3 traps) — 10 minutes daily
- [ ] Time-box: SQL questions ~8–10 min each, Python ~15 min each
- [ ] Re-read Google's official prep guide from your recruiter — it reflects the actual rubric
- [ ] Prepare 2–3 clarifying questions you'd ask before coding (input size? nulls? duplicates? sorted?)
- [ ] Always end with complexity analysis (time + space) and one "how this scales" comment — expected at Senior level
