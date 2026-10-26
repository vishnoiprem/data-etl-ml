# Lesson 40 — Data Engineer Behavioral Question Taxonomy (40 mapped)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)
>
> **Purpose:** Grep this file before any interview. Each of the 40 questions in the standard bank is mapped to the lesson where the pattern is taught, the company-specific verbatim match (if any), and the worked-example scenario (if any).

---

## How to use this file

For every behavioral interview:

1. **5 minutes before** — read the loop structure for your target
   company (table below).
2. **Pick your 5 story stories** using `01_story_mining.md`. Cover
   at least one question from each of: project deep-dive, conflict,
   ambiguity, failure, learning.
3. **Run your 5 stories through** the lessons above — *every*
   story should cover 2+ questions in this taxonomy. The cap is
   *not* one-story-per-question; the cap is one-and-the-same story
   for 4-5 questions.

## The 40-question taxonomy

| # | Question | Lesson | Worked example | Company verbatim match |
|---|---|---|---|---|
| 1 | Why do you think we should not hire you? | `02_theory/` (signal-vs-noise) | — | All |
| 2 | Tell me about a time you made a mistake. | `01_fast_track/03_avoiding_downleveling` | — | All |
| 3 | Tell me about a time you disagreed with someone and how you resolved it. | `03_tactics/` (story categories) | — | All |
| 4 | Tell me about yourself. | `01_fast_track/02_introduction` | — | All |
| 5 | What is the project you are most proud of? | `06_de_project_deep_dive` | ride-share pipeline | All |
| 6 | Tell me about your past projects. | `06_de_project_deep_dive` | ride-share pipeline | All |
| 7 | What product that you led are you most proud of and why? | **`10_data_product_pride`** | ride-share funnel | All |
| 8 | Tell me about a decision you made based on your instincts. | **`07_decision_by_instinct`** | ride-share ETA pipeline | All |
| 9 | Tell me about a time you improved a complex process. | `03_tactics/05_tightening_delivery` | — | All |
| 10 | Why do you want to work at {company}? | `04_reverse_interview` | — | All |
| 11 | Tell me about a skill you recently learned. | `03_tactics/` (story categories) | — | All |
| 12 | Tell me about a time you had a conflict with your manager. | **`08_difficult_team_members`** | ride-share team | All |
| 13 | What types of team members do you find difficult? | **`08_difficult_team_members`** | ride-share team | All |
| 14 | Tell me about a relevant complex program you've managed. | **`09_complex_program_stakeholders`** | ride-share foundation | All |
| 15 | What are your weaknesses? | `02_theory/` (signal-vs-noise) | — | All |
| 16 | Tell me about a time you were wrong. What changed your mind? | **`14_being_wrong_humble_pivot`** | ride-share schema | **Google 2026** |
| 17 | Tell me about a project with unclear requirements. How did you scope it? | **`13_unclear_requirements_scoping`** | ride-share cost attribution | **Google 2026** |
| 18 | Describe a time you had to learn something new under time pressure. | `03_tactics/` | — | **Google 2026** |
| 19 | Tell me about a time you disagreed on a technical approach. | `03_tactics/` | — | **Google 2026** |
| 20 | Tell me about a time you had to learn something quickly. | `03_tactics/` | — | All |
| 21 | How do you approach personal growth and learning? | `02_theory/` | — | All |
| 22 | How do you encourage cross-functional collaboration? | `04_reverse_interview` | — | All |
| 23 | Talk me through your work experience in the past year. | `01_fast_track/02_introduction` | — | All |
| 24 | What other companies are you interviewing at and why? | `04_reverse_interview` | — | All |
| 25 | Tell me about your experience. | `01_fast_track/02_introduction` | — | All |
| 26 | Tell me about a system you are currently working on. | `06_de_project_deep_dive` | ride-share pipeline | All |
| 27 | Tell me about a time you optimized a team's workflow. | `03_tactics/` | — | All |
| 28 | How will you develop yourself professionally as a DE? | `02_theory/` | — | All |
| 29 | PM at a food app, conversion dropped. How do you investigate? | **`12_product_sense_investigation`** | ride-share pickup metric | **Meta 2026** (product-sense) |
| 30 | How do you influence without authority? | **`11_influence_without_authority`** | ride-share data contract | All |
| 31 | What parts of {company}'s mission resonate with you? | `04_reverse_interview` | — | All |
| 32 | What excites you most about technology? | `02_theory/` | — | All |
| 33 | Tell me about a time you led a project end-to-end. | `06_de_project_deep_dive` | ride-share pipeline | **Meta 2026** |
| 34 | Tell me about a process you improved that had measurable business impact. | `03_tactics/` | — | **Meta 2026** |
| 35 | Tell me about a time you disagreed with your manager and how you resolved it. | `08_difficult_team_members` | ride-share team | **Meta 2026** |
| 36 | Tell me about a time you had to learn a new tool or system quickly. | `03_tactics/` | — | **Meta 2026** |
| 37 | Tell me about a time you made a mistake and what you learned. | `01_fast_track/03_avoiding_downleveling` | — | All |
| 38 | Why did you become an engineer? | `02_theory/` | — | All |
| 39 | Walk me through your experience at your current company. | `01_fast_track/02_introduction` | — | **Meta 2026** |
| 40 | Why data engineering? | `04_reverse_interview` | — | **Meta 2026** |

