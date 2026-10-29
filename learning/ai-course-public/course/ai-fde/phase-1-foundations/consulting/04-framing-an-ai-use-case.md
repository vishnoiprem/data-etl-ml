# Lesson 04 — Framing an AI Use Case (the 1-pager)

> **The single most important document you will write on any engagement.** 35 minutes. No code.

By the end of this lesson you can write the **1-pager** — the document the FDE hands the customer at the end of week 1 to align on scope, and the document the FDE hands their own team at the start of week 2 to align on the build. You have a 8-section template, a fully worked PacificFreight example, and a checklist for reviewing your own.

---

## 🎯 Outcome

You produce **one artifact**:

- `pacificfreight-1pager.md` — a 1-page markdown document with the 8 sections below, fully filled in for the PacificFreight engagement.

When you finish, you can write a 1-pager in 45 minutes for any new customer, and a reviewer can tell within 30 seconds whether the scope is real.

## 🧠 Mindset

The 1-pager is the **boundary object** between three groups that don't otherwise share a language:

- **The customer** — wants the problem solved, doesn't care about the AI
- **The FDE's engineering team** — wants to know what to build, doesn't care about the customer's politics
- **The FDE themselves** — needs to keep everyone honest about what was actually agreed

A good 1-pager is **short** (1 page, not 5), **testable** (every claim has a number), and **bounded** (clear about what is OFF the table). A bad 1-pager is long, vague, and tries to please everyone.

The four things a 1-pager is NOT:

1. **Not a requirements doc.** A 1-pager has 8 sections. A requirements doc has 80. The 1-pager is what you negotiate; the requirements doc is what you build *after* the 1-pager is signed.
2. **Not a sales deck.** No "we are excited to partner with you" language. No marketing words. The customer is paying you to be specific, not enthusiastic.
3. **Not a technical design.** The 1-pager says *what* you will build, not *how*. The "how" is the solution outline (lesson 05).
4. **Not a contract.** The 1-pager is a working agreement. A contract is a different document with a different audience (legal, procurement). Don't let legal turn your 1-pager into a contract.

> **FDE rule:** if your 1-pager fits on a slide, it's the right size. If it doesn't, you haven't decided what's important yet.

## 🛠️ Practice — the 8 sections

Every 1-pager has these 8 sections, in this order. I give you the **template**, the **why each section exists**, and the **PacificFreight content** for each.

### 1. User

> *Who, specifically, is this for? In their own words.*

**Why this section exists:** to force specificity. "Everyone" is not an answer.

**PacificFreight content:**

> **Primary user:** Mei, the CS lead, and her 2-person CS team. They draft ~150 inbound "where is my parcel?" replies per day, end to end (read → look up → draft → send).
>
> **Secondary user:** Sarah (ops manager). She is the one paying for the engagement and the one who will judge whether it worked.
>
> **Not the user:** the end customer. The CS person is in the loop — the tool never writes directly to a customer.

### 2. Job to be done

> *What is the user trying to accomplish, end to end, in their own words?*

**Why this section exists:** to set the system boundary. The tool is part of a job, not the whole job. The job description tells you what is upstream and downstream of the tool.

**PacificFreight content:**

> When a "where is my parcel?" email lands, the CS person:
> 1. Reads the email
> 2. Looks up the shipment in the internal PHP tracker (~20 seconds)
> 3. Drafts a reply in PacificFreight's voice (4-6 minutes)
> 4. Copy-pastes into Gmail and sends
>
> Total: 4-7 minutes per email. ~10 hours/day across the team. Most of that time is step 3.

### 3. Pain

> *What is the bottleneck? What hurts most, and how do you know?*

**Why this section exists:** to make sure you're solving the right problem. If the pain is step 2 (the lookup), the tool is different than if the pain is step 3 (the drafting).

**PacificFreight content:**

