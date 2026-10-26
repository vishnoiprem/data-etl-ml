# 07 — Mock Discovery: Enterprise Migration

> **Lesson 7 of 12 — Customer Interaction** · ~15 min

A second full mock discovery call transcript. An enterprise
financial-services company evaluating your analytics
platform for a Hadoop-to-cloud migration. The scenario is
different from Lesson 06; the moves are the same.

---

## 1. The setup

- **Candidate:** Maya, 9 years data engineering, current
  Senior DE. Interviewing for Senior SA at a hyperscaler.
- **Interviewer:** Raj, Senior SA at the hyperscaler. Plays
  the role of "VP of Data" at a Fortune 500 financial-
  services company.
- **Round:** 30 minutes total — 5 minutes of setup, 20
  minutes of discovery, 5 minutes of close.
- **Scenario:** The financial-services company is
  evaluating a Hadoop-to-cloud migration. They have 80 TB
  of data, 50 data engineers, and a 6-month timeline
  before their Hadoop contract expires.

---

## 2. The transcript

> **Maya:** "Thanks for making the time, Raj. I'd love to
> use our 30 minutes to understand your current
> architecture, what you're trying to achieve with the
> migration, and what the decision-process looks like on
> your side. Is that OK?"
>
> **Raj:** "Sure, sounds good."
>
> **Maya:** "Great. To start, tell me about the current
> setup — what's the Hadoop footprint look like, what
> does your team do with it, and who's the typical user
> of the data?"
>
> **Raj:** "We have an on-prem Hadoop cluster — 80 TB of
> data, mostly in HDFS, with Hive on top for SQL. We
> have 50 data engineers who write Spark and Hive jobs.
> The typical user is a risk analyst or a regulatory
> reporting team."
>
> **Maya:** "Got it — on-prem Hadoop, 80 TB, Hive and
> Spark, 50 engineers, risk and regulatory use cases.
> What's driving the migration? Is this a cost thing, a
> skills thing, or something else?"
>
> **Raj:** "All of the above, honestly. The Hadoop
> contract expires in 6 months, our team is mostly
> trained on Hive and Pig, and the new joiners don't know
> either. The risk team wants real-time, which Hadoop
> can't do well. And the cloud is where the rest of the
> company is going."
>
> **Maya:** "Helpful — three drivers: contract expiry,
> skills gap, and the rest of the company is moving to
> cloud. Of those three, which is the most urgent?"
>
> **Raj:** "The contract expiry. After that, we'd be
> running unsupported Hadoop, which isn't acceptable for
> a regulated workload."
>
> **Maya:** "Got it. So the timeline is firm: 6 months.
> What does 'done' look like for the migration? Is it
> the data in the cloud, the workloads migrated, or the
> team retrained?"
>
> **Raj:** "All three, ideally. We need the data in the
> cloud, the workloads migrated, and the team able to
> operate it. We don't want to be on the hook for
> Hadoop-shaped technical debt in the new system."
>
> **Maya:** "Helpful. Let me make sure I heard you
> correctly: the data needs to be in the cloud, the
> workloads need to be migrated (which means the Spark
> and Hive jobs), and the team needs to be able to
> operate the new system without re-creating Hadoop-
> shaped debt. Is that right?"
>
> **Raj:** "Exactly."
>
> **Maya:** "OK. Let me ask about the team. You have 50
> data engineers, mostly on Hive and Pig. How open is
> the team to learning a new stack? And are you hiring,
> or is headcount flat?"
>
> **Raj:** "The team is open. The new joiners are
> already on cloud-native stacks, and the senior people
> know they need to learn. We're not hiring aggressively
> — headcount is flat, but we have a few open reqs for
> senior engineers."
>
> **Maya:** "Helpful. So the team is willing to learn,
> and you have some headroom to hire senior. Let me ask
> about the regulatory side — you mentioned this is a
> regulated workload. What are the constraints I should
> know about? FedRAMP, PCI, residency, audit?"
>
> **Raj:** "PCI for sure — we have card data flowing
> through. Plus SOX for the financial reporting. And
> the data residency requirements — we have EU data that
> needs to stay in the EU."
>
> **Maya:** "Got it — PCI, SOX, EU data residency. Each
> of these has implications for the architecture. Let
> me ask about the decision process. Who on your team
> owns this evaluation, and how does the decision get
> made?"
>
> **Raj:** "I do, ultimately. But the CISO needs to
> sign off on the security architecture, the CIO needs
> to sign off on the platform choice, and the board
> needs to approve the budget because it's a $4M+
> project."
>
> **Maya:** "OK — you're the decision-owner, with CISO,
> CIO, and board sign-off. Four stakeholders. What's
> the timeline? And what's driving it — the Hadoop
> contract expiry, or something else?"
>
> **Raj:** "The Hadoop contract expiry is the firm
> deadline. But the board is also asking when we'll
> have real-time risk analytics, which is a separate
> ask but is on the same architectural track."
>
> **Maya:** "Helpful. So the firm deadline is the
> contract expiry, and the soft driver is the real-time
> risk analytics. Two different motivations, same
> project. Let me ask about the budget. Is it firm at
> $4M, or is there room to flex?"
>
> **Raj:** "The board approved $4-6M. We have room
> within that range, but going above $6M would need a
> re-approval."
>
> **Maya:** "Got it — $4-6M range, with a re-approval
> above $6M. Let me make sure I heard you correctly.
> You're migrating 80 TB of Hadoop data to the cloud
> in 6 months because the Hadoop contract expires. The
> migration needs to cover the data, the workloads, and
> the team's ability to operate the new system. The
> constraints are PCI, SOX, and EU data residency. The
> decision is yours with CISO, CIO, and board sign-off,
> and the budget is $4-6M with a soft ask for real-time
> risk analytics on the same architecture. Is that the
> picture?"
>
> **Raj:** "Yeah, that's right."
>
> **Maya:** "Here's what I'd suggest. The migration is
> a 3-phase project, and the architecture decisions
> cascade. The first decision is the data lake and
> warehouse, the second is the migration tooling, and
> the third is the workload re-platforming. Each has
> different sign-off, different timelines, and different
> stakeholders.
>
> I'd suggest we start with a 90-minute working session
> with your team and the CISO, focused on the data lake
> + warehouse choice. That gets us aligned on the
> foundational decision, and we can layer the migration
> tooling and workload re-platforming in subsequent
> sessions.
>
> Does Tuesday at 10am work for that first session?
> I'd suggest including the CISO, your senior engineers,
> and the platform team. I'll bring an architect who's
> done this migration for [similar financial-services
> customer]."
>
> **Raj:** "Tuesday at 10am works. Let me confirm with
> the CISO and the platform team and get back to you
> by EOD tomorrow."
>
> **Maya:** "Perfect. I'll send a calendar placeholder.
> If anyone can't make it, let me know and we'll find
> a time that works for the full group."

