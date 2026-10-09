# Lesson 01 — Requirement Discovery

> **The 5-question framework, extended for RAG-readiness.** 35 minutes. No new code.

By the end of this lesson you can take the Phase 1 1-pager and ask the **next layer** of questions — the ones that determine whether the customer's data, people, and infrastructure are ready for a RAG-augmented service. You have a 10-question discovery deck template and a worked PacificFreight example.

---

## 🎯 Outcome

You produce **one artifact**:

- `discovery-deck.md` — a 1-2 page markdown document with the original 5 questions (from Phase 1 lesson 02) PLUS 5 more questions that probe RAG-readiness, data privacy, and deployment topology.

When you finish, you can walk into a customer meeting at the *start* of Phase 2 and walk out with a 10-question matrix that tells you whether to build, scope down, or walk away.

## 🧠 Mindset

Phase 1's 5-question framework is enough to write a 1-pager. Phase 2's 5 extra questions are enough to write a **PRD** (next lesson) and an **architecture view** (after that).

The original 5 questions assume the answer to all of them is "yes, we have that" — a name, a job, a bottleneck, a metric, a scope. The 5 new questions probe the **system-ness** of the answer:

> Phase 1 asked "what's the user?" Phase 2 asks "is the user's environment ready to host an LLM service?"
> Phase 1 asked "what's the success metric?" Phase 2 asks "can you measure it on the data you actually have?"
> Phase 1 asked "what's off the table?" Phase 2 asks "what about PII, multi-tenancy, and deployment?"

The traps:

1. **The data-trap.** The customer says "we have the data." You ask "in what format, how fresh, who owns updates?" and discover the data is in 3 spreadsheets updated by 2 people on Fridays. **RAG-readiness question #2.**
2. **The privacy-trap.** The customer says "send it to OpenAI / Anthropic / Cohere." You ask "do you have a PII policy?" and discover the emails contain passport numbers. **RAG-readiness question #3.**
3. **The deployment-trap.** The customer says "we'll use it." You ask "where will it run, who manages it, how is it monitored?" and discover the customer's IT team won't approve any new cloud vendor. **RAG-readiness question #4.**

> **FDE rule:** if any of the 5 new questions gets a "we don't know" or a hand-wave, **stop the engagement until the customer has an answer**. The cost of skipping this is a 4-week build that can't ship.

## 🛠️ Practice — the 10 questions

### The original 5 (from Phase 1 lesson 02, for reference)

1. **Who is the user?**
2. **What are they trying to do, end to end?**
3. **What is the bottleneck?**
4. **What would "fixed" look like?**
5. **What is off the table?**

If the customer can answer all 5, you have Phase 1 scope. For Phase 2, ask the next 5.

### The new 5 (RAG-readiness)

#### Q6 — Where does the knowledge live?

> *"For the drafter to draft a reply, it needs to retrieve two things: the shipment status (which lives in your tracker) and the policy text (which lives in your style guide). Where do those two things live today, in what format, how fresh, and who owns updates?"*

