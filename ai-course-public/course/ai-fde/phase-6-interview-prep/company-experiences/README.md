# Module 10 — Real Interview Experiences (what candidates actually saw)

> **The 9 modules in Phase 6 prep you for the 8 interview rounds. This module shows you what the rounds actually look like at specific companies.** Each entry is a real candidate report (with the source attribution), distilled into the 4 questions every FDE candidate cares about: (1) what was the loop? (2) what was the take-home / case study? (3) what did they test? (4) what would the candidate do differently?

---

## Why this module exists

The 9 modules in Phase 6 are general. The reality is: **every company tweaks the loop.** OpenAI's FDE loop is a 1-week take-home + a 1-hour case-study walkthrough + an AI-enabled LeetCode screen. Palantir's loop is decomposition-heavy (the 5 questions, 60 min each). AWS FDE is 5-6 rounds including a customer simulation. Anthropic is 4-5 rounds with a GenAI depth round. **Reading the real reports is the difference between generic prep and company-specific prep.**

The signal in each report: **what the candidate would do differently.** That's the lesson.

---

## The 5 questions every report answers

1. **What was the loop?** (number of rounds, length, who you talked to)
2. **What was the take-home / case study?** (the prompt, the time budget, the deliverables)
3. **What did they test?** (the rubric, the signals, the anti-patterns)
4. **What would the candidate do differently?** (the lesson, distilled)
5. **What's the Phase 6 module that preps it?** (the cross-reference)

## The 5 most useful companies to prep for

Based on the reports in this module, the 5 most useful FDE loops to understand are:

1. **Palantir** — invented the FDE loop. If you can pass Palantir, you can pass any FDE loop. The 4-step framework (Clarify → Decompose → Design → Tradeoffs) is the spine. AI is prohibited; behavioral is embedded in every round.
2. **OpenAI** — the take-home is "basically the job." The AI-enabled coding screen is the new norm. Customer-facing explanation is the differentiator.
3. **Anthropic** — the customer simulation is the highest-signal round. Constitutional AI + Responsible Scaling Policy are testable depth signals. Reference checks happen during the cycle.
4. **AWS FDE** — 6 rounds with a dedicated customer scenario round. The Well-Architected Framework (6 pillars) is the AWS-specific depth signal. Defend the simplest design that meets constraints.
5. **LangChain / Sierra AI / Rippling / startups** — take-home-first loops. Sierra's "interviewers run your code before the demo" is the unique differentiator. LangChain's "interview is the job" is the founding-FDE pattern. The 4-step framework + a project deep dive is enough.

**Read at least 3 reports before your loop.** General prep gets you past the resume screen. Company-specific prep gets you past the onsite.

## The 6 most useful FDE signature rounds to prep for

Beyond the 5 most useful companies, the 6 most useful FDE signature rounds to understand are:

1. **Decomposition (Palantir)** — the signature round. The 4-step framework is the spine. Practice out loud.
2. **Take-home demo walkthrough (Sierra AI / LangChain)** — the centerpiece. The eval set is the differentiator.
3. **Customer simulation (AWS FDE / Anthropic)** — the highest-signal round at AWS FDE. Calm under pressure + no overpromising + trade-off explanation.
4. **Constitutional AI / safety depth (Anthropic)** — the disqualifier round. Read the Constitutional AI paper + the Responsible Scaling Policy.
5. **AI-enabled coding screen (OpenAI)** — the new norm. Plan, prompt, and verify — not just the final answer.
6. **Well-Architected Framework system design (AWS FDE)** — the 6 pillars (security / reliability / cost / performance / operational excellence / sustainability) are the testable depth signal.

**Each report in this directory maps to one or more of these signature rounds.** A complete FDE prep covers all 6.

---

## The company-specific reports (1 file per report)

| File | Company | Loop | Lesson |
|---|---|---|---|
| `openai-semantic-search.md` | OpenAI | 1-week take-home + 1-hr case-study + AI-enabled LeetCode | "Don't over-index on hard LeetCode. Practice explaining technical choices in plain English, especially customer-facing." |
| `palantir-fde-decomposition.md` | Palantir | 4 stages: recruiter + technical screen + 3-of-5 onsite (decomposition, learning, coding, re-engineering, system design) + hiring manager | "Practice decomposition out loud. AI is prohibited. Behavioral is embedded in every round." |
| `langchain-deployed-engineer.md` | LangChain | 3 stages: recruiter + 20-min product presentation + build-an-agent take-home with a Slack channel | "The interview is the job. Use every resource they give you (Academy, docs, Slack). Cover ALL product benefits. Be receptive to feedback without ego." |
| `anthropic-fde-customer-simulation.md` | Anthropic | 5 stages: recruiter + tech screen + **customer simulation** (signature) + take-home + system design + HM | "Customer simulation is the highest-signal round. Read Constitutional AI + Responsible Scaling Policy. Reference checks happen during the cycle." |
| `aws-fde-customer-simulation.md` | AWS FDE | 6 rounds: recruiter + phone screen + take-home + coding + system design + **customer scenario** (signature) | "Customer scenario filters the most candidates. Read the Well-Architected Framework (6 pillars). Defend the simplest design that meets constraints." |
| `sierra-ai-agent-engineer.md` | Sierra AI | 5 stages: recruiter + **1-week take-home** (centerpiece) + demo walkthrough + customer simulation + HM | "Interviewers run your code before the demo. Demo in 5-10 min, then defend the choices. Eval set is the differentiator." |

**Add a new file per real report you find.** The pattern: copy this README's structure, fill in the 5 questions, link back to the Phase 6 module that preps each round.

---

## How to use this module

1. **Pick your target company.** Read that company's report first.
2. **Read the Phase 6 module that matches each round.** The cross-reference in the report tells you which module to study.
3. **Rehearse the take-home prompt.** The OpenAI semantic-search take-home is in `../take-home/01-prototype.md`; the Labelbox RLHF take-home is in `../take-home/02-pipeline.md`.
4. **Practice explaining choices in plain English.** The OpenAI candidate's #1 tip: "I would spend way more time practicing how to explain technical choices in plain English, especially in a customer-facing context."
5. **Add new reports as you find them.** Each report is a `.md` in this directory. The pattern is the 5 questions above.

---

## The thesis

The 9 modules teach the framework. The 10th module shows you what the framework looks like in the wild. **Reading 3-5 real reports is the difference between "I prepped for FDE interviews" and "I prepped for OpenAI FDE interviews."**

**General prep gets you past the resume screen. Company-specific prep gets you past the onsite.**
