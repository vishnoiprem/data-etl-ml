# Meta Data Engineer Interview Guide

Source: https://www.tryexponent.com/guides/meta-data-engineer-interview
Updated 2 months ago by Meta candidates
Written by Kevin Landucci, Subject Matter Expert

---

## Interview Process Overview

Meta's data engineer (DE) interview covers more ground than most data engineering loops. The technical screen has the highest pass bar candidates report in the process, and the onsite blends product sense, data modeling, SQL, and Python into every round — a format built to test range.

The loop moves through three stages over roughly **3-5 weeks**:

1. **Recruiter screen** — 30 min, background, motivation, prep handoff
2. **Technical screen** — 60 min in CoderPad (5 SQL + 5 Python), pass bar: 3 correct in each half
3. **Onsite loop** — 4 blended technical rounds + 1 standalone behavioral round

The loop is tightly standardized across teams. The distinctive pressure is **density**: the technical screen packs 10 questions into a single hour, and every onsite round layers four skill areas on top of each other.

---

## Stage 1: Recruiter Screen

A 30-minute call focused on fit, motivation, and logistics. Meta recruiters share official prep resources upfront.

**What interviewers look for:**
- Clarity on recent work (walk through current role + a recent project in under 5 minutes)
- Motivation for Meta (grounded in product, scale, or team — not brand)
- Role alignment (experience maps to DE competencies)
- Compensation fit
- Communication pace (the rest of the loop is built for speed)

**Recent questions:**
- Tell me about yourself.
- Walk me through your experience at your current company.
- Why Meta?
- Why data engineering?

---

## Stage 2: Technical Screen

60 minutes in CoderPad:
- ~5 min intros
- 25 min SQL (5 questions)
- 25 min Python (5 questions)
- Short wrap-up

**Pass bar:** at least 3 correct in each half.

The interviewer posts each question inline, you solve against a full suite of test cases, and you can ask clarifying questions at any point. Confirm your language preference with your recruiter a few days before the screen.

### What Interviewers Look For

- **Speed with precision** — quickly write working code that passes the full test suite
- **Reasoning out loud** — narrate your approach in real time
- **Clarifying questions** — confirm input shape, edge cases, and expected output before writing
- **Recovery under pressure** — how you respond when a test case fails or you're stuck
- **SQL and Python fluency** — move between the two without losing pacing

> Meta interviewers expect you to think out loud. Talking through your approach, asking syntax questions, and speaking up when stuck are all part of how the round is evaluated — not signs of weakness.

### SQL Preparation

Come in fluent with:
- Joins across multiple connected tables
- GROUP BY and HAVING
- Subqueries and CTEs
- Window functions (LAG, LEAD)
- Aggregations and CASE logic

**Sample SQL questions:**
1. Given a library schema with books, users, and a check-in/checkout table, find each user and the number of books they checked out but didn't return before the due date.
2. Given the same schema, find the number of users who checked out books in a specific category, grouped by age.
3. Find the number of people who checked out a book on the same day another person returned it.
4. From a transaction table, find the sum of total orders and the count of unique customers.
5. Find the number of users who called three or more people in the last week.

### Python Preparation

Come in fluent with:
- String and array manipulation
- Dictionary and hash table patterns
- File reading and writing
- Exception handling with try/except
- Basic sorting and list operations

**Sample Python questions:**
1. Given a list of strings, find the second letter of the first word in each string and return the character along with its count of occurrences.
2. Write a function that reads a `data.csv` file, processes it, and handles a file-not-found exception by outputting "file not found."
3. Given a dictionary of employees with their department and salary, find the second-highest salary in each department.
4. Join two lists and sort the result.
5. Remove items from a list based on a specific key.

> Some candidates connect with a second recruiter after clearing the technical screen to walk through the upcoming onsite loop format. Use that call to confirm schedule, ask about lunch/team time, and clear up pacing questions.

---

## Stage 3: Onsite Loop

Four hour-long technical rounds plus a behavioral round, typically completed in a single day.

Each technical round moves through **product sense → data modeling → SQL → Python**, with the case study changing from round to round. You might spend 10 min on product sense, pivot into data modeling for a schema that supports the product case, then close with SQL and Python tied to the same domain.

> Each round is scored independently. Consistency across rounds matters more than peak performance in one.

### Product Sense + Data Modeling (highest weight)

Data modeling carries the most weight in the onsite loop and is almost always introduced through a product sense prompt. Every technical round opens with a case study tied to a real-feeling product surface, and you spend the first stretch working through how the product functions, what metrics matter, and what user/business questions the data needs to answer before you touch a schema.

**Common product scenarios:**
- An Instagram metric that's dropping
- Ride-sharing service like Uber
- Ecommerce store
- Reddit-style notification system
- Movie theater ticketing platform

The product case anchors every technical choice that follows. Schema, relationships, and partitioning choices should ladder back to the product question the round opened with.

> Prepare for scale and performance trade-off follow-ups. Interviewers may push into how you'd partition a transactional table once it grows past 1 TB — round-robin vs. hash-based partitioning, bucketing by timestamp. Show you can reason about partitioning, indexing, and storage cost as a function of query pattern and data volume.

