# 03 — A Sr. SA at AWS Shares His Experience

> **Lesson 3 of 8 — SA Interview Introduction** · ~15 min

An interview-style narrative from "Raj," a Sr. Solutions
Architect at AWS in the data-and-analytics specialty. This is
a composite of conversations I've had with Sr. SAs at AWS,
GCP, and Snowflake over the last 3 years. Names and specific
deal details are fictionalized; the shape of the work is real.

Read this as a story, not a tutorial. It will calibrate your
expectations for what the SA role actually feels like.

---

## 1. The setup

Raj is a Sr. SA at AWS, in the data-and-analytics specialty,
based in a major US city. He's been at AWS for 5 years — 2
years as an SA I, 3 years as a Sr. SA. Before AWS, he was a
data engineer at two different companies for 6 years total.
He covers a territory with ~40 named accounts, of which he
actively works 12-15 at any given time. His deals range from
$200k/year for a mid-market customer to $20M/year for a
strategic enterprise account.

His compensation: $185k base + $260k RSU + $90k variable
(performance-based, partially tied to deal outcomes). Year-1
total: ~$535k.

---

## 2. The interview (paraphrased)

> **Q: Walk me through a typical week.**

**Raj:** 60% of my time is in customer meetings. 25% is
deep-work — architecture diagrams, whiteboarding, proposals,
public content. 15% is internal — deal-team syncs, 1:1s with
my manager, peer SAs, the AE on each of my accounts.

A Tuesday last week: I had a discovery call at 9 with a
healthcare customer who's evaluating EMR + Lake Formation.
That's a 3-month deal, $1.2M/year, two competitors in the
mix. Then I had a 1-hour architecture review at 11 with a
fintech customer — they're building a real-time fraud-
detection pipeline on Kinesis and want my eyes on their
throughput plan. Lunch with the AE on the healthcare
account — relationship maintenance, not a working lunch.
The afternoon was 3 hours of deep-work: I wrote the
architecture proposal for the healthcare customer and
reviewed a peer's reference architecture for a public-sector
deal.

Wednesday was 5 hours of customer travel. I flew to a
manufacturing customer 90 minutes away, did a 3-hour
whiteboarding session on their IoT ingestion architecture,
and flew back. I was home by 8pm but the calendar showed
"customer travel, 5 hours" — that's part of the job.

> **Q: What do you love about it?**

**Raj:** Two things. First, the *variety*. In 5 years I've
worked on use cases as varied as genomics pipelines, real-
time fraud detection, autonomous-vehicle training pipelines,
and food-safety traceability. I would be bored stiff as a
data engineer working on the same kind of pipeline at the
same kind of company. The variety is the lever for me.

Second, the *impact*. When I help a customer ship a
pipeline, I see the business outcome — the fraud-detection
customer shipped a model that catches $20M/year of
fraudulent transactions. I built the architecture, but the
customer's team did the work. The credit goes to them; the
satisfaction of the contribution goes to me.

> **Q: What do you hate about it?**

**Raj:** Three things. First, the *calendar chaos*. A
"normal" week is 25-30 hours of meetings. I have to be very
intentional about blocking deep-work time, and even then,
customer emergencies override blocks. I've gotten good at it,
but my first 2 years I lost most of my mornings to back-to-
back calls.

Second, the *deals you lose*. I worked 9 months on a $4M
deal with a financial-services customer. We did discovery,
whiteboarding, a 6-week POC, a 40-page proposal. They
chose a competitor at the end. The loss wasn't because of
bad work — they had a pre-existing relationship with the
competitor we couldn't overcome. But it still hurts. You
have to learn to separate "good process" from "good
outcome." Not every deal you should win is one you do.

Third, the *constant need to be "on."* I'm in customer
calls 60% of my time, and every customer call is a
performance. You can't be tired, can't be unprepared, can't
be visibly annoyed by a 7th meeting on the same topic. Some
people love the stage. I do, most days. But the energy
drain is real, and the recovery takes discipline.

> **Q: How is the SA role different from your data-
> engineering role?**

**Raj:** When I was a data engineer, the success metric was
"does the pipeline work." When I'm an SA, the success
metric is "does the customer *buy* and *go live* and *stay
a customer*." Three very different metrics.

Engineering optimizes for correctness, performance, and
maintainability. Sales-adjacent work optimizes for trust,
narrative, and timing. I was *good* at engineering but I
wasn't *fulfilled* by it — I wanted my work to be
customer-facing, not internal.

