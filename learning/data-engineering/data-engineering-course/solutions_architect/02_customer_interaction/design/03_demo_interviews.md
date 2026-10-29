# 03 — Demo Interviews

> **Lesson 3 of 12 — Customer Interaction** · ~15 min

The second-most-important customer-interaction round. The
demo is where the deal moves from "interesting" to
"concrete," and the moment the customer starts to *see*
themselves using the product. This lesson covers live demo
vs recorded, the 3-phase structure, and what to do when
things break.

---

## 1. Live demo vs. recorded

There are 2 types of demos, and the SA needs to know when
to use which.

| Type | When to use | Pros | Cons |
|---|---|---|---|
| **Live demo** | First demo, executive demo, complex use case | Tailored to the customer; the customer can interrupt; the SA can adapt to questions | Will break. The SA needs recovery skills. |
| **Recorded demo** | Follow-up demo, async to a wider audience, low-stakes scoping | Reliable; no live breakage; can be sent to a wider audience | Generic; not tailored; customer can't interact |

The 80% rule: most demos should be **live**. Recorded
demos are for after the live demo, when the customer
wants to share with their team or has a specific question
to send to a wider audience.

The SA interview almost always tests *live* demo skills,
because that's where the SA adds value. A senior SA can
turn a live demo into a tailored narrative; a recorded
demo doesn't differentiate.

---

## 2. The 3-phase demo structure

Every good demo has 3 phases. The phases have specific
durations and specific modes.

| Phase | Duration | SA's mode | What it sounds like |
|---|---|---|---|
| **1. Frame** | 2-3 min | Set the narrative. Tell the customer what they'll see and why. | "In the next 15 minutes, I'll show you how [customer] would use [product] to [outcome]. I'll pause for questions at 3 points." |
| **2. Show** | 10-15 min | Run the demo. Pause for questions at the 3 promised points. | "Let me start by showing you [scenario]. Here's the data flowing in. Here's the transformation. Here's the dashboard." |
| **3. Close** | 3-5 min | Summarize. Tie the demo to the customer's pain. Propose the next step. | "We've seen [outcome]. This maps to what you said about [pain]. The next step is [specific]." |

The 3 phases add up to 15-20 minutes. The "Frame" phase
is the most-skipped. Without a frame, the customer spends
the first 2-3 minutes of the demo wondering "what am I
about to see, and why?" and disengages.

The 3-phase structure is the same whether the demo is
live or recorded. Live demos also have a "breakage
handling" sub-mode (see Section 4).

---

## 3. The 3 pause points

A senior SA pauses 3 times during the demo. Each pause
has a purpose.

| Pause | When | What the SA says |
|---|---|---|
| **1. After the setup** | After the first 3-5 minutes (showing the data input) | "Before I show you the transformation, are there questions about what we're looking at so far?" |
| **2. After the transformation** | After 5-7 more minutes (showing the key feature) | "Pause here — does this match how you'd expect it to work, given your workflow?" |
| **3. After the output** | After 2-3 more minutes (showing the result) | "Now that you've seen the output, what's your reaction? Anything you'd want to see differently?" |

The 3 pauses serve 3 purposes:

1. **Customer check-in** — does the customer still
   understand what they're seeing?
2. **Course correction** — the SA can adjust if the
   customer is confused or has different expectations.
3. **Engagement** — the customer is participating, not
   passively watching.

A junior SA doesn't pause. They race through the demo and
wonder why the customer doesn't ask any questions at the
end. The customer *can't* ask questions because they
haven't had a chance to formulate any.

---

## 4. Breakage handling

The demo will break. The customer's internet will drop.
The product will have a bug. The data won't load. The
sandbox will be empty. The customer will ask a question
that the demo doesn't cover.

The test is *not* whether your demo is reliable (it won't
be). The test is *how you recover*.

The 3-step recovery pattern:

| Step | What to do | What to say |
|---|---|---|
| **1. Acknowledge** | Don't pretend it didn't happen. Name what broke. | "That's the demo breaking — the data isn't loading. Let me try a quick fix." |
| **2. Recover** | Try a fix. If it works, continue. If it doesn't, have a backup plan. | Switch to a different browser / a recorded clip / a slide / a whiteboarding session. |
| **3. Re-engage** | Pull the customer back. Don't let the break define the demo. | "While we're on the recovery, let me show you [a different feature] that addresses the same problem." |

A worked example:

