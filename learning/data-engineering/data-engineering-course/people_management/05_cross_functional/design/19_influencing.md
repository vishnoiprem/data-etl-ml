# 19 — Influencing Without Authority

> **Lesson 19 of 21 — Cross-functional Collaboration** · ~20 min

The influence-vs-power model, the 5 sources of influence, and
how to use them. Influence is the substrate of every
cross-functional relationship. The EM who has formal
authority over their team but no influence outside it is the
EM who can't ship cross-team projects.

---

## 1. Influence vs power

Power is **formal authority** — the ability to direct
someone's work, evaluate their performance, or approve
their compensation. Power is what you have over your
direct reports.

Influence is **the ability to shape someone's decisions
without the authority to direct them**. Influence is what
you have over your peer EMs, your PM partner, your
skip-level, and the rest of the org.

The mistake new EMs make: trying to use power where they
have only influence. The PM who's late on a deliverable
isn't going to respond to "I'm your EM, get this done."
The PM will respond to "here's how this affects your
team's customer commitment."

The senior move: **diagnose whether the relationship is a
power relationship or an influence relationship**, and use
the right tools for the right context.

---

## 2. The 5 sources of influence

The classic framework is from French and Raven (1959). It's
50+ years old and still the most useful model for this.

| Source | What it means | When to use it |
|---|---|---|
| **Expertise** | "I know something you don't." | Technical decisions, architectural choices, deep domain knowledge. |
| **Relationship** | "I trust you personally." | Conflict resolution, sensitive decisions, when stakes are high. |
| **Data** | "The numbers show X." | Strategic decisions, prioritization, when opinions are split. |
| **Reciprocity** | "I helped you with Y, can you help me with Z?" | Cross-team asks, when you have a track record. |
| **Legitimacy** | "I'm the right person to make this call." | When you have a formal role, in your domain. |

The senior move is to **combine sources**. The EM who
shows up with data + a relationship + a specific
proposal is the EM who gets the decision. The EM who
shows up with one source ("the data says X") is the EM
who has to fight for it.

---

## 3. The "build the relationship before you need it" pattern

The most important influence move is to **build the
relationship before you need it**. The EM who reaches out
to a peer EM for the first time when there's a conflict
is the EM who loses the conflict. The EM who has been
having coffee with the peer for 6 months is the EM who
resolves the conflict in a 15-minute conversation.

The pattern:

1. **Identify the 5-10 people you need to influence** in
   the next 6-12 months. Peer EMs, PM partners, Design
   partners, key cross-functional stakeholders.
2. **Build the relationship proactively.** 30-minute
   coffee, 1:1, or async "what are you working on"
   message. The senior move is to **be specific about
   what you want to learn** — not just "let's get to
   know each other."
3. **Show up when they need help.** Reciprocity is built
   by small acts over time. The EM who helped the PM
   partner debug a customer issue 3 months ago is the
   EM who gets the PM's help on the next big project.
4. **Make the ask when you need the influence.** When
   you need the relationship, name it explicitly: "I
   need your help on [X]. Here's why it matters to your
   team. Here's what I'm asking for."

---

## 4. The "data + relationship + proposal" pattern

The most useful influence script is to combine the 3
sources:

> *"I want to talk about [X]. The data tells us [specific
> finding, with numbers]. Our relationship has been [X —
> we worked together on Y, you've been helpful on Z, I
> trust your read on this]. Here's my proposal: [specific
> proposal, with the tradeoff]. What do you think?"*

The senior move is the last sentence. The peer who is
asked to weigh in is the peer who collaborates. The peer
who is told what to do is the peer who resists.

---

## 5. The "I'll do the work" move

Sometimes the most useful influence move is to **just do
the work**. The EM who wants the team to adopt a new
practice but can't get buy-in can build a prototype in
their own team and show the results. The PM who wants a
new feature but can't get engineering buy-in can write the
spec and design the mocks.

The senior move is to **do the smallest possible version**
of the work, demonstrate the value, and let the others
adopt. The "build it and they will come" pattern works
when the build is small and the value is clear.

The mistake: building the full thing and then trying to
get adoption. The full build is a 6-month investment that
nobody has approved. The smallest possible version is a
2-week spike that demonstrates the value.

---

## 6. The 3 signs your influence is failing

| Sign | What it means | What to do |
|---|---|---|
| **You're being asked the same questions repeatedly.** | Your stakeholders don't trust that the answer is stable. | Write it down in a 1-pager, share proactively, refer people to it. |
| **Decisions are being made without you.** | You're not in the room. | Diagnose why. The senior move is to ask directly: "I noticed the decision was made without me — was that intentional?" |
| **You're being polite-listened-to but not action-ized.** | Your stakeholders are nodding but not following through. | Switch from influence to escalation. The senior move is to escalate to a shared boss with the specific request: "I need help getting this unstuck." |

The mistake: trying to influence harder when the
influence is failing. Sometimes escalation is the right
move. The senior move is to **escalate cleanly** — name
what you tried, name what's blocked, name the specific
unblock you need.

---

## 7. A worked example: influencing the security team to
adopt our logging standard

The security team has its own logging standard. The
platform team wants them to adopt the new standard for
consistency. The platform team has no formal authority
over the security team.

> **Sam (platform EM):** "I want to talk about the logging
> standard. The data tells us we have 3 different
> log formats across the org, and the SIEM integration
> costs us 30% of our incident response time. Our
> relationship has been good — we collaborated on the
> IAM rollout last year. Here's my proposal: we build a
> 1-week spike that converts the top 5 security log
> sources to the new format and measures the SIEM
> integration time. If the spike shows a 50%+ reduction
> in integration time, we co-present the results to the
> CTO and propose a 90-day adoption plan. What do you
> think?"
>
> **Security EM:** "I'm not opposed in principle, but I
> need to understand the migration cost. What's the
> 1-week spike going to require from my team?"
>
> **Sam:** "1 engineer, 20% of their time, for 1 week. I'll
> provide the platform team support. If the spike works,
> the 90-day plan is your call on the timeline."
>
> **Security EM:** "Okay, let's do it. Send me the proposal
> doc by end of week."

**What makes this land:** Sam combined data (3 formats, 30%
of incident response time), relationship (referenced the IAM
collaboration), and a specific proposal (1-week spike, 1
engineer, 20% time, 50% threshold). The proposal is small
enough to be low-risk. The metric is specific enough to be
measurable. The Security EM has ownership of the
follow-through. The senior move is the metric — 50%
reduction in integration time — because it makes the
decision criterion explicit and un-gameable.

---

## 8. Canonical questions this lesson answers

From `docs/reference/em_interview_canonical_questions.md`:

- People Management #12: *"Tell me about a time you had to
  influence someone without authority."*
- Behavioral #3: *"Tell me about a time you had to
  influence a peer team."*
- Behavioral #34: *"Tell me about a time when you had to
  work with a team that had different priorities."*
- Behavioral #84: *"Tell me about a time when you had to
  build a relationship with a stakeholder."*
- Behavioral #120: *"Tell me about a time when you had to
  influence someone without authority."*

---

## Try it

Identify 1 cross-functional decision you need to make in
the next 30 days. Diagnose which of the 5 sources of
influence you have for it. If you only have 1, the
senior move is to **build the others before the
decision**. If you have 3+, you have a strong case.

---

## Action item

This week, identify the 5-10 people you need to influence
in the next 6-12 months. For each, write the current
state of the relationship (1-2 sentences: have we met?
when was the last 1:1? what's the trust level?). The
senior move is to **proactively reach out to the 3 with
the lowest trust** before you need them.