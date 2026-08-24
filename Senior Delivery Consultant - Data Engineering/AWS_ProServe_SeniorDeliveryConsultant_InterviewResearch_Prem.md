# AWS Professional Services — Senior Delivery Consultant, Data Engineering
## Worldwide Interview Question Research (Latest First) + Prep Notes
### Prem Vishnoi | Job ID 10471887 | AWS Singapore Pte Ltd

---

## First — why this round is actually a better fit than the sales one

This is a **hands-on technical delivery role**, not a quota-carrying sales seat. You design and build AWS solutions directly with customers — architecture, migration, implementation. There's no sales gap to bridge here. Your Makro, Lazada, SCB, and internal GenAI assistant stories aren't a bridge to something you haven't done — they ARE the job.

Two things from the JD worth flagging before we go further:

1. **This req is public-sector-facing** ("especially in public sector cloud environments") and **requires the ability to obtain Singapore government security clearance.** That's new — it didn't come up in the sales round. Worth asking the recruiter early what that process/timeline looks like and what it requires of you, so there are no surprises.
2. The JD explicitly wants ML/Data Analytics workshop-leading experience alongside core data engineering — so your GenAI assistant story and dynamic pricing model both belong front and center here, not just the lakehouse story.

---

## Honest caveat on data availability

AWS ProServe/Delivery Consultant interview reports are thinner online than for roles like SDE or Solutions Architect — Glassdoor shows only 3 reviews under "Delivery Consultant" and 2 under "AWS ProServe Consultant" globally. I widened the search across Glassdoor, Indeed, Blind, and Fishbowl, and across adjacent Delivery Consultant specializations (GenAI/ML, Security, App Dev, Data Analytics) since they share the same ProServe hiring process. No Singapore-specific report surfaced — the closest regional data point is Manila. Treat the pattern below as directionally reliable, not exhaustive.

---

## Reported experiences, most recent first

**Feb 2026 — Manila, Philippines — "Delivery Consultant" (Glassdoor)**
Candidate went through 8 interviews total, described as difficult but rewarding. Emphasis was on grounding every answer in an Amazon Leadership Principle, with questions blending technical and business perspective in the same conversation.

**Early 2026 — Blind thread, ProServe loop for an App Dev-track role**
A candidate prepping for a loop the next day was told by a commenter to expect questions spanning ML, SQL, big data, DevOps, and distributed systems — i.e., broad technical breadth rather than one deep specialty.

**Dec 2025 — "Delivery Consultant" (Glassdoor)**
Process: recruiter screen, then a Technical & System Design round with a Senior Data Scientist that emphasized ownership and Infrastructure-as-Code, then two further rounds. The core question was to walk through a past project end-to-end — from ingestion through to delivery — in your own words.

**Oct 2025 — Seattle, WA — "Delivery Consultant" (Glassdoor)**
First round combined a coding question with behavioral questions. A recurring technical thread was CI/CD process — how you build, test, and deploy pipelines.

**Jul 2025 — Blind, GenAI/ML Delivery Consultant phone screen prep thread**
A candidate outlined the expected structure: ML deployment/monitoring/scaling (latency, throughput, batch vs. real-time), GenAI and LLM fundamentals (embeddings, fine-tuning, agent frameworks), end-to-end system architecture on AWS, an optimization-style coding round, and consulting-style stakeholder-alignment questions. Useful even for the Data Engineering track since AI/ML delivery increasingly sits inside the same practice.

**Jun 2025 — Dulles, VA — "Delivery Consultant" (Glassdoor)**
Multi-stage loop with several interviewers of varying difficulty. Mix of STAR-format Leadership Principle questions and technical deep dives.

**2025 (undated in-thread) — Blind, Delivery Consultant (Security) role**
Candidate referenced a final loop coming up for this specialization — confirms the same "phone screen → final loop" shape holds across specializations, not just Data Engineering.

**Recent (undated) — Blind, Senior/L6-level ProServe loop**
Recruiter call, then a phone interview, then a final loop with five interviewers. The candidate reported the loop was almost entirely about Leadership Principle evidence — few if any direct skills questions — and they were ultimately rejected on the grounds of "not enough data to make a decision." Worth taking seriously: the lesson is to bring more than one strong story per principle, since five separate interviewers may each probe a different angle of the same principle.

**Recent (undated) — Blind, Associate/L4 Cloud Consultant, App Dev**
Online assessment, then a phone screen (one medium-difficulty LeetCode-style problem plus three Leadership Principle questions with follow-ups), then a final loop of 5–7 hours with no coding questions in that final stage — it shifted fully to architecture, technical depth, and behavioral rounds.

---

## Older reports (structure still broadly consistent)

**2022 — "Amazon Professional Services Consultant" (Glassdoor)**
Technical rounds leaned on DBMS, operating systems, and networking fundamentals. One reviewer described a single hour containing 4 SQL questions, 3 Python questions, and 7 statistics questions. The online assessment blended a personality-style behavioral test with database/CS-basics technical questions.

