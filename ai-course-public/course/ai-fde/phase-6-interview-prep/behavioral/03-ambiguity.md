# Behavioral Sub-Lesson 3 — Ambiguity / No Spec (the "I set the spec" family)

> **FDEs operate in ambiguity.** The customer doesn't have a spec. The PM hasn't written a PRD. The data is messy. The interviewer is testing whether you can set the spec yourself — or whether you wait for someone to give you one. The candidate who says "I asked my manager" is signaling they can't operate in ambiguity. The candidate who says "I built the eval set" is signaling they can.

---

## Why ambiguity questions are the FDE signal

The 3 things the interviewer is testing:

1. **Can you set the spec?** FDEs write the spec when none exists. The eval set is the spec; the prompt is the implementation.
2. **Can you make decisions without all the information?** FDEs operate with 60-70% information and ship anyway. The interviewer wants to know you can close the gap.
3. **Can you own the spec?** If you set the spec, you own the consequences. The interviewer wants to know you can own the failures, not just the successes.

**The FDE pattern:** when the spec is unclear, the FDE writes the spec. The spec is the eval set (for AI systems) or the cost model (for infra) or the runbook (for operations). The spec is the contract.

**The 5-question cheat sheet (from the behavioral/README.md):**

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Spec was unclear | Engagement 1: eval set as spec | 30-row eval set in week 1 |
| 2. Made a decision without all the information | Engagement 7: the region failover | Manual decision, hysteresis, SLO preserved |
| 3. Set the spec yourself | Engagement 5: the 5-question test for the next FDE | 3 next FDEs, 10/10 at 90 days |
| 4. Operated with conflicting requirements | Engagement 4: the cost + quality tradeoff | $5/month ceiling + 79% thumbs-up rate |
| 5. Closed the gap | Engagement 10: the principal handoff | 3 design decisions, 1 runbook update |

**This sub-lesson dives into questions 1-3 (unclear spec, decision without info, set the spec yourself).** Questions 4-5 are referenced; see the FDE case studies for the full write-ups.

---

## Question 1: "Tell me about a time the spec was unclear."

### The FDE-specific signal

The interviewer is testing 4 things:

1. **Did you wait for the spec or write it?** FDEs write the spec when none exists. Did you?
2. **What was the spec?** A real, named artifact. The eval set is the spec for AI systems; the cost model is the spec for infra; the runbook is the spec for operations.
3. **How did you validate the spec?** Did you ship the spec to the customer? Did the customer accept it?
4. **What was the metric?** Did the spec measure the customer-facing outcome, or did it measure the implementation?

### The PacificFreight answer (Engagement 1: the eval set as spec)

