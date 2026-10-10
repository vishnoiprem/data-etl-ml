# Section 11 Quiz — Role Plays (synthesis)

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** In Role Play 1 (trust misconfig), the learner is asked to diagnose an `AccessDeniedException` on `sts:AssumeRole`. What is the *first* thing the senior DE does?

- A. Re-deploy the stack
- B. Read the error message
- C. Edit the role in the console
- D. Open the S3 bucket policy

---

**Q2.** In Role Play 2 (streaming falling behind), the manager asks "what's going on?" What is the *first* thing the senior DE says?

- A. "I need 30 minutes to look at the CloudWatch metrics before I give you a plan"
- B. "It's a capacity problem, I'll add more workers"
- C. "The schema drifted, the producer team broke it"
- D. "I'll fix it by EOD"

---

**Q3.** In Role Play 3 (pitching Data Quality), the manager is allergic to "shiny new tools." What is the *first* number the senior DE gives?

- A. The cost: $40/month, 2 days of engineering time
- B. The 3 rule types
- C. The number of Glue Data Quality customers
- D. The CloudWatch metric name

---

**Q4.** In all 3 role plays, what is the common pattern the senior DE uses?

- A. Diagnose off-line, then communicate a plan
- B. Diagnose in the meeting, then ask for more time
- C. Blame the producer team
- D. Promise a fix without a plan

---

**Q5.** The 3 role plays all share one common communication pattern. Which is it?

- A. Open with the answer, then back-fill the details
- B. Use "we" instead of "I" for actions
- C. End with a clear ask
- D. Avoid numbers in the first 30 seconds

---

# Answer Key

1. **B** — Read the error message. The error message tells you whether it's a trust problem or an identity problem. The senior move is to read, not to act.
2. **A** — Ask for 30 minutes. The senior move is to *not* diagnose in the meeting. Acknowledge the urgency, ask for a follow-up, then come back with a plan.
3. **A** — The cost. Managers want a number. The 3 DQ rule types and the CloudWatch metric name are technical details; the cost is what the manager can budget against.
4. **A** — Diagnose off-line, then communicate a plan. The opposite of diagnosing in the meeting (which signals you're unprepared) and the opposite of promising without a plan (which signals overconfidence).
5. **C** — End with a clear ask. "I need sign-off on the worker bump" / "I need a 2-hour SLA on schema notifications" / "I need 2 days this sprint and $50/month." Senior DEs always close with the ask.
