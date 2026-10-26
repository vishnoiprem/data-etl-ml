# 08 — Mock Demo: Architecture Diagram Walkthrough

> **Lesson 8 of 12 — Customer Interaction** · ~15 min

A 4-minute mock demo transcript with analysis. The candidate
is walking through an architecture diagram for a real-time
recommendation pipeline. The demo isn't a click-through of
the product — it's a *narrative walk-through* of the
solution, which is a more common senior-SA format than a
live product demo.

---

## 1. The setup

- **Candidate:** Priya, 10 years data engineering, current
  Senior DE. Interviewing for Principal SA at a streaming-
  data vendor.
- **Interviewer:** Marcus, Principal SA at the vendor. Plays
  the role of "Director of Engineering" at a 500-person
  e-commerce company.
- **Round:** 15 minutes total — 2 minutes of setup, 10
  minutes of demo, 3 minutes of close.
- **Scenario:** The e-commerce company is evaluating the
  vendor's streaming product for a real-time product
  recommendation pipeline. The diagram has been pre-drawn
  (on a whiteboard or Excalidraw).

---

## 2. The transcript

> **Priya:** "Thanks for sharing the diagram in advance.
> In the next 10 minutes, I'll walk you through how this
> architecture handles your real-time recommendation
> pipeline, with a focus on the 3 places where I'd expect
> the design to differ from your current setup. I'll
> pause for questions at 3 points."
>
> **Marcus:** "Sounds good."
>
> **Priya:** "OK, starting at the top. The customer clicks
> happen here — at the front-end, in your React app. The
> click event is published to Kafka via a Kafka producer
> in your edge service. From there, it lands in the
> streaming product's source topic, where it gets
> processed. Does this match how your clickstream works
> today?"
>
> **Marcus:** "Yes, similar — we use a different message
> broker, but the pattern is the same."
>
> **Priya:** "Great. Now, the streaming product takes that
> source topic, joins it with your user profile and
> product catalog, and produces a feature vector that
> represents the user's current session. This is the
> first place I'd expect the design to differ from your
> current setup."
>
> **Marcus:** "Why?"
>
> **Priya:** "Because the streaming product does the
> sessionization as a stateful operation, which means
> the session state lives in the streaming layer, not in
> your application database. The implications are: you
> don't need to query the database for every click, and
> the session window can be 30 minutes or 4 hours
> without performance impact. The question is — does
> that match how your team thinks about sessionization,
> or do you have constraints I should know about?"
>
> **Marcus:** "It's flexible — we don't have a hard
> constraint on where the session lives."
>
> **Priya:** "Helpful. Continuing — the feature vector
> flows into the feature store, which your recommendation
> model consumes in real time. The model returns a ranked
> list of products, which the back-end serves back to
> the front-end. The end-to-end latency from click to
> served recommendation is sub-100ms. Pause here —
> before I go into the second area, does the data flow
> match your expectation?"
>
> **Marcus:** "Yes, that's roughly what we're trying to
> build."
>
> **Priya:** "Great. The second place the design differs
> is the feature store. Your current setup — if I
> understood the discovery call — uses a batch-loaded
> feature store, refreshed every hour. The architecture
> I'm showing you has a streaming feature store that's
> updated in real time. The implication is that the
> recommendation freshness goes from 1 hour to 1
> second. What's your team's appetite for moving from
> batch to streaming on the feature store?"
>
> **Marcus:** "We've been wanting to move to streaming,
> but the operational overhead has been a concern. The
> team has limited SRE capacity."
>
> **Priya:** "Got it — that's the right concern to flag.
> In this architecture, the streaming product manages
> the operational burden of the streaming layer. Your
> team would manage the feature store, but the
> streaming layer is managed by us. That's 60-70% less
> operational overhead compared to running your own
> Flink or Spark Streaming cluster."
>
> **Marcus:** "OK, that's helpful."
>
> **Priya:** "The third place — and this is where I'd
> want your input — is the back-pressure handling. When
> the front-end traffic spikes (say, a flash sale), the
> click event rate can go from 1k events/second to 50k
> events/second. The streaming layer has to absorb that
> without dropping events. The architecture handles this
> by buffering in Kafka and scaling the streaming layer
> horizontally. The question for your team is: what's
> your appetite for managing the back-pressure
> thresholds? Do you want them tuned by us, by your
> team, or jointly?"
>
> **Marcus:** "Jointly, probably — but I'd want our team
> to understand the levers."
>
> **Priya:** "Got it. We'd set up a working session with
> your SRE team to walk through the levers and
> thresholds. Does that work?"
>
> **Marcus:** "Yes."
>
> **Priya:** "Great. Let me summarize what we've covered.
> The architecture takes the clickstream from the front-
> end, joins it with user and product data in the
> streaming product, produces a real-time feature vector,
> and feeds a streaming feature store that the
> recommendation model consumes. The 3 places where the
> design differs from your current setup: sessionization
> in the streaming layer (vs. in the application
> database), streaming feature store (vs. batch-loaded),
> and back-pressure handling on clickstream spikes. Each
> has a specific implication for your team. The next
> step I'd suggest is a 90-minute working session with
> your team to walk through the feature store
> operational model. Does Tuesday at 2pm work?"
>
> **Marcus:** "Tuesday at 2 works. Let me check with the
> SRE team."
>
> **Priya:** "Perfect. I'll send a calendar placeholder."

