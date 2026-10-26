# 02 — What is a Solutions Architect?

> **Lesson 2 of 8 — SA Interview Introduction** · ~15 min

The 3 flavors of Solutions Architect, what each one actually
does on a Tuesday morning, the trade-offs you'd be making, and
what the comp looks like at AWS, GCP, Azure, and Salesforce.

This is the most important lesson in Module 01. Read it twice.

---

## 1. The 3 flavors

"Solutions Architect" is one job title that hides at least three
different careers. The work, the customer contact, the technical
depth, and the comp at each level are *not* the same.

| Flavor | Primary output | Customer contact | Typical employer | Career path |
|---|---|---|---|---|
| **Pre-sales SA** | A technical win — the customer picks your solution | Heavy (50-80% of time): discovery, demos, whiteboarding, objections | AWS, GCP, Azure, Snowflake, Databricks, Confluent | Pre-sales SA → Sr. SA → Principal SA |
| **Post-sales SA** | A successful implementation — the customer goes live | Heavy (50-70%): implementation, enablement, escalation | Salesforce, ServiceNow, Workday, MongoDB, large enterprise vendors | Post-sales SA → Sr. SA → Delivery Architect |
| **Technical SA (Hyperscaler)** | A strategic technical relationship — the customer adopts the platform | Medium-heavy (30-50%): strategic accounts, deep architecture | AWS (Senior/Principal SA), GCP (L7-L8), Azure | Technical SA → Principal SA → Distinguished SA |

These are not titles you'd interview for interchangeably. The
interview loop for a pre-sales SA at AWS is *fundamentally
different* from the loop for a post-sales SA at Salesforce.
The bar differs, the round structure differs, the "tell me about
a time" stories differ.

A few things worth internalizing before you read on:

- **Most engineers who say "I want to be an SA" mean the first
  one** — the pre-sales SA at a hyperscaler. That's the most
  visible role and the one this track focuses on. If you're
  targeting the post-sales or technical-SA path, the content
  still applies, but the comp and the round structure differ.
- **The flavors blur at smaller companies.** A "Senior
  Solutions Engineer" at a Series B startup might be all three
  at once — running discovery, building PoCs, and supporting
  implementation. The level-mappings above are for FAANG-scale
  vendors. At a 200-person company, all three flavors live in
  one job.
- **"Solutions Architect" ≠ "Solutions Engineer."** The titles
  are used interchangeably at some companies (Snowflake uses
  both interchangeably) and strictly differently at others
  (AWS: SA = pre-sales; SE = sometimes used for the post-sales
  equivalent). Always read the JD. The 5 bullets under
  "responsibilities" tell you which flavor.

---

## 2. Day-in-the-life at each flavor

The best way to understand the difference between the flavors
is to look at what they actually *do* on a Tuesday morning. The
shapes of the calendars are very different.

### Pre-sales SA, AWS (SAs I-III) / GCP (L5-L6)

> **You own 6-15 active deals. ~50-70% of your time is in
> customer meetings.**

- **8:00-8:30** — Email + Slack. A deal-team channel has a
  question about a customer's compliance requirements. A
  proposal you're contributing to has a review deadline at
  noon.
- **8:30-9:30** — Prep for a customer discovery call at 10.
  The customer is a Fortune 500 retailer evaluating your
  data warehouse product. You've read their current
  architecture (a Snowflake + dbt stack on AWS) and you have
  5 discovery questions queued. You spend 45 minutes
  tailoring them — the last discovery call uncovered that
  their ETL tooling is the actual blocker, not the
  warehouse.
- **9:30-10:30** — Discovery call. 30-minute call with the
  customer's Director of Data and one of their senior
  engineers. You listen for 60% of the time, ask clarifying
  questions, identify the decision-maker and the
  decision-process. The call ends with a follow-up: you
  send a 1-page technical brief by EOD, and they set up a
  workshop for next Tuesday.
- **10:30-11:00** — Coffee. You decompress from the call.
  This is the actual leverage hour of the day, and it's
  invisible on your calendar.
- **11:00-12:00** — Whiteboarding prep. The workshop next
  Tuesday will be 2 hours long; you need to walk through 3
  architecture options for their analytics pipeline. You
  sketch all 3, drop them into a Google Doc, and draft the
  "go-forward" recommendation.
- **12:00-1:00** — Lunch with the account executive (AE).
  The relationship work. You're not managing the deal (the
  AE is), but your technical credibility *unblocks* the deal.
  This lunch is why the AE trusts you in the next room.
- **1:00-2:30** — Internal sync. A weekly deal-team meeting
  with 4 AEs and 2 other SAs. You walk through your top 5
  deals, name the risks, ask for help on 2.
- **2:30-4:00** — Architecture review for a different deal.
  A different customer wants to compare your streaming
  product vs Kafka. You write a 1-pager that lands the
  comparison on 5 dimensions: throughput, latency, schema
  evolution, ops burden, TCO. The page takes 90 minutes.
- **4:00-5:00** — Proposal review. You review a 40-page
  proposal an SE on your team wrote for a healthcare
  customer; you mark up the technical sections, sign off,
  send back to the AE.