---

## 3. The analysis

### What Maya did well

- **Set the agenda in the first 30 seconds** — same
  pattern as Sam, same success.
- **Asked the prioritization question.** "Of the three
  drivers, which is the most urgent?" — surfaces the
  *firm* deadline vs. the *soft* drivers, which
  changes the architecture conversation.
- **Defined "done" explicitly.** "Is it the data in the
  cloud, the workloads migrated, or the team
> retrained?" — this is the question that prevents
  scope creep later. Most migrations fail because the
  definition of done was implicit, not explicit.
- **Surfaced the regulatory constraints early.** PCI,
  SOX, EU residency are the things that *constrain* the
  architecture. Surfacing them in the discovery call
  (not later, in the architecture review) means the
  architecture proposal is tailored to the constraints.
- **Identified the level-3 aspiration.** The real-time
  risk analytics is the *aspirational* outcome, not the
  surface "Hadoop migration." Maya anchored on both.
- **Qualified all 5 (decision-maker, process, timeline,
  why-now, budget).**
- **Proposed a structured multi-session plan.** The
  3-phase architecture decision cascade is a senior SA
  move — it shows Maya is thinking about the project
  structure, not just the next call.

### What Maya could have done better

- **Could have asked about the customer's customer.**
  The risk analysts and the regulatory reporting teams
  are the end-users. Anchoring on their needs (e.g.,
  "what does the risk analyst need that they don't
  have today?") would deepen the trust.
- **Could have asked about the team sentiment.** "How
  does the team feel about the migration — is there
  anyone who's resistant, or is it broadly supported?"
  The team sentiment is a leading indicator of project
  success.
- **Could have proposed a backup next step.** Same
  feedback as Sam: if Tuesday at 10am doesn't work,
  what's the alternative? A 4/4 close would have a
  backup in the same breath.

### The rubric score

| Signal | Score |
|---|---|
| **Active listening** | 4/4 — summarizing, second questions, prioritization |
| **Pain-point discovery** | 4/4 — distinguished firm deadline from soft driver; reached level 3 |
| **Qualification** | 4/4 — all 5 covered, with specificity (4 stakeholders, $4-6M range) |
| **Customer's customer** | 2.5/4 — didn't anchor on the end-user |
| **Closing the call** | 3.5/4 — strong next step, no backup |

**Overall: 3.6/4.** Same score as Sam, same area to grow.

---

## 4. The 4 differences from the SaaS scenario

| Dimension | SaaS (Lesson 06) | Enterprise (Lesson 07) |
|---|---|---|
| **Decision-maker** | 1 (Director of Data) | 1 VP, with 3 stakeholders (CISO, CIO, board) |
| **Timeline driver** | Soft (board goal) | Firm (contract expiry) |
| **Constraints** | Few (1-2) | Many (PCI, SOX, residency) |
| **Budget** | $200-400k | $4-6M |

The 4 differences shape the *depth* of the discovery call,
not the *structure*. The 5-question framework, the
qualification questions, and the close pattern are the
same. What changes is the *specificity* — enterprise
discovery is longer, more constraint-heavy, and more
multi-stakeholder.

---

## 5. The pattern across both mocks

Sam and Maya's transcripts share 6 moves. These are the
moves that work in any discovery call:

1. **Agenda-setting in the first 30 seconds.**
2. **"What does that block?" — the second-question
   pattern.**
3. **"How often?" — the quantification pattern.**
4. **"If the problem disappeared, what would you ship?"
   — the level-3 pain question.**
5. **The 5-question qualification.**
6. **A specific summary + a specific next step.**

The 6 moves are the spine of a 4/4 discovery call. The
rest is adapting to the customer's specifics — the
stakeholders, the constraints, the timeline, the budget.

---

## Try it

Run this scenario with a friend. Have your friend play
"VP of Data at a Fortune 500 financial-services company,"
using Raj's script above (or improvising a different
spin).

You play Maya. Hit the 6 moves. The specific thing to
practice in this scenario is the **multi-stakeholder
qualification** — when there are 4 stakeholders (you,
CISO, CIO, board), the qualification gets longer. The
candidate who can hold 4 stakeholders in their head
without losing the thread is the candidate who passes
the round.

Record it. Listen back. Notice the moments where you
switched from the surface pain to the underlying
constraint (PCI, SOX) to the aspirational outcome
(real-time risk). Those are the senior SA moves.

Run the scenario 2-3 times before the interview. The
investment is 60-90 minutes; the return is the discovery
round.
