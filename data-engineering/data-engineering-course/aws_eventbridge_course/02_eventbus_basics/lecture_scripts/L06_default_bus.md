---
l_id: L06
title: "The Default Event Bus"
duration: "5:30"
prereqs:
  - L05 (What is an Event Bus?)
---

# L06 — The Default Event Bus

> **Section:** 2 — EventBus Basics
> **Duration:** 5:30

## Prereqs

- L05 — What is an Event Bus?

## Key terms

- **Default bus** — the bus that AWS creates automatically in every
  account, in every region, with the literal name `default`. You
  cannot delete it.
- **AWS service event** — an event published by an AWS service when
  something happens (EC2 state change, S3 object created, CodeBuild
  build failed, …). The source is `aws.<service>` (e.g. `aws.ec2`,
  `aws.s3`).
- **Implicit resource policy** — the default bus has a *managed*
  resource policy that allows AWS service principals to put events
  on it. You usually don't need to touch it.
- **`PutEvents` API** — the boto3 / SDK call that publishes a custom
  event onto a bus. Anyone with `events:PutEvents` on the bus can
  publish.

## Lecture

Every AWS account comes with one free event bus, in every region,
with the name `default`. It is the **default** because if you don't
specify a bus in your `PutEvents` call, AWS sends the event to the
default bus. It is also the bus that almost every AWS service uses
when it publishes an event.

### What's already on the default bus

You don't need to do anything to get it. As soon as your account
exists, in every region, there is a `default` bus with this ARN:

```text
arn:aws:events:us-east-1:111122223333:event-bus/default
```

And it has a managed resource policy that allows AWS service
principals (e.g. `events.amazonaws.com`, `ec2.amazonaws.com`,
`s3.amazonaws.com`) to put events on it. You can read the policy but
you rarely need to change it.

### What arrives on the default bus

Three flavors of event:

1. **AWS service events.** When an EC2 instance transitions to
   `stopped`, when an S3 object is created, when a CodeBuild build
   fails — the service publishes an event onto the default bus in
   the region where the resource lives. The `source` is `aws.<service>`
   and the `detail-type` is the event name (e.g. `EC2 Instance
   State-change Notification`).
2. **Custom app events via `PutEvents`.** Your own code can call
   `events.put_events(Entries=[{...}])` and target the default bus
   explicitly. The `source` should be your reverse-DNS identifier
   (e.g. `com.acme.orders`).
3. **Scheduled events from EventBridge Scheduler.** A schedule can
   target the default bus (or any other bus). The `source` is
   `aws.scheduler` and the `detail-type` is `Scheduled Event`.

```text
    AWS EC2 in us-east-1 ─► default bus (us-east-1)
    AWS S3  in us-east-1 ─► default bus (us-east-1)
    Your app via PutEvents ─► default bus (any region)
    EventBridge Scheduler ─► default bus (any region)
```

### A real default-bus event

Here's a typical EC2 state-change event as it lands on the default
bus (formatted for readability):

```json
{
  "version": "0",
  "id": "7bf73129-1428-4cd3-a780-98db251d0d54",
  "detail-type": "EC2 Instance State-change Notification",
  "source": "aws.ec2",
  "account": "111122223333",
  "time": "2026-10-10T12:00:00Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:ec2:us-east-1:111122223333:instance/i-0abc123def456"
  ],
  "detail": {
    "instance-id": "i-0abc123def456",
    "state": "stopped"
  }
}
```

Eight envelope fields plus a free-form `detail` object. The
envelope is the same for every event; the `detail` is what each
source defines for itself. This is what event patterns match
against (section 3) and what your Lambda receives as the `event`
argument (section 4).

### Why you'd *not* use the default bus

The default bus is convenient, but in larger accounts you usually
want a **custom bus** instead. Common reasons:

- **Noisy by default.** Every AWS service that publishes events
  publishes to the default bus. Even if you have zero rules, the
  bus receives a constant trickle of events from across your
  account. A custom bus is opt-in.
- **Hard to share across accounts.** The default bus is account-local.
  If you want another account (or a SaaS partner) to publish to
  you, you typically create a custom bus and attach a resource
  policy granting that principal access.
- **Hard to clean up.** You can't delete the default bus, and you
  can't fully detach it from the implicit "AWS services publish
  here" behavior. A custom bus is something you own end to end.

For personal projects and single-account dev environments, the
default bus is fine. For anything in production, you'll usually
have one or more custom buses as well.

### One boto3 call to inspect it

You can list every bus in the account and confirm the default is
there:

```python
import boto3
client = boto3.client("events", region_name="us-east-1")
for bus in client.list_event_buses()["EventBuses"]:
    print(bus["Name"], bus["Arn"])
# default  arn:aws:events:us-east-1:111122223333:event-bus/default
```

We extend this in L07 to also create a custom bus — and in L09 we
wire it up into a real, idempotent script with tests.

## Hands-on

Optional: from your laptop, run

```bash
aws events list-event-buses --region us-east-1
```

You should see exactly one entry: `default`. (If your account has
been used before, you may see more.)

## Quiz prep

- What is the literal name of the auto-created bus? (`default`)
- Can you delete the default bus? (No.)
- Three flavors of event that arrive on the default bus?

## Key takeaways

- Every account, every region, has a `default` bus — auto-created,
  auto-named, undeletable.
- The default bus receives **AWS service events**, **custom app
  events via `PutEvents`**, and **scheduled events** from
  EventBridge Scheduler.
- It has a **managed resource policy** granting AWS service
  principals permission to publish.
- For production, you usually create a **custom bus** for
  isolation, opt-in event flow, and cross-account sharing.

## Further reading

- _Amazon EventBridge User Guide_ — "AWS service events"
- L07 — Custom Event Buses
- L09 — Section Recap + `create_event_bus.py` walk-through
