# Behavioral Sub-Lesson 2 — Disagreement with a Stakeholder (the "I disagreed" family)

> **Disagreement is the FDE's daily work.** The FDE disagrees with the customer (about the spec), the manager (about the priority), the team (about the architecture), and the user (about the workflow). The interviewer is testing whether you can disagree AND ship. The candidate who disagrees but doesn't ship is signaling they can't close. The candidate who ships but never disagrees is signaling they don't have the judgment to push back.

---

## Why disagreement questions are the FDE signal

The 3 things the interviewer is testing:

1. **Can you disagree with conviction?** Did you have a position, or did you just go along?
2. **Can you disagree respectfully?** Did you push back without damaging the relationship?
3. **Can you ship after disagreeing?** Did the disagreement become the input to the design, or did it become a blocker?

**The FDE pattern:** disagree → acknowledge → offer → ship. The disagreement is the input; the shipping is the output.

**The 5-question cheat sheet (from the behavioral/README.md):**

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Disagreed with manager | Engagement 3: postmortem | 0 manual review steps added |
| 2. Disagreed with customer | Engagement 2: the pivot | 2 weeks saved |
| 3. Pushed back on a requirement | Engagement 1: Mei's "drafts per minute" | Thumbs-up rate replaces throughput |
| 4. Disagreed with your team | Engagement 6: the architecture review | 3 design decisions, 1 PR |
| 5. Disagreed with yourself | Engagement 9: the postmortem of a personal failure | 0 repeat incidents in 90 days |

**This sub-lesson dives into questions 1-3 (manager, customer, requirement).** Questions 4-5 are referenced; see the FDE case studies for the full write-ups.

---

## Question 1: "Tell me about a time you disagreed with your manager."

### The FDE-specific signal

The interviewer is testing 4 things:

1. **Did you have a position?** FDEs have opinions. Did you defend them, or did you just execute?
2. **Was your position grounded in data?** "I think X" is a junior answer. "The data shows Y" is the FDE answer.
3. **Did you ship after the disagreement?** Disagreement is the input; shipping is the output.
4. **Was your manager right in hindsight?** The FDE retrospects honestly.

### The PacificFreight answer (Engagement 3: the postmortem, the circuit breaker)

- **Situation:** PacificFreight's drafter had a week 11 SEV-1: a 10-minute OpenAI outage caused a hallucination spike. Mei reverted 4 drafts. My manager reviewed the postmortem and wanted to add a "manual review step" — every draft would be reviewed by a human before being sent.
- **Task:** Decide whether to add the manual review step.
- **Action:** I disagreed. The data showed: Mei sends 150 emails/day; manual review would add 30 seconds per email; that's 75 minutes/day of human time; Mei is the only CS person; she'd be reviewing drafts 2 hours/day instead of handling customers. I proposed an alternative: a circuit breaker that fails closed (returns a fallback response) when the OpenAI API is unhealthy. The breaker is 0 seconds of human time; the fallback is a templated reply that Mei can edit. My manager agreed.
- **Result:** 0 manual review steps added. The circuit breaker was deployed in 1 PR. Mei's throughput stayed at 150 emails/day. The 10-minute OpenAI outage 2 weeks later triggered the breaker, not the manual review.

**The metric is the closing line:** "0 manual review steps added. Mei's throughput stayed at 150 emails/day. The breaker is the scalpel; manual review is the sledgehammer."

### The 3 anti-patterns for this question

1. **"I disagreed but did what my manager said."** Without the alternative you proposed. Disagreeing without offering an alternative is junior.
2. **"I disagreed and won."** Without the data. "I won" is a red flag. FDEs don't win against managers; they find resolutions.
3. **"My manager was wrong."** Too blunt. The FDE diagnoses, then acknowledges the manager's concern, then offers an alternative. "My manager was wrong" is a relationship-damaging answer.

---

## Question 2: "Tell me about a time you disagreed with the customer."

### The FDE-specific signal

This question is the FDE-flavored version of question 1 in sub-lesson 1 (the "customer was wrong" question). The interviewer wants:

1. **A specific customer, a specific disagreement.** Not "I disagreed with the customer once." A real, named customer + a real, named disagreement.
2. **The data.** Why did you disagree? What did you measure that the customer didn't?
3. **The resolution.** Did the customer come around? Did the engagement survive?
4. **The retrospective.** Was the customer right in hindsight? (FDEs retrospect honestly.)

### The PacificFreight answer (Engagement 2: the legal-tech walkaway, the data audit)

- **Situation:** A legal-tech customer (a 30-person contract review firm) asked me to build a RAG system over 200K legal contracts. They said: "We have 2 weeks. Build the RAG." I disagreed.
- **Task:** Convince the customer that 2 weeks was unrealistic without damaging the relationship.
- **Action:** I ran a 1-day data audit. I found: (a) 30% of PDFs were unreadable without re-scanning, (b) 20% of DOCX had embedded images with no alt-text, (c) the labels were inconsistent (the same contract clause was labeled 5 different ways). I presented the data to the customer: "Your data isn't RAG-ready. I'd be shipping a system that hallucinates on 30% of queries. I can take the engagement in 6 weeks after the data is clean, or in 2 weeks if you accept 30% hallucination rate." The customer chose the 2-week option; I walked away.
- **Result:** 2 weeks saved. The customer came back 6 months later with a clean dataset. We shipped a working RAG system in 3 weeks. The customer said: "You were right to walk away. We would have blamed you for the hallucinations."

