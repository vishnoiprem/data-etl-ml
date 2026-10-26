# 03 — Coaching and Developing Engineers

> **Lesson 3 of 21 — Managing Individuals** · ~25 min

The GROW model for coaching 1:1s, the difference between coaching
and managing, the skip-level 1:1 cadence, and how to coach without
becoming a bottleneck. The 1:1 is the substrate for everything
else in this module — get it right and the rest is easier.

---

## 1. What "coaching" actually means

Most new EMs think coaching = giving advice. They've been good at
their job for 5-8 years, people have sought them out for guidance,
and they're used to having the answer. So they coach by telling.

That works for senior ICs who already trust you and have the
context. For everyone else — especially for the people who most
need coaching — it doesn't work. Telling creates dependency. The
engineer comes back next 1:1 with the same problem. You give more
advice. The cycle repeats. Three months later they're no closer to
solving it themselves, and they're subtly resentful that you're
solving it for them.

The senior-EM move: coaching is **helping someone else find their
own answer**, not providing yours. The model for this is GROW.

## 2. The GROW model

GROW is a 4-question framework from executive coaching. It maps
cleanly onto engineering 1:1s:

| Letter | Question | What you're really doing |
|---|---|---|
| **G**oal | "What do you want to be different by the end of this conversation?" | Anchoring the 1:1 on a specific outcome, not a vague topic. |
| **R**eality | "What's actually happening now? What have you tried?" | Forcing diagnosis before prescription. The engineer surfaces what's really going on. |
| **O**ptions | "What are your options? What could you do?" | Generating alternatives without recommending. The engineer owns the choice. |
| **W**ill | "What will you do? By when? How will I know it happened?" | Committing to a specific action with a specific check-in. |

Notice what's missing: *your* advice. The coach's job is to ask
better questions, not to give better answers. This is
uncomfortable for new EMs because the silence after "What are your
options?" feels like a failure. It's not. The silence is where the
engineer does the thinking.

A 30-minute coaching 1:1 in GROW looks like:

- 5 min: small talk, set the Goal for the conversation
- 10 min: explore Reality — what's happening, what's been tried
- 10 min: explore Options — generate 3-4 paths, weigh tradeoffs
- 5 min: commit to a Will — specific action, specific check-in

When you first start running GROW 1:1s, you'll feel like you're
not "doing" enough. You're not — that's the point. The engineer
is doing the work. Your job is to ask questions that make the work
visible.

---

## 3. Coaching vs managing

Coaching and managing are different modes you switch between
depending on context:

| Mode | When | What it sounds like |
|---|---|---|
| **Coaching** | Engineer has the context, you don't, or the engineer needs to grow | "What do you think we should do?" "What have you tried?" "What would you do if you weren't worried about what your manager thought?" |
| **Managing** | There's an urgent decision, you have context they don't, or the stakes are too high to delegate | "I need you to do X by Friday. Here's why." "I'm escalating this to my director — here's the message I'm sending." |
| **Teaching** | The engineer is missing a skill or framework that would unlock the rest | "Here's the framework I use for incident reviews — let me walk you through it." |
| **Sponsoring** | The engineer needs advocacy you can provide | "I'm going to nominate you for the promo. Here's what I need from you." |

The mistake new EMs make: defaulting to managing or teaching when
coaching is the right move. The senior move is to **stay in
coaching mode for as long as the engineer can sustain it**, and
only shift to managing when there's a genuine time or stakes
constraint.

A useful heuristic: if you find yourself saying "I think you
should..." in a 1:1, ask instead "What does your gut say?" If
their answer is good, stay in coaching. If their answer is
missing context they need, shift to teaching. If the stakes are
high and time is short, shift to managing.

---

## 4. The skip-level 1:1

Skip-level 1:1s are 1:1s you have with the reports of your direct
reports — your "skips." They're a load-bearing part of the EM job
for 3 reasons:

1. **You learn things you can't learn through your directs.** Your
   directs have incentives to filter the bad news upward. Skip-
   levels don't.
2. **You grow people your directs don't have time to grow.** A
   senior engineer who wants to staff-manage, a tech lead who's
   struggling, a junior who's bored — your direct may not have
   the cycles or the context to coach them. You do.