**Why:** if the tracker has an API, the drafter calls it. If it's a daily CSV dump, the drafter reads the file. If it's a PHP webapp with no API, the drafter needs a Phase 2.5 lift (or the customer's IT team needs to provide an API). **You can't build without knowing the data shape.**

**Red flag:** the customer says "it's in our system" without naming the system. Push: "is it a database, a file, a webapp, an API, a vendor's tool?"

**PacificFreight answer:**

> Tracker: a PHP webapp that Daniel (IT) owns. No API today. Daily export to a JSON file at `data/shipments.json`. The CS team has read-only access to the JSON. **Phase 2 reads the JSON; Phase 3 asks Daniel for an API.**
>
> Policy: in `style-guide.md` in our shared Google Drive. Sarah owns it. Updated quarterly, last updated 2026-09-15.

#### Q7 — How fresh is the data?

> *"When the tracker changes, how fast does the JSON export reflect the change? When the policy changes, how fast does the drafter see the new rules?"*

**Why:** a daily JSON export means the drafter is **24 hours stale**. For "where is my parcel?" that's fine. For "is this customs payment received?" that's wrong. **Freshness is a hard constraint on the use case.**

**Red flag:** the customer says "real-time" but the only available export is a daily batch. Push: "is the customer OK with a 24-hour lag?"

**PacificFreight answer:**

> Tracker: 24-hour lag via the daily export. Acceptable for the drafter because the customer-facing event ("payment received") is also updated by a 24-hour batch on the carrier side.
>
> Policy: the drafter is built on a snapshot of `style-guide.md`. Sarah commits to re-running `build_policy_chunks.py` within 48 hours of any policy change.

#### Q8 — What is the PII / data-privacy posture?

> *"Customer emails contain names, addresses, sometimes passport numbers for customs. What is your policy on sending that data to OpenAI / Anthropic / Cohere / any third-party LLM? Do you have a data-processing agreement with the LLM vendor? Does the data leave your region?"*

**Why:** if the answer is "no, we can't send PII to OpenAI," you self-host (Llama 3 70B, vLLM, on the customer's VPC). If the answer is "yes, with a DPA," you use the cloud API and you redaction-strip names before sending. **This decides the deployment topology, the model choice, and the cost.**

**Red flag:** the customer says "we don't have a policy" or "ask legal." Both mean the engagement is paused until legal answers.

**PacificFreight answer:**

> PII policy: PDPA (Singapore) compliance. Daniel has confirmed that customer name + shipment ID + last event are OK to send to OpenAI under their existing DPA. **Email body is NOT sent to OpenAI** — only the extracted shipment ID + the looked-up status. (We redaction-strip in the application layer.)
>
> Regional constraint: data must stay in Singapore. **We use OpenAI's Singapore region (or self-host if that's not available).**

#### Q9 — Where will the service run, and who owns it?

> *"The service runs in a Docker container. Where will the container run? Who restarts it when it crashes? Who monitors the logs? Who applies security patches? Who pays the bill?"*

**Why:** the drafter is a 24/7 service that the CS team depends on. **Somebody** needs to own its operations. If the answer is "nobody," you don't ship — you write a runbook and a paging policy in the same week as the build, not after.

**Red flag:** the customer says "we'll figure it out." Push: "name one person who gets paged at 3 AM if the service is down."

**PacificFreight answer:**

> Deployment target: a single VM on PacificFreight's existing AWS Singapore account, managed by Daniel (IT).
>
> Owner: Daniel owns the VM. Mei owns the service config (style guide, tracker path, prompt).
>
> Paging: the CS team has a Slack channel that the service posts errors to. Mei checks it daily. Daniel has on-call for VM-level issues.
>
> Cost: ~$5/month for the VM + ~$1-3/month in LLM cost. Daniel has a separate AWS budget for this.

#### Q10 — What does the pilot look like?

> *"Phase 1 ended with Mei using a CLI. Phase 2 should end with the whole CS team using the service. What does the pilot look like? How many users, what volume, what success metric, what decision at the end?"*

**Why:** the pilot is the **test** that decides if Phase 3 happens. Without a defined pilot, the FDE's "did it work?" at the end of week 4 is a vibe check, not a measurement.

**Red flag:** the customer says "let's just see how it goes." Push: "what number moves, in what direction, by when, to call this a success?"

**PacificFreight answer:**

> Pilot (weeks 3-4 of Phase 2):
> - All 3 CS team members use the service for every "where is my parcel?" email
> - Volume: ~150 emails/day
> - Success: 80% of drafts are sent with no edits (up from Phase 1's Mei-only baseline of ~70%)
> - Decision at end of week 4: GO to Phase 3 (production rollout) if 80% is met. NO-GO if < 60%. PIVOT (re-scope, different model) if 60-80%.

---

## The full PacificFreight discovery deck (assembled)

```markdown
# PacificFreight — Phase 2 Discovery Deck

## Phase 1 1-pager (signed 2026-09-15)
[link to pacificfreight-1pager.md]

## The 5 new questions

### Q6. Where does the knowledge live?
- Tracker: PHP webapp (Daniel owns), daily JSON export at data/shipments.json
- Policy: style-guide.md in Google Drive (Sarah owns), quarterly updates
- Phase 2: read the JSON + chunk the markdown
- Phase 3: ask Daniel for a tracker API

### Q7. How fresh is the data?
- Tracker: 24h lag, acceptable for the use case
- Policy: re-chunk within 48h of any change (Sarah commits)

### Q8. PII / data-privacy?
- PDPA Singapore, DPA with OpenAI ✓
- Send: name + shipment ID + last event. NOT: email body.
- Region: Singapore. Use OpenAI SG region or self-host.

### Q9. Where will it run?
- VM on AWS Singapore (Daniel owns)
- Slack channel for errors (Mei monitors)
- Cost: $5/mo VM + $1-3/mo LLM

### Q10. What does the pilot look like?
- 3 CS users, 150 emails/day, 2 weeks
- Success: 80% as-is, 70% → 80%
- Decision: GO if ≥ 80%, NO-GO if < 60%, PIVOT if 60-80%
```

---

## 🏛️ FDE Lens — the technical reality underneath

Each of the 5 new questions maps to a technical decision:

| Question | Technical decision it drives |
|---|---|
| Q6 (where does the data live) | File-based vs API-based lookup in the service |
| Q7 (how fresh) | Caching strategy, polling interval, or "snapshot at startup" |
| Q8 (PII) | Redaction layer, region pinning, model choice (cloud vs self-host) |
| Q9 (where will it run) | Deployment shape (container, VM, serverless), monitoring stack, paging policy |
| Q10 (pilot) | Eval set size, success metric threshold, go/no-go criteria |

When the customer says "we want to do RAG," the 5 new questions turn it into a buildable spec. **Skip them and you will build for 4 weeks, demo to the customer, and hear "we can't actually use this in production because of [PII / deployment / freshness]."**

## 🌙 Reflect

Write 3-5 sentences:

1. Q6 ("where does the knowledge live") is the most common blocker. Why is "we have the data" never enough?
2. Q8 (PII) is the question that can stop an engagement. Why is the FDE responsible for asking it, not legal?
3. Q10 (the pilot) is the question that decides if the engagement scales. What's the cost of running a pilot with no defined success metric?
4. A new customer (a healthcare company) wants to use the same drafter for patient appointment emails. How would Q6-Q10 change?
5. The customer answered all 5 new questions "we don't know yet." Walk through what you say in the meeting.

**What's next** — C2 turns this discovery deck into a **PRD** and a **solution-design document**. The discovery deck is what you *heard*; the PRD is what you're *building*; the design doc is *how you'll build it*. The three documents are the consulting track's deliverable, and they go to three different audiences: the discovery deck goes to the customer, the PRD goes to the engineering team, the design doc goes to the customer's exec sponsor.
