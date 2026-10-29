# 02 — Leadership Stories: Influence Without Authority

> **Lesson 2 of 6 — Story Bank** · ~15 min

3 templates for influence / leadership stories, with worked
examples. Most senior candidates don't have enough of these.

---

## 1. What an influence story sounds like

An influence story has:

- A specific person (or group) you needed to convince
- A specific position they started from (and why)
- A specific tactic you used (not just "I talked to them")
- A specific outcome (with a number)

The structure is SOAR-ish but with a different focus: the
*tactic* is the protagonist, not the project.

---

## 2. Template 1: The cross-team alignment

**The shape:**

> I needed [team X] to [do thing Y] so that [project Z] could
> ship. They had reasons not to (or no reason to prioritize
> it). What I did was [specific tactic]. The outcome was [Y
> happened, with metric].

**Worked example:**

> *I needed the data science team to adopt a new schema for the
> analytics pipeline. They had two reasons not to: (1) their
> downstream models would break, and (2) the migration would
> cost them a quarter of model retraining work.*
>
> *What I did: I scheduled a 90-minute working session with the
> 3 data scientists whose models were most affected. I came
> prepared with a backward-compatible schema proposal that
> preserved their existing model interfaces and added the new
> fields with sensible defaults. I also offered to be the
> point-of-contact for any breakage for the first 3 months.*
>
> *Outcome: all 3 data scientists signed off on the schema
> within 2 weeks. Two of them migrated immediately, the third
> delayed 2 months (which we had budgeted for). Zero downstream
> breakage. The backward-compat pattern has since been used for
> 2 subsequent schema changes on the team.*

**The senior signals in this story:**
- A *named* group with *named* concerns
- A *specific* tactic (working session, not "lots of meetings")
- A *specific* concession (backward-compat, point-of-contact)
- A *measurable* outcome (signed off within 2 weeks, zero
  breakage)
- A *transferable* takeaway (the backward-compat pattern)

**Variations to consider:**
- "Tell me about a time you influenced someone more senior
  than you" — same structure, but emphasize the *upward* nature
  of the influence.
- "Tell me about a time you changed someone's mind" — same
  structure, but emphasize the *before/after* of the person's
  position.

---

## 3. Template 2: The reluctant stakeholder

**The shape:**

> [Person X] was skeptical of [change Y] because of [their
> specific concern, not generic resistance]. I addressed the
> concern with [specific tactic]. The result was [outcome].

**Worked example:**

> *The platform team was reluctant to adopt our proposed gRPC
> migration because they'd had a bad experience with a similar
> migration 2 years prior that had caused 3 weeks of
> intermittent 5xx errors. Their specific concern wasn't
> "gRPC is bad" — it was "we don't trust the rollout process
> we have."*
>
> *What I did: I read the postmortem from the previous
> migration. I sat with the platform lead and asked her to walk
> me through what she'd do differently. I built a rollout
> proposal that addressed each of her 3 specific concerns:
> feature-flagged rollout, 1-week shadow mode, explicit
> rollback criteria. I also offered to do the rollout as a
> pair-with-her for the first service.*
>
> *Outcome: she approved the migration. We did the rollout
> together, caught 2 issues during shadow mode, and shipped
> the migration with zero 5xx incidents. The platform team
> has since used the same rollout pattern for 4 subsequent
> migrations. The platform lead and I co-presented the pattern
> at our internal eng all-hands.*

**The senior signals:**
- You understood the *underlying* concern (process, not
  technology)
- You *read the postmortem* (specific dive-deep move)
- You *gave something* (your time, the pairing) to make it
  easy
- You *measured* the outcome (zero 5xx)
- You *propagated* the pattern (4 subsequent migrations, an
  all-hands talk)

**The trap:** it's tempting to make this story about how you
were *right* and they were *wrong*. Don't. The story is about
how you understood *why* they were skeptical and addressed
the underlying concern. They weren't being unreasonable —
they were being appropriately risk-averse based on prior
experience.

---

## 4. Template 3: The leadership-through-teaching story

**The shape:**

> I had a junior engineer who was [struggling with X]. Rather
> than [taking over / writing the code myself], I [taught /
> coached / paired with them]. The result was [they grew into
> Y].

**Worked example:**

> *A new hire on my team was struggling with code review —
> not technically, but in prioritization. They were
> reviewing 5-6 PRs a day in detail, which was blocking
> their own work and not actually catching more bugs than a
> faster review would.*
>
> *What I did: I paired with them for a week of code reviews.
> I demonstrated a 20-minute "first-pass" review that looked
> for the 3 things that actually matter (correctness on the
> hot path, interface contract, test coverage on changed
> code) and skipped the rest. We calibrated together on
> what to look for.*
>
> *Outcome: within 2 weeks, their median review time dropped
> from 90 minutes to 22 minutes. They caught 2 real bugs in
> the first month that would have shipped to production. Six
> months later, they were the team's go-to reviewer for the
> data-pipeline area and were mentoring a new hire on the
> same skill.*

**The senior signals:**
- You saw a *system* problem (the team would benefit from
  faster reviews) not just an individual problem (this hire
  is slow)
- You *demonstrated* the skill rather than telling
- You *measured* both the speed and the quality outcomes
- You *propagated* the learning (they now teach it)

**The trap:** this story is easy to tell as "I taught someone
something," which is E4. The senior move is to emphasize
*what changed in the team* because of the teaching, not just
what the individual learned.

---

## 5. How to choose which template to use

| Question | Best template |
|---|---|
| "Tell me about influencing without authority" | Template 1 (cross-team alignment) |
| "Tell me about changing someone's mind" | Template 2 (reluctant stakeholder) |
| "Tell me about developing others" | Template 3 (leadership through teaching) |
| "Tell me about leading a project" | Template 1, but the *project* is the protagonist |
| "Tell me about a time you had to convince someone senior" | Template 2, with the seniority delta emphasized |

If you have only 1 leadership story in your bank, make it
Template 1 — it flexes to the most questions.

---

## Try it

Pick one of the 3 templates above. Spend 30 minutes writing
your own version of the template using your own career. Apply
the 5-question "so what" test from `02_theory/06_so_what_test.md`
and the 5-bar checklist from
`01_fast_track/design/03_avoiding_downleveling.md`.

If your story passes both tests, add it to your bank. If not,
find a different career moment and try again.
