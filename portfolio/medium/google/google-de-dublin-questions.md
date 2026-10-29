# Google Data Engineer (Dublin) — Interview Questions & Rounds (India → Ireland Experience)

> Source: "How I Cracked Google Data Engineer Interview | India to Ireland" — a candidate with ~10 years in data engineering (IBM Labs, Rakuten, Joom, Deliveroo) who applied from India and got an offer for Google Dublin. He applied multiple times before getting shortlisted. The interview was split into **six parts**. He couldn't give verbatim questions but described each round's content and difficulty precisely.

---

## SIX-PART STRUCTURE
1. Application + recruiter screening
2. SQL coding
3. Python coding (DSA)
4. Data modeling (+ more complex SQL)
5. Data architecture / system design (data-focused)
6. Googleyness / behavioral

> Note: order of SQL vs Python rounds varies; he describes the DSA/Python round first in detail, then SQL. Don't over-index on sequence.

---

## PART 1 — Application + Recruiter Screen
- Applied directly via Google careers; got shortlisted after a couple of months (after multiple past attempts that didn't).
- Call covered background, current role, skills alignment.
- **Plus a short technical screen:** a few **rapid-fire theoretical questions, mostly Python and SQL.** "Nothing too deep, but enough to understand whether I had the basics."
- Recruiter explained the full process and shared external Google prep resources.
- **His tip:** at this stage, ask the recruiter any questions about the role/process — they're happy to clarify the upcoming rounds.

---

## PART 2 — DSA / Python Round
- Choose your language (he used Python; recommends it as the most-used DE language).
- **Questions involved arrays and dictionaries**, and were **not straightforward** — he had to **convert the given data into a better-suited data structure**, with **multiple steps and conversions** to reach the solution.
- Asked to explain **time and space complexity** after solving.
- If your solution isn't optimal, **they may ask you to improve it.**
- **Difficulty: medium-to-hard LeetCode** — BUT "don't get confused with the word hard," because the **focus areas are limited to arrays, strings, dictionaries, numbers, and trees.**
- He **never prepared graph problems at a hard level.**
- Also know the **time/space complexity of the basic data structures.**

> Key behavior: think out loud — explain your plan first, then write the solution, then discuss complexity.

---

## PART 3 — SQL Round (the most critical; "no room for mistakes")
- Started with a **medium** problem on a given data model, then moved to **hard** problems.
- **Lots of edge cases** — if you miss one, the result is wrong.
- Involves **aggregations, joins, window functions**, and crucially **edge-case handling**.
- Key to the round: **accuracy and clarity.**
- **His tip:** discuss the approach FIRST, then write — so you don't write an answer and then scramble to fix edge cases.
- **Brush up on:** joins, aggregations, and **most importantly time-series analysis concepts in SQL.**

---

## PART 4 — Data Modeling (+ more complex SQL)
- **Design a data model first, then write SQL queries on top of it** for a given use case.
- The model must be **flexible enough to answer the business questions** they pose.
- **This round is all about your approach** — ask lots of clarifying questions: what the data represents, what the use cases are, how frequently the data changes, etc.
- **Don't jump into modeling immediately** — understand the domain first.
- While designing, **explain your thought process clearly**: why you chose a structure, how it scales, how it avoids redundancy.
- Then you're asked **business questions** to solve with SQL on your own model.
- **Practice:** star & snowflake schemas, fact & dimension tables, normalization vs denormalization, and **slowly changing dimensions.**

---

## PART 5 — Data Architecture / System Design (data-focused)
- **Goal: design a data pipeline handling both batch and real-time data** (depends on the use case given).
- Scenarios vary, but the **fundamental principles are constant: ingestion, storage, serving, and monitoring** — all included.
- **Know a variety of open-source AND cloud tools and where each fits** in the pipeline.
- This round **also includes SQL questions** (shorter than the dedicated SQL round).
- **Spark questions are mostly theoretical** — how Spark handles certain operations, common issues you've faced and how you solved them.
- Includes **past-project discussion** — so **list a few impactful projects beforehand** and be able to explain your **exact role, the technical decisions you made, and the business impact.**

---

## PART 6 — Googleyness / Behavioral
- Google places **a lot of importance** on this round.
- Assesses: how you collaborate, handle challenges, learn, and communicate; how you deal with ambiguity and difficult situations.
- Questions framed around **real scenarios**: a time you led something, resolved a conflict, took initiative, dealt with failure, or contributed to a team effort.
- **His advice:** focus on **authenticity.** Use STAR to structure if it helps, but **don't sound robotic** — be clear, honest, yourself. Show collaboration, curiosity, and a positive, inclusive attitude.

---

## AFTER THE ROUNDS
- Final decision goes through **multiple levels of review**; feedback took a few weeks.
- Offer call → offer, timelines, next steps.
- For the Dublin role: relocation + visa process (documentation, approvals, immigration partners) after accepting.

---

## HIS TOP TAKEAWAYS
1. **SQL is the most critical round** — medium→hard, edge-case heavy, no room for mistakes. Prep time-series SQL especially.
2. **DSA is medium→hard but narrow** — arrays, strings, dictionaries, numbers, trees. **Skip hard-level graphs.**
3. **Model-then-query** appears again — design flexibly, ask clarifying questions, explain trade-offs.
4. **System design = ingestion, storage, serving, monitoring** + batch & real-time + open-source/cloud tool fit.
5. **Spark questions here are theoretical** + experience-based ("issues you faced and how you solved them").
6. **Prepare impactful project stories** — your role, technical decisions, business impact.
7. **Behavioral: be authentic, not robotic.**
8. Overarching: **strong fundamentals, clear thought process, confident communication.**
