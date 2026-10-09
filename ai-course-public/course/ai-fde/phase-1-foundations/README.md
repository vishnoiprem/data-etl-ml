# AI FDE — Phase 1: Foundations

> **The on-ramp to becoming an AI Forward-Deployed Engineer.**
> Two parallel tracks. One real customer. One working AI tool at the end.

An **AI FDE** sits between consulting and engineering. They walk into a customer's office, spend a week asking questions, leave with a working AI tool, and a plan to scale it. This phase teaches you to do exactly that — at the smallest possible scope.

---

## What you will produce by the end of Phase 1

1. **A first working AI tool** — a Python CLI that takes a customer email and drafts a reply a human can review-and-send in 30 seconds.
2. **A clear problem statement** — a 1-page document you could hand to your client and a stakeholder.
3. **An initial solution outline** — the system sketch (data flow, components, cost, risks) you would present in a Phase 2 kickoff.

That is it. Phase 1 is **not** a full RAG system, **not** a multi-agent orchestrator, **not** a production deployment. It is the smallest end-to-end thing that proves the value.

---

## The scenario (one customer, used in every lesson)

**Customer:** PacificFreight Co. — a 12-person cross-border logistics SMB in Singapore & Vietnam.
**Pain:** ~150 inbound customer emails per day asking *"where is my shipment?"* Each reply takes a human 4-7 minutes to look up in the internal tracker, draft a reply, and send.
**Goal of the AI tool:** take the inbound email + a shipment ID, look up the tracking event, and draft a reply a human can review-and-send in 30 seconds.

Read the full brief: [`scenario-brief.md`](./scenario-brief.md).

The same scenario is used in every lesson in both tracks. That is the point — the technical lessons build the tool, the consulting lessons teach you how to *frame* the work, and the FDE role is where they meet.

---

## Two parallel tracks

| Track | What you learn | What you produce | Files |
|---|---|---|---|
| **Technical** | Python, Git, AI SDKs, shipping a working CLI | A runnable Python CLI that drafts replies | [`technical/`](./technical/) |
| **Consulting** | Discovery, framing, prompting patterns, scoping | A problem statement + a solution outline | [`consulting/`](./consulting/) |

You can take the tracks in either order, but the **end-of-phase deliverable** is the same artifact seen from two sides: the **code** (technical) and the **document that justifies the code** (consulting).

See:
- [TECHNICAL-TRACK.md](./TECHNICAL-TRACK.md) — the 4-lesson map
- [CONSULTING-TRACK.md](./CONSULTING-TRACK.md) — the 5-lesson map

---

## The standard template (locked in for every lesson)

### Technical lesson (.md + .py/.sh)

```markdown
# Lesson N: <Title>
## 🎯 You will build
## 🧠 Concept (5 min)
## 🛠️ Build It (20-40 min)
## 🏛️ FDE Lens
   — the one question to ask the client before you start coding
## 🌙 Reflect
   — what to write down + "What's next" pointer
```

### Consulting lesson (.md only)

```markdown
# Lesson N: <Title>
## 🎯 Outcome
   — the artifact you produce (a doc, a question list, a 1-pager)
## 🧠 Mindset
   — the principle
## 🛠️ Practice
   — the exercise, with a worked example
## 🏛️ FDE Lens
   — the technical reality underneath
## 🌙 Reflect
   — what to write down + "What's next" pointer
```

---

## Shared assets (used by both tracks)

- [`shared/shipments.json`](./shared/shipments.json) — 50 mock shipments across 5 statuses (the "internal tracker" stand-in)
- [`shared/sample-emails.md`](./shared/sample-emails.md) — 10 real-shaped inbound emails (clean, ambiguous, multilingual, missing info)
- [`shared/style-guide.md`](./shared/style-guide.md) — how PacificFreight wants replies to sound

---

## How to use this phase

1. **Read `scenario-brief.md` first** (5 min). It sets the customer.
2. **Pick a track** to start. Most people start with Technical — it's tangible.
3. **Do one lesson per session.** Each is 20-40 min of build time + 5 min of reflection.
4. **At the end of each lesson, write the reflection.** It compounds.
5. **At the end of the phase, you have a tool + a 1-pager + a plan.** That is the deliverable you walk into Phase 2 with.

---

## What's after Phase 1

Phase 1 is the on-ramp. After it, you can go to:

- **`course/practice/`** — per-lesson architect-grade labs (the conceptual + teaching track)
- **`course/hardcode/`** — 19 production-grade AI systems (the "hard coder" track)
- **`course/capstone-starters/01-ai-doc-qa/`** — the full document-Q&A RAG capstone (a natural Phase 2 build for PacificFreight)
- **`course/workbooks/exercises/`** — paired exercises for the AI engineer codebook

---

**Last updated:** 2026-10-09
**Tone:** hands-on, FDE-style, with practical code in every lesson
**Goal:** You finish Phase 1 and you can walk into a customer's office on Monday.
