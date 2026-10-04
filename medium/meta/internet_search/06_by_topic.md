# Questions by topic

Ids link to entries: R = first-hand, `03_real_questions_other_locations.md`; G = guide, `04_prep_site_questions.md`; B = behavioral, `05_behavioral_leadership.md`. `[1st]` marks a first-hand entry (R or B01-B05). Everything else is guide content. There is no Singapore (SG) or APAC entry, see `02_real_questions_singapore.md`.

## SQL

First-hand
- R01 Same-day purchase percentage (books/sales schema). Repeated in G43 (Interview Kickstart) and, per Weekday, in near-identical form. seen_in 2+
- R02 Multi-transaction customer identification
- R03 Top 5 customers by average payment of invitees. Also in the Weekday and Interview Kickstart copies. seen_in 2+
- R04 Author statistics and domain analysis (vague)
- R05 Sales totals by payment type
- R16 Onsite SQL on a provided schema (CASE, HAVING, CTE, FULL OUTER JOIN, COALESCE, LAG)
- R18 Recursive CTEs, cross joins, window functions, EXCEPT, islands
- R21 Related-table schema, LeetCode-style, built up in steps
- R23 2021 onsite: 6-7 SQL queries
- R26 3 SQL (1 hard), Infrastructure Strategy team
- R27 3 coding + 3 SQL screen, gaps-and-islands tip
- R28 "What is NULL + 1" (commenter, weak)
- R33 Screen ladder: GROUP BY/HAVING, window/CTE, LAG/LEAD
- R38 Paid customers who bought both A and B
- R39 Promotion share of sales on first and last day (similar: G03)
- R40 Top 5 co-purchased products

Guide
- G01 UNION vs UNION ALL (2 sources)
- G02 Top 5 sales products
- G03 Sales share first vs last working day of month
- G07 7-day rolling DAU, DAU/MAU, top 100 by stickiness
- G16 July MAU retained from June
- G17 Days between first and last post
- G18 LEFT vs RIGHT JOIN
- G19 WHERE vs HAVING
- G21 Library: checked out, not returned by due date (and two follow-on queries)
- G22 Sum of orders and unique customers
- G23 Users who called 3+ people last week (2 sources)
- G33 Messenger: percent of yesterday's active users who made a video call
- G37 to G39 Interview101 retention, peak-engagement and cohort queries
- G43 Authors with at least 5 books
- G46 Weekday generic: second-highest salary, duplicates, top 3 per department
- G47 StrataScratch curated titles (16)

## Python

First-hand
- R06 to R13 Average price; most common comment across locations; search an unsorted list; consecutive-year workshops; largest number from digits; overlapping meetings (also LeetCode Meeting Rooms); interval scheduling; budget-constrained book purchase
- R17 Balanced tree rebalancing (LeetCode-style, reported as very hard)
- R20 Anagrams, reversal, dict/array work, matrix transposition
- R22 Strings, lists, dicts, sliding window; simulated streaming
- R25 Streaming Python question (2021)
- R34 to R37 Fill None with previous; unmatched words; character frequency; key of nth largest value

Guide
- G04 Monotonic list
- G14 Missing number
- G15 Arithmetic string evaluation
- G24 to G27 Second letter counts; read data.csv with error handling; second-highest salary per department; list join and removal
- G34 Dynamic SQL formatter
- G35 Aced bank: edit distance, linked list, LRU cache, intervals, anagrams, parentheses, move zeros
- G40 Interview101 DataFrame quartiles and trend significance

## Data modeling

First-hand
- R15 Fact grain, SCD2, bridge tables, keys
- R19 LinkedIn / Craigslist / Uber model
- R24 2021 data model and design, SQL over it
- R31 Ride-sharing case; R41 ride-sharing data warehouse (same concept as R31; with R19 seen_in 3)
- R32 E-commerce case

Guide
- G05 Epic Games model plus ETL plus SQL
- G06 Google Classroom, Uber relational DB (Uber repeats R19/R31/R41)
- G08 Facebook Marketplace model
- G29 E-commerce store (matches R32)
- G31 Movie theater ticketing
- G41 Reels star schema, cross-platform model, ad auctions
- G45 Ride-sharing schema; books with multiple authors

## Architecture / ETL

- R29 Streaming pipelines, change logs from a database (advice, weak)
- G13 Idempotent flattening of out-of-order, duplicated JSON events
- G30 Reddit-style notification system
- G32 15-minute tumbling windows over ride requests
- G48 PracHub titles: batch and streaming ETL architecture, dimensional model, two-hop follows

## Product sense / metrics

First-hand
- R14 4 to 6 metrics with numerator and denominator
- R25 Key metrics (2021 interview 3)
- R30 Instagram-like metric drop, with follow-ups

Guide
- G09 Health of Facebook Groups (2 sources)
- G10 Reels engagement down 5%
- G11 Comment ranking metrics
- G12 Is Marketplace healthy
- G20 DAU spike day 30, drop day 50
- G28 Instagram metric drop (matches R30)
- G36 Remove the profile photo onboarding step; bookstore SQL
- G42 Memory highlights feature
- G44 Reels success, News Feed drop, WhatsApp group video, Messenger DAU/WAU/MAU dashboard

## Behavioral

First-hand
- B01 Tell me about yourself; recent experience; Why Meta?
- B02 Why Meta?; Why data engineering?
- B03 Conflict with team lead or manager (seen_in 3: Aced experience, Aced guide, Prepfully "conflict with your manager")
- B04 Improved a process with business impact (seen_in 2)
- B05 Learned a tool quickly (seen_in 2)

Guide
- B06 Led a project end to end
- B07 Different org challenges your approach
- B08 Used data when others used instinct
- B09 Most complex project
- B10 Went the extra mile
- B11 Biggest challenge in the role
- B12 Pipeline outage under deadline
- B13 Quick decision, cross-functional project
- B14 Moving fast under ambiguity; challenging architecture
- B15 Aced bank behavioral items

## Merge notes

Counted once: the ride-sharing/Uber model (R19, R31, R41, G06, G45); Instagram metric drop (R30, G28); e-commerce model (R32, G29); users who called 3+ people (G23 in two Aced pages); UNION vs UNION ALL (G01 in two sources).
