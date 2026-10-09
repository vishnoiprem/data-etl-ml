# Scenario Brief — PacificFreight Co.

> **Read this first.** Every lesson in both tracks uses this customer.

---

## The customer

**PacificFreight Co.** is a 12-person cross-border logistics SMB based in Singapore with an ops team in Ho Chi Minh City. They move small commercial freight and personal effects between SG, VN, MY, TH, and PH.

- **Founded:** 2017
- **Team:** 12 total — 4 ops, 3 drivers/warehouse, 2 customer service, 3 leadership/finance
- **Volume:** ~150 inbound customer emails per day; ~80 outbound shipments per day
- **Tools today:** a custom internal shipment tracker (a small PHP web app), Gmail, a shared Google Sheet for handover notes, WhatsApp for urgent customer messages

## The pain

Customer service is the bottleneck. ~70% of inbound emails are the same question in different words:

> *"Where is my shipment PF-10234? I ordered 3 weeks ago and I haven't received anything."*

Each reply takes a human 4-7 minutes:

1. Open the internal tracker
2. Find the shipment by ID
3. Read the latest event ("Held at customs, awaiting duty payment")
4. Open Gmail
5. Draft a reply that:
   - acknowledges the customer
   - explains the status in plain English
   - tells them what to do next
   - signs off in the company voice
6. Send

With 150 such emails per day across 2 CS staff, that's **~16 hours/day** of human time on a task that is 80% templated.

## Why this is an FDE-shaped problem, not just a software problem

- **No API access to the tracker.** The PHP app has no public API and no one's going to write one in a week.
- **The data is messy.** Status events are written by hand. Half are English, half Vietnamese. Some have typos.
- **The customer voice matters.** PacificFreight's reputation is on every reply. The AI tool must draft in their voice, not OpenAI's.
- **There is a real human in the loop.** The CS person must review-and-send. We are not auto-replying.
- **The win is small but measurable.** Cutting 4-7 minutes to 30 seconds per email = ~12 hours/day back to the team.

## The first working tool (Phase 1 deliverable)

A Python CLI that:

1. Reads an inbound email (from a file or stdin)
2. Extracts the shipment ID (regex first, LLM as fallback)
3. Looks the shipment up in the local tracker (a JSON file in this phase; the real tracker in Phase 2)
4. Drafts a reply in PacificFreight's voice
5. Prints the draft to stdout for the CS person to copy-paste into Gmail

That's it. No web UI. No database. No agent loop. The smallest thing that proves the value.

## The 1-pager (the consulting deliverable)

By the end of the consulting track, you will write a 1-pager that captures this whole brief in one printed page, with 8 specific sections (user, job, pain, AI hypothesis, success metric, cost ceiling, risks, test plan). See [`consulting/04-framing-an-ai-use-case.md`](./consulting/04-framing-an-ai-use-case.md).

## What stays out of scope for Phase 1

To be explicit, so the scope doesn't creep:

- ❌ Building a web UI (Phase 2)
- ❌ Auto-sending replies without human review (never, in this engagement)
- ❌ Replacing the PHP tracker (separate engagement)
- ❌ Multilingual reply generation (Phase 3, if PacificFreight wants to pay for it)
- ❌ Slack/WhatsApp integration (later, only if the 1-pager succeeds)

## Sample data you will use

- 50 mock shipments in [`shared/shipments.json`](./shared/shipments.json) — covers all 5 statuses
- 10 real-shaped inbound emails in [`shared/sample-emails.md`](./shared/sample-emails.md) — including ambiguous and multilingual ones
- PacificFreight's voice in [`shared/style-guide.md`](./shared/style-guide.md) — the rules the draft reply must follow

## Why this customer, in one sentence

A 12-person SMB that needs AI to do the boring 80% so their humans can do the hard 20% — that is the FDE's natural customer, and that is the engagement you can finish in 1 week.
