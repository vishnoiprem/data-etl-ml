# Behavioral Sub-Lesson 1 — Customer Interaction (the "difficult customer" family)

> **This is the highest-frequency FDE behavioral question.** Every loop has at least 2-3 customer-interaction questions. The signal: a candidate who names a real customer, a real disagreement, and a real resolution is showing they can survive the customer room. The candidate who says "I worked with stakeholders" is signaling they can't.

---

## Why customer-interaction questions are the FDE signal

FDEs spend ~30-40% of the week in customer rooms (per the [awesome-generative-ai-guide FDE README](https://github.com/aishwaryanr/awesome-generative-ai-guide/blob/main/interview_prep/roles/forward-deployed-engineer/README.md)). The interviewer is testing whether you can:

1. **Diagnose before prescribing.** Don't jump to a solution. Ask 3-5 questions first.
2. **Acknowledge before pushing back.** Don't start with "you're wrong." Start with "I understand."
3. **Find a resolution, not a win.** FDEs don't win against customers. They find resolutions that respect both the customer's constraint and the system's constraint.
4. **Own the result, not just the action.** The metric is the closing line.

**The 5-question cheat sheet (from the behavioral/README.md):**

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Difficult customer | Engagement 8: cost ceiling breach | $4.09/month |
| 2. Said no to the customer | Engagement 2: the pivot | 2 weeks saved |
| 3. Disagreed with manager | Engagement 3: postmortem | 0 manual review steps added |
| 4. Spec was unclear | Engagement 1: eval set as spec | 30-row eval set in week 1 |
| 5. Made myself unnecessary | Engagement 10: principal handoff | 3 next FDEs, 10/10 at 90 days |

**This sub-lesson dives into question 1 (difficult customer) + the 3 variants.** Questions 2-5 are in sub-lessons 2, 3, 4, and the behavioral README.

---

## Question 1: "Tell me about a time you handled a difficult customer."

### The FDE-specific signal

The interviewer is testing 4 things:

1. **Can you read the room?** Did you understand the customer's underlying concern (not just the surface complaint)?
2. **Can you find a resolution?** Did you propose 2-3 options, or did you push one solution?
3. **Can you own the result?** Did you stay accountable after the resolution, or did you hand off?
4. **Can you name a metric?** Did you close with a number?

### The STAR template (FDE-flavored)

- **Situation (1-2 sentences):** Name the customer (real or composite), the engagement, the timeline, the surface complaint.
- **Task (1 sentence):** What you had to do.
- **Action (3-5 sentences):** What you actually did, with specifics (the diagnosis, the options, the resolution, the handoff).
- **Result (1-2 sentences):** The outcome, with a metric (the closing line).

### The PacificFreight answer (Engagement 8: cost ceiling breach)

- **Situation:** PacificFreight's CS team (12 people) was using the drafter at 150 emails/day. By week 8, the bill was $25/week, 5× over the $5/month ceiling. Sarah (the CFO) escalated to Daniel (the IT lead) and demanded the system be shut down. Daniel came to me, not as a request but as a complaint.
- **Task:** Bring the bill under $5/month without breaking Mei's 79%+ thumbs-up rate, and without losing Daniel's trust.
- **Action:** I ran a 3-week fix. Week 1: emergency throttle (tightened the rate limiter from 60 req/min to 20 req/min per user, disabled the SLM for the e-commerce tenant). Week 2: multi-tenant split (separated the e-commerce customer's usage into its own Redis namespace + its own rate-limit budget). Week 3: SLM at 90% routing (the fine-tuned Qwen-1.5B handled 90% of drafts, GPT-4o-mini handled the other 10% — the long-tail queries that needed the bigger model). The fix combined all 4 Phase 5 projects.
- **Result:** Final bill: $4.09/month, under the $5/month ceiling. Mei's thumbs-up rate stayed at 79%+. Daniel said: "I was ready to kill the project; you gave me a YAML I could defend in front of Sarah." The fix was 3 design decisions, 2 PRs, 0 customer-facing downtime.

**The metric is the closing line:** "$4.09/month, under the ceiling. Mei's thumbs-up rate stayed at 79%+. 0 customer-facing downtime."

### The 3 anti-patterns for this question

1. **"I just listened to the customer."** Listening is necessary but not sufficient. The interviewer wants the resolution.
2. **"I escalated to my manager."** Escalation is sometimes right, but the FDE owns the result. "I escalated" is a red flag unless you can name what you did AFTER the escalation.
3. **"The customer was unreasonable."** Don't blame the customer. The FDE finds a way to make it work. If the customer was truly unreasonable, the answer is "I said no and walked away" (see question 2, sub-lesson 2).

---

## Question 2: "Tell me about a time the customer was wrong."

### The FDE-specific signal

This question tests whether you can push back on a customer without damaging the relationship. The interviewer wants:

1. **A specific customer, a specific wrong belief.** Not "I disagreed with the customer once." A real, named customer + a real, named wrong belief.
2. **The diagnosis.** Why was the customer wrong? What data did you have that they didn't?
3. **The respectful pushback.** How did you tell them they were wrong without making them feel stupid?
4. **The resolution.** How did you bring them around? What changed their mind?

### The PacificFreight answer (Mei's "always include the customer's name" request)

- **Situation:** PacificFreight's CS team was using the drafter. Mei asked me to make the system "always include the customer's name in the email." I pushed back.
- **Task:** Convince Mei that "customer's name" was the wrong metric without making her feel dismissed.
- **Action:** I asked Mei: "Whose name? The CS rep's name or the end customer's name?" Mei paused. I explained: "Your customers are CS teams. The end customer is the person on the other side of the email — they don't know the CS rep's name. The CS rep needs to know the end customer's name to write a personal response. If we always include the CS rep's name, the email reads like a template." Mei thought for 5 minutes. We changed the spec: "include the CS rep's first name in the signature, not the end customer's name."
- **Result:** Mei sent 150 emails/day through the drafter with the new spec. Her thumbs-up rate went from 71% to 79% in 2 weeks. The wrong-metric problem was caught in week 2 instead of week 8.

**The metric is the closing line:** "Thumbs-up rate went from 71% to 79% in 2 weeks. The wrong metric was caught in week 2 instead of week 8."

### The 3 anti-patterns for this question

1. **"The customer was wrong about X."** Without the diagnosis. Why were they wrong? What did you know?
2. **"I just did what the customer said."** This is the FDE failure mode. The FDE pushes back when the customer is wrong. "I just did what they said" is a junior answer.
3. **"I told the customer they were wrong."** Too blunt. The FDE diagnoses, then acknowledges, then offers alternatives. "I told them they were wrong" is a relationship-damaging answer.

---

## Question 3: "Tell me about a time you said no to the customer."

### The FDE-specific signal

This question tests your judgment. FDEs say yes to most things; they say no to the few things that would damage the customer, the system, or the engagement. The interviewer wants:

1. **A specific "no."** Not "I usually say yes." A real engagement where you said no.
2. **The reasoning.** Why did you say no? What was the cost of saying yes?
3. **The relationship management.** How did the customer react? Did they come back? Did the engagement survive?
4. **The metric.** What was the cost of saying no? Was it the right call in hindsight?

### The PacificFreight answer (Engagement 2: the pivot, the legal-tech walkaway)

This answer is a composite — it's a different customer than the drafter, but it's the most memorable "I said no" story. See `case-studies/engagement-2-pivot.md` for the full write-up. The short version:

- **Situation:** A legal-tech customer (a 30-person contract review firm) asked me to build a RAG system over 200K legal contracts. The contracts were in 3 inconsistent formats (PDF scans with OCR errors, DOCX with embedded images, plain text with formatting issues). The customer said: "We have 2 weeks. Build the RAG."
- **Task:** Decide whether to take the engagement.
- **Action:** I ran a 1-day data audit. I found: (a) 30% of PDFs were unreadable without re-scanning, (b) 20% of DOCX had embedded images with no alt-text, (c) the labels were inconsistent (the same contract clause was labeled 5 different ways across the corpus). I told the customer: "Your data isn't RAG-ready. I'd be shipping a system that hallucinates on 30% of queries. I won't take this engagement until the data is clean." I walked away.
- **Result:** 2 weeks saved. The customer came back 6 months later with a clean dataset. We shipped a working RAG system in 3 weeks. The customer said: "You were right to walk away. We would have blamed you for the hallucinations."

**The metric is the closing line:** "2 weeks saved, no hallucinations, and the customer came back 6 months later with a clean dataset. The walkaway was the right call."

### The 3 anti-patterns for this question

1. **"I said no because it was a bad idea."** Without the data. Why was it a bad idea? What did you measure?
2. **"I said no and the customer was upset."** Without the resolution. Did the customer come back? Did the engagement survive? The "no" is the input; the relationship management is the output.
3. **"I never say no."** This is a red flag. FDEs say no when the engagement is doomed. "I never say no" means the candidate doesn't have the judgment to know when to walk away.

---

## Question 4: "Tell me about a time you said yes to the customer when you wanted to say no."

### The FDE-specific signal

This question tests your flexibility. FDEs say yes to most things; they say yes even when they think the customer is wrong, as long as the cost of saying yes is bounded. The interviewer wants:

1. **A specific "yes" that felt risky.** Not "I always say yes." A real engagement where you wanted to say no.
2. **The reasoning.** Why did you say yes? What was the bounded cost? What was the upside?
3. **The execution.** How did you ship it? What guardrails did you put in place?
4. **The retrospective.** Was the yes the right call? What would you do differently?

### The PacificFreight answer (Engagement 5: the handoff, the 6-week transition)

- **Situation:** PacificFreight's Daniel asked me to extend the engagement by 6 weeks to do a "proper handoff" to the in-house team. I wanted to say no — the engagement was supposed to end at week 12, and I had 3 other customers waiting.
- **Task:** Decide whether to extend.
- **Action:** I said yes. I asked Daniel: "What does 'proper handoff' mean? Who takes over? What's the 5-question test for the next FDE?" Daniel didn't have answers. I wrote the 5-question test (the "FDE has left" test) and used it as the rubric for the 6-week transition. Week 1-2: I trained Daniel's team. Week 3-4: I shadowed Daniel's team. Week 5-6: Daniel's team ran the system without me. The transition was 3 design decisions, 4 runbook updates, 0 customer-facing downtime.
- **Result:** Daniel's team took over at week 18. The "FDE has left" test is now the rubric for the next 30 customers. I lost 6 weeks of capacity, but the handoff is the highest-signal FDE pattern.

**The metric is the closing line:** "3 design decisions, 4 runbook updates, 0 customer-facing downtime. The handoff is the highest-signal FDE pattern. The 5-question test is now the rubric for the next 30 customers."

### The 3 anti-patterns for this question

1. **"I said yes because the customer asked."** Without the bounded cost. FDEs say yes when the cost is bounded. What was the guardrail?
2. **"I said yes and it was a disaster."** Without the lesson. Every FDE has a "yes" that went wrong. The lesson is the signal.
3. **"I always say yes."** Same as question 3 — a red flag. FDEs say no when the engagement is doomed. "I always say yes" means the candidate doesn't have the judgment to know when to walk away.

---

## The 4-question cheat sheet (customer interaction)

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Difficult customer | Engagement 8: cost ceiling breach | $4.09/month, 79%+ thumbs-up, 0 downtime |
| 2. Customer was wrong | Mei's "always include the customer's name" | 71% → 79% thumbs-up in 2 weeks |
| 3. Said no to the customer | Engagement 2: the legal-tech walkaway | 2 weeks saved, customer came back in 6 months |
| 4. Said yes when I wanted to say no | Engagement 5: the 6-week handoff | 3 design decisions, 4 runbook updates, 0 downtime |

**Memorize these 4.** They're the answers to 80% of customer-interaction behavioral questions.

---

## How to use this sub-lesson

1. **Pick the most relevant story from the 4 above.** Use question 1 for the "difficult customer" prompt, question 2 for "the customer was wrong," etc.
2. **Practice the STAR format out loud.** 3-4 minutes per answer. Time yourself.
3. **Use the metric as the closing line.** "$4.09/month" / "71% → 79%" / "2 weeks saved" / "0 customer-facing downtime." The metric is the FDE signal.
4. **Rehearse with an AI assistant.** Have it score you on the 3 anti-patterns per question.
5. **Add your own stories.** The 4 above are PacificFreight examples. The candidate should have 1 story per question from their own experience.

---

## The cross-reference: how this maps to Phase 6

| Question | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Difficult customer | `../customer-simulation/README.md` (the 5 scenarios) | Read the room + find a resolution |
| 2. Customer was wrong | `../decomposition/README.md` (the 5 clarifying questions) | Diagnose before prescribing |
| 3. Said no to the customer | `../company-experiences/../README.md` (the "FDE walks away" pattern) | Judgment to know when to walk away |
| 4. Said yes when I wanted to say no | `../project-deep-dives/pacificfreight-deep-dive.md` (the 45-min script) | Bounded cost + guardrails + handoff |

---

## The thesis

**Customer-interaction questions are the FDE signal.** The candidate who can name a real customer, a real disagreement, and a real resolution — with a metric — is showing they can do the work. The candidate who says "I worked with stakeholders" is not.

**The 4 questions above are the answers to 80% of customer-interaction behavioral questions.** The 4 STAR answers (with the 4 closing-line metrics) are the muscle memory. Practice them out loud, time yourself at 3-4 minutes per answer, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Behavioral prep gets you past the customer-simulation round at AWS FDE, Anthropic, Sierra AI, and the 5-question test at every FDE loop.**