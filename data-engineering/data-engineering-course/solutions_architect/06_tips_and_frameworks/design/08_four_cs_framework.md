# 08 — The 4 C's Framework: Customer, Context, Constraints, Choice

> **Lesson 8 of 9 — Tips & Frameworks** · ~10 min

The SA-specific *architecture* framing. Customer,
Context, Constraints, Choice. The 4-part structure
for any architecture answer, with 3 worked examples.

This is the *spine* of any architecture answer in
the SA loop. Internalize it, practice it, and your
architecture rounds become concise, customer-
tailored, and defensible.

---

## 1. The 4 C's framework

| # | C | What it is | What it answers |
|---|---|---|---|
| 1 | **Customer** | Who's the customer, what's their role, what do they care about? | "Who is this for?" |
| 2 | **Context** | What does the customer's world look like today? What's the current architecture, the current constraints, the current team? | "Where are they starting from?" |
| 3 | **Constraints** | What are the hard constraints (latency, scale, cost, compliance, team capacity)? | "What can't we compromise?" |
| 4 | **Choice** | What architecture do you recommend, given the Customer / Context / Constraints? | "What should we build?" |

The 4 C's flow in order: Customer → Context →
Constraints → Choice. The answer is *anchored* in
the customer's reality, not in a generic best-
practice.

---

## 2. Why the 4 C's matter for SA interviews

The senior SA move is to *anchor every
architecture answer* in the customer's reality.
The 4 C's are the structure that produces this
anchoring.

The 4 C's:

- **Force you to center the customer.** If your
  answer doesn't start with "the customer is X,"
  you've skipped the most important part.
- **Force you to acknowledge context.** The
  customer has a current state, not a blank slate.
  The architecture must address the migration.
- **Force you to name constraints.** "It depends"
  becomes "given the constraint of X, the answer is
  Y."
- **Force you to recommend.** The Choice is your
  recommendation, with rationale and tradeoffs
  (Lesson 02 of this module).

The 4 C's produce the senior SA answer in 60-90
seconds.

---

## 3. The 3 worked examples

### Example 1: Real-time fraud detection pipeline

> **Customer:** "The customer is a Fortune 500
> payment processor. Their fraud team is the
> primary user, and they care about two things:
> catching more fraud and reducing false positives."
>
> **Context:** "Today, the customer runs a nightly
> batch fraud-detection job on a Hadoop cluster. The
> model is trained weekly and scored nightly. The
> fraud team has been complaining about latency
> for 18 months."
>
> **Constraints:** "The hard constraints are:
> sub-100ms p99 scoring latency at 10k
> transactions/sec peak; PCI-DSS compliance for
> card data; 24-month project timeline; the team
> has limited SRE capacity."
>
> **Choice:** "Given those constraints, I'd
> recommend a streaming-first architecture with
> Kafka for event ingestion, a streaming feature
> store in DynamoDB for sub-10ms reads, and a
> SageMaker-hosted model for sub-50ms scoring.
> The architecture uses the team's existing Kafka
> expertise (they already have it for clickstream)
> and minimizes new operational burden."

The 4 C's, 90 seconds. The Choice is anchored
in the Customer / Context / Constraints, not a
generic best-practice.

### Example 2: E-commerce checkout page

> **Customer:** "The customer is a Fortune 500
> retailer with $5B annual revenue. Their VP of
> E-commerce is the primary stakeholder, and she
> cares about checkout conversion rate."
>
> **Context:** "Today, the customer's checkout
> page is server-rendered, with a 4-second p99
> load time. Mobile conversion is 30% lower than
> desktop. The team has 6 frontend engineers, no
> SRE capacity, and a 3-month timeline to a
> holiday season launch."
>
> **Constraints:** "The hard constraints are:
> sub-1-second p99 load time (down from 4s);
> no operational burden on the small team;
> integration with the existing payment
> processor; PCI-DSS scope minimization."
>
> **Choice:** "Given those constraints, I'd
> recommend a static-rendered checkout page
> (Next.js or Astro) deployed to a CDN
> (CloudFront), with API calls to the payment
> processor at submit time. The architecture
> reduces the load time from 4s to ~500ms by
> serving from the edge, and minimizes PCI scope
> by keeping the page static and using the
> payment processor's hosted fields."

