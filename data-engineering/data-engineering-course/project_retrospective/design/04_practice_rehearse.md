# 04 — Practice: Rehearse Your Story

> **Lesson 4 of 6** · ~25 min

The 5/3/90-second versions of the same retrospective,
how to cut without losing the impact, and the
"what sounds bad" tells that surface only when you
record yourself. The practice mechanics that turn a
written retrospective into an interview-ready one.

---

## 1. Why rehearse

Writing a retrospective is 40% of the work. Rehearsing
it is the other 60%.

A written retrospective is read at ~200 words per
minute. A spoken retrospective runs at ~150 words
per minute (slower, with pauses for breath and
emphasis). The spoken version is *different* — it
has tone, pacing, and the small "um"s and "uh"s
that mark you as unrehearsed.

A senior candidate doesn't write a great retrospective
and then wing it. A senior candidate writes it,
rehearses it at 3 lengths, records themselves, and
listens back. The recording is the move that most
candidates skip.

This lesson is the mechanics of that rehearsal.

---

## 2. The 5/3/90 ladder

Every retrospective you write should be rehearsed at
**three lengths**: 5 minutes, 3 minutes, and 90
seconds. The interviewer won't tell you which length
they want. The shape of their question implies it.

### The 5-minute version (the default)

The full structure from Lesson 03: Context, Approach,
Outcome, Lessons, What I'd Do Differently. This is
the version you lead with when the interviewer says:

- "Walk me through a project you're proud of."
- "Tell me about a complex technical effort you led."
- "Tell me about a re-platforming project."

If they give you 5 minutes of airtime, use all 5. If
they give you less, cut.

### The 3-minute version (the tight version)

The same 5-beat structure, but with less detail on
each beat. You trim the Approach and Outcome beats
the most (they have the most detail to spare). You
keep the Context, Lessons, and "What I'd Do
Differently" beats intact — they're the signal.

The 3-minute version is what you use when the
interviewer says:

- "Tell me about a project you led." (no "complex"
  qualifier)
- "Give me a 3-minute version of your biggest
  project."
- A question where the time pressure is implicit.

### The 90-second version (the elevator pitch)

The 5 beats compressed to 5 sentences. Context in 1
sentence. Approach in 1 sentence. Outcome in 1
sentence. Lessons in 1 sentence. "What I'd Do
Differently" in 1 sentence. Total: ~150-180 words
at 150 wpm = 90 seconds.

The 90-second version is what you use when:

- The interview is running short and the interviewer
  asks for a quick version.
- You're in a recruiter screen (where the format is
  always tight).
- The interviewer asks a behavior question that your
  PR can answer, and you need to land the punchline
  fast.

**Every retrospective you write should have all 3
versions rehearsed.** If you can't compress to 90
seconds, you don't actually know the story. If you
can't expand to 5 minutes, you don't have the depth.

---

## 3. How to cut without losing the impact

The biggest mistake candidates make when compressing
is to **cut the lessons**. That's the worst cut
possible. The lessons are the signal. The Context
and Approach are setup.

The right cuts, in order:

### Cut 1: The Context — keep the number, drop the team

The Context beat is setup. The interviewer needs
the *baseline* (the number that made the project
necessary), not the full team description. Drop the
team size, the org chart, the project history.
Keep the one number that anchors the rest of the
story.

**Before (45s):** "We had a 4-year-old nightly ETL
pipeline running on a custom Airflow-on-EC2 setup
that I'd inherited when I joined the team in 2022.
The runtime had crept to 8 hours, the cost was
$180k/year, and the data was 24 hours stale by the
time the morning dashboards ran. The data science
team had started working around the staleness with
manual snapshots — which was expensive, error-
prone, and unsustainable."

**After (15s):** "We had a 4-year-old nightly ETL
pipeline that was taking 8 hours to run and costing
$180k/year, with 24-hour data staleness."

The number — the 8 hours, the $180k, the 24 hours —
is what makes the project concrete. The setup is
forgettable.

### Cut 2: The Approach — keep the judgment call, drop the timeline

The Approach beat is the heart of the PR. The
interviewer needs the *judgment call*, not the
gantt chart. Drop the week-by-week timeline, the
standup cadence, the meeting count. Keep the one
decision that defines the project.

**Before (90s):** "I spent 2 weeks just listening
to the data science team. I scheduled a 90-minute
working session with the 3 data scientists whose
models were most affected. I came prepared with a
backward-compatible schema proposal that preserved
their existing model interfaces and added the new
fields with sensible defaults. I also offered to be
the point-of-contact for any breakage for the first
3 months. All 3 signed off within 2 weeks. Two
migrated immediately, the third delayed 2 months
(which we'd budgeted for). The migration took 4
months from kickoff to cutover, with a 3-week
shadow mode before the final cutover."

**After (45s):** "I spent 2 weeks listening to the
data science team — what they needed, what would
break, what was non-negotiable. I came back with a
backward-compatible schema that preserved their
model interfaces and added the new fields with
defaults. I also offered to be the point-of-contact
for any breakage for the first 3 months. They
signed off in 2 weeks."

The judgment call — the listening-first approach,
the backward-compat schema, the point-of-contact
commitment — is what makes the Approach beat
senior. The timeline is for the project post-mortem,
not the interview.

### Cut 3: The Outcome — keep the surprise, drop the recap

The Outcome beat needs *one* improvement number
and *one* surprise. The recap of every other metric
is filler. Cut it.

**Before (90s):** "We shipped on schedule. Runtime
went from 8 hours to 45 minutes — a 10x improvement.
Cost dropped from $180k/year to $72k/year, a 60%
reduction. Data freshness went from 24 hours to
sub-minute. Zero downstream breakage across the 12
data-science models. The pattern is now used for
the next 2 schema changes on the team. The team
grew from 4 to 6 during the project."

**After (45s):** "We shipped on schedule. Runtime
went from 8 hours to 45 minutes. Cost dropped 60%.
The surprise: the cost reduction was larger than
we'd projected, but the migration took 2 weeks
longer than estimated because 3 of our 12 source
systems had un-documented schema drift that we
caught in shadow mode."

The improvement number anchors the result. The
surprise is what makes the Outcome beat credible.
The rest is recap.

### Cut 4: The Lessons — never cut

The Lessons beat is the signal. Don't cut it. If
you have to cut somewhere else, cut more from
Context or Outcome.

### Cut 5: The "What I'd Do Differently" — never cut

Same. The "What I'd Do Differently" beat is the
self-awareness signal. Don't cut it. If you have
to compress further, merge the 2-3 changes into
1-2 changes ("Two things I'd change: I'd write the
design doc as a shared doc, and I'd set up a
shared Slack channel on day 1 — both would have
saved us 2-3 weeks of miscommunication.").

---

## 4. Recording yourself + the "what sounds bad" tells

The single highest-leverage practice technique is
**recording yourself and listening back.** Most
candidates rehearse in their head, which doesn't
surface the problems. Recording does.

### How to record

- Use your phone. Voice memo is fine.
- Record 3 takes of each retrospective: the
  5-minute, the 3-minute, the 90-second.
- Listen back with a pen. Note every "um", "uh",
  "like", "you know", and "kind of" you hear.

### The 7 "what sounds bad" tells

These are the patterns that surface in the
recording but not in your head. If you hear any of
them, fix them before the interview.

**Tell 1: "So basically..."** (and its cousins
"so yeah", "so essentially"). This is a
filler-word signal that you're stalling for time.
Cut it. Start with the noun.

**Tell 2: "I think maybe..." / "I guess..."** This
is the hedge that signals you don't own the
decision. Replace with: "I decided..." or "We
decided...". Own the call.

**Tell 3: "We did X, we did Y, we did Z" with no
"I".** This is the "no-I" problem. In a 5-minute
retrospective, you should say "I" at least 5-7
times. The interviewer is evaluating *you*, not
your team.

**Tell 4: "It was a really hard project" / "It was
a very complex system".** These are vague intensifiers
that don't earn their keep. Cut them or replace with
the actual number.

**Tell 5: "Unfortunately..." / "The problem was..."**
This is the apologetic opener that signals you're
about to make an excuse. Replace with: "The
unexpected part was..." or "The thing that went
differently was...". Reframe from excuse to
observation.

**Tell 6: Long pauses (>2 seconds).** These signal
that you've lost the thread. If you're pausing,
you're not rehearsed. Practice until the flow is
continuous.

**Tell 7: Trail-offs ("...and stuff", "...and all
that", "...whatever").** These signal that you
don't know how to end the sentence. End with a
period, not a fade. Every sentence should have a
clean landing.

### The fix

After listening to the recording, transcribe one
take by hand. You'll find that the spoken version
is 10-20% longer than the written version, and
that the cuts you need to make are *different*
from the cuts you'd make on the page. Rewrite
from the transcription, not from the original.

Do this 3 times for each retrospective. By the
third take, the filler is gone and the structure
is automatic.

---

## 5. The "tell me a story you haven't told yet" test

The hardest version of the PR question is when the
interviewer has heard your primary and asks for a
different one. They want to know if you have
*depth*, not just one polished story.

The fix: rehearse **all 3** of your retrospectives
at all 3 lengths (5/3/90). That's 9 rehearsed
versions. It's 2-3 hours of practice. It's the
single biggest differentiator between a candidate
who can tell one good story and a candidate who can
tell any story on demand.

---

## Try it

Pick one of your 3 retrospectives. Rehearse it at
all 3 lengths (5/3/90 seconds). Record each one.
Listen back. Note the tells. Rewrite from the
transcription. Re-record.

When you can do all 3 lengths cleanly without
notes, you're ready for the interview.
