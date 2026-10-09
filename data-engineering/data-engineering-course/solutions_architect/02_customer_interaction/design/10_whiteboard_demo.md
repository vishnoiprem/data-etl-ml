# 10 — The Whiteboard Demo: Drawing Architecture Live

> **Lesson 10 of 12 — Customer Interaction** · ~20 min

The single most-practiced lesson in this module. The
whiteboard demo is the round that combines architecture
design with customer interaction — you draw the
architecture, the customer challenges every choice, and
you defend. The 4-step process, the common pitfalls, and
a worked example.

---

## 1. The format

The whiteboard demo (or "architecture walkthrough" or
"design under pressure") is the round where the candidate
designs an architecture live, in real time, while a
"customer" (usually the interviewer) challenges every
choice.

The format:

- **Duration:** 45-60 minutes.
- **Surface:** whiteboard, Excalidraw, Google Docs drawing,
  or shared Miro.
- **Setup:** the interviewer gives a scenario ("design a
  real-time recommendation pipeline for a 500-person
  e-commerce company, 10M daily active users, 50ms p99
  latency requirement"). The candidate asks 2-3 clarifying
  questions, then starts drawing.
- **Mid-design:** the "customer" (interviewer) interrupts
  with new constraints ("actually, we have a regulatory
  requirement that data must stay in the EU").
- **End:** the candidate defends the design against 3-5
  specific challenges from the customer.

The round tests *defensible design under pressure*, not
just "can you design." A candidate who can design but
can't defend fails. A candidate who can defend but can't
design also fails. The round rewards both.

---

## 2. The 4-step process

The 4-step process for a 4/4 whiteboard demo:

| Step | Duration | What to do |
|---|---|---|
| **1. Clarify** | 5-7 min | Ask 3-5 clarifying questions. Don't draw yet. |
| **2. Sketch** | 10-15 min | Draw the architecture. Box-and-arrow. Use the customer's vocabulary. |
| **3. Defend** | 20-25 min | Walk through the design, naming the tradeoffs at each major choice. The customer challenges. |
| **4. Adapt** | 5-10 min | The customer introduces 1-2 new constraints mid-design. Adapt without losing the thread. |

The 4 steps are sequential, but the defend and adapt
phases loop. The customer challenges a choice, the
candidate defends, the customer introduces a new
constraint, the candidate adapts.

---

## 3. Step 1: The 5 clarifying questions

Before drawing, ask 3-5 clarifying questions. The questions
that almost always matter:

1. **What's the workload pattern?** (Read-heavy? Write-
   heavy? Both? What's the request rate, the data
   volume, the latency requirement?)
2. **What's the consistency requirement?** (Strong
   consistency? Eventual consistency? Read-after-write?
   Eventual is usually fine, but ask.)
3. **What's the durability requirement?** (Can we lose
   data? For how long? What's the recovery time
   objective?)
4. **What are the regulatory/compliance constraints?**
   (PCI, HIPAA, GDPR, data residency?)
5. **What's the team's operational capacity?** (Do they
   have an SRE team? How mature is their observability
   practice?)

The 5 questions are the *spine* of the clarifying phase.
Adapt to the scenario. A real-time analytics scenario
asks about latency; a batch processing scenario asks
about throughput; a transactional scenario asks about
consistency.

The clarifying phase is the move that *most* candidates
skip. They jump to drawing at minute 1. The senior SA
candidate spends 5-7 minutes clarifying first. The
interviewer (and the bar-raiser) reads this as a
*listening* signal.

---

## 4. Step 2: The sketch

The sketch phase is where the box-and-arrow architecture
goes on the board. The senior SA sketch has 4
characteristics:

1. **Logical, not physical.** Boxes are services or
   components, not specific machines. The customer can
   map the boxes to their preferred infrastructure
   later.
2. **Data flow direction is clear.** Arrows have a
   direction. The customer can read the diagram in 10
   seconds.
3. **Hot paths are visually emphasized.** Use a different
   color or thicker line for the data flow that's
   latency-critical.
4. **Failure modes are sketched in.** The senior SA
   sketch includes at least one "if this component
   fails" annotation (e.g., "primary → replica failover
   in 30s").

The 4 characteristics signal senior SA. A junior sketch
is a 20-component diagram with no failure modes, no hot-
path emphasis, and physical-level detail (e.g., specific
EC2 instance types).

---

## 5. Step 3: The defense