3. **You model the 1:1 muscle for your directs.** If your directs
   see you running good 1:1s with their reports, they'll start
   running better ones with theirs.

**Cadence:** monthly for skips you've worked with for a while,
biweekly for new skips or skips who are struggling. Never less than
monthly — if you're only seeing someone's skip every quarter,
something has gone wrong.

**What to talk about:** not their work (their manager handles
that). Talk about their career, their goals for the next 6-12
months, what's getting in the way, what they'd want to be doing
more of. The skip-level 1:1 is the engineer's chance to be seen
by someone senior who isn't their day-to-day manager.

**What NOT to do:** don't use the skip-level to back-channel
decisions you've already made with your direct. If your direct
asks "did Priya mention X to you?" answer "I'd love for you to
ask Priya directly — that's a great question for your 1:1 with
her." The skip-level is for the skip's growth, not for your
political maneuvering.

---

## 5. A worked example: the GROW 1:1 transcript

**Setup:** Priya, an E5 on Sam's team, has been struggling to get
her tech-lead decisions respected by 2 senior engineers on the
team. Sam has 30 minutes for a 1:1.

> **Sam:** "What do you want to be different by the end of this
> conversation?"
>
> **Priya:** "I want to figure out why Aarav and Jordan keep
> pushing back on my design decisions. It feels like they're
> testing me."
>
> **Sam:** "What's actually happening? Walk me through the last
> time it came up."
>
> **Priya:** "Last week I proposed the new schema migration
> approach. Aarav said 'I think we should consider the streaming
> approach,' and Jordan said 'I'd like to see the data before we
> commit.' Both of them went around me to my manager."
>
> **Sam:** "What did you make of that in the moment?"
>
> **Priya:** "Honestly? I felt undermined. They've been on the
> team for 4 years, I've been here 18 months. It felt like they
> didn't trust me."
>
> **Sam:** "What's another way to read it?"
>
> **Priya:** "...maybe they had specific concerns about the
> approach that they didn't feel safe raising with me directly?"
>
> **Sam:** "What are your options for handling the next time it
> comes up?"
>
> **Priya:** "I could escalate to my manager. I could ask them
> directly in front of the team. I could ask them privately. I
> could just ignore it."
>
> **Sam:** "Which of those feels most aligned with the kind of
> tech lead you want to be?"
>
> **Priya:** "Probably the private one. But I'm worried it'll feel
> like I'm pulling rank."
>
> **Sam:** "What's the version of that conversation you'd feel
> good about?"
>
> **Priya:** "I'd ask them what their specific concerns are,
> listen to understand, and then propose a path. If we still
> disagree, I'd escalate together rather than around each other."
>
> **Sam:** "What will you do? By when?"
>
> **Priya:** "I'll talk to Aarav tomorrow in a 1:1. I'll loop
> you in if it doesn't land by Friday."

**Analysis:** Sam asked 7 questions. Gave zero advice. Priya
landed on an action plan that she'll own, with a check-in
Sam can hold her to. The senior move isn't the answer Sam would
have given — it's the answer Priya will actually execute because
she arrived at it herself.

---

## 6. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #1: *"Tell me about a time you had a conflict
  with someone. How did you resolve it and what did you learn?"*
- People Management #3: *"Tell me about a time when you dealt with
  a conflict with engineers."*
- Behavioral #4: *"How would you respond if your team disagreed
  with your ideas?"*
- Behavioral #28: *"Tell me about a time you mentored someone."*
- Behavioral #88: *"Tell me about a time when you had to coach
  someone."*

---

## Try it

Pick one of your directs (or one of your mentees, if you're an IC).
Set a 30-minute 1:1. Run it in GROW. Use the questions above.

After the conversation, ask yourself: did I give advice, or did I
help them find their own answer? If you gave advice more than
once, ask yourself why. Was the situation actually coaching, or
was it teaching or managing in disguise?

---

## Action item

This week, run 2 GROW 1:1s. Tell me in your own words what felt
different. The first one will feel like you're not doing enough.
By the second, you'll start to see the engineer doing the work.