---

## 3. The analysis

### What Priya did well

- **Set the agenda in the first 30 seconds.** Same
  pattern as the discovery mocks — agenda, duration,
  3 pause points.
- **Used the 3-pause structure.** Paused at 3 specific
  points (after the data ingestion, after the feature
  vector, after the back-pressure). Each pause had a
  purpose.
- **Surfaced 3 design differences.** Instead of walking
  through every feature, Priya anchored on the 3 places
  where the design *differs* from the customer's current
  setup. This is senior SA — the customer already knows
  the parts that are similar; they want to understand
  the parts that are different.
- **Tied each difference to an implication.** "The
  implication is X" — and asked a question. Each design
  choice had a "why it matters for you" connection.
- **Surfaced a customer concern (operational overhead)**
  *and offered a specific response*. The team had limited
  SRE capacity; Priya addressed this with a specific
  answer (60-70% less overhead because the streaming
  product manages the operational burden).
- **Closed with a specific next step.** 90-minute
  working session, Tuesday at 2pm.

### What Priya could have done better

- **Could have asked about the customer's customer.**
  The end-user is the e-commerce shopper. The
  architecture serves them; what does a real-time
  recommendation look like for *them*?
- **Could have used more numbers.** Sub-100ms latency,
  60-70% less overhead, 1 hour to 1 second — but not
  much else. The architecture could have included cost
  estimates, throughput numbers, scaling characteristics.
- **Could have had a backup.** If Tuesday at 2 doesn't
  work for the SRE team, what's the alternative?

### The rubric score

| Signal | Score |
|---|---|
| **Customer-tailored narrative** | 4/4 — anchored on the 3 differences from current setup |
| **Pacing** | 4/4 — 3 deliberate pauses, clear time-boxing |
| **Breakage handling** | N/A — this was an architecture walk, not a product demo |
| **Driving to a next step** | 4/4 — specific date, specific agenda |
| **Honesty about limits** | 3.5/4 — could have noted "we don't do X" if relevant |

**Overall: 3.9/4.** A high-score walk-through.

---

## 4. The 4-pattern: walk-through demo

The architecture-walk-through demo has a 4-pattern that
the product-click-through demo does not:

| Pattern | What it is |
|---|---|
| **1. Frame** | Set the agenda. Name the 3 areas where the design differs. |
| **2. Walk** | Walk through the architecture in logical order (data flow, then transformations, then outputs). |
| **3. Differentiate** | At each major component, name how this differs from the customer's current setup. |
| **4. Tie back** | Tie the differentiation to an implication for the customer. |

The 4-pattern is the *senior* SA demo structure. The
*junior* SA demo structure is the feature tour: walk
through every feature in order. The senior structure is
the differentiation: focus on the 3-5 places where the
design differs from the customer's current setup.

The senior structure is more efficient (less time on
similar features, more time on differences) and more
memorable (the customer remembers "they explained
specifically why sessionization in the streaming layer
is different from sessionization in the app database,"
not "they showed me 15 features").

---

## Try it

Pick an architecture in your specialty — a real one,
not a fictional one. Plan a 10-minute walk-through demo
using the 4-pattern. Identify the 3 places where the
design *differs* from a typical customer's current
setup. Build the "tie back" to the implication.

Run the walk-through with a friend. Your friend plays
the customer's Director of Engineering. At each pause,
have your friend ask a real question (the kind a real
Director would ask). Practice the "tie back" pattern.

The investment is 30-45 minutes. The return is the
ability to run a senior-SA demo on any architecture,
in any specialty. That's the demo round.