The defense is where the senior SA earns the 4/4. Every
major choice needs:

- **The choice itself.** (We're using Kafka for event
  streaming.)
- **The rationale.** (We need horizontal scalability and
  ordered partitioning by user_id for the feature
  pipeline.)
- **The alternative considered and rejected.** (We
  considered Kinesis, but Kinesis's per-shard throughput
  would require 4x the shards for our 50ms p99
  requirement.)
- **The tradeoff.** (Kafka adds operational complexity
  compared to Kinesis, but the per-shard cost is 50%
  lower at our scale.)

The 4-part structure is the "defensible choice" pattern.
A senior SA can produce all 4 parts in 30-45 seconds
per choice. A junior SA produces 1-2 parts and trails
off.

The 4-part structure is also what the customer (or the
interviewer) is listening for. When you make a choice,
they want to hear the alternative you considered and
*why* you rejected it. If you can't produce the
alternative, the choice looks uninformed.

---

## 6. Step 4: The adaptation

The mid-design constraint is the move that tests
*listening under pressure*. The customer (interviewer)
introduces a new constraint:

> "Actually, we just remembered — we have a regulatory
> requirement that data must stay in the EU."

The senior SA response:

1. **Acknowledge the constraint** without breaking stride.
2. **Identify the impact** on the design (1-2 specific
   components).