> **Demo break:** The dashboard is supposed to show
> real-time orders, but it's showing stale data.
>
> **Junior SA:** "Hmm, that's weird. Let me check
> something." (Fumbles for 60 seconds. Customer is silent.
> Demo dies.)
>
> **Senior SA:** "OK, the dashboard's not loading. Two
> things I can do: I can switch to a different browser
> (give it 30 seconds), or I can switch to a recorded clip
> of the same dashboard that I have in my back pocket. Let
> me try the browser first... (30 seconds)... that worked.
> Let me back up to where we were. The dashboard is showing
> the last 5 minutes of orders, and you can see here the
> spike at 9:14am — that's the campaign launch. Is that
> what you'd expect to see in your setup?"

The senior SA did 3 things the junior SA didn't:

1. **Acknowledged the break** ("OK, the dashboard's not
   loading.")
2. **Had a backup** (recorded clip).
3. **Re-engaged the customer** ("Is that what you'd expect
   to see in your setup?") with a question that pulled
   them back into the demo.

The senior SA's recovery took 60 seconds and the demo
continued. The junior SA's recovery took 60 seconds and
the demo died. The difference is the *practice* of the
3-step pattern.

---

## 5. The customer-tailored narrative

A generic demo runs through every feature in order. A
customer-tailored demo follows the customer's narrative.

The 4-step process:

1. **Re-state the customer's pain** (from the discovery
   call). "You mentioned that the schema-change coupling is
   blocking your real-time recommendations."
2. **Map the demo to the pain.** "I'll focus on how [product]
   handles schema evolution without rebuilding the feature
   store."
3. **Show, don't tell.** Walk through the relevant features.
4. **Tie back to the pain.** "So you've seen how [feature]
   solves the schema-change problem. This is what you'd see
   in your setup."

The customer-tailored narrative is the difference between
a 2.5/4 demo and a 4/4 demo. The customer walks away
thinking "this SA actually gets our problem" instead of
"this was a feature tour."

A worked example:

> **Generic demo (junior SA):** "Here's the data ingestion
> feature. Here's the transformation feature. Here's the
> dashboard. Here's the alerting. Here's the API."
>
> **Customer-tailored demo (senior SA):** "Your problem is
> the schema-change coupling between your dbt models and
> the feature store. Let me show you how we typically
> handle that. First, here's how the data lands — it goes
> through a schema-registry-aware ingestion that handles
> backward-compatible changes automatically. Second,
> here's how the feature store consumes it — it only
> rebuilds the features that depend on the changed
> schemas, not the whole feature store. Third, here's the
> impact — the rebuild time goes from 6 hours to 15
> minutes. That maps to your real-time recommendations
> being unblocked."

The customer-tailored demo is half the length, twice as
relevant, and 10x more memorable. The customer remembers
the *outcome* (6 hours to 15 minutes) and the *pain-solution
connection* (schema-change → real-time). They don't
remember the 15 features the SA clicked through.

---

## 6. Honesty about limits

The single biggest trust-killer in a demo is over-claiming.
"We do X" when you don't, or "we can do that" when you
can't.

The senior SA's pattern:

- **Honest about what the product does well.** Showcase
  the strengths confidently.
- **Honest about what the product doesn't do well.** "We
  don't do real-time sub-100ms latency today. If that's a
  hard requirement, [competitor] is a better fit."
- **Honest about workarounds.** "We do X via Y, but it's
  not turnkey — you'd need to write some glue code."

The customer can tell when an SA is over-claiming. The
trust loss is permanent. The senior SA who says "we don't
do that, but here's how we'd handle your use case" is the
SA who gets the deal 3 months later when the customer is
evaluating options.

---

## 7. The "demo close"

The close of the demo is the most-skipped phase. Most SAs
end with "any questions?" — which is a weak close.

The 3 components of a strong demo close:

1. **Summary tied to pain.** "You've seen how we handle
   schema changes without rebuilds, which addresses the
   blocker you described."
2. **What's next.** "The next step I'd suggest is a
   60-minute technical deep-dive where we walk through
   your actual data. Does [date] work?"
3. **Backup.** "If you'd want to share this with your team
   first, I can send a recorded version of what you saw
   today."

The close is what turns a demo into a *next step*. Without
a specific next step, the demo is a memory, not an
agreement.

---

## Try it

Pick a product or solution in your specialty. Plan a
15-minute demo. Use the 3-phase structure. Identify the
3 pause points. Plan a backup for at least 1 expected
breakage. Write the close (summary + next step + backup).

Run the demo out loud, with a friend playing the customer.
At each pause point, your friend should ask a real
question. At some point, your friend should ask you to
show something the demo doesn't cover. Practice the
3-step breakage pattern.

Record it. Listen back. The first time, you'll feel the
demo is too long. The second time, you'll hear the moments
where you rushed or over-explained. The third time, you'll
see how the pauses and the customer-tailored narrative
change the energy of the call.

Do this for 3 different scenarios in your specialty. By
the 3rd, you'll have a pattern you can apply to any new
scenario.