The 4 C's, 90 seconds. The Choice addresses the
*specific* constraints (3-month timeline, small
team, holiday launch), not a generic frontend
modernization.

### Example 3: Self-serve insurance product

> **Customer:** "The customer is a 12-person
> insurtech startup launching a self-serve term
> life product. Their CTO is the primary
> stakeholder, and she cares about getting to
> market fast while meeting regulatory
> requirements."
>
> **Context:** "The team has 12 engineers and
> no existing production infrastructure. They've
> built the application code but not deployed
> it. They have 4 months to launch in 5 states."
>
> **Constraints:** "The hard constraints are:
> HIPAA-adjacent for medical exam data; state-
> level insurance compliance; PCI-DSS for card
> data; 4-month timeline to launch in 5 states;
> ~$50k/month budget."
>
> **Choice:** "Given those constraints, I'd
> recommend a fully-managed cloud architecture:
> ECS Fargate for compute (no Kubernetes
> operational burden), Aurora Serverless for
> the policy database, Stripe for payments (PCI-
> DSS offloaded), and S3 for document storage
> with KMS encryption. The architecture is 80%
> standard reference patterns and 20%
> customized for state-level filing
> requirements, which the team can iterate on
> post-launch. Estimated cost at launch: ~$8k/
> month, with headroom to $30k/month at 100k
> policies."

The 4 C's, 120 seconds. The Choice addresses
every constraint, the budget, and the post-
launch headroom.

---

## 4. The 60-second compressed version

For quick check-ins or follow-up questions, the
4 C's can be compressed to 60 seconds:

> "Given [Customer] with [Context], the
> constraints are [Constraints], so I'd
> recommend [Choice]."

The compressed version is the elevator pitch.
The full 4 C's version is the architecture
review. Both are senior SA moves.

---

## 5. The 3 anti-patterns for the 4 C's

### Anti-pattern 1: Skipping the Customer

You jump straight to the architecture. The
interviewer reads this as "I don't center the
customer."

**Fix:** Always start with the Customer. Even
one sentence makes the difference.

### Anti-pattern 2: Generic Context

You say "the customer is a typical mid-size
company." The interviewer reads this as "I
don't know the customer's reality."

**Fix:** Be specific. "The customer is a 200-
person SaaS company with 12 engineers, on AWS,
with a $50k/month infrastructure budget."

### Anti-pattern 3: Vague Constraints

You say "the customer wants good performance
and reasonable cost." The interviewer reads
this as "I don't think in constraints."

**Fix:** Be specific. "Sub-100ms p99 latency,
10x growth over 2 years, PCI-DSS scope."

The 3 anti-patterns are *common*. The senior SA
move is to avoid them every time.

---

## 6. The 4 C's + the 4-part tradeoff structure

The 4 C's are the *framing* of the answer. The
4-part tradeoff structure (from Lesson 02 of this
module) is the *substance* of the Choice step.
Together:

- **Customer / Context / Constraints** — the
  framing.
- **Choice** — with the 4-part structure (the
  choice, the rationale, the alternative, the
  tradeoff).

The 5-step pattern (4 C's + 4-part tradeoff)
produces a 90-120 second architecture answer
that is *anchored*, *defensible*, and *senior*.

---

## Try it

Pick any of the 3 worked examples above (or any
architecture scenario from your specialty).
Re-tell the 4 C's out loud in 90 seconds.

Then, pick a *different* architecture scenario
(something from your own work). Apply the 4 C's.
Re-tell out loud. Time yourself.

Run this 5 times. By the 5th, the 4 C's will be
in muscle memory. That's the architecture round
of any SA interview.
