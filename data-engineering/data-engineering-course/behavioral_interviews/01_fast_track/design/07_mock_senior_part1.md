# 07 — Be Seen as a Senior Engineer (Part 1: Mock Interview)

> **Lesson 7 of 8 — Fast Track** · ~20 min

A full mock interview. Read the questions, listen to the
candidate's answers, score them yourself, *then* turn to
Lesson 08 for the frame-by-frame analysis.

**This is the most important exercise in Module 01.** Don't skip
it.

---

## 1. The setup

- **Candidate:** "Sam," interviewing for a Senior Data Engineer
  role (E5 at Meta, L5 at Google, Senior at most).
- **Background:** 6 years of experience, currently at a mid-size
  SaaS company, has led 2 cross-team projects, has shipped
  1 major incident postmortem, has not been a manager.
- **Interviewer:** "Jordan," senior engineer on the data platform
  team.
- **Round:** 45-minute behavioral.

Sam is competent but not polished. Some answers will be strong,
some will lose points. Your job is to score each one on the rubric
from `02_introduction.md` before reading the analysis in
Lesson 08.

---

## 2. The transcript

### Q1: "Tell me about yourself."

> *"Sure. So my name is Sam, I've been a data engineer for about
> 6 years now. I started at a small fintech, then moved to my
> current company where I've been for the last 3 years. Most of
> my work has been on the data infrastructure side — pipelines,
> warehouses, that kind of thing. In my current role I've been
> focused on migrating us from a batch-based system to more
> real-time streaming, and I've also done some work on data
> quality and observability. I'm interviewing because I want to
> work on bigger systems with more users. Yeah. That's me."*

### Q2: "Tell me about a project you're particularly proud of."

> *"Yeah, so the streaming migration is probably the one. We had
> a bunch of batch jobs that ran overnight and by the time we
> got the data in the morning it was already stale, especially
> for the user-facing dashboards. So I led the move to streaming,
> which was a big project. I designed the new architecture using
> Kafka and Flink, and worked with the data science team to
> make sure the new schemas worked for their use cases. We
> shipped it in about 4 months and the data freshness went from
> 24 hours to under a minute, which was a huge win. The team
> was happy, the stakeholders were happy."*

### Q3: "Tell me about a time you had a conflict with a coworker."

> *"Hmm, that's a good one. So at my current company, there was
> a situation where one of my peers — actually a senior engineer
> — was resistant to using Kafka. He wanted to stick with the
> batch approach. I tried to convince him but he wasn't really
> budging. I ended up going to my manager about it, and my
> manager agreed with me, and we moved forward with Kafka. He
> came around eventually but it was kind of a frustrating
> experience. I think the takeaway is that sometimes you just
> have to escalate."*

### Q4: "Tell me about a time you failed."

> *"I missed a deadline on a project once. I had estimated 6
> weeks for a project and it ended up taking 10. The thing is,
> the requirements kept changing as we went, which made it hard
> to estimate. In the end we shipped it and it was fine. I
> learned that I need to be more careful with estimates and
> also that I need to push back when requirements change. Yeah."*

### Q5: "How do you handle ambiguity?"

> *"I think ambiguity is just a fact of life in engineering. You
> never have perfect information. I try to be flexible and
> adapt as I go. I ask a lot of questions and try to keep
> stakeholders updated. I think the most important thing is to
> just keep moving and not get paralyzed."*

### Q6: "Tell me about a time you had to influence someone
without authority over them."

> *"I think the streaming project is a good example of that.
> I had to convince the data science team to adopt the new
> schema even though they weren't directly reporting to me.
> I did this by setting up a series of meetings and listening
> to their concerns, and then proposing a schema that addressed
> their needs. They came on board and we shipped it."*

### Q7: "Anything you'd like to ask me?"

> *"Yeah, what does the team look like and how big is it? And
> I guess what does a typical day look like for a senior
> engineer on this team?"*

---

## 3. Your scoring pass

Before you read the analysis in Lesson 08, score Sam on the rubric
from `02_introduction.md`. The five dimensions:

- **Ownership** — did they drive outcomes, not just outputs?
- **Judgment** — did they make calls under ambiguity and defend
  them?
- **Collaboration** — did they bring others along, disagree
  well?
- **Growth** — did they learn from failure?
- **Communication** — specific, structured, concise?

For each answer, give a 1-4 score:
- 1 = "below bar"
- 2 = "meets bar"
- 3 = "above bar"
- 4 = "strong hire"

Also note the timestamp in the answer where you would have
intervened if you were coaching Sam.

---

## 4. The big picture before the analysis

Sam is *technically credible* — every answer references real work.
That's the floor. The question is whether Sam sounds like a senior
engineer or a strong E4.

The things to listen for:
- Does Sam name a specific decision, or just describe work?
- Does Sam quantify, or just say "huge win"?
- Does Sam show ownership of *people* outcomes, or only technical
  outcomes?
- Does Sam's failure story show growth, or just a confession?
- Does Sam's collaboration story show empathy, or just "I won"?

Spend 5 minutes writing down your scores before turning the page.