> The bottleneck is **step 3 — the drafting**. Sarah has timed it: the lookup is 20 seconds, the drafting is 4-6 minutes. CS people rewrite every reply because they are afraid of sounding robotic. The cost of the bottleneck is not the time itself — it is the *quality variance* (some replies are 2 sentences, some are 8 paragraphs) and the *emotional cost* (CS people say they "dread" the 50th email of the day).
>
> **What would NOT fix the pain:** faster lookup (already 20s), more CS hires (Sarah has tried, can't hire), canned-template replies (CS team rejected these 2 years ago — said they "sounded like a robot").

### 4. AI hypothesis

> *What is the smallest AI-shaped intervention that would fix the pain?*

**Why this section exists:** to commit to a *specific shape*, not a category. "Use AI" is not a hypothesis. "Draft a reply in the CS team's voice, for the CS person to review-and-send" is.

**PacificFreight content:**

> A CLI tool that takes the inbound email + a shipment ID, looks up the shipment, and drafts a reply in PacificFreight's voice (per `shared/style-guide.md`). The CS person reviews the draft and copy-pastes into Gmail. **The tool never sends.**
>
> This is the smallest intervention that attacks the bottleneck (step 3). It does not touch step 2 (lookup is already fast) or step 4 (sending stays human).

### 5. Success metric

> *How will we know, by when, that this worked? One number, one direction, one date.*

**Why this section exists:** to make the engagement *evaluable*. If you can't measure success, you can't ship.

**PacificFreight content:**

> **Primary metric — as-is ratio:** of the drafts the tool produces, what % does the CS person send without edits?
>
> - Baseline: 0% (no drafts today — they write from scratch)
> - Target: **≥80%** as-is within 4 weeks
> - Measured: CS person clicks "send as-is" or "send with minor edit" vs. "rewrite from scratch"
>
> **Secondary metric — per-email time:**
> - Baseline: 4-7 minutes
> - Target: **< 1 minute** within 4 weeks
>
> **Guardrail metric — CS satisfaction:** the CS team rates the tool ≥ 4/5 on a weekly 1-question survey. If it drops below 3/5 for 2 weeks in a row, we pause and re-scope.

### 6. Cost ceiling

> *What is the customer willing to spend, and what does the FDE expect it to cost?*

**Why this section exists:** to prevent the customer from being surprised by the bill, and to prevent the FDE from over-engineering. Both sides need a number.

**PacificFreight content:**

> **Customer ceiling:** Sarah has approved up to **USD 200/month** in LLM API spend for Phase 1 (covers the 150 emails/day × 30 days = 4,500 drafts/month at the prices in `03-modern-ai-tooling.py`).
>
> **FDE estimate:** at gpt-4o-mini pricing, the actual cost is ~USD 8-15/month. Headroom is 13-25x. The ceiling is set by what Sarah can expense without CFO approval, not by technical cost.
>
> **FDE time budget:** 4 weeks of one FDE (~80 hours). 60% on tool, 30% on change-management with the CS team, 10% on measurement.

### 7. Risks

> *What could go wrong, and what is the early warning?*

**Why this section exists:** to make risks *discussable* in week 1, not surprises in week 4. The customer must agree to these risks in writing.

**PacificFreight content:**

> | Risk | Likelihood | Early warning | Mitigation |
> |---|---|---|---|
> | Tool drafts wrong status (hallucinates) | Medium | CS person flags a "looks wrong" in week 1 | Tool is draft-only; CS person always reviews; the model is told "never invent a status you weren't given" |
> | CS team rejects the tool ("more work, not less") | Medium | Survey drops below 3/5 in week 2 | 30% of FDE time is change-management; ship to 1 CS person first, not all 3 |
> | Email contains PII the tool should not log | Low | PII audit in week 1 | Tool does not log email body to `usage.jsonl`; only logs token counts + cost |
> | Customer asks for auto-send in week 3 | High | Sarah mentions it in week 2 standup | 1-pager says "auto-send is off the table"; FDE redirects to Phase 2 |
> | Tool can't read multi-shipment emails (mentions 2+ PF IDs) | Medium | CS person flags in week 1 | Phase 1: tool handles the *most recent* ID only; multi-shipment is Phase 2 |

### 8. Test plan

> *How will we know, in week 4, that the as-is ratio actually moved?*

**Why this section exists:** to commit to a *measurement* method, not just a metric. A number without a measurement plan is a wish.

**PacificFreight content:**

> **Phase 1 pilot (weeks 3-4):**
> - Mei (CS lead) uses the tool on every "where is my parcel?" email for 10 business days
> - After each send, she clicks one of: "as-is" / "minor edit" / "rewrite"
> - Daily we compute the as-is ratio and per-email time
>
> **Eval set (20 emails, frozen in week 2):**
> - 5 "clean" emails (one PF ID, one shipment)
> - 5 "messy" emails (greetings, signatures, multiple PF IDs mentioned)
> - 5 "multilingual" emails (Vietnamese, Tagalog, Bahasa)
> - 5 "edge case" emails (angry, already-delivered, no PF ID)
>
> We run the eval set against the tool every Friday. If as-is ratio on the eval set drops below 70%, we pause the pilot.
>
> **Go/no-go decision (end of week 4):**
> - GO if as-is ratio ≥ 80% AND per-email time < 1 min AND CS satisfaction ≥ 4/5
> - NO-GO if any of the above fails. We write a 1-page post-mortem and decide whether to iterate, pivot, or stop.

---

## The full PacificFreight 1-pager (assembled)

```markdown
# PacificFreight Co. — AI Drafter 1-pager

**Engagement:** 4-week pilot, starting week 1
**FDE:** [your name]
**Customer sponsor:** Sarah (ops manager)
**Date:** [today]

## 1. User
**Primary:** Mei (CS lead) + 2-person CS team. They draft ~150
"where is my parcel?" replies/day.
**Secondary:** Sarah (ops). Pays the bill, judges the result.
**Not the user:** the end customer (CS person is always in the loop).

## 2. Job to be done
1. Read inbound email
2. Look up shipment in PHP tracker (~20s)
3. Draft a reply in PacificFreight's voice (4-6 min) ← bottleneck
4. Copy-paste into Gmail, send

## 3. Pain
Step 3. CS people rewrite every reply from scratch (fear of
sounding robotic). Cost is quality variance + emotional drag,
not just minutes.

## 4. AI hypothesis
A CLI that takes the email + shipment ID, looks up the shipment,
and drafts a reply in PacificFreight's voice. The CS person
reviews and sends. **The tool never sends.**

## 5. Success metric
- Primary: as-is ratio ≥ 80% within 4 weeks
- Secondary: per-email time < 1 min
- Guardrail: CS satisfaction ≥ 4/5; pause if < 3/5 for 2 weeks

## 6. Cost ceiling
- Customer ceiling: USD 200/month
- FDE estimate: USD 8-15/month at gpt-4o-mini pricing
- FDE time: 4 weeks × 1 FDE (~80h)

## 7. Risks
| Risk | Likelihood | Early warning | Mitigation |
|---|---|---|---|
| Hallucinated status | Med | Week-1 flag | Draft-only; model told not to invent |
| CS team rejects it | Med | Survey < 3/5 in week 2 | Ship to 1 CS first; 30% time on change-mgmt |
| PII in emails | Low | PII audit in week 1 | Don't log email body to usage.jsonl |
| "Can it auto-send?" | High | Sarah mentions it in week 2 | "Off the table" in this 1-pager |
| Multi-shipment email | Med | Week-1 flag | Phase 1 handles most-recent ID only |

## 8. Test plan
- 10-day pilot with Mei in weeks 3-4
- 20-email eval set (clean / messy / multilingual / edge), run every Friday
- Go/no-go at end of week 4: all 3 success metrics met → GO
```

---

## 🏛️ FDE Lens — the technical reality underneath

Every section of the 1-pager maps to a technical decision you will make later:

| 1-pager section | Technical decision it locks in |
|---|---|
| User | UI surface (CLI for one CS user, not a web app for 50) |
| Job to be done | System boundary (read-only from tracker, write-only to draft) |
| Pain | Architecture (drafter, not classifier; not RAG; not agent) |
| AI hypothesis | Pattern choice (Pattern 1 — system + user — from lesson 03) |
| Success metric | Eval harness design (the 20-email set, the as-is measurement) |
| Cost ceiling | Model choice (gpt-4o-mini, not gpt-4o) and prompt size budget |
| Risks | Logging policy (no email body in usage.jsonl), draft-only enforcement |
| Test plan | Eval cadence (weekly), go/no-go criteria (the 3 numbers) |

When the customer asks "why did you build it this way and not another way?", the answer is in the 1-pager. The 1-pager is the source of truth for *why*.

## 🌙 Reflect

Write 3-5 sentences:

1. The 1-pager is "what you signed up to build." What is the cost of skipping it and going straight to code? Give a PacificFreight example.
2. The as-is ratio target is 80%, not 100%. Why? What would happen if the FDE promised 100%?
3. The "off the table" risks (auto-send, refunds) are in the risks section but not in the success metrics. Why split them?
4. The customer ceiling (USD 200/month) is 13x the FDE estimate (USD 8-15). Is the headroom a feature or a bug?
5. A new customer says "I just want a chatbot on my website." Walk through how you would turn that into a 1-pager in 45 minutes.

**What's next** — Lesson 05 turns the 1-pager into a **solution outline**: components, data flow, cost projection, and a week-by-week build plan. The 1-pager says *what*; the solution outline says *how*. Together they are the deliverable of Phase 1.