The other big difference: the *time horizon*. An engineer
ships a feature, deploys it, and (mostly) moves on. An SA
wins a deal and then has to *defend* the deal — through
implementation, through escalations, through the customer's
next renewal. A win is the start of a 3-year relationship,
not the end of a project.

> **Q: What's the most important skill for the SA role?**

**Raj:** *Listening*. Everything else is downstream of
listening. If you can't listen to a customer describe their
problem without jumping to a solution, you'll sell them the
wrong thing. If you can't listen to a junior AE's concern
about a deal without being defensive, you'll lose trust in
the deal team. If you can't listen to your peer's feedback
on your architecture diagram, you'll ship bad work.

The technical bar is real and it's high. You have to know
your product, your competitor's product, and the customer's
domain well enough to design something that actually
works. But the listening bar is *higher*. Every interview
round tests it. Every customer interaction tests it. Every
internal team meeting tests it.

> **Q: What advice do you have for someone interviewing?**

**Raj:** Three things.

First, *practice the customer interaction rounds out loud
with a friend who plays the customer.* Most candidates
under-prepare for the discovery and demo rounds because
they feel "soft." They aren't soft — they're the *core* of
the SA loop. If you can't run a 30-minute discovery call
without notes, you won't pass the loop.

Second, *have 5-7 STAR stories ready that are pre-sales-
flavored.* Not "I shipped a feature." But "I worked with a
customer to ship a feature." Not "I led a design review."
But "I helped a customer sell an architecture internally."
The behavioral round at AWS is specifically looking for
*customer-facing* stories, not internal-engineering
stories.

Third, *be ready to defend your architecture against
objections.* The whiteboarding round is not a whiteboard-
coding round. It's "you drew an architecture; now the
interviewer (playing the customer's CTO) is going to
challenge it." If you can't defend your design choices,
you'll fail. If you can — even with "I don't know, but
here's how I'd find out" — you'll pass.

> **Q: What's the worst part of the interview loop?**

**Raj:** The *bar-raiser round* — the one where a non-
hiring-manager SA interviews you and decides whether
you're a "bar-raiser hire" (hire above bar) or a
"strong no hire." The interviewer is looking for 1 thing:
would you be a *good peer*? Not "are you smart" — they
assume that. But "could I sit next to you in a deal-team
meeting and trust your technical judgment?" That's
harder than any of the technical rounds, and it's the
round most candidates fail.

> **Q: How do you measure your own success?**

**Raj:** Three things, in priority order.

First, *customer outcomes.* Did the customers I worked
with ship their workloads, go live, and stay on the
platform? That's the *only* metric I really care about.
The deals I worked in 2024 are now in their second
renewal year. The fact that they're still customers is
the proof that the work was good.

Second, *influence on the product.* I file ~10 product
feedback tickets per quarter, and 2-3 of them turn into
product roadmap items. The 2024 launch of the [redacted]
service was a direct result of feedback I filed in 2023.

Third, *peer reputation.* I want the SAs in my region to
ask me for help, and the AEs to want to be on my deals.
Both are soft signals, but both are how the deal
allocations are made.

---

## 3. What to take from this

Three patterns from Raj's interview:

1. **The listening bar is the highest bar.** Every SA
   interview round — discovery, demo, objection, whiteboarding,
   behavioral — tests listening. The candidate who has the
   best technical answers but the worst listening will fail.
2. **Customer-facing stories beat internal stories.** The
   behavioral round at AWS looks specifically for stories
   where the candidate's *customer* (not their team, not
   their manager) was the protagonist.
3. **The bar-raiser round is the gate.** It's the round that
   the candidate can't prep for by knowing more facts. It
   tests *character* — would the SAs in the region want to
   work with you? Practice that round specifically.

The 7 lessons in Module 02 (Customer Interaction) and the 11
in Module 05 (Behavioral for SAs) are the *practice* for
these 3 patterns. Use Raj's interview as a calibration check
at the end of each module.

---

## Try it

Pick one of the 3 patterns above and write down a 90-second
personal answer that demonstrates the pattern. Out loud, no
notes.

- **If you chose "listening":** Tell a story where you listened
  to a customer / stakeholder and it changed your approach.
- **If you chose "customer-facing stories":** Tell a story
  where your customer / external user was the protagonist
  (not your team, not your manager).
- **If you chose "bar-raiser":** Tell a story where a peer
  trusted your technical judgment under pressure.

Set a 90-second timer. If your answer comes in over 2
minutes, you're storytelling, not answering. Cut it to 90
seconds and the signal will get sharper.
