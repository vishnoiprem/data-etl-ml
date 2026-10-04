# Prep-site and guide questions (NOT first-hand)

Everything here comes from vendor guides, question banks and blog posts. Several sites say "candidate-reported", but none shows who reported it, when or where, so treat these as "likely/typical", not as confirmed questions. Counts such as "reported 31 times" on Interview101 are unverified marketing numbers. Where a guide question matches a first-hand one in `03`, the match is noted. Region is Other for all (no guide mentioned Singapore; Interview101, Weekday and Interview Kickstart were checked for it and had none). Ids G01... are used by `06_by_topic.md`. Confidence is `guide` throughout.

## Prepfully (https://prepfully.com/interview-guides/facebook-data-engineer)

### G01 UNION vs UNION ALL
- Round: Technical screen / recruiter call   Topic: SQL   Region: Other
- Question: "What is the difference between UNION and UNION ALL? Which is faster?"
- Follow-ups: none
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide (also Zero2DataEngineer https://zero2dataengineer.substack.com/p/how-to-prepare-for-metas-data-engineering). seen_in 2
### G02 Top 5 sales products
- Round: Technical screen   Topic: SQL   Region: Other
- Question: "Find the top 5 sales products from the order table."
- Follow-ups: none
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide
### G03 Sales share, first vs last working day
- Round: Technical screen   Topic: SQL   Region: Other
- Question: "For a given Sales table, compare the percentage of total sales on the first and last working day of the month." Similar in spirit to R39.
- Follow-ups: none
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide
### G04 Monotonic list
- Round: Technical screen   Topic: Python   Region: Other
- Question: "Given a list of integers, work out a solution to find whether the list is monotonic (increasing or decreasing) or not."
- Follow-ups: none
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide
### G05 Epic Games model, ETL and SQL
- Round: Full stack onsite   Topic: Data modeling   Region: Other
- Question: "Prepare a design model for a gaming company such as Epic Games." then "Design ETL pipelines for the above model." then "Write SQL queries for the above design model." (Prepfully says these are sample scenarios, not verbatim interview questions.)
- Follow-ups: chained as above
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide
### G06 Google Classroom and Uber databases
- Round: Full stack onsite   Topic: Data modeling   Region: Other
- Question: "Design a database for an app such as Google Classroom." and "Design a relational database for Uber." (sample scenarios). The Uber one matches R19, R31, R41.
- Follow-ups: none
- Source: Prepfully — https://prepfully.com/interview-guides/facebook-data-engineer — 2026 — guide

## DataVidhya (https://datavidhya.com/blog/meta-data-engineering-interview-guide/) — samples the site calls "representative", not reports

### G07 7-day rolling DAU and stickiness
- Round: SQL   Topic: SQL   Region: Other
- Question: "You have an events table with user_id, event_name, and event_timestamp. Compute the 7-day rolling DAU for the last 90 days. Then compute the DAU/MAU ratio as a stickiness metric. Then identify the top 100 users by stickiness."
- Follow-ups: chained as above
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide
### G08 Facebook Marketplace data model
- Round: Data modeling   Topic: Data modeling   Region: Other
- Question: "Design a data model for Facebook Marketplace" answering listings per seller, sold in the last 30 days, average sale price, and seller performance over time; walk through fact tables, dimensions and grain.
- Follow-ups: none
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide
### G09 Health of Facebook Groups
- Round: Product sense   Topic: Product sense / metrics   Region: Other
- Question: "How would you measure the health of Facebook Groups?" Interview101 lists a similar prompt ("End-to-end community health infrastructure for Facebook Groups").
- Follow-ups: none
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide. seen_in 2 (with Interview101)
### G10 Reels engagement down 5%
- Round: Product sense   Topic: Product sense / metrics   Region: Other
- Question: "A PM tells you Reels engagement dropped 5% week-over-week. How do you investigate?"
- Follow-ups: none
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide
### G11 New comment ranking metrics
- Round: Product sense   Topic: Product sense / metrics   Region: Other
- Question: "We want to launch a new comment ranking algorithm. Design the metrics to evaluate it."
- Follow-ups: none
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide
### G12 Is Marketplace healthy?
- Round: Product sense   Topic: Product sense / metrics   Region: Other
- Question: "You are working with a PM on Facebook Marketplace. They want to know if Marketplace is healthy. Define the metrics. Prioritize them. Write the SQL for the top one. Then tell me what you would do if it dropped 10% next week."
- Follow-ups: chained as above
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide
### G13 Idempotent event flattening
- Round: Python / pipeline design   Topic: Architecture/ETL   Region: Other
- Question: Stream of JSON user events (user_id, event_type, event_timestamp, variable properties dict); write a function producing one flat record per user per day with counts per event_type, handling out-of-order and duplicate records, idempotent for backfill.
- Follow-ups: none
- Source: DataVidhya — https://datavidhya.com/blog/meta-data-engineering-interview-guide/ — 2026 — guide

## DEV Community teaching problems (https://dev.to/gowthampotureddi/facebook-data-engineering-interview-questions-prep-guide-1da6) — curated, not from candidates

### G14 Missing number
- Round: n/s   Topic: Python   Region: Other
- Question: Given an array nums of n distinct integers in [0, n], return the single missing number in O(n) time and O(1) space.
- Follow-ups: none
- Source: DEV Community — https://dev.to/gowthampotureddi/facebook-data-engineering-interview-questions-prep-guide-1da6 — n/s — guide
### G15 Arithmetic expression string
- Round: n/s   Topic: Python   Region: Other
- Question: Given a string of integer operands and + - * / (no parentheses, standard precedence), return the integer result.
- Follow-ups: none
- Source: DEV Community — https://dev.to/gowthampotureddi/facebook-data-engineering-interview-questions-prep-guide-1da6 — n/s — guide
### G16 MAU retention June to July
- Round: n/s   Topic: SQL   Region: Other
- Question: Return the number of monthly active users in July 2022, users who were active in both July and June.
- Follow-ups: none
- Source: DEV Community — https://dev.to/gowthampotureddi/facebook-data-engineering-interview-questions-prep-guide-1da6 — n/s — guide
### G17 Days between first and last post
- Round: n/s   Topic: SQL   Region: Other
- Question: For each user who posted at least twice in 2024, return the days between their first and last post.
- Follow-ups: none
- Source: DEV Community — https://dev.to/gowthampotureddi/facebook-data-engineering-interview-questions-prep-guide-1da6 — n/s — guide

## Zero2DataEngineer (Substack)

### G18 LEFT JOIN vs RIGHT JOIN
- Round: Recruiter call   Topic: SQL   Region: Other
- Question: "How does a LEFT JOIN differ from a RIGHT JOIN?"
- Follow-ups: none
- Source: Substack — https://zero2dataengineer.substack.com/p/how-to-prepare-for-metas-data-engineering — 2025-02-18 — guide
### G19 WHERE vs HAVING
- Round: Recruiter call   Topic: SQL   Region: Other
- Question: "When would you use WHERE vs HAVING in SQL?"
- Follow-ups: none
- Source: Substack — https://zero2dataengineer.substack.com/p/how-to-prepare-for-metas-data-engineering — 2025-02-18 — guide
### G20 DAU spike on day 30, drop on day 50
- Round: ETL round (partial; rest paywalled)   Topic: Product sense / metrics   Region: Other
- Question: Interviewer shows a DAU dashboard over 60 days with a spike at day 30 and a drop at day 50: "How would you investigate to explain this shift?"
- Follow-ups: author's suggested framework only, not reported follow-ups
- Source: Substack — https://zero2dataengineer.substack.com/p/meta-data-engineer-onsite-interview — 2025-03-07 — guide (author frames it as a playbook, not first-hand)

## Aced guide (https://www.aced.io/guides/meta-data-engineer-interview) — states "candidate-reported", unattributed

### G21 Library: checked out, not returned by due date
- Round: Technical screen SQL   Topic: SQL   Region: Other
- Question: Given a library schema with books, users and a check-in/checkout table, find each user and the number of books they checked out but did not return before the due date.
- Follow-ups: same schema: users who checked out books in a category, grouped by age; number of people who checked out a book on the same day another person returned it
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G22 Orders sum and unique customers
- Round: Technical screen SQL   Topic: SQL   Region: Other
- Question: From a transaction table, find the sum of total orders and the count of unique customers.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G23 Users who called 3+ people last week
- Round: Technical screen SQL   Topic: SQL   Region: Other
- Question: Find the number of users who called three or more people in the last week.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide (also in Aced question bank, "1 year ago"). seen_in 2
### G24 Second letter of first word, counted
- Round: Technical screen Python   Topic: Python   Region: Other
- Question: Given a list of strings, find the second letter of the first word in each string and return the character with its count of occurrences.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G25 Read data.csv, handle missing file
- Round: Technical screen Python   Topic: Python   Region: Other
- Question: Write a function that reads a data.csv file, processes it, and outputs "file not found" when the file is missing.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G26 Second-highest salary per department
- Round: Technical screen Python   Topic: Python   Region: Other
- Question: Given a dictionary of employees with department and salary, find the second-highest salary in each department.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G27 List joins and removals
- Round: Technical screen Python   Topic: Python   Region: Other
- Question: Join two lists and sort the result; remove items from a list based on a specific key.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G28 Instagram metric drop and its data model
- Round: Onsite product sense / modeling   Topic: Product sense / metrics   Region: Other
- Question: An Instagram metric is dropping: walk through root-cause analysis, the data model that would support it, and the follow-up investigation. Matches R30.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G29 E-commerce store model
- Round: Onsite data modeling   Topic: Data modeling   Region: Other
- Question: Design a data model for an ecommerce store covering products, orders, customers and inventory. Matches R32.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G30 Reddit-style notification system
- Round: Onsite data modeling   Topic: Architecture/ETL   Region: Other
- Question: Design a notification system for a Reddit-style app: what do the backend and data model look like?
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G31 Movie theater ticketing
- Round: Onsite data modeling   Topic: Data modeling   Region: Other
- Question: Design a movie theater ticketing system: how would you store the data needed to support end-to-end functionality?
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G32 15-minute tumbling windows
- Round: Onsite Python   Topic: Architecture/ETL   Region: Other
- Question: Given a stream of ride requests for a service like Uber, compute the number of ride requests in each 15-minute tumbling window.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G33 Messenger video-call percentage
- Round: Onsite SQL   Topic: SQL   Region: Other
- Question: Calculate what percentage of Messenger users who were active yesterday made a video call.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G34 Dynamic SQL formatter
- Round: Onsite Python   Topic: Python   Region: Other
- Question: Write a function that dynamically formats a SQL query based on input parameters.
- Follow-ups: none
- Source: Aced guide — https://www.aced.io/guides/meta-data-engineer-interview — 2026 — guide
### G35 Aced question-bank generic coding items
- Round: n/s   Topic: Python   Region: Other
- Question (list): Edit distance; Reverse a linked list; Is this a valid palindrome?; Implement LRU Cache; Merge Intervals; Group anagrams; Valid Parentheses; Move all zeros to the end of an array.
- Follow-ups: none
- Source: Aced — https://www.aced.io/questions?company=meta-facebook&role=data-engineer — 2026 — guide (bank is not labelled first-hand; 20 of 55 shown)
### G36 Aced bank: PM-style and bookstore items
- Round: n/s   Topic: Product sense / metrics   Region: Other
- Question (list): "You're a PM at Facebook. How would you decide whether to remove the profile photo step from the onboarding experience?"; "Given a bookstore database schema, write SQL queries using joins and aggregations to answer questions about sales, inventory, and customer data".
- Follow-ups: none
- Source: Aced — https://www.aced.io/questions?company=meta-facebook&role=data-engineer — 2026 — guide

## Interview101 (https://www.interview101.com/interviews/meta/data-engineer) — "reported N times" counts unverified

### G37 7-day retention of first-time story posters
- Round: SQL   Topic: SQL   Region: Other
- Question: Write a query to calculate 7-day rolling retention for first-time story posters.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide
### G38 Posts with peak engagement then drop
- Round: SQL   Topic: SQL   Region: Other
- Question: Find posts with peak engagement in the first hour that then dropped below 10% of peak.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide
### G39 Cohort monthly message volume, power users
- Round: SQL   Topic: SQL   Region: Other
- Question: Identify user cohorts' monthly message volume progression with power-user tracking.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide
### G40 Session-length quartiles by country; impression trends
- Round: Python   Topic: Python   Region: Other
- Question: Create a DataFrame summary showing session length quartiles by country; identify pages with statistically significant upward impression trends.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide
### G41 Reels star schema; cross-platform model; ad auctions
- Round: Data modeling   Topic: Data modeling   Region: Other
- Question: Design a star schema for Instagram Reels with algorithm variants and SCDs; build a unified cross-platform model (Facebook, Instagram, WhatsApp); design an event-driven model for advertising auctions with time-travel queries.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide
### G42 Memory highlights feature
- Round: Product sense full stack   Topic: Product sense / metrics   Region: Other
- Question: Design a "memory highlights" feature: metrics, schema, ETL logic.
- Follow-ups: none
- Source: Interview101 — https://www.interview101.com/interviews/meta/data-engineer — 2026 — guide

## Interview Kickstart and Weekday

### G43 Authors with at least 5 books
- Round: Technical screen SQL   Topic: SQL   Region: Other
- Question: Identify authors who have published at least 5 books. The same page repeats R01, R03, R06, R07, R11 in near-identical form, so it likely copies the Blind/Medium report.
- Follow-ups: none
- Source: Interview Kickstart — https://interviewkickstart.com/blogs/articles/meta-data-engineer-interview — 2026 — guide
### G44 Product-sense prompts
- Round: Onsite product sense   Topic: Product sense / metrics   Region: Other
- Question (list): "How would you measure the success of Instagram Reels?"; "A drop in Facebook News Feed engagement is reported. What data would you look at first?"; "If WhatsApp launched a new group video feature, which metrics would you track to evaluate adoption and retention?"; "How would you design a dashboard for tracking DAU/WAU/MAU trends for Messenger?"
- Follow-ups: none
- Source: Interview Kickstart — https://interviewkickstart.com/blogs/articles/meta-data-engineer-interview — 2026 — guide
### G45 Bookstore multiple authors; ride-sharing schema
- Round: Onsite data modeling   Topic: Data modeling   Region: Other
- Question: "Design a schema for a ride-sharing app (facts, dimensions, PK/FK relationships)."; "How would you model books that can have multiple authors in a bookstore schema?"
- Follow-ups: none
- Source: Interview Kickstart — https://interviewkickstart.com/blogs/articles/meta-data-engineer-interview — 2026 — guide
### G46 Weekday generic list
- Round: n/s   Topic: SQL   Region: Other
- Question (list): second-highest salary from an Employees table; find all duplicates in a table; top 3 highest earning employees in each department; schema for a Twitter-like site; model for an online bookstore; ride-sharing data model. Weekday also lists reverse a string, cycle in a linked list, permutations and BST check, which are generic and not DE-specific.
- Follow-ups: none
- Source: Weekday — https://www.weekday.works/post/meta-data-engineer-interview-questions — 2025 — guide

## StrataScratch (https://www.stratascratch.com/blog/facebook-data-engineer-interview-questions) — curated by the site

### G47 StrataScratch curated titles
- Round: n/s   Topic: SQL   Region: Other
- Question (list of 16 titles): Find the maximum step reached for every feature; SMS Confirmations From Users; Users By Average Session Time; Acceptance Rate By Date; Spam Posts; Highest Energy Consumption; Successfully Sent Messages; Recommendation System; Cum Sum Energy Consumption; Find the number of processed and not-processed complaints of each type; Subpopulations; Comparing Performance of Engines; Are We Friends?; GROUP or ORDER BY; Friends You May Know; Views and Storage Space.
- Follow-ups: none
- Source: StrataScratch — https://www.stratascratch.com/blog/facebook-data-engineer-interview-questions — n/s — guide (page says curated, not candidate-reported)

## PracHub (https://prachub.com/companies/meta/positions/data-engineer)

### G48 PracHub card titles (20 of 48 shown)
- Round: n/s   Topic: Data modeling   Region: Other
- Question (titles only): Design a scalable dimensional model; Solve SQL and Python coding tasks; Tackle Python tasks under time pressure; Return top-3 content per category; Recommend two-hop follows in Python; Design batch and streaming ETL architecture; Analyze private-account product metrics; Find Values Owned Only by the Selected User.
- Follow-ups: none
- Source: PracHub — https://prachub.com/companies/meta/positions/data-engineer — 2026 — snippet-only (card titles; full text not visible)

Entry count: 48 (G01 to G48). List entries (G35, G36, G44, G46, G47, G48) each bundle several questions.