The pre-sales SA's day is **50% customer-facing, 30%
deep-work (whiteboarding, proposals, POCs), 20% internal
collaboration**. The leverage is real — your 6-15 deals per
quarter each close at $100k-$10M+, and you materially
influence each one. But the kind of work is *consultative
technical sales*, not pure engineering.

### Post-sales SA, Salesforce / MongoDB / ServiceNow

> **You own 3-8 active implementations. ~60-80% of your time
> is on customer calls and code reviews.**

- **8:00-8:30** — Email + Slack. Customer A's data ingestion
  migration has a blocker (a 2-day-old ticket). Customer B's
  integration spec needs review.
- **8:30-10:00** — Live working session with Customer A's
  engineering team. They've hit an idempotency edge case in
  the API integration. You pair-debug the request flow,
  identify the bug (a missing idempotency key on their
  retries), and ship the fix in their sandbox.
- **10:00-11:30** — Architecture review for Customer B. You
  walk their senior engineer through your recommended
  topology for connecting their on-prem Oracle DB to your
  cloud product via Kafka Connect. You draw it on the
  whiteboard (or Miro), record the session, send the
  recording + the draw.io file with annotations.
- **11:30-12:00** — Customer enablement. You record a 10-minute
  Loom walking the customer through the connector
  configuration for a non-obvious edge case.
- **12:00-1:00** — Lunch.
- **1:00-2:30** — Deep dive. You're building a reference
  implementation for a common integration pattern
  (Salesforce → Snowflake CDC). You write the code
  alongside the customer's team, push it to a shared repo,
  review their PRs.
- **2:30-3:30** — Internal escalation. A customer is hitting
  a platform issue that's blocking go-live. You escalate to
  engineering, write the impact summary, and own the
  communication loop to the customer.
- **3:30-5:00** — Documentation. You write a "common pitfalls"
  doc based on this week's 3 customer implementations. This
  becomes part of the customer's onboarding kit.

The post-sales SA's day is **60% in customer work (calls,
code review, debugging), 30% deep work (reference impls,
docs), 10% internal**. The technical depth is *higher* than
the pre-sales flavor — you're often writing or reviewing
production-grade code in the customer's stack. The deal
leverage is different — you're not closing the deal (the AE
already did), you're making sure the customer *goes live*
and *stays a customer*.

### Technical SA, Hyperscaler (AWS Sr. SA / GCP L7 / Azure)

> **You own 4-8 strategic accounts. ~30-50% of your time is
> in deep technical conversations, mostly with senior
> engineers and CTOs.**

- **8:00-8:30** — Email. A strategic customer's principal
  engineer flagged a question about a service limit you
  authored internally. A peer SA in another region is
  asking for your review on their account-plan document.
- **8:30-10:00** — Architecture office hours. A standing
  weekly slot where 5 of your strategic customers drop in
  with questions. Today, a customer's CTO is asking how to
  think about a multi-region active-active architecture for
  their payments service. You whiteboard it for 60 minutes,
  produce a follow-up doc with 3 options by EOD.
- **10:00-12:00** — Deep design review. A senior engineer at
  one of your strategic customers has been working on a
  new architecture for 3 months. They want your eyes before
  they present it to their CTO. You spend 90 minutes on the
  walkthrough, another 30 on your written review.
- **12:00-1:00** — Lunch with the AE leader for your
  territory. Quarterly catch-up. You talk about the 3
  biggest deal risks in the region, the 2 expansion
  opportunities you've spotted in current accounts.
- **1:00-2:30** — Internal strategy work. You're the
  technical voice in the region's quarterly review.
  Today: a 1-pager on the "AI workloads in the region"
  trend — what customers are building, what their blockers
  are, what your product team should be aware of.
- **2:30-4:00** — Public-facing work. You're a speaker at a
  regional tech event next month, and you need to prep a
  talk on "reference architectures for AI workloads."
  You sketch the talk arc, identify 3 customer case
  studies to anonymize, send a draft to the events team.
- **4:00-5:00** — Public Q&A. You spend the last hour of
  the day answering questions on the company's public
  tech forum. Your answers are read by 500-2000 people;
  the technical credibility you build here feeds back
  into your deals.

The Technical SA's day is **30% customer-facing (deep
technical conversations only), 40% deep-work (architecture
review, public content, internal strategy), 30% influence
work (public content, internal voice, peer collaboration)**.
The leverage is *highest* — your 4-8 strategic accounts are
each $10M-$100M/year — but the *kind* of work is the most
senior+ of the three flavors. There is no scaffolding; you
define what "good" looks like in your accounts.

---

## 3. The pre-sales vs. post-sales vs. technical-SA trade-off

The single most important table in this module.

