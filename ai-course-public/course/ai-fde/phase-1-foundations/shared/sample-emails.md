# Sample Inbound Emails — PacificFreight

> **10 real-shaped emails** the CS team receives every day. Use these to test your CLI.
> Each has a metadata block (sender, when received) and a body.
> Some are clean, some are ambiguous, some are missing the shipment ID on purpose.

---

## Email 1 — clean and easy (the "happy path")

**From:** Aisha Rahman <aisha.r@example.com>
**Received:** 2026-10-09 08:14 (SGT)
**Subject:** Where is my parcel PF-1001?

```
Hi PacificFreight,

Can you check on my shipment PF-1001? I was told it would arrive last week
but I haven't received it yet. Could you let me know what's happening?

Thanks,
Aisha
```

---

## Email 2 — multilingual (Vietnamese)

**From:** Linh Nguyen <linh.n@example.vn>
**Received:** 2026-10-09 09:02 (SGT)
**Subject:** Hỏi về đơn hàng

```
Chào PacificFreight,

Cho tôi hỏi đơn PF-1009 đã giao chưa ạ? Tôi không thấy thông báo giao hàng.

Cảm ơn,
Linh
```

> *Approximate English: "Hi PacificFreight, may I ask whether order PF-1009 has been delivered? I haven't received a delivery notification. Thanks, Linh."*

---

## Email 3 — missing the shipment ID (must be inferred)

**From:** Wei Chen <wei.chen@example.cn>
**Received:** 2026-10-09 09:30 (SGT)
**Subject:** Help with my shipment to Shanghai

```
Hello,

I sent a parcel from Singapore to Shanghai about 10 days ago through your
service. I think the booking reference starts with PF-10. Customs is
holding it and I got a message but I can't read it properly. Can someone
help me?

Wei
```

> The real ID is **PF-1010**. The tool must find it.

---

## Email 4 — multiple shipments, customer is confused

**From:** Sarah Williams <sarah.w@example.com>
**Received:** 2026-10-09 10:11 (SGT)
**Subject:** RE: Damage to my parcel?

```
Hi,

I'm following up on a damaged parcel that arrived at your Sydney hub. The
booking was PF-1008 I think. I also have another one PF-1006 still in
transit to Chennai. Could you update me on both?

Sarah
```

> Two IDs. Tool should flag this and reply to the urgent one first.

---

## Email 5 — wrong ID format (extra spaces, all caps)

**From:** Daniel Tan <daniel.tan@example.sg>
**Received:** 2026-10-09 10:45 (SGT)
**Subject:** PF 1002

```
Hi team,

Where is " PF 1002 " ? My KL customer is asking.

Daniel
```

> Whitespace + lowercase-of-an-uppercase expectation. Tool must normalize.

---

## Email 6 — angry + urgent (tone matters)

**From:** Carlos Reyes <carlos@example.ph>
**Received:** 2026-10-09 11:02 (SGT)
**Subject:** URGENT — still no delivery after 2 weeks

```
This is the THIRD time I'm writing in. Shipment PF-1004. Two weeks. No
parcel. No explanation. No phone call back. If this is not resolved today
I am filing a chargeback with my card provider.

I want a manager to call me.

Carlos
```

> Tool must draft a *de-escalating* reply that hands off to a human, not a defensive one.

---

## Email 7 — already delivered, customer didn't see the SMS

**From:** Mei Lin <mei.lin@example.my>
**Received:** 2026-10-09 11:33 (SGT)
**Subject:** re: shipment status

```
Hi,

You said my package would arrive last week. It's been 2 weeks. I never
got anything. Reference: PF-1003.

Mei
```

> The real status is `held_customs` and the customer needs to pay a duty — but the email reads like "delayed". The tool must read the tracker, not just the customer's framing.

---

## Email 8 — no shipment ID at all (very common)

**From:** Aarav Patel <aarav.p@example.in>
**Received:** 2026-10-09 12:01 (SGT)
**Subject:** Status?

```
Hi, where is my parcel? Sent from Singapore to Mumbai a few days ago.

Aarav
```

> The tracker has **PF-1011**. Tool should match by customer name (Aarav) or destination (Mumbai) as a fallback, or ask the human to clarify.

---

## Email 9 — short, polite, contains only the ID

**From:** Hiroshi Tanaka <hiroshi@example.jp>
**Received:** 2026-10-09 12:18 (SGT)
**Subject:** PF-1007

```
Status please.

Hiroshi
```

> Minimum viable email. Tool must not over-explain.

---

## Email 10 — clearly out of scope (we are not the carrier)

**From:** Priya Nair <priya.n@example.in>
**Received:** 2026-10-09 12:50 (SGT)
**Subject:** Wrong delivery?

```
Hi, I ordered a phone case from Shopee last week and a different brand
arrived. I think your company delivered it. Can you help me with the
return?

Priya
```

> Priya is in our tracker (PF-1006, in transit to Chennai) but the actual complaint is about a Shopee order. The tool must not pretend to help with the Shopee return — it should reply about PF-1006 and politely redirect the Shopee question to Shopee.

---

## How to use these

Run your CLI on each one. For each draft reply, ask:

1. **Did the tool find the right shipment ID?** (or correctly say it couldn't?)
2. **Did the draft follow [`style-guide.md`](./style-guide.md)?**
3. **Did the tone match the customer's tone?** (Email 6 needs a human, not an apology; email 9 needs brevity, not a paragraph.)
4. **Did the tool refuse to answer things it shouldn't?** (Email 10's Shopee question.)

You are looking for **4 out of 5 correct** before you demo this to PacificFreight. Anything worse and you ship a tool that embarrasses them.