3. **Propose the adaptation** (e.g., "we'll keep the EU
   data in eu-west-1, and the global data in us-east-1,
   with a federated query layer on top").
4. **Verify with the customer** ("does that match the
   regulatory requirement, or do you need a stricter
   separation?").

The senior SA does this in 30-60 seconds, without
losing the thread. The junior SA starts the design
over, which is the failure.

The 4-step adaptation pattern is the "active listening
under pressure" signal. It's the move that separates the
senior SAs from the senior engineers.

---

## 7. Common pitfalls

### Pitfall 1: Drawing without clarifying

You jump to drawing at minute 1. The customer has to
stop you with "wait, what's the latency requirement?"
You look unprepared.

**Fix:** Always clarify for 5-7 minutes first. The
clarifying phase is *part of* the design.

### Pitfall 2: Generic architecture

You draw the standard 3-tier architecture (web, app,
database) regardless of the scenario. The customer
interrupts with "but this is a streaming pipeline, not
a web app." You have to redraw.

**Fix:** Tailor the architecture to the scenario. The
clarifying questions are the *spine* of the tailoring.

### Pitfall 3: Physical-level detail

You draw EC2 instance types, specific RDS instance
classes, specific S3 bucket names. The customer can't
read the diagram, and you've wasted 10 minutes on
detail that doesn't matter at this stage.

**Fix:** Logical-level diagrams. Services, not machines.
Names, not versions.

### Pitfall 4: No failure modes

You draw the happy path only. The customer asks "what
happens if the recommendation service goes down?" and
you have no answer.

**Fix:** Always include at least one failure mode in
the diagram (replication, failover, DLQ, etc.).

### Pitfall 5: No tradeoffs

You defend your choices with "this is the best" instead
of "this is the best *given* these tradeoffs." The
customer reads this as over-claiming.

**Fix:** Always name the tradeoff. "We chose Kafka over
Kinesis because of the per-shard cost, but Kafka adds
operational complexity. The right answer depends on the
team's operational capacity."

### Pitfall 6: Folding on the first challenge

The customer challenges a choice, and you immediately
say "OK, let's change it." The customer reads this as
"you didn't actually have a reason for the choice."

**Fix:** Defend the choice. If the customer has a real
objection, adapt. If the objection is exploratory, hold
the line and explain the rationale.

---

## 8. A worked example: 5-minute sketch + defense

The scenario: design a real-time recommendation pipeline
for a 500-person e-commerce company, 10M DAU, 50ms p99
latency.

### The clarifying questions (5 minutes)

> "Five clarifying questions before I start drawing.
> First, what's the workload pattern? I'm assuming the
> clickstream is high-volume (10M DAU × ~50 events/day
> = 500M events/day), and the recommendation request
> rate is high (10M DAU × 5 recommendations per session
> = 50M requests/day). Is that right?"
>
> "Second, what's the consistency requirement? I'm
> assuming eventual consistency is fine — a click that
> happened 100ms ago doesn't need to influence the
> next recommendation immediately. But read-after-write
> for the user's own actions — if I clicked on a
> product, the next recommendation shouldn't include
> that product. Is that right?"
>
> "Third, what's the durability requirement? I'm
> assuming we can lose up to 60 seconds of clickstream
> data in a disaster, but no more. Is that right?"
>
> "Fourth, what are the regulatory constraints? PCI for
> sure, since this is e-commerce. Anything else — GDPR
> for EU users, CCPA for California, anything state-
> level?"
>
> "Fifth, what's the team's operational capacity? Do
> you have an SRE team, or is this going to be run by
> the data engineering team?"

### The sketch (10 minutes)

The candidate draws:

- **Source:** Front-end React app, click events published
  to Kafka via an edge service.
- **Stream processing:** Kafka topic → Kafka Streams or
  Flink → stateful sessionization.
- **Feature store:** Stream-processed events flow into
  a feature store (e.g., DynamoDB or Redis), with the
  user profile and product catalog joined in.
- **Model serving:** Recommendation model reads the
  feature store, returns a ranked list of products.
- **API:** Back-end API serves the ranked list back to
  the front-end, with p99 latency budget of 50ms.
- **Storage:** Long-term storage in S3 (Parquet) for
  analytics and model retraining.

The candidate marks the hot path (front-end → API →
model serving → feature store) in a different color, and
annotates at least one failure mode (e.g., "if the
feature store is unavailable, fall back to a cached
recommendation list").

### The defense (15-20 minutes)

> "Three major choices I'd want to defend.
>
> First, Kafka over Kinesis. Kinesis's per-shard
> throughput would require ~80 shards for the
> clickstream, at $0.015/shard-hour, which is
> significantly more expensive than Kafka at our scale.
> The tradeoff is operational complexity — Kafka
> requires a Zookeeper or KRaft cluster, which is
> operationally heavier than Kinesis. The right answer
> depends on the team's operational capacity.
>
> Second, a streaming feature store over a batch-
> refreshed one. The 50ms p99 latency requirement
> rules out a batch-refreshed feature store (which
> would have a freshness of minutes to hours). The
> streaming feature store has sub-second freshness,
> which meets the latency requirement. The tradeoff
> is that the streaming feature store is more
> operationally complex and more expensive to operate
> than a batch one.
>
> Third, model serving in a low-latency serving layer
> (e.g., SageMaker or Vertex AI) over a synchronous
> database query. The 50ms p99 latency requirement
> rules out a synchronous database query (which would
> add 20-50ms of round-trip time). The model serving
> layer keeps the model in memory and returns a ranked
> list in <10ms."

### The adaptation (5-10 minutes)

> **Customer:** "Actually, we have a GDPR requirement
> — EU user data must stay in the EU."
>
> **Candidate:** "Got it. The adaptation is to deploy
> the feature store and the model serving layer in
> eu-west-1 for EU users, and us-east-1 for the rest
> of the world. The clickstream ingestion can route
> based on user residency. The model can be trained
> globally but served regionally.
>
> Two questions to verify: first, is the data
> residency requirement strict (data must remain in
> the EU at all times), or is it eventual (data can
> cross regions during processing but must be stored
> in the EU)?
>
> Second, can the model be trained globally (with
> EU data being used in training but not in serving),
> or does the model need to be EU-only?"

The 4-step response (acknowledge, identify impact,
propose adaptation, verify) is the senior SA move. The
candidate doesn't lose the thread, doesn't redraw the
diagram, and turns the constraint into a clarifying
question.

---

## Try it

Pick 1 system design problem from `../system_design/`
(e.g., URL shortener, Twitter, Uber Eats). Run a
whiteboard demo for it, with a friend playing the
"customer" (Principal Engineer).

Use the 4-step process:

1. **Clarify for 5-7 minutes.** Use the 5 clarifying
   questions as the spine.
2. **Sketch for 10-15 minutes.** Logical-level, with
   data flow and at least one failure mode.
3. **Defend for 15-20 minutes.** Defend each major
   choice with the 4-part structure (choice, rationale,
   alternative, tradeoff).
4. **Adapt for 5-10 minutes.** Have your friend
   introduce a new constraint mid-design. Practice the
   4-step adaptation.

Record it. Listen back. Notice the moments where you
skipped a clarifying question, drew at physical-level
detail, folded on a challenge, or lost the thread on
adaptation. Those are the gaps to close.

Run 3 different problems with 3 different friends. By
the 3rd, you'll have the 4-step process in muscle memory.
That's the whiteboard round.