**Aug 2021 — Chicago, IL — "AWS ProServe Consultant" (Glassdoor)**
Structure: online coding exam, then a one-hour combined behavioral + technical interview with a ProServe consultant, then a final five-hour panel spanning architecture, behavioral, and application design. Reported fundamentals-level questions included explaining HTTP, API versioning, and n-tier architecture — a reminder that even senior loops sometimes sanity-check basics.

**2020 — Fishbowl, AWS Professional Services Solutions Architect loop**
Described as less about raw technical skill and more about how well you defend your reasoning under Leadership-Principle-style "dive deep" questioning — interviewers pushed hard on specifics, occasionally down to oddly granular technical trivia. A prepared solution-architecture presentation was part of the final onsite. Some interviewers were reported as visibly disengaged — a reminder not to read too much into interviewer body language.

---

## What this adds up to: the likely shape of YOUR loop

Synthesizing across all of the above (this is inference, not a confirmed AWS-published process):

1. **Recruiter screen** — logistics, level, comp range, which Leadership Principles the loop will emphasize (ask for this explicitly — Amazon recruiters are usually transparent if you ask).
2. **Possible online/technical assessment** — sometimes skipped for senior, experienced hires; if present, expect SQL/Python/data-fundamentals style questions rather than pure algorithmic LeetCode.
3. **Technical/hiring-manager round** — a past-project walkthrough end-to-end (ingestion → processing → storage → consumption is the exact framing that recurs across multiple reports), plus architecture reasoning.
4. **Final loop** (reports range 5–7 hours across several separate interviews) — a mix of:
   - Leadership Principle behavioral interviews (STAR format, multiple interviewers, each probing different principles)
   - A technical deep-dive / system design conversation, likely including a whiteboard or presented architecture
   - A Bar Raiser round — behavioral plus some functional questions, focused on long-term potential and whether you clear the bar versus current employees at your level
   - Possibly a prepared presentation of a past architecture or solution

---

## Technical topics to actually prepare (job req + every report combined)

- **Data lake / lakehouse:** S3, Lake Formation, Glue (ETL + Data Catalog), Iceberg, schema evolution
- **Big data processing:** EMR, Spark, Athena, Redshift (and Redshift Spectrum)
- **Streaming:** Kinesis, MSK/Kafka — when to justify streaming vs. batch
- **IaC & automation:** Terraform, CloudFormation, Python scripting (explicitly preferred in the JD)
- **Migration patterns:** legacy database → Aurora/Redshift, on-prem Hadoop → EMR/S3
- **Security & compliance:** IAM, encryption, HIPAA/GDPR-style frameworks — emphasized because this req is public-sector
- **CI/CD for data pipelines** — came up directly in the Oct 2025 report
- **Fundamentals** — HTTP, API versioning, n-tier architecture still get asked even at senior level, so don't skip the basics review

---

## Leadership Principles most likely emphasized

Given the JD's language ("trusted advisor," "public sector," "leading the implementation process," "managing risks"): **Customer Obsession, Ownership, Dive Deep, Insist on the Highest Standards, Earn Trust, Deliver Results.** This is the same core set from your AWS Sales prep — no new story-building required, just re-angle the delivery.

---

## What carries straight over from your existing prep

| Your story | Where it lands here |
|---|---|
| Makro lakehouse (5 days → 2 hrs, 10B+ rows/day) | Your system design / architecture answer — literally the "walk me through a project end-to-end" question multiple reports describe |
| SCB AML (15+ countries, MAS compliance) | Dive Deep + Insist on Highest Standards + directly relevant to the public-sector/compliance angle of this req |
| Internal GenAI assistant | Strong if the loop touches ML/GenAI delivery at all — several reports show this blending into Data Engineering DC loops |
| Org scaling 8→30, $3M budget | Ownership + Deliver Results |
| Dynamic pricing model | Earn Trust — same influence-without-authority story, still works |
| Your AWS service mapping (S3/Glue/Lake Formation/Redshift/SageMaker Lakehouse) from the sales prep | Directly reusable — and now you're expected to have actually built it, which you have, so this plays as strength, not something to sell |

---

## Questions worth asking them

1. What does the security clearance process actually involve from here, and what's the typical timeline?
2. What's the split between public sector and commercial engagements in the ASEAN Data Engineering practice?
3. What does a typical engagement look like — team size, duration, and how much is hands-on building vs. advisory?
4. How is success measured for a Delivery Consultant, and how is that different from a Solutions Architect at AWS?
5. What's the path from Delivery Consultant into more senior or practice-lead roles?

---

## One neutral data point worth knowing, not worrying about

A couple of anonymous Blind commenters described ProServe's internal reputation as less organized than other AWS orgs, with complaints about non-billable time and org churn. That's a handful of anecdotes, not a verified picture — but worth a couple of direct questions to your recruiter or future manager about team stability and how billable/non-billable time is structured, so you're deciding with real information rather than guessing.