**What interviewers look for:**
- Product reasoning first — translate a product case into the data questions to answer
- Clarifying questions — pressure-test ambiguous requirements before committing
- Schema fluency — fact tables, dimensions, PKs/FKs, many-to-many relationships
- Scale trade-offs — partitioning, bucketing, indexing at production volumes
- ETL awareness — ingestion, transformation, load steps
- Design evolution — adapt the model when requirements shift mid-round

**Common mistakes to avoid:**
- Skipping clarifying questions before committing to a design
- Mixing up PK/FK or leaving relationships implicit
- Forgetting relationship tables for many-to-many joins
- Over-indexing on one layer of the architecture instead of sketching the full pipeline
- Saving trade-off explanations for the end instead of narrating as you design

**Sample questions:**
1. Design a data model for a ride-sharing app like Uber — table relationships, PK/FKs, partition strategy.
2. An Instagram metric is dropping — root-cause analysis approach + supporting data model.
3. Design a data model for an ecommerce store (products, orders, customers, inventory).
4. Design a notification system for a Reddit-style app (backend + data model).
5. Design a movie theater ticketing system — end-to-end data storage.

### SQL + Python in the Onsite

Prompts are more open-ended than the technical screen and embedded in the product/modeling case study, so they have business context and a narrower set of correct answers.

SQL pushes into **analytical territory** (funnel metrics, user-segment breakdowns, production-scale queries).
Python moves into **data processing, streaming patterns**, and logic tied back to the round's product case.

**What interviewers look for:**
- Business reasoning in the query — product question → right metric/filter/grouping
- Scale awareness — indexing, filter order, query cost
- Clean Python structure — readable and testable, especially embedded in a larger flow
- Streaming/windowing intuition — tumbling vs. sliding windows, late-arriving events
- Debugging out loud — respond well to pushback on correctness/efficiency

> Onsite Python often moves into streaming/pipeline territory. Be ready to reason about tumbling and sliding windows, late-arriving events, and production-volume behavior.

**Sample questions:**
1. Given a stream of ride requests, compute the number of requests in each 15-minute tumbling window.
2. Calculate what percentage of Messenger users active yesterday made a video call.
3. Write a function that dynamically formats a SQL query based on input parameters.

---

## Stage 4: Behavioral (Ownership Round)

30-minute standalone onsite session outside the blended technical rounds. Tests how you operate as a senior engineer: how you own outcomes, navigate friction, and pull impact out of ambiguous situations.

Meta interviewers want **structured, outcome-driven stories** — how you defined the problem, what you did, and what measurably changed. Be ready for them to dig into your specific role, trade-offs weighed, and how you'd approach the same situation now.

**What interviewers look for:**
- Retrospective clarity — describe your role precisely + what you'd change
- Cross-functional impact — stories that moved partners, teams, or product outcomes
- Handling friction — navigate disagreement without losing momentum
- Learning speed — pick up unfamiliar tools/systems/domains and deliver
- Communication discipline — pace stories tightly (rounds move quickly through multiple prompts)

**Sample questions:**
- Tell me about a time you led a project end-to-end.
- Tell me about a time you disagreed with your manager/team lead and how you resolved it.
- Tell me about a process you improved that had a measurable business impact.
- Tell me about a time you had to learn a new tool/system quickly and deliver results.

---

## Preparation Plan

1. **Practice 5+5 screen under real time pressure** — 25-min timer for 5 SQL, another 25 for 5 Python. Goal is consistent accuracy at pass-bar pace, not peak performance on one question.
2. **Clarify before you code** — read the prompt out loud, restate it, confirm input shape / edge cases / expected output before typing.
3. **Working solution first, then optimize** — get correctness on the board, then walk through what's expensive, what you'd index/partition, where it breaks at scale.
4. **Study data modeling through real product lenses** — use live consumer products as scenarios; cover fact/dim, PKs/FKs, many-to-many; practice adapting when requirements shift.
5. **Let product sense frame every data modeling prompt** — work through what the product does, what metrics define success, what questions the data must answer before drawing tables.
6. **Structure behavioral stories for speed** — under 5 min; lead with situation, walk through your actions, close with measurable outcome. Going over 5 min costs question volume.
7. **Run timed mock interviews** in the same format you'll face.

---

## Compensation (levels.fyi)

| Level | Total Comp |
|-------|------------|
| IC3   | ~$168K     |
| IC4   | ~$226K     |
| IC5   | ~$311K     |
| IC6   | ~$439K     |

---

## FAQs

**How long does the process take?** Roughly 3-5 weeks from recruiter screen to final decision.

**What makes it challenging?** Density — high pass bar on screen, four skills layered into every onsite round. Senior candidates cite time pressure as the most demanding element.

**What are common mistakes?** Skipping clarifying questions, over-engineering SQL when a simpler query works, ignoring scale trade-offs in data modeling, narrating only at the end instead of as you work, mixing up PKs/FKs, going over the 5-min behavioral cap.

---

## Additional Resources

- Meta interview question bank (Exponent)
- Meta company hub on Exponent
- Top SQL data engineering interview questions
- Data engineering interview course
- Meta DE onsite prep guide (PDF)
- Meta DE technical screen prep guide (PDF)