**Bold lessons** are the 8 new lessons in this batch (`07`-`14`).
They cover the gaps the canonical 40-question bank and the 2026
Google/Meta DE guides revealed.

## Company loop structures (2026)

### Meta Data Engineer (Aced 2026, DataDriven Sept 2026, Interview101 2026)

| Stage | Duration | Format |
|---|---|---|
| Recruiter screen | 30 min | Non-technical. "How much data? What tools? Why Meta?" |
| Technical phone screen | 60 min, CoderPad | **5 SQL + 5 Python. Pass bar 3/5 in each half.** |
| Onsite: SQL/coding | 45-60 min | Funnel/cohort/time-series + Python. **No DSA.** |
| Onsite: data modeling | 45-60 min | **Dedicated round. Star schema, SCD2, bridge tables, partitioning.** |
| Onsite: product sense + full-stack | 60 min | "Product goal → metric → schema → ETL SQL." |
| Onsite: Ownership | 30 min | Meta Core Values (Move Fast, Be Bold, Be Open, Build Social Value, Focus on Long-Term Impact). |

**Total**: **3-5 weeks.** **L5 = Senior DE.** IC5 base ~$311K (per levels.fyi 2026).

### Google Data Engineer (Datavidhya May 2026, Interview101 2026)

| Stage | Duration | Format |
|---|---|---|
| Recruiter screen | 30 min | Phone. |
| Phone screen 1 | 45 min | SQL + light coding. |
| Phone screen 2 (optional, senior+) | 45 min | Borderline or senior candidates. |
| Onsite 1: Algorithm coding | 45 min | Medium LeetCode. |
| Onsite 2: Data System Design | 45 min | YouTube watch time, search analytics, ad targeting. |
| Onsite 3: SQL & Data Modeling | 45 min | BigQuery nested/repeated, SCD, partition/cluster. |
| Onsite 4: Googleyness & Leadership | 45 min | 30% of overall eval. |
| Hiring Committee | 2-4 weeks | You don't meet them. They read packets. |
| Team matching | 1-4 weeks | After the loop. |
| Offer & comp | 1 week | Comp committee. |

**Total**: **6-12 weeks.** **L5 base $195K-$240K, Yr-1 RSU $130K-$250K, Yr-1 TC $365K-$550K** (Datavidhya 2026).

## Sources (latest to oldest)

1. **Aced.io (2026)** — Meta DE full loop, verbatim Ownership questions, pass-bar 3/5.
2. **DataDriven.io (Sept 2026)** — Meta architecture examples (ad metrics, content moderation, cross-platform).
3. **Interview101.com (2026)** — Meta 5+5 SQL+Python, Google pivot-under-constraint.
4. **Datavidhya (May 2026)** — Google full loop with HC, Googleyness pillars, L5 comp.
5. **Tryexponent.com / aced.io (2026)** — Meta product sense + ownership examples.
6. **Glassdoor (Meta 2026)** — 5-round loop reports.
7. **(Older 2024-2025)** — covered in `02_theory/` and `03_tactics/` already.

## Your pre-interview checklist

- [ ] Read the **company-specific loop structure** above for your target.
- [ ] Have **5 stories** mined from the last 2 years (use `01_story_mining.md`).
- [ ] Each story covers **2+ questions** from the table above.
- [ ] Each story is **2-3 minutes** (Google) or **3-5 minutes** (Meta).
- [ ] Each story has a **number**: dollars, percent, count, time-saved.
- [ ] Each story has a **"so what"** — never end at "and then we shipped."
- [ ] You can deliver each story **out loud** in 90 seconds without notes.
- [ ] You have **2 stories for the "wrong / pivot" beat** (Google #1 signal).
- [ ] You have **1 instinct-decision story** (Datavidhya 2026).
- [ ] You have **1 scoping story** for unclear requirements (Datavidhya 2026).

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
