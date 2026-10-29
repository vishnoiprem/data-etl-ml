---
l_id: L02
title: "What is Event-Driven Architecture?"
duration: "6:30"
prereqs:
  - L01 (Course Overview)
---

# L02 — What is Event-Driven Architecture?

> **Section:** 1 — Foundations
> **Duration:** 6:30

## Prereqs

- L01 — Course Overview
- General familiarity with web applications and APIs (no AWS knowledge required)

## Key terms

- **Event** — a statement that something happened, expressed as a JSON
  document. Past tense by convention: "Order Placed", "User Signed Up",
  "File Uploaded".
- **Producer** — the component that *emits* an event. Producers do not
  know — or care — which consumers will react.
- **Consumer** — the component that *reacts* to an event. Consumers do
  not know — or care — which producer sent it.
- **Broker** — the intermediary that receives events from producers and
  fans them out to consumers. EventBridge is one such broker.
- **Synchronous (sync) call** — caller blocks until the callee returns.
  The contract is "I need an answer right now."
- **Asynchronous (async) call** — caller fires the work and continues.
  The contract is "do this whenever, I'll react when I find out."

## Lecture

Before we can talk about EventBridge intelligently, we need to be
precise about what an **event** is and what it means for a system to be
**event-driven**. A lot of words get thrown around here, so let's pin
them down.

### Events vs. commands vs. messages

Three terms get used interchangeably in marketing copy. They are
**not** the same thing:

| Concept | Past tense? | Who knows the receiver? | Example |
|---|---|---|---|
| **Event** | Yes ("Order Placed") | Nobody — it's a fact | "Order 123 was placed at 12:00" |
| **Command** | No ("Charge Card") | The sender picks the receiver | "Charge $49.99 to card X" |
| **Message** | Either | Sender picks queue, not consumer | A row in an SQS queue |

EventBridge is **event-shaped**. Producers don't address events at
specific consumers; they publish facts and let the broker route them.
This is the single most important mental shift in the whole course.

### The producer / consumer / broker triangle

A typical event-driven system has three roles:

```text
   PRODUCER                  BROKER                CONSUMER
  ┌─────────┐  PutEvents  ┌──────────┐  rule  ┌──────────┐
  │  Web    │ ──────────► │ Event    │ ─────► │ Lambda   │
  │  App    │             │ Bridge   │        │ Function │
  └─────────┘             │  Bus     │        └──────────┘
                          │          │        ┌──────────┐
                          │          │ ─────► │ SQS      │
                          │          │        │ Queue    │
                          └──────────┘        └──────────┘
```

The **producer** publishes one event. The **broker** holds rules. Each
**consumer** subscribes by attaching a rule. The producer doesn't
know how many consumers exist, and consumers can be added or removed
without changing the producer.

### Synchronous vs. asynchronous — why decoupling matters

Consider a "place order" flow. In a **synchronous** monolith-style
design, the API does everything inline:

```python
def place_order(request):
    order = save_to_db(request)            # blocking
    charge_card(order)                      # blocking, 2-3 seconds
    send_email(order)                       # blocking, often slow
    update_inventory(order)                 # blocking
    return OrderResponse(order)
```

A single user waits 4-6 seconds. The `send_email` outage takes down
the whole checkout. The team can only ship work in lockstep.

In an **event-driven** design, the API only does what *must* be
synchronous:

```python
def place_order(request):
    order = save_to_db(request)                          # blocking
    eventbridge.put_events(Entries=[{                    # fire-and-forget
        "Source": "com.acme.orders",
        "DetailType": "Order Placed",
        "Detail": json.dumps({"orderId": order.id, ...}),
    }])
    return OrderResponse(order)
```

The user gets a 200 ms response. Email, inventory, analytics, and
loyalty-points all run on their own schedule, can fail independently,
and can be added by a new team that *didn't even exist when the API
was written*. This is the power of decoupling: **the producer's API
contract is the event, not the list of consumers**.

### When event-driven is the wrong answer

It's not always the right tool:

- **You need an immediate answer.** A login API can't fire an event
  and then "see what comes back" — the user is waiting on the session
  token. Use a sync call.
- **You need exactly-once, ordered processing.** Use SQS FIFO or a
  Step Functions state machine, not vanilla EventBridge.
- **The system is small and owned by one team.** Pub/sub overhead
  isn't free; if everyone reads the same code, in-process function
  calls are simpler.

In section 3 we'll see how to combine EventBridge with sync APIs and
queues to get the best of both worlds.

## Hands-on

Nothing to do for this lecture — it is conceptual. In L05 we'll
create our first event bus and you'll see the producer/broker/consumer
triangle in code.

## Quiz prep

- In one sentence, what is an event?
- Why does decoupling (producers not knowing consumers) matter?
- Give an example where a synchronous call is still the right answer.

## Key takeaways

- An **event** is a past-tense fact in JSON; producers don't address
  specific consumers.
- The **broker** (EventBridge) holds the routing rules; producers and
  consumers are decoupled by the event schema.
- **Synchronous** = "I need an answer now"; **asynchronous** = "do this
  whenever, I'll react when I find out."
- Decoupling lets you add consumers, retry independently, and let
  teams ship in parallel.
- Event-driven is the *wrong* answer when you need an immediate,
  ordered, exactly-once response.

## Further reading

- _Serverless Land_ — EventBridge patterns catalog
- _AWS Prescriptive Guidance_ — Event-driven architecture patterns
- L03 — The Pub/Sub Pattern (and how it differs from a queue)
- L04 — Why EventBridge? (and where CloudWatch Events fits)