- **Situation:** PacificFreight's drafter had no spec in week 1. Mei said: "I want the system to draft emails like me." No examples, no rubric, no acceptance criteria.
- **Task:** Set the spec for an AI system with no documented requirements.
- **Action:** I built a 30-row eval set in week 1. The eval set was 30 historical emails that Mei had drafted, with her final version as the ground truth. I ran the eval set against the v1 prompt. The v1 prompt scored 51% thumbs-up (vs Mei's 71% baseline). I tuned the prompt + the retrieval. The v3 prompt scored 71% thumbs-up. The eval set became the contract between prompt engineer and customer.
- **Result:** 30-row eval set shipped in week 1. v1 prompt at 51% thumbs-up; v3 at 71% thumbs-up; v6 at 79% thumbs-up. The eval set was the spec; the prompt was the implementation. Every Monday for 12 weeks, I ran the eval set and shipped improvements.

**The metric is the closing line:** "30-row eval set in week 1. v1 at 51% thumbs-up; v6 at 79% thumbs-up. The eval set is the spec; the prompt is the implementation."

### The 3 anti-patterns for this question

1. **"I asked the customer for the spec."** The customer doesn't have a spec. That's why they hired you. "I asked the customer" is a junior answer.
2. **"I made my best guess."** Without the validation. FDEs make their best guess, then validate it with an eval set, a cost model, or a runbook. The validation is the FDE signal.
3. **"I shipped without a spec."** FDEs don't ship without a spec. They ship with the eval set as the spec. "I shipped without a spec" is a red flag.

---

## Question 2: "Tell me about a time you had to make a decision without all the information."

### The FDE-specific signal

This question tests your decision-making under uncertainty. FDEs operate with 60-70% information; the interviewer wants:

1. **A specific decision, a specific gap.** Not "I had to make a tough call once." A real, named decision + a real, named information gap.
2. **The decision-making framework.** How did you close the gap? What was the bounded cost? What was the upside?
3. **The execution.** Did you ship the decision? Did you monitor for the failure mode?
4. **The retrospective.** Was the decision right? What would you do differently?

### The PacificFreight answer (Engagement 7: the region failover, the ap-southeast-1 outage)

- **Situation:** PacificFreight's drafter was running on a VM in AWS ap-southeast-1 (Singapore). On a Tuesday at 03:14 SGT, AWS ap-southeast-1 went down. The drafter was unavailable for 22 minutes. Mei sent 8 emails through the drafter during the outage; 3 of them were hallucinated. Sarah asked: "Can we failback to ap-southeast-1 once it's back, or should we stay on the Tokyo replica?" I had to decide.
- **Task:** Decide between failback (return to ap-southeast-1 once it's healthy) and stay-on-Tokyo (keep using the Tokyo replica).
- **Action:** I chose stay-on-Tokyo with manual hysteresis. Reasoning: (a) failback is riskier than staying on the replica; the replica is healthy, the primary is not; (b) the SLO is "minimize RTO," not "stay in Singapore for data sovereignty"; (c) the customer (Mei) doesn't care which region the system runs in, she cares that it runs. The decision was bounded: stay on Tokyo for 24 hours, then re-evaluate. I monitored the ap-southeast-1 health dashboard every 30 minutes.
- **Result:** 0 customer-facing incidents during the 24-hour stay on Tokyo. The drafter was 100% available from the replica. At hour 24, I re-evaluated; ap-southeast-1 was healthy; I failed back. Mei didn't notice the region change. The 3 hallucinated emails were reverted.

**The metric is the closing line:** "0 customer-facing incidents during the 24-hour stay on Tokyo. Mei didn't notice the region change. The SLO is 'minimize RTO,' not 'stay in Singapore for data sovereignty.'"

### The 3 anti-patterns for this question

1. **"I made a tough call."** Without the framework. "Tough call" is a junior answer. The framework is the FDE signal.
2. **"I escalated to my manager."** Without the decision you made. Escalation is sometimes right, but the FDE owns the decision. "I escalated" is a red flag unless you can name what you decided AFTER the escalation.
3. **"It was a judgment call."** Without the bounded cost. FDEs make judgment calls with bounded cost. The bounded cost is the FDE signal.

---

## Question 3: "Tell me about a time you set the spec yourself."

### The FDE-specific signal

This question is the FDE-flavored version of question 1 (the "spec was unclear" question). The interviewer wants:

1. **A specific spec you wrote.** Not "I set the spec once." A real, named spec — the eval set, the cost model, the runbook, the policy file, the 5-question test.
2. **The validation.** Did the customer accept the spec? Did the spec become the contract?
3. **The downstream impact.** Did the spec outlive the engagement? Did it become a template for the next 30 customers?
4. **The metric.** What was the result? How did the spec measure the customer-facing outcome?

### The PacificFreight answer (Engagement 5: the 5-question test for the next FDE)

- **Situation:** PacificFreight's Daniel asked me to extend the engagement by 6 weeks to do a "proper handoff" to his team. I asked Daniel: "What does 'proper handoff' mean? Who takes over? What's the 5-question test for the next FDE?" Daniel didn't have answers.
- **Task:** Set the spec for the handoff.
- **Action:** I wrote the 5-question test. The 5 questions are: (1) Can you run the eval set? (2) Can you read the runbook? (3) Can you trace a request end-to-end? (4) Can you ship a rollback? (5) Can you hand off to the next FDE? I used the test as the rubric for the 6-week transition. Week 1-2: I trained Daniel's team on the 5 questions. Week 3-4: I shadowed Daniel's team running the system. Week 5-6: Daniel's team ran the system without me; they passed the 5-question test.
- **Result:** 3 next FDEs, 10/10 at the 90-day check. The 5-question test is now the rubric for the next 30 customers. The spec outlived the engagement.

**The metric is the closing line:** "3 next FDEs, 10/10 at the 90-day check. The 5-question test is now the rubric for the next 30 customers. The spec outlived the engagement."

### The 3 anti-patterns for this question

1. **"I set the spec."** Without the artifact. The artifact is the FDE signal. What was the spec? Where is it?
2. **"The customer accepted my spec."** Without the validation. How did you know the spec was right? What did you measure?
3. **"I wrote the spec."** Without the downstream impact. Did the spec outlive the engagement? Did it become a template?

---

## The 3-question cheat sheet (ambiguity)

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Spec was unclear | Engagement 1: eval set as spec | 30-row eval set in week 1, v6 at 79% thumbs-up |
| 2. Decision without all info | Engagement 7: the region failover | 0 customer-facing incidents in 24h, manual hysteresis |
| 3. Set the spec yourself | Engagement 5: the 5-question test | 3 next FDEs, 10/10 at 90 days |

**Memorize these 3.** They're the answers to 80% of ambiguity behavioral questions.

---

## How to use this sub-lesson

1. **Pick the most relevant story from the 3 above.** Use question 1 for the "spec was unclear" prompt, etc.
2. **Practice the STAR format out loud.** 3-4 minutes per answer. Time yourself.
3. **Use the metric as the closing line.** "30-row eval set" / "0 customer-facing incidents" / "3 next FDEs, 10/10." The metric is the FDE signal.
4. **Rehearse with an AI assistant.** Have it score you on the 3 anti-patterns per question.
5. **Add your own stories.** The 3 above are PacificFreight examples. The candidate should have 1 story per question from their own experience.

---

## The cross-reference: how this maps to Phase 6

| Question | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Spec was unclear | `../take-home/01-prototype.md` (the eval-set-as-spec pattern) | Write the spec when none exists |
| 2. Decision without all info | `../system-design/README.md` (the 4-step framework) | Bounded cost + monitor + re-evaluate |
| 3. Set the spec yourself | `../project-deep-dives/pacificfreight-deep-dive.md` (the 45-min script) | Own the spec + downstream impact |

---

## The thesis

**FDEs operate in ambiguity.** The candidate who can set the spec, make decisions with bounded cost, and own the consequences is showing they can do the work. The candidate who says "I asked my manager" or "I waited for the spec" is not.

**The 3 questions above are the answers to 80% of ambiguity behavioral questions.** The 3 STAR answers (with the 3 closing-line metrics) are the muscle memory. Practice them out loud, time yourself at 3-4 minutes per answer, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Ambiguity prep gets you past the customer-simulation round at AWS FDE, Anthropic, Sierra AI, and the "tell me about a time the spec was unclear" question at every FDE loop.**