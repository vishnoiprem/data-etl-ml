# Step 2 — Decompose (entities, services, flows)

> **The decomposition step is the system's skeleton.** After 5 clarifying questions, you list 3-5 entities, 3-5 services, and 3-5 flows. **No technology yet.** The signal: a candidate who can decompose without naming a database or an LLM is showing they can think before they build.

---

## The 3 lists (always, in this order)

### 1. Entities (3-5, named, not numbered)

Entities are the nouns. They become the data model later.

| Question | Entities |
|---|---|
| Email reply drafter | User, Email, Shipment, Draft, Feedback, Metric |
| Shipment tracker | Carrier, Shipment, Status, Webhook, User |
| Document sharing | User, Document, Permission, Audit, Share, Notification |
| AI deployment with cost ceiling | Tenant, Draft, Cost, Circuit, Alert |

**The signal:** 3-5 entities, named, with a 1-line description each. Not "User" but "User — the CS team, ~50 people, 1 role per user." The description is the data model.

### 2. Services (3-5, one per entity, roughly)

Services are the verbs. They become the API endpoints later. **One entity per service is the rule of thumb; some entities share a service.**

| Entities | Services |
|---|---|
| User, Email, Shipment, Draft, Feedback, Metric | DraftService (Email + Shipment + Draft), FeedbackService (Feedback), MetricsService (Metric), UserService (User) |

**The signal:** the candidate who can map entities to services without naming a technology (FastAPI, gRPC, etc.) is showing they can think about boundaries.

**The rule of thumb:** if a service owns 2 entities, those entities should have a 1-to-many relationship. (One User has many Emails.) If they have a many-to-many relationship, they should be in different services. (Drafts and Feedback are many-to-many through the Email.)

### 3. Flows (3-5, end-to-end, with conditions)

Flows are the sentences. They connect entities through services. **Each flow has a trigger and a side effect.**

| Flow | Trigger | Steps | Side effect |
|---|---|---|---|
| Email → Draft | Email arrives | RetrievalService fetches Shipment → LLM produces Draft → DraftService saves Draft | Draft is logged to usage.jsonl |
| Draft → Feedback | User clicks thumbs-up | FeedbackService updates Feedback | Metric is updated, eval set is rebuilt |
| Cost → Alert | Cost meter tick | CostService increments Cost → CircuitService checks ceiling → AlertService pages on-call | On-call is paged if at 80% of ceiling |

**The signal:** the candidate who can name the trigger, the steps, and the side effect is showing they understand the system's behavior, not just its structure.

---

## The 3 decomposition anti-patterns

1. **Naming a technology before step 3.** "We'd use Postgres for entities, FastAPI for services, Kafka for flows" is a junior answer. The technology comes in step 3.
2. **Listing 10 entities.** 3-5 is the signal. 10 is the symptom of not thinking.
3. **Listing entities that don't connect.** If your entities don't appear in any flow, they're not entities — they're attributes. "Color" is an attribute of "Document," not an entity.

---

## The 4 decomposition patterns (the cheat sheet)

### Pattern 1: User-Generated Content (UGC)

- **Entities:** User, Content, Metadata, Comment, Vote
- **Services:** ContentService, CommentService, VoteService
- **Flows:** User creates Content → Content is indexed → User votes → Vote updates Content's score

### Pattern 2: Workflow / Approval

- **Entities:** User, Request, Approval, Notification, Audit
- **Services:** RequestService, ApprovalService, NotificationService
- **Flows:** User submits Request → Approval is assigned → Approver approves → Notification is sent → Audit is logged

### Pattern 3: Real-Time Tracking

- **Entities:** Source, Event, Entity, State, Subscriber
- **Services:** IngestionService, StateService, NotificationService
- **Flows:** Source emits Event → State is updated → Subscribers are notified

### Pattern 4: AI / ML Inference

- **Entities:** User, Input, Context, Output, Feedback, Metric
- **Services:** RetrievalService, InferenceService, FeedbackService
- **Flows:** User submits Input → Context is retrieved → Inference produces Output → User provides Feedback → Metric is updated

**The PacificFreight drafter is Pattern 4.** The 4 case-study questions in `../README.md` are 1 UGC, 1 Workflow, 1 Real-Time, 1 AI/ML. The candidate who recognizes the pattern buys 5 minutes of thinking time.

---

## How to use this file

1. **Memorize the 3 lists** (entities, services, flows).
2. **Memorize the 4 patterns.** They're the cheat sheet for 80% of decomposition questions.
3. **Practice on the 5 sample questions in `../README.md`.** Time yourself: 10-12 minutes for the 3 lists.
4. **Rehearse with an AI assistant.** Have it score you on the 3 anti-patterns.
5. **Use the 4 patterns as scaffolding.** If you don't know the answer, fall back to "this is a Pattern 4 (AI/ML inference)" — that's a 30-second answer that buys you thinking time.