| Dimension | Pre-sales SA | Post-sales SA | Technical SA |
|---|---|---|---|
| **What you ship** | Wins (deals) | Implementations | Strategic technical relationships |
| **Customer contact** | Heavy (50-80%) | Heavy (60-80%) | Strategic (30-50%, deep) |
| **Code written per week** | Light (PoCs, demos) | Heavy (customer code) | Variable (demo code, reference, deep analysis) |
| **Decision-maker contact** | Director / VP / occasional C-suite | Director / Manager / IC | Senior engineer / Architect / CTO |
| **Comp (year 1, FAANG)** | $250-450k | $250-400k | $400-800k |
| **Reversibility** | High — can move to post-sales, sales engineering, or back to engineering | Medium — can move to engineering, delivery, or pre-sales with effort | Low — the specialized skill is hard to translate; a move is a re-pitch |
| **Failure mode** | Deals you couldn't close (you'll always have some) | Implementations that go sideways, customer escalations | Strategic accounts that churn, public content that ages badly |
| **Best signal of success** | "I closed deals I shouldn't have" | "Customer goes live and stays a customer" | "CTOs in my territory ask for me by name" |
| **What you give up** | Deep technical depth, IC work, ownership of the implementation | Pre-sales dynamism, the win moment, deal variety | High-volume customer contact, the win/lose clarity of a sale |

---

## 4. Compensation (FAANG-scale, 2024-2026, rough)

Numbers change, and public comp data is noisy. These are
**rough ranges** for US-based, hyperscaler-scale SA roles,
based on publicly shared levels.fyi data and offer-letter data
I've seen. Treat them as order-of-magnitude, not exact.

| Level | Title | Base | Variable/RSU | Total (year 1) |
|---|---|---|---|---|
| **AWS SA I / GCP L5 / Azure IC5** | Pre-sales SA | $130-170k | $80-150k | **$210-320k** |
| **AWS SA II / GCP L6 / Azure IC6** | Senior SA | $160-200k | $150-300k | **$310-500k** |
| **AWS Sr. SA / GCP L7 / Azure IC7** | Principal SA | $190-240k | $300-600k | **$490-840k** |
| **AWS Principal SA / GCP L8 / Azure IC8** | Sr. Principal SA | $230-300k | $500-1M+ | **$730k-1.3M+** |

For comparison, the IC equivalent:

| Level | Title | Total (year 1) |
|---|---|---|
| **L5 (Google) / E5 (Meta) / IC5** | Senior Engineer | $400-700k |
| **L6 / E6 / IC6** | Staff Engineer | $700k-1.1M |
| **L7 / E7 / IC7** | Sr. Staff | $1.2-2M |
| **L8 / E8 / IC8** | Principal | $2-4M+ |

Two patterns worth noticing:

1. **At SA I/II (L5/L6 equivalent), pre-sales SA comp is
   noticeably *below* the IC ladder.** The trade-off at this
   level is real — you're trading dollars for customer contact
   and varied work. If you don't love the customer-facing work,
   this is a bad trade.
2. **At Sr. SA / Principal SA (L7/L8 equivalent), the comp
   converges with the IC ladder.** At this level, the dollar
   trade-off is gone; the question becomes "what kind of work
   do I want to do for the next 5-10 years."

The comp for post-sales SA is typically 10-15% *below*
pre-sales SA at the same level (less variable comp, more
stable base).

---

## 5. A worked example: Sam, 7 years DE, SA-track pivot

**Sam**, 7 years data engineering, currently a Senior DE at
a mid-size fintech. He's been the de facto SE on his team's
last 6 deals and wants to make the move full-time.

- **Sam's current day:** 70% engineering (writing dbt models,
  building pipelines, designing schemas), 20% cross-team
  customer work (the embedded-SE work), 10% meetings.
- **Sam's day as a pre-sales SA:** 30% engineering (POCs,
  demos), 50% customer-facing, 20% meetings/internal. Total
  comp: -15% in year 1, but +30% in variability (bonuses tied
  to deals).
- **Sam's day as a post-sales SA:** 50% engineering (in the
  customer's code), 30% customer-facing, 20% internal. Total
  comp: -10% in year 1, similar variability.
- **Sam's day as a Technical SA:** 20% engineering (demo
  code, reference architectures), 40% deep customer work,
  40% internal/external influence. Total comp: 0% in year 1
  (base higher, less variability, more RSU), +30% in year 2
  as RSU vests.

Sam is in the position most senior ICs are in. He's already
doing the work; the move is whether to make it the whole job.
The trade is real, and it's not reversible in a weekend. The
next lesson is one common path: the AWS SA Associate program.

---

## Try it

Pick a current Solutions Architect at your target employer (a
LinkedIn connection, a colleague, a friend-of-a-friend) and
answer these in writing. The point isn't to evaluate them —
it's to evaluate the *role*.

1. **What does their Tuesday look like?** (Be specific. What
   customer calls? What proposals?)
2. **What did they ship in the last 6 months that wasn't
   code?** (A deal they won? An enablement doc? A reference
   architecture?)
3. **What do they most complain about?** (Calendar? Proving
   their value? Travel?)
4. **What part of their job would I most enjoy?**
5. **What part of their job would I most hate?**

If you can't answer #4 and #5 with specific answers, you don't
yet have a model of what the SA role looks like — and you
should get one (informational interviews with 3 current SAs
at your target companies, or the test drive in the next
lesson) *before* taking the offer.
