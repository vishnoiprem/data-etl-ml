# Lesson 01 — Understanding the Problem

> **The skill of listening so you build the right thing.** 25 minutes. No code.

By the end of this lesson you have:

- A **stakeholder map** for the PacificFreight engagement
- A **discovery question list** of 15-20 questions, organized into 4 buckets
- A **theory of the problem** in 3 sentences (the "if I'm right, then..." statement)
- A clear answer to the question *"what is the customer trying to accomplish, in their own words?"*

This is the lesson most engineers skip. The FDE's job is to **not skip it**.

---

## 🎯 Outcome

You produce **three artifacts**, each in a markdown file:

1. `stakeholder-map.md` — a 1-pager mapping every person who can say yes, no, or block the project
2. `discovery-questions.md` — a numbered list of 15-20 questions to ask in the first meeting
3. `theory-of-the-problem.md` — a 3-sentence "if I'm right, then..." statement

When you finish, you can walk into a 30-min meeting with PacificFreight and **not embarrass yourself by building the wrong thing**.

## 🧠 Mindset

The FDE's first job is **not to understand the AI**. It is to understand the **human's job that the AI is replacing or augmenting**. That is what most engineering-trained people skip — and it is why most AI projects fail.

The mindset is:

> **The customer does not have an AI problem. They have a job-to-be-done problem, and AI may or may not be the right tool.**

Your first three meetings are about learning the job. The AI comes later. If you can't describe the job in the customer's own words, you don't understand it well enough to build anything.

Three traps to avoid:

1. **The solution trap.** "We can use an LLM to..." is the first sentence most engineers want to say. Don't. The customer doesn't care yet. They want to know you heard them.
2. **The scale trap.** "What if you have 10x the volume?" is a great question for week 4. In week 1, "what does the CS person do today when they get this email?" is the right question.
3. **The stakeholder trap.** Talking only to the person who invited you. The CS team might love your tool; the ops manager might hate it. You need to talk to **everyone who can say no**, not just everyone who said yes.

## 🛠️ Practice

### Exercise 1 — Stakeholder map (10 min)

Read [`../scenario-brief.md`](../scenario-brief.md) again. Then make a stakeholder map. Use this template:

```markdown
# PacificFreight — Stakeholder Map

## Who invited you in
- **[Name, role]** — what they want from this engagement in 1 sentence

## Who can say YES
- **[Name, role]** — what they care about, what would make them say yes

## Who can say NO
- **[Name, role]** — what they care about, what would make them say no

## Who can BLOCK you (different from saying no)
- **[Name, role]** — what they care about, why they might block

## Who is affected but not in the room
- **[Name, role]** — what changes for them if you ship
```

**Worked example for PacificFreight:**

> - **Who invited you in:** Sarah, the ops manager. Wants to free up CS time.
> - **Who can say YES:** Sarah (ops), James (CEO). They control the budget.
> - **Who can say NO:** Mei (CS lead). If she says "this is more work, not less," you lose.
> - **Who can BLOCK you:** Daniel (IT). He owns the PHP tracker. If he says "no API," the tracker is out of scope.
> - **Who is affected but not in the room:** the CS team (3 people). They are the daily users. If they hate it, you fail.

The lesson: your "yes" people (Sarah, James) are not your daily users. Your daily users (the CS team) are not in the room unless you put them there.

### Exercise 2 — Discovery questions (10 min)

A good discovery question list is **organized by what you are trying to learn**, not by who you are asking. Use the 4-bucket structure:

```markdown
# PacificFreight — Discovery Questions

## Bucket A — The job
1. Walk me through what happens when a "where is my parcel?" email lands today.
2. How long does each step take? Where does the time go?
3. What tools do you switch between? (Gmail, the tracker, a spreadsheet, ...)

## Bucket B — The pain
4. Of the steps you just described, which one is the most painful?
5. If you could wave a magic wand and only fix ONE step, which one?
6. How many of these emails per day, per week, per month?
7. What happens if a customer doesn't get a reply for 24 hours?

## Bucket C — The data
8. Where does the shipment status actually live? (Tracker, spreadsheet, paper?)
9. How fresh is the data? Real-time or end-of-day?
10. Is there an API to the tracker? If not, who owns it?
11. Can you give me 20 real inbound emails I can look at (with names redacted)?

## Bucket D — The constraints
12. Are there emails you would NEVER auto-reply to? (Angry customers, legal, refunds)
13. What is the monthly ceiling you'd be willing to spend on a tool that does this?
14. Who signs off on customer-facing copy? (CS lead? Marketing? Legal?)
15. Are there compliance rules I should know? (PDPA in SG, GDPR, ...)
16. Can I deploy code in your environment, or do you need to host?
17. What does success look like at the end of 4 weeks?
```

**Worked example — the magic wand question:**

> *Q5: "If you could wave a magic wand and only fix ONE step, which one?"*

This question is **the** question. Whatever the customer answers is the *first* thing you build. Everything else is Phase 2. If the answer is "the lookup," you build a CLI that looks up. If the answer is "the drafting," you build a drafting tool. If the answer is "the sending," you build a Gmail plugin.

Don't second-guess the answer. Build the magic wand.

### Exercise 3 — Theory of the problem (5 min)

The "if I'm right, then..." statement is the **riskiest thing you write in week 1**. It is also the most useful.

```markdown
# PacificFreight — Theory of the problem

If I am right, then:
- PacificFreight's CS team spends 60-70% of their time on "where is my parcel?" emails.
- The bottleneck is NOT the lookup (which is fast) but the DRAFTING (which is slow and error-prone).
- A tool that drafts a reply in their voice, for the CS person to review-and-send, would cut
  the per-email time from 4-7 minutes to 30 seconds — freeing ~10 hours/day of CS time.

What would prove me wrong:
- If most "where is my parcel?" emails are actually about something other than status
  (refunds, address changes, lost parcels), then the tool is the wrong shape.
- If the CS team is bottlenecked on the lookup, not the drafting, then the tool is the
  wrong shape.
- If the volume is much lower than 150/day, the ROI doesn't justify a tool.
```

**Why this is the most important thing you write:**

You will spend 4 weeks building. At the end, the customer will ask "did it work?" If you didn't write this in week 1, you can't answer that question honestly. If you did, you can either say "yes, here's the data" or "no, I was wrong about X, and we should pivot to Y."

> **FDE rule:** every engagement gets a "theory of the problem" doc in week 1. If you can't write it, you don't understand the engagement well enough to build anything.

## 🏛️ FDE Lens — the technical reality underneath

The discovery questions above are not arbitrary. They map to specific decisions you will make later:

| Question | What it determines |
|---|---|
| #8 (where does the data live) | Phase 1 tracker shape (JSON file vs. SQL vs. scraping) |
| #10 (is there an API) | Phase 2 scope (write API integration vs. work around it) |
| #11 (can I see real emails) | Whether you can build a real prompt or a guess at one |
| #12 (never auto-reply) | Whether the tool is read-only-draft or write-and-send |
| #15 (compliance) | Whether the tool needs a PII redaction layer |
| #16 (deploy in your env or mine) | Whether you use FastAPI/Flask or a hosted service |

The FDE skill is to **hear a customer's answer and immediately know which technical decision it changes**. You will get better at this with practice. Week 1 of your first engagement, you miss half of them. By your third engagement, you catch most of them in the meeting.

## 🌙 Reflect

Write 3-5 sentences:

1. Why is the "magic wand" question the most valuable one in the discovery list?
2. What's the difference between "who can say NO" and "who can BLOCK you"? Give a PacificFreight-flavored example of each.
3. The "if I'm right, then..." statement is risky. What makes it risky, and why write it anyway?
4. You are in week 1 of a new engagement. The customer wants you to "just start building." What do you say?

**What's next** — Lesson 02 takes the discovery questions from this lesson and turns them into a **framing framework** — the 5 questions that turn a vague "use AI" ask into a testable scope. You will use the framework on the PacificFreight engagement and produce a 1-pager in lesson 04.
