# Lesson 35: Difficult questions

> **Week 7 · Day 35 · 90 min**
> **Deliverable:** The 20 hardest executive interview questions, each with a 90-second answer.

## 🎯 Architect Level
Staff.

## 🧠 Concept

The "difficult" questions are the ones that test judgment, not knowledge. They are the questions where the wrong answer loses the offer and the right answer doesn't necessarily win it. The right answer shows how you think, not what you know.

The 20 hardest executive questions, grouped:

**Strategy & judgment (Q1-5):**
1. "What's the most overrated trend in data and AI right now?"
2. "If you could only fix one thing in our data estate, what would it be?"
3. "What would you do if the CEO's AI mandate is impossible in the timeframe?"
4. "How do you know when to kill a project?"
5. "What's the most-successful data project you've seen at another company? Why?"

**Leadership & people (Q6-10):**
6. "Tell me about a time you had to fire someone you liked."
7. "How do you handle a BU head who refuses to share data?"
8. "What's the worst hire you've made? What did you learn?"
9. "How do you develop senior leaders?"
10. "When have you decided NOT to hire someone everyone else wanted?"

**Failure & accountability (Q11-15):**
11. "Tell me about a data quality incident that got to the customer."
12. "Tell me about a time you missed a commitment. What did you do?"
13. "What's the worst decision you've made as a leader? Why?"
14. "Tell me about a time you had to deliver bad news to the board."
15. "When have you been wrong, and how did you handle it?"

**Conflict & politics (Q16-20):**
16. "How do you handle a CTO who wants a different architecture?"
17. "Tell me about a time you disagreed with your CEO. What did you do?"
18. "How do you influence without authority?"
19. "When have you had to choose between the right thing and the expedient thing?"
20. "Tell me about a time you lost an argument and had to execute anyway."

The single biggest mistake is to **answer with a story you've never told before**. Every answer in this list is a STAR. Rehearse all 20 before the loop. The interview is not the time to find the story.

The second biggest mistake is to **avoid the failure question**. "I don't really have one" is the wrong answer. Every leader has failures. The right answer is the failure, the learning, and the change in behavior.

The third biggest mistake is to **make the conflict story about the other person**. "My CTO was wrong" is a bad story. "My CTO and I disagreed; I found out I was missing X" is a good story. The hero of the conflict story is you, but the lesson is about your growth.

## 🛠️ Build It

**Spec:** Build the 20 answers, each in 90 seconds, each with a STAR frame and a follow-up defense.

**Acceptance:**
- 20 questions, 20 answers
- Each answer: 90 seconds, STAR, 1 lesson
- Each answer: 1 follow-up defense (60 seconds)
- 1 paragraph on the trade-off (vulnerability vs. competence)

**Starter:** Use your real resume. Map each question to a real story. If you don't have a real story for a question, use [STORY NEEDED] and build one before the loop.

**Solution (sample 5, abridged):**

**Q1: What's the most overrated trend?**
> "Vector databases as a separate platform. The 80% case is 'I need semantic search' — pgvector or a search engine handles it. The 20% case is 'I need billion-scale vector with low latency' — then yes, Pinecone. But the 'every company needs a vector database' pitch is overblown. [CONFIRM: form this opinion more concretely from your actual work.]"

**Q6: Tell me about a time you had to fire someone you liked.**
> "STAR. S: senior engineer on my team, strong technically, underperforming on collaboration. T: 6 months in, the team was starting to avoid them. A: I had the direct conversation, then a 60-day PIP with specific milestones. They didn't make it. I did the off-ramp with severance and references. R: The team recovered in 4 weeks. The lesson: avoid the conversation longer than 6 months, the cost compounds."

**Q11: Tell me about a data quality incident that got to the customer.**
> "STAR. S: bad customer ID propagated to the marketing platform. T: 2,000 customers received the wrong offer. A: detected via support ticket spike, war-room within 1h, identified the source within 4h, corrected within 24h, customer comms within 48h. R: $X cost in support, $Y in churn risk. Fix: contract on the source system, DQ check in the pipeline, sign-off on customer-facing comms."

**Q16: How do you handle a CTO who wants a different architecture?**
> "The first conversation is to understand. 'Why do you want X?' The second is to share my view. The third is to find the joint decision. If we can't agree, we escalate to the CEO with a joint memo: the options, the trade-offs, our recommendation. The CEO decides. The CDO's job is to defend, not to win. The CTO's job is the same. The losing argument is the one where one of us tries to win."

**Q19: When have you had to choose between the right thing and the expedient thing?**
> "STAR. S: source system was sending PII in clear text; the expedient fix was to mask in the warehouse. T: the right fix was a contract change at the source. A: I had the conversation with the source-system owner; we agreed on a 90-day plan; we delivered. R: the right thing cost 3 weeks of engineering time, the expedient thing would have cost a security audit finding and a CISO escalation."

**Trade-off (vulnerability vs. competence):** The interview is a balance. Show the failure and the learning; show the strength and the limits. The CDO who is "perfect" is the CDO who has never failed.

## 🏛️ Architect Notes

- **Trade-off:** Vulnerability vs. competence. The right ratio is 30% vulnerability, 70% competence. More vulnerability = no confidence. Less = no authenticity.
- **Capacity / cost:** 20 answers × 90 seconds = 30 minutes of speaking time. Build 20 stories. Rehearse 5 times. The interview is not the rehearsal.
- **When NOT to use:** Don't use the same story twice. The interviewer will notice. Have 20 different stories.
- **Production checklist:**
  - [ ] 20 questions, 20 answers
  - [ ] 90 seconds per answer
  - [ ] STAR frame
  - [ ] 1 lesson per answer
  - [ ] 1 follow-up defense per answer
  - [ ] Trade-off paragraph

## 🌙 Reflect

- Which 5 questions are your weakest? Re-record.
- Which story is your most authentic? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Case Study 7 — The Three-C's Conflict.