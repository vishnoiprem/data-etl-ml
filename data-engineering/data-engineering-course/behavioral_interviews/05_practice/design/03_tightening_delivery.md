# 03 — Workshop: Tightening Delivery (From 5 Minutes to 2)

> **Lesson 3 of 5 — Workshops** · ~12 min

A ruthless editing pass to cut every sentence that doesn't
answer "so what." This is the difference between a 2/4
answer and a 4/4 answer.

---

## 1. The problem

Most candidates write stories that are 4-5 minutes long.
A 4-minute answer is a *downlevel signal*. It says: *"I
don't know what's important in this story, so I'm telling
you all of it."* The senior move is to **edit ruthlessly**
until the story is 90-120 seconds, and every sentence
earns its place.

The transformation from 5 minutes to 2 is not a content
transformation. It's an *editing* transformation. The
content is usually already there. The problem is that
2 minutes of signal is buried in 3 minutes of context,
qualifiers, throat-clearing, and over-explanation.

This workshop is the editing pass.

---

## 2. The 4 cuts

There are 4 specific cuts that turn a 5-minute story into
a 2-minute one. Apply all 4 to every story in your bank.

### Cut 1: Setup sentences that don't earn their place

**Before:**

> *"I started at my current company about 3 years ago as
> a Senior Data Engineer. Before that, I was at a smaller
> company for 2 years. The team I joined was a 6-person
> data platform team responsible for..."*

This is 30 seconds of biographical context. The
interviewer doesn't need it. They've read your resume. Cut
it.

**After:**

> *"Last year, on my 6-person data platform team, we..."*

The 30 seconds becomes 5. The interviewer knows you're
qualified (you're in the room). Get to the substance.

### Cut 2: Explanation of things the interviewer already knows

**Before:**

> *"We were using Kafka, which is a distributed messaging
> system, and we wanted to migrate to a streaming
> architecture, which is a different paradigm from the
> traditional batch processing model where..."*

The interviewer knows what Kafka is. They know what
streaming is. They know what batch processing is. Cut.

**After:**

> *"We were on Kafka, running nightly batch jobs that
> produced stale data for our user-facing dashboards."*

5 seconds instead of 30. The information is the same; the
explanation of common knowledge is gone.

### Cut 3: Justification of decisions that don't need it

**Before:**

> *"I chose the dual-write approach because it would
> allow us to validate the new system before cutting
> over, and because it was lower risk than a big-bang
> cutover, and because we had a partner with a hard
> launch date, and because..."*

This is 4 justifications stacked. The interviewer will
follow the first one. Cut the rest.

**After:**

> *"I chose dual-write with a 4-week shadow validation
> period — lower risk than a big-bang cutover, and
> compatible with the partner's hard launch date."*

Two justifications, tightly bound. The "because" chain
that often accompanies this kind of reasoning is almost
always cuttable.

### Cut 4: Outcomes that don't quantify

**Before:**

> *"It worked out well. The team was happy. The
> stakeholders were pleased. The data was much more
> useful."*

Vague positives. The interviewer reads them as
"this person doesn't have a number."

**After:**

> *"Data freshness went from 24 hours to sub-minute.
> Zero downstream breakage. The pattern is now the
> default for the next 2 schema changes on the team."*

Specific. Quantified. Propagated. The "team was happy"
filler is gone.

---

## 3. The "so what" pass

Read the story out loud. After every sentence, ask: *"So
what? What does this sentence contribute to the interviewer's
understanding of my judgment, ownership, or impact?"* If the
sentence doesn't answer "so what," cut it.

Worked example, before and after:

**Before (5 minutes):**

> *"So at my current company, which is a mid-size SaaS
> company that does analytics for e-commerce businesses, I
> was on a team that was responsible for the data
> platform. The team had 6 people, including me, and we
> owned the pipelines that fed our analytics product. We
> were using a batch-based architecture, which meant that
> our customers' dashboards were always at least 24 hours
> stale, and that was becoming a problem because the
> product was shifting toward real-time use cases, and
> our customers were starting to notice. So I led the
> migration to a streaming architecture, which was a
> big project. It took about 4 months. The technical
> work was relatively straightforward — we used Kafka
> and Flink — but the hard part was aligning the data
> science team, who were worried about schema changes
> breaking their downstream models. I worked with them
> for a few weeks to land on a backward-compatible
> schema. We shipped on time, the data was much fresher,
> and the data science team's models didn't break. It
> was a good outcome. The team was happy."*

**After (90 seconds):**

> *"Last year I led the migration of our analytics
> pipeline from nightly batches to streaming. The hard
> part wasn't technical — it was that the data science
> team was blocking the migration because their
> downstream models would break under the new schema.
>
> *I spent 2 weeks listening to them. I came back with
> a backward-compatible schema proposal and an offer to
> be the point of contact for any breakage for the
> first 3 months.*
>
> *We shipped 4 months later. Data freshness went from
> 24 hours to sub-minute. Zero downstream breakage.
> The backward-compat pattern is now the default for
> the next 2 schema changes on the team."*

The "after" has 3 sentences of setup, 1 sentence of
action, 1 sentence of outcome, 1 sentence of takeaway.
90 seconds. Every sentence earns its place.

---

## 4. The discipline

The discipline of "90-120 seconds" is what forces you to
*choose what's important*. If you have unlimited time,
you'll include everything. With a strict time limit, you
have to pick the 1-2 beats that matter and tell only those.

This is also why the practice loop matters. The first
time you edit a story down to 90 seconds, you'll feel
like you're cutting essential content. You probably
aren't. The next time you tell the story to a friend,
they'll tell you which cuts they didn't notice. Then you
cut more. Then you tell it again. Eventually you have a
90-second story where every sentence lands.

---

## 5. The "one more thing" temptation

After the 90-second story ends, there's almost always a
temptation to add "one more thing." The pipeline also
helped the partner team. The pattern was also adopted
by another org. The schema work also led to a follow-on
project.

Resist the temptation. **End on the beat.** The "one more
thing" almost always dilutes the closing sentence. The
interviewer remembers the last sentence you said, not the
second-to-last. If you add a "one more thing," the beat
you worked to land is no longer the closing line.

The exception: if the interviewer asks a follow-up that
explicitly invites more ("tell me more about..."), then
*of course* you continue. The rule is about your
*initial* delivery, not your follow-up.

---

## Try it

Take your longest story (probably 4-5 minutes when you
tell it). Apply all 4 cuts. Time the result. Apply the
"so what" pass. Time it again.

If the result is under 2 minutes, you've successfully
tightened delivery. If it's still over 2.5 minutes,
you missed a cut. Find it.
