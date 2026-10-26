# 10 — Tell Me about Your Biggest Pre-Sales Win

> **Lesson 10 of 11 — Behavioral for SAs** · ~12 min

The "biggest win" question is the most-practiced
behavioral question. The senior SA move is to anchor on
the *customer's* win, not your own — and to show the
specific moves that made it land.

---

## 1. The question

> *"Tell me about your biggest pre-sales win."*

This question tests 4 signals:

- **Customer focus.** Did the customer's outcome drive
  the win?
- **Technical judgment.** Did your technical moves
  matter?
- **Execution.** Did you ship the work on time?
- **Scale of impact.** How material was the win?

The senior SA move is to *anchor on the customer's
win*. The deal size is the headline, but the
*customer's outcome* is the lead. The senior SA tells
a story where the customer succeeded because of *your*
work, not a story where you "won" against a competitor.

---

## 2. The worked STAR story (Maya, Principal SA at
Snowflake)

> **Situation (15 sec):** "My biggest pre-sales win
> was a $6M, 5-year deal with a Fortune 500 healthcare
> customer — anonymized due to NDA — choosing our data
> cloud for a clinical analytics platform. The deal
> was the largest in the region for that year, and it
> had been competitive: 2 incumbents were already in
> the customer's environment. The customer was
> switching from a competitor's on-prem warehouse."
>
> **Task (10 sec):** "I was the lead SA on the deal.
> I was accountable for the customer's technical
> evaluation, the architecture proposal standing up
> to the CTO's review, and the customer choosing us
> over the 2 incumbents."
>
> **Action (60 sec):** "The deal was won in 3
> distinct moves.
>
> Move 1: I spent 2 full days with the customer's
> clinical analytics team, observing their workflow.
> I identified 3 specific issues they hadn't named:
> their queries were 10x slower than they needed to
> be for clinical decision support; their pipeline
> ran hourly and missed 5% of cases; their
> compliance team couldn't audit data lineage end
> to end. Naming the issues was the trust-building
> moment. The customer told me, 'no vendor has
> surfaced these before.'
>
> Move 2: I designed a tailored architecture
> addressing each of the 3 issues. The architecture
> proposed a streaming ingestion layer for the
> clinical data (sub-second freshness); a
> columnar-pruned query layer (10x faster for the
> decision-support use case); and a column-level
> lineage graph (the compliance audit trail). The
> architecture was 60% standard, 40% customized. The
> 40% customized is what won the deal.
>
> Move 3: I built a 4-week POC with the customer's
> actual clinical data, in their environment. I
> worked alongside their team. The POC delivered
> on each of the 3 issues with measurable results:
> query latency dropped from 8 seconds to 0.7
> seconds; ingestion freshness went from hourly to
> 30 seconds; lineage audit was traceable end to
> end. The customer had hard data to take to their
> CTO."
>
> **Result (15 sec):** "The customer chose us. The
> $6M, 5-year deal closed. The customer went live 6
> months later and is now a reference customer for
> the healthcare vertical. The 3 architectural
> innovations we designed became standard features
> shipped to all healthcare customers the following
> year — the columnar-pruned query layer shipped in
> Q1, the streaming ingestion for clinical data
> shipped in Q2, the lineage graph shipped in Q3."
>
> **Reflection (10 sec):** "The transferable lesson:
> the pre-sales win is built in 3 phases, and each
> phase produces a specific asset. Phase 1 (deep
> discovery) produces a list of *unnamed* issues —
> the customer trusts you because you see what
> they don't. Phase 2 (architecture) produces a
> tailored design with 40% customized, which is
> what differentiates you from the incumbents.
> Phase 3 (POC) produces hard data the customer
> can take to the senior stakeholder. The pattern
> works on any pre-sales engagement."

---

## 3. The 4 signals the story hits

1. **Customer focus.** Maya spent 2 days *observing*
   the customer's workflow, not pitching. She named
   3 issues they hadn't named. The customer's
   reference status is the proof.
2. **Technical judgment.** The 3 architectural
   innovations (streaming ingestion, columnar-pruned
   queries, lineage graph) are the *technical*
   differentiators. The 60% / 40% framing is the
   senior SA move — 40% customized wins the deal.
3. **Execution.** The 4-week POC was built in the
   customer's environment with the customer's data.
   Hard data, not promises.
4. **Scale of impact.** $6M, 5-year deal, largest in
   the region, customer became a reference, and the
   architectural innovations shipped to all
   customers.

The story is a 4/4. The "biggest win" question is the
candidate's strongest story; this is the structure.

---

## 4. The 3-phase pre-sales framework

The framework from the worked example, abstracted:

| Phase | Duration | What you do | The artifact |
|---|---|---|---|
| **1. Deep discovery** | 1-2 weeks | Observe the customer's workflow. Identify *unnamed* issues. | A list of 3-5 specific issues the customer didn't know they had |
| **2. Tailored architecture** | 2-4 weeks | Design an architecture that addresses each issue. 40% customized is the goal. | A 1-page architecture brief with 3 options and a recommendation |
| **3. POC** | 2-6 weeks | Build the POC in the customer's environment with the customer's data. | Hard data the customer can take to the senior stakeholder |

The 3 phases add up to 5-12 weeks. The deal closes
in the *evidence* the customer gathers in phase 3.

The senior SA move is to run all 3 phases with rigor.
The junior SA cuts phase 1 (jumping to architecture
before understanding), or phase 2 (using a generic
template), or phase 3 (running the POC in a sandbox,
not the customer's environment).

---

## 5. The "unnamed issues" pattern

The senior SA move in phase 1: surface the issues the
customer *didn't know they had*. This is the highest-
leverage trust-building move.

How to surface unnamed issues:

1. **Observe the workflow.** Don't just ask questions;
   watch the team work. The observation surfaces what
   the team has normalized.
2. **Ask the second question.** When the customer says
   "our queries are slow," ask "what does 'slow' look
   like for the user?" — the answer is usually an
   unnamed issue (e.g., "the clinician is waiting 10
   seconds and falling back to their own spreadsheet").
3. **Compare to peers.** Senior SAs have seen 50+
   similar customers; they know what's normal. The
   comparison surfaces what's abnormal in the
   customer's environment.
4. **Talk to end-users.** The customer team often
   sanitizes their problem description for the
   vendor; the end-users don't.

The unnamed-issues pattern is what differentiates the
SA who *understands the customer's problem* from the
SA who *proposes a solution*. The first wins.

---

## 6. The "60/40 architecture" pattern

The senior SA move in phase 2: a 60/40 architecture.

- **60% standard** — the standard reference
  architecture that any SA would propose. Shows the
  customer that your solution is grounded in proven
  patterns.
- **40% customized** — the tailored components that
  address the customer's *unnamed* issues. Shows the
  customer that you've actually understood their
  problem.

A 100% standard architecture reads as "you didn't
think about us." A 100% customized architecture
reads as "you over-engineered for our edge case." The
60/40 split is the senior SA balance.

---

## 7. The "POC in the customer's environment" rule

The senior SA move in phase 3: build the POC in the
*customer's* environment, with the *customer's* data.

Why this matters:

- **Customer ownership.** The customer feels the POC
  is theirs, not yours. They invest more in making
  it work.
- **Hard data.** The POC produces real performance
  numbers (latency, freshness, audit trail) on the
  customer's actual data, not synthetic data. The
  hard data is what closes the deal.
- **Reference.** After the deal closes, the customer
  can keep the POC environment running as a reference
  architecture.

A POC in the vendor's sandbox doesn't produce any of
these benefits. The senior SA move is to insist on the
customer's environment, with the customer's data, with
the customer's team alongside.

---

## 8. The 3 anti-patterns

### Anti-pattern 1: "I won" framing

You tell the story as "I won the deal against the
competition." The interviewer reads this as "the deal
is about me."

**Fix:** Reframe as "the customer chose us because we
helped them solve a problem they couldn't articulate."
The customer is the protagonist.

### Anti-pattern 2: No specifics

The story is general: "a big deal, complex customer,
great team, lots of work." The interviewer reads this
as "I don't have specific moves to point to."

**Fix:** 3 specific moves with specific outcomes. The
3 phases of the framework.

### Anti-pattern 3: No reflection

The deal happened; the story ends. The interviewer
reads this as "I don't have a model of what works."

**Fix:** Name the transferable lesson. The pattern is
the signal; the deal is the example.

---

## Try it

Identify your biggest pre-sales win (or your most
material customer-facing project). Use the 5-step
process from Lesson 04. Write the STAR story in
90-120 seconds.

Specifically, for this question:

- Name the customer.
- Name the 3 unnamed issues (or equivalent: the
  things the customer didn't know they had).
- Describe the 3-phase process (discovery,
  architecture, POC).
- Quantify the outcome (deal size, customer
  expansion, reference status).
- Reflect on the transferable pattern.

Re-tell out loud. Record. Listen back. The first
time, you'll hear the moments where the story is
"I won" instead of "the customer succeeded." Reframe
those. By the 3rd time, the story will be clean.

This is the *strongest* story in your bank. Master it,
and the "biggest win" question becomes a free win.
