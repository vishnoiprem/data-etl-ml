# 04 — Conflict Stories: Disagreement, Pushback, Resolution

> **Lesson 4 of 6 — Story Bank** · ~12 min

3 templates for conflict / disagreement stories, with worked
examples. The conflict story is the one most likely to get
candidates downleveled — and the one with the highest payoff
when told well.

---

## 1. Why conflict stories are the most downleveled

Conflict stories fail in two ways:

1. **The "I was right" story** — the candidate describes how
   they were right and the other person was wrong, and how
   they won. This is a *huge* downlevel. The interviewer
   reads it as "this person will be the source of conflict
   on my team."
2. **The "I was wrong" story** — the candidate describes a
   conflict they handled badly. With no growth beat, this
   reads as "this person is still bad at conflict."

The senior version of the conflict story has three moves:

- Describe the *other person's* position charitably and
  accurately
- Describe the *tactic* you used (not just the outcome)
- Describe the *synthesis* — what emerged from the
  disagreement, not who won

---

## 2. Template 1: The technical-disagreement story

**The shape:**

> [Person X] and I disagreed about [technical approach Y].
> Their concern was [specific]. My position was [specific].
> What I did was [specific tactic]. The synthesis was
> [what we ended up with], which was better than either
> original position.

**Worked example:**

> *The data infra lead and I disagreed about whether to use
> Kafka or Kinesis for our new event pipeline. His concern:
> Kinesis is fully managed, lower operational burden, and
> our team already has AWS expertise. My position: Kafka
> has better throughput characteristics and we already have
> Kafka expertise on the analytics team.*
>
> *What I did: I didn't try to win the argument. I asked
> him to write down the specific operational risks he was
> worried about (he came up with 3: on-call burden, vendor
> lock-in, blast radius). I wrote down the specific
> technical risks I was worried about (I came up with 2:
> throughput ceiling, multi-region replication). We
> presented both lists to the team.*
>
> *The synthesis: we landed on Kafka, but with three
> concessions I hadn't originally proposed: (1) a
> multi-region active-passive setup instead of active-
> active, to bound the blast radius; (2) a 1-week shadow
> mode before cutover, to validate throughput; (3) a
> quarterly review where we'd re-evaluate the choice.
> The infra lead signed off. We've been running it for
> 14 months, zero incidents, and we're now in the third
> quarter of the periodic review process.*

**The senior signals:**
- The *other person's* concern is described specifically
  and reasonably
- The *tactic* is described (write down the risks, present
  both lists)
- The *synthesis* is genuinely better than either original
  position (3 concessions from you, not zero)
- A *measurable* outcome (14 months, zero incidents)
- A *transferable* pattern (the periodic review process)

**The trap:** it's tempting to tell this as "I was right
about Kafka." The senior move is to tell it as "we both
had legitimate concerns, and the answer was a synthesis
that neither of us would have reached alone."

---

## 3. Template 2: The pushback-on-the-manager story

**The shape:**

> My manager wanted [X]. I thought [Y] was better. The
> conversation went [specifically]. The result was
> [outcome].

**Worked example:**

> *My manager wanted to do a big-bang cutover for a
> migration that I owned. I thought shadow mode for 3
> weeks was the right call. The conversation: I didn't
> push back in the meeting (I could tell he had already
> committed to the big-bang approach with his director).
> I sent a follow-up email with a 1-page risk doc: the
> 3 specific things most likely to go wrong, the
> mitigation cost, and a proposed shadow-mode alternative
> with timeline.*
>
> *He replied within 2 hours and agreed to the shadow
> mode. The cutover happened on schedule, and 2 of the
> 3 risks I had flagged did materialize during shadow
> mode — we caught both before they hit production.*
>
> *The result: he later told me the risk doc was the
> reason he changed his mind. The pattern — flag risks
> in writing, with a specific alternative — has become
> my default for any disagreement with someone more
> senior.*

**The senior signals:**
- You *chose* the medium (writing, not a meeting) for
  tactical reasons
- You *prepared* a specific alternative, not just
  disagreement
- You *named* the risks specifically (3 things, not
  vague concerns)
- You *credit* the manager for changing his mind
- The *pattern* propagated

**The trap:** the trap is to tell this as "I was right
and convinced my manager." The senior move is to honor
the manager's original position (he had good reasons —
he'd already aligned with his director) and frame the
result as a *better answer* that emerged from the
exchange.

---

## 4. Template 3: The peer-feedback story

**The shape:**

> A peer was doing [X] that was problematic. I raised it
> with them in [specific setting]. The conversation went
> [specifically]. The result was [change in behavior].

**Worked example:**

> *A peer on my team was giving terse, blunt feedback in
> code reviews that was starting to bother other team
> members. I heard about it 3 times in a week from
> different people.*
>
> *What I did: I asked the peer for a 30-minute 1:1. I
> started with "I want to share an observation, not a
> criticism, and I want to understand if I'm reading
> this right." I described the pattern I'd heard
> (specific examples, with PR links). I asked if there
> was something I was missing.*
>
> *He told me he was under a lot of personal stress and
> had been cutting corners on tone because he was
> trying to move fast. He didn't realize it was
> affecting the team. We agreed on a small experiment:
> he would draft his review comments in a doc first,
> then paste, and we would check in after 2 weeks. The
> team feedback 2 weeks later was noticeably better,
> and the doc-then-paste habit stuck.*
>
> *What I learned: most "tone" problems are really
> "context" problems. The person doesn't intend to be
> harsh; they're just optimizing for the wrong thing.
> Surfacing the actual context (team feedback,
> specific examples) usually gets to the real cause
> faster than telling them to "be nicer."*

**The senior signals:**
- A *specific* pattern you noticed (3 times, different
  sources)
- A *tactical* choice of setting (1:1, not in public)
- A *humbling* discovery (the cause was personal, not
  malicious)
- A *measurable* outcome (team feedback 2 weeks later)
- A *transferable* pattern (context vs. tone)

**The trap:** this story is easy to tell as "I gave
someone feedback and they improved." The senior move is
to emphasize the *learning you took from it* — what you
now understand about how tone problems actually work.

---

## 5. The don't-blame rule, restated

Every conflict story must avoid blaming the other person.
The senior move is to describe the *situation* and the
*tactic*, not the *person*:

- "The data infra lead was being unreasonable" — bad
- "The data infra lead had a legitimate concern about
  operational burden" — good

- "My manager was being stubborn" — bad
- "My manager had already aligned with his director on
  the cutover approach" — good

- "My peer was being harsh" — bad
- "My peer was under personal stress and didn't realize
  the impact" — good

The senior move is to *always* have a charitable,
specific reason for the other person's position. Even if
the reason is "they were being unreasonable" — find a
*more specific* framing that explains *why* they were
being unreasonable. "He was being unreasonable" is a
judgment. "He was being unreasonable because he'd had
a bad experience with a similar migration 2 years ago"
is a charitable description of the underlying cause.

---

## Try it

Pick one of the 3 templates. Write your own version. Apply
the don't-blame rule rigorously. Have a friend read the
story and ask them: "does the other person in this story
sound like a reasonable person with a specific view?" If
not, rewrite.
