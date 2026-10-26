# 05 — Ambiguity Stories: Operating in Incomplete Information

> **Lesson 5 of 6 — Story Bank** · ~12 min

3 templates for ambiguity stories, with worked examples. The
ambiguity story is the one that separates senior from
mid-level. Most mid-level engineers describe ambiguity as
something that happens *to them*. Senior engineers describe
ambiguity as something they *cut through*.

---

## 1. What an ambiguity story actually tests

The interviewer is asking: when you don't have the full
picture, what do you do? The wrong answers are:

- "I ask a lot of questions" (philosophy, not evidence)
- "I try to keep stakeholders updated" (process, not
  judgment)
- "I keep moving" (action without direction)

The right answer is a specific instance where you took a
vague mandate or unclear situation, did *something
concrete* to reduce the ambiguity, and ended up with a
clearer problem to solve. The something-concrete is the
protagonist.

---

## 2. Template 1: The vague-mandate story

**The shape:**

> I was given [vague 1-line mandate]. The mandate was
> ambiguous because [specific reason]. What I did to
> reduce the ambiguity was [specific tactic]. The
> resulting problem statement was [clearer]. The outcome
> was [measurable].

**Worked example:**

> *I was given a 1-line mandate from my director: "improve
> our data quality." That was the brief. The mandate was
> ambiguous because "data quality" could mean anything
> from schema validation to freshness to accuracy to
> coverage.*
>
> *What I did: I scheduled 4 30-minute interviews with
> the top 4 consumers of our data, asked each of them
> "what do you wish was different about the data you
> consume?", and wrote down their answers verbatim. The
> result was a 1-page list of the actual problems they
> cared about. Three of the four had the same top
> problem: late-arriving events in the user-events table
> (events were arriving 6-48 hours late, breaking their
> dashboards).*
>
> *I scoped the project to that. I shipped a fix in 6
> weeks that cleared a 2-year backlog of late-event
> tickets. The other problems on the list became
> separate, well-scoped projects for other engineers.*
>
> *If I had skipped the interviews and started building
> generic data-validation tooling, I would have spent 3
> months building something nobody specifically wanted.
> Instead, I spent 4 hours on the interviews and 6
> weeks on a fix that 3 out of 4 consumers cared about
> deeply.*

**The senior signals:**
- A *named* tactic (4 interviews, specific question, 1-page
  list)
- A *specific* synthesis (3 of 4 had the same problem)
- A *scoping* move (cut the project to the actual problem)
- A *measurable* outcome (6 weeks, 2-year backlog cleared)
- A *counterfactual* (what would have happened if you'd
  skipped the interviews)

**The trap:** it's tempting to make this story about the
"tool" you built. The senior move is to make the *cutting
through the ambiguity* the protagonist. The tool is a
sentence; the synthesis is the story.

---

## 3. Template 2: The unclear-requirements story

**The shape:**

> I was asked to [build X]. The requirements were unclear
> because [specific reason]. What I did to make them
> concrete was [specific tactic]. The result was
> [clearer requirements + a different/better scope].

**Worked example:**

> *I was asked to build a "user analytics dashboard." The
> requirements were unclear because the person asking
> (a product manager) had a vision in her head but
> hadn't written it down, and the 3 stakeholders who
> would consume the dashboard each had different ideas
> about what it should show.*
>
> *What I did: rather than building the dashboard, I
> scheduled 3 45-minute sessions with the 3 stakeholders
> and asked each of them to draw on a whiteboard what
> they wished the dashboard would look like. I took
> photos. I then spent 2 hours synthesizing the 3
> drawings into a 1-page spec with 5 specific questions
> marked "unresolved" — one for each place the 3
> drawings disagreed.*
>
> *I sent the spec to the PM and asked her to schedule
> a 30-minute meeting with the 3 stakeholders to resolve
> the 5 questions. The meeting took 25 minutes. We
> shipped the dashboard 4 weeks later, on the first
> attempt, and 2 of the 3 stakeholders said it was
> exactly what they wanted.*
>
> *The alternative would have been to start building
> and resolve the disagreements as they came up during
> development. That approach would have taken 2x
> longer and produced something that none of the 3
> stakeholders felt ownership of.*

**The senior signals:**
- *Refused* to start building without resolution
- Used a *creative* tactic (whiteboard drawings, photos)
- Made the PM *own* the resolution meeting
- *Quantified* the alternative (2x longer, lower
  ownership)

**The trap:** the trap is to make the story about how you
saved the project by being diligent. The senior move is
to make the story about the *people work* — getting 3
stakeholders to converge on a shared spec.

---

## 4. Template 3: The decision-with-incomplete-info story

**The shape:**

> I had to decide [X] without full information because
> [specific reason]. I made the call based on [specific
> signal I did have]. The result was [outcome]. The
> thing I'd watch for that would change my mind was
> [specific].

**Worked example:**

> *We had a production issue that was degrading user
> experience but not breaking the service. The diagnosis
> was unclear — we had 3 plausible root causes and
> couldn't reproduce in staging. I had to decide
> whether to roll back the previous deploy (which would
> cost us 2 weeks of work) or to push a hotfix (which
> might not address the root cause).*
>
> *I made the call to push the hotfix, based on the
> signal that the degradation correlated strongly with
> one specific deploy timestamp and the hotfix addressed
> the most likely root cause. I told the team: if the
> hotfix doesn't reduce the degradation by 50% within 2
> hours, we roll back.*
>
> *The hotfix reduced the degradation by 80% within 90
> minutes. We were back to normal. The thing I would
> have watched for that would have changed my mind: if
> the degradation had been customer-visible (it
> wasn't, just internal metrics), I would have rolled
> back immediately rather than risk the hotfix making
> things worse.*

**The senior signals:**
- A *named* decision (hotfix vs. rollback)
- A *named* signal (deploy correlation, magnitude of
  degradation)
- A *named* trigger that would change the decision (50%
  reduction within 2 hours)
- A *named* boundary (customer-visible vs. internal-
  only)
- A *measurable* outcome (80% reduction in 90 minutes)

**The trap:** the trap is to make this story about being
right. The senior move is to make it about the *decision
framework* — what signals you used, what would change
your mind. The right answer is a process the interviewer
can imagine themselves using.

---

## 5. The "vague is bad" reminder

Ambiguity questions are notorious for getting vague
answers. Candidates will say "I ask a lot of questions"
or "I keep stakeholders updated" — both of which are
generic and unfalsifiable.

The fix: every ambiguity story has to have a *specific
tactic that produced a specific insight*. If your story
is "I asked questions and figured it out," it's not
specific enough. The interviewer will follow up: "what
*specific* question did you ask, and what *specific*
answer changed your approach?" If you don't have a
specific answer to that follow-up, the story is too
vague.

---

## Try it

Pick one of the 3 templates. Write your own version. The
test: can a friend read your story and identify the
*specific tactic* you used to cut through the ambiguity?
If they can't, the story is too vague. Rewrite until the
tactic is unmistakable.
