---
l_id: L07
title: "Custom Event Buses"
duration: "6:00"
prereqs:
  - L06 (The Default Event Bus)
---

# L07 — Custom Event Buses

> **Section:** 2 — EventBus Basics
> **Duration:** 6:00

## Prereqs

- L06 — The Default Event Bus

## Key terms

- **Custom event bus** — a bus you create explicitly with
  `CreateEventBus`. The name is whatever you want (within the AWS
  naming rules: 1–256 chars, alphanumerics + `-` `_` `.`).
- **Isolation** — using a separate bus so events on bus A cannot
  accidentally trigger rules on bus B.
- **Resource policy** — a JSON policy attached to a bus that
  controls *who can put events on it*. Without one, only the bus
  owner (your account) can publish.
- **Tag-on-create** — you can attach up to 50 tags at bus creation
  time. Tags show up in Cost Explorer and IAM policy conditions.

## Lecture

A custom event bus is just a bus you created yourself with
`CreateEventBus`. That's the entire API. But the *reason* you create
one is what matters, and there are three good reasons.

### 1. Isolation — keep unrelated events apart

The default bus receives events from every AWS service in your
account. A rule on the default bus with a sloppy pattern can
accidentally fire on an event you didn't anticipate. A custom bus
is opt-in: only the events you or your partners publish show up.

```text
   ┌────────────────────────────────────────────────────────┐
   │ AWS account 111122223333, us-east-1                    │
   │                                                        │
   │  default bus                                           │
   │   ↳ all AWS service events                             │
   │                                                        │
   │  custom bus "acme-orders"                              │
   │   ↳ only Order Placed / Order Shipped / …               │
   │                                                        │
   │  custom bus "acme-billing"                             │
   │   ↳ only Invoice Issued / Payment Received / …         │
   └────────────────────────────────────────────────────────┘
```

If the orders team ships a new event, the billing team's rules don't
see it. The default bus doesn't grow. Blast radius shrinks.

### 2. Environment separation — dev / staging / prod

Many teams create one custom bus per environment to keep test
events from accidentally firing production targets:

```text
   custom bus "acme-orders-dev"
   custom bus "acme-orders-staging"
   custom bus "acme-orders-prod"
```

The production bus has tightly scoped rules and a tightly scoped
resource policy (only prod apps can publish to it). Dev and staging
are open.

### 3. Cross-account sharing — give a partner or another account
access

This is the big one. The default bus is account-local. To let
**another AWS account** or a **SaaS partner** put events onto a bus
in *your* account, you create a custom bus and attach a resource
policy granting that principal `events:PutEvents`. We cover that in
detail in L08.

### Naming rules

A bus name must:

- Be 1–256 characters long.
- Match the regex `[\.\-_A-Za-z0-9]+` (alphanumerics, `.`, `-`, `_`).
- Be unique within (account, region) — same name in two regions is
  fine; same name twice in one region is not.

Common patterns:

- `acme-orders`, `acme-billing` (team or domain)
- `acme-orders-prod`, `acme-orders-dev` (team + env)
- `partner-zendesk`, `partner-datadog` (per partner — though AWS
  auto-names partner buses for you)

### What you can't do

- **You can't rename a bus.** Pick a stable name at creation time.
- **You can't move a bus to another region.** Event buses are
  regional. If you need it in `eu-west-1`, create it there.
- **You can't make a bus global.** Cross-region routing requires
  a rule with a cross-region target (section 3 / section 7).
- **You can't delete the default bus.** But you can delete any
  custom bus you own, which cascades to its rules and targets.

### The boto3 call

The full API is small:

```python
import boto3
client = boto3.client("events", region_name="us-east-1")

resp = client.create_event_bus(
    Name="acme-orders",
    Tags=[{"Key": "team", "Value": "orders"}, {"Key": "env", "Value": "prod"}],
)
print(resp["EventBusArn"])
# arn:aws:events:us-east-1:111122223333:event-bus/acme-orders
```

If the bus already exists, `CreateEventBus` raises
`ResourceAlreadyExistsException` — which is why the production
script in L09 is **idempotent**: it catches the error and treats it
as a successful no-op.

### Costs and limits

Custom event buses themselves are free. You pay for:

- **Events ingested** — $1.00 per million events published
  (custom or AWS service events).
- **Events matched to a target** — first 100k / month free per
  region, then tiered.
- **Archive storage** — separate cost, only if you turn on an
  archive.

Soft limits (you can raise these):

- 100 event buses per (account, region)
- 300 rules per bus
- 5 targets per rule

## Hands-on

Optional: create a custom bus in your account.

```bash
aws events create-event-bus \
    --name acme-orders \
    --tags Key=team,Value=orders Key=env,Value=dev \
    --region us-east-1
```

You should see an `EventBusArn` echoed back. (Delete it later with
`aws events delete-event-bus --name acme-orders`.) In L09 we wrap
this into a real Python script with tests.

## Quiz prep

- Name three reasons to create a custom bus instead of using the
  default.
- Can you rename a bus? (No — pick the name at creation time.)
- What's the regex for a bus name?

## Key takeaways

- A **custom bus** is just a bus you created with `CreateEventBus`.
- You create one for **isolation, environment separation, and
  cross-account / cross-principal sharing**.
- The name is 1–256 chars, `[A-Za-z0-9._-]+`, unique per
  (account, region).
- You can't rename, move, or globalize a bus — pick a stable name
  in the right region from day one.
- Buses are free; you pay for events published, events matched,
  and (if you turn it on) archive storage.

## Further reading

- _Amazon EventBridge User Guide_ — "Creating an event bus"
- _Amazon EventBridge Pricing_ — https://aws.amazon.com/eventbridge/pricing/
- L08 — Partner Event Bus (SaaS events)
- L09 — Section Recap + `create_event_bus.py` walk-through