**The metric is the closing line:** "2 weeks saved, no hallucinations, and the customer came back 6 months later. The walkaway was the right call. The 30% hallucination rate was the data point that changed the customer's mind."

### The 3 anti-patterns for this question

1. **"I disagreed with the customer."** Without the data. "I disagreed" is a junior answer. The data is the FDE signal.
2. **"I told the customer they were wrong."** Too blunt. The FDE diagnoses, then presents the data, then offers alternatives. "I told them they were wrong" is a relationship-damaging answer.
3. **"The customer didn't listen."** Without the resolution. Did the engagement survive? Did the customer come back? The "no" is the input; the relationship management is the output.

---

## Question 3: "Tell me about a time you pushed back on a requirement."

### The FDE-specific signal

This question tests whether you can challenge the spec. FDEs push back when the requirement is wrong, vague, or measurable in a way that doesn't match the customer-facing outcome. The interviewer wants:

1. **A specific requirement, a specific pushback.** Not "I pushed back on a requirement once." A real, named requirement + a real, named pushback.
2. **The alternative.** What did you propose instead? FDEs don't just say no; they say "here's a better metric."
3. **The acceptance.** Did the customer accept the alternative? Did the engagement survive?
4. **The metric.** What was the before/after? How did the new metric measure the customer-facing outcome?

### The PacificFreight answer (Mei's "drafts per minute" requirement)

- **Situation:** PacificFreight's Mei asked for a "drafts per minute" metric for the drafter. She wanted to measure throughput: how many drafts per minute can the system produce?
- **Task:** Decide whether to ship the "drafts per minute" metric.
- **Action:** I pushed back. "Drafts per minute" measures throughput, not customer-facing outcome. Mei is a CS rep; she doesn't care how fast the system drafts; she cares whether the draft is good. I proposed "thumbs-up rate" instead: of the 150 drafts Mei sends per day, what % does she accept without edits? We measured it for 2 weeks: 71% baseline. We tuned the prompt + the retrieval. The thumbs-up rate went to 79% in 2 weeks.
- **Result:** Mei's thumbs-up rate went from 71% to 79% in 2 weeks. "Drafts per minute" would have been a vanity metric — it would have gone up as the system drafted faster, but the drafts would have been worse. The new metric measures the customer-facing outcome.

**The metric is the closing line:** "Thumbs-up rate went from 71% to 79% in 2 weeks. The new metric measures the customer-facing outcome. The old metric would have been a vanity metric."

### The 3 anti-patterns for this question

1. **"I pushed back on the requirement."** Without the alternative. FDEs don't just say no; they say "here's a better metric." The alternative is the FDE signal.
2. **"I changed the requirement."** Without the acceptance. Did the customer accept the change? Did they come around?
3. **"The requirement was wrong."** Without the data. Why was it wrong? What did you measure that the customer didn't?

---

## The 3-question cheat sheet (disagreement)

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Disagreed with manager | Engagement 3: postmortem (manual review vs circuit breaker) | 0 manual review steps added |
| 2. Disagreed with customer | Engagement 2: the legal-tech walkaway (2 weeks vs 6 weeks) | 2 weeks saved, customer came back in 6 months |
| 3. Pushed back on a requirement | Engagement 1: Mei's "drafts per minute" (throughput vs thumbs-up) | 71% → 79% thumbs-up in 2 weeks |

**Memorize these 3.** They're the answers to 80% of disagreement behavioral questions.

---

## How to use this sub-lesson

1. **Pick the most relevant story from the 3 above.** Use question 1 for the "disagreed with manager" prompt, etc.
2. **Practice the STAR format out loud.** 3-4 minutes per answer. Time yourself.
3. **Use the metric as the closing line.** "0 manual review steps" / "2 weeks saved" / "71% → 79%." The metric is the FDE signal.
4. **Rehearse with an AI assistant.** Have it score you on the 3 anti-patterns per question.
5. **Add your own stories.** The 3 above are PacificFreight examples. The candidate should have 1 story per question from their own experience.

---

## The cross-reference: how this maps to Phase 6

| Question | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Disagreed with manager | `../customer-simulation/README.md` (the 5 scenarios) | Disagree + ship + data |
| 2. Disagreed with customer | `../company-experiences/../README.md` (the "FDE walks away" pattern) | Judgment + data + relationship management |
| 3. Pushed back on a requirement | `../decomposition/README.md` (the 5 clarifying questions) | Diagnose before prescribing + alternative metric |

---

## The thesis

**Disagreement is the FDE's daily work.** The candidate who can disagree with conviction, with data, and with a path to shipping is showing they can do the work. The candidate who says "I worked with stakeholders" or "I usually agreed with my manager" is not.

**The 3 questions above are the answers to 80% of disagreement behavioral questions.** The 3 STAR answers (with the 3 closing-line metrics) are the muscle memory. Practice them out loud, time yourself at 3-4 minutes per answer, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Disagreement prep gets you past the customer-simulation round at AWS FDE, Anthropic, Sierra AI, and the "tell me about a time you disagreed" question at every FDE loop.**