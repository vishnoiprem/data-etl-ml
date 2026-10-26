# Lesson 05 — Solution Outline (the build plan)

> **The 1-pager says WHAT. The solution outline says HOW.** 30 minutes. No new code, but a diagram you can draw in 5 minutes.

By the end of this lesson you can turn the 1-pager into a **solution outline** — the document the engineering team actually builds from. You have a 6-section template, a fully worked PacificFreight example with a data-flow diagram, and a week-by-week build plan. Together with lesson 04, this is the **second half of the Phase 1 deliverable**.

---

## 🎯 Outcome

You produce **one artifact**:

- `pacificfreight-solution-outline.md` — a 1-2 page markdown document with: components, data flow (ASCII diagram), inputs/outputs, cost projection, week-by-week build plan, open questions.

When you finish, an engineer who has never met the customer can read the outline and start building on day 1 of week 2.

## 🧠 Mindset

The 1-pager is **for the customer**. The solution outline is **for the builder**. They have different audiences, different levels of detail, and different success criteria:

| | 1-pager | Solution outline |
|---|---|---|
| Audience | Customer, FDE's manager | Engineering team |
| Length | 1 page | 1-2 pages |
| Level of detail | What, not how | What *and* how, at component level |
| Success criterion | Customer signs | Engineer can start coding |
| Living document? | No — sign in week 1 | Yes — update weekly |
| Tone | Negotiating | Specifying |

The biggest trap with the solution outline is **over-specifying**. It is not a low-level design. It is a *map* — enough for an engineer to find their way, not enough that they never have to think. The right level of detail is "what are the components and how do they talk," not "here is the SQL schema for the shipment table."

> **FDE rule:** if the solution outline is longer than 2 pages, you are building, not outlining. Move the detail into the code, the README, or the runbook.

## 🛠️ Practice — the 6 sections

### 1. Components

> *What are the moving parts? One line each.*

**Why this section exists:** to break the build into parts an engineer can own. If you can't list the components, you can't divide the work.

**PacificFreight content:**

> **Five components:**
>
> 1. **Email reader** — takes a `.eml` file or stdin, returns the email body
> 2. **ID extractor** — finds the shipment ID (regex first, LLM fallback)
> 3. **Tracker lookup** — reads `shared/shipments.json`, returns the shipment
> 4. **Reply drafter** — calls `complete()` from `03-modern-ai-tooling.py`
> 5. **Output formatter** — prints to stdout (human) or JSON (pipe)
>
> **Out of scope for Phase 1:**
> - Gmail integration (read inbox)
> - Send integration (post to Gmail)
> - Multi-shipment handling
> - Auto-language detection
> - Refund / escalation logic

### 2. Data flow

> *How do the components talk? What is the input, what is the output?*

**Why this section exists:** so the engineer can see the *shape* of the system in 30 seconds. A picture is worth 1000 words of prose.

**PacificFreight content:**

```
┌─────────────┐    .eml / stdin    ┌──────────────┐
│  Operator   │ ─────────────────▶ │ email_reader │
│ (Mei, CS)   │                    └──────┬───────┘
└─────────────┘                           │ body: str
                                          ▼
                                ┌──────────────────┐
                                │  id_extractor    │
                                │  regex → LLM?    │
                                └────────┬─────────┘
                                         │ shipment_id: str | None
                                         ▼
                                ┌──────────────────┐
                                │ tracker_lookup   │
                                │ shipments.json   │
                                └────────┬─────────┘
                                         │ shipment: dict | None
                                         ▼
┌─────────────┐    stdout / JSON   ┌──────────────────┐
│  Operator   │ ◀───────────────── │ reply_drafter    │
│ reviews &   │                    │ system+user      │
│ copy-pastes │                    │ from 03-modern   │
└─────────────┘                    └──────────────────┘
```

**Input:** a `.eml` file path or stdin (one email at a time)
**Output:** the drafted reply, printed to stdout (default) or JSON (`--json` flag)
**Operator:** Mei, in her terminal, runs `pf-draft PF-1003` (or pipes an `.eml` file)

### 3. Inputs and outputs

> *For each component, what goes in, what comes out, and what is the contract?*

**Why this section exists:** to make the components *testable*. If you can't say what a component takes and returns, you can't write a test for it.

**PacificFreight content:**

> | Component | Input | Output | Failure mode |
> |---|---|---|---|
> | `email_reader` | path: str (file or `-`) | body: str | exit 1 if file not found |
> | `id_extractor` | body: str | shipment_id: str \| None | return None if no ID found (regex fails AND LLM call skipped in Phase 1) |
> | `tracker_lookup` | shipment_id: str | shipment: dict \| None | exit 2 if not in tracker |
> | `reply_drafter` | body: str, shipment: dict | draft: str | retry 3x with jitter on LLM error |
> | `output_formatter` | draft: str, format: str | prints to stdout | n/a |
>
> **Key Phase 1 decision:** `id_extractor` is **regex-only**. No LLM call. The 80% case (clean PF-XXXX in the email) is handled by regex. The 20% messy case returns None and the tool exits with a clear error — Mei pastes the ID by hand. This is cheaper than paying the LLM for every email.

### 4. Cost projection

> *What will this cost to run, per month, at the customer's expected volume?*

**Why this section exists:** so the customer can budget, and so the FDE can flag cost surprises before they happen. The cost projection is *operational* (what the customer pays the LLM vendor) — not engineering time.

**PacificFreight content:**

> **Volume assumption:** 150 emails/day × 22 business days = 3,300 drafts/month
>
> **Per-draft token estimate (from lesson 03 + lesson 04):**
> - System prompt: ~350 tokens (style guide + persona)
> - User prompt: ~200 tokens (email body + shipment status)
> - Output: ~150 tokens (the reply)
> - **Total: ~700 tokens/draft**
>
> **Cost at gpt-4o-mini pricing (from `03-modern-ai-tooling.py`):**
> - Input: 350 × $0.15/1M = $0.0000525
> - Output: 150 × $0.60/1M = $0.0000900
> - **Per draft: ~$0.00014**
> - **Monthly: 3,300 × $0.00014 = ~$0.47/month**
>
> **Customer ceiling:** $200/month. **Headroom: 425x.** Even at gpt-4o pricing (15x more expensive), we stay well under the ceiling.
>
> **What would change the projection:**
> - Switching from gpt-4o-mini to a larger model (10-30x cost increase)
> - Adding few-shot examples to the prompt (~2x input tokens, ~1.5x cost)
> - Adding JSON mode (output is longer if you ask for structured fields, ~1.2x cost)
> - Going from 150 emails/day to 1,500 emails/day (10x — still well under ceiling)

### 5. Week-by-week build plan

> *What gets built, in what order, by whom?*

**Why this section exists:** so the customer knows when to expect what, and so the FDE doesn't ship everything in week 1 and have nothing to show in week 4. The plan is also a forcing function for *not over-scoping* — if it doesn't fit in 4 weeks, it doesn't ship.

**PacificFreight content:**

> **Week 1 — Foundations (this week)**
> - Stakeholder map, discovery questions, theory of problem (lesson 01) ✓
> - 5-question framing (lesson 02) ✓
> - Prompting pattern chosen (lesson 03) ✓
> - 1-pager signed (lesson 04) ✓
> - Solution outline signed (this lesson) ✓
> - **Deliverable:** the 1-pager + this outline, signed by Sarah
>
> **Week 2 — Build the v0**
> - Mei gets read access to the PHP tracker (read-only API key, or a daily JSON dump)
> - FDE builds `01-python-tooling.py` (lookup CLI) — runs in Mei's terminal
> - FDE builds `03-modern-ai-tooling.py` (unified LLM client) — Mei's first prompt returns a draft
> - **Deliverable:** Mei can run a command and get a draft reply in 30 seconds
>
> **Week 3 — Pilot with one user**
> - Mei uses the tool on 10 real emails per day
> - FDE measures as-is ratio daily, fixes the worst failure modes
> - FDE builds the 20-email eval set, runs it every Friday
> - **Deliverable:** end-of-week as-is ratio number + the eval set
>
> **Week 4 — Go/no-go**
> - Mei uses the tool on all her emails
> - FDE writes the post-mortem (1 page): what worked, what didn't, what's next
> - Go/no-go meeting with Sarah
> - **Deliverable:** post-mortem + go/no-go decision + (if GO) Phase 2 scope
>
> **What is NOT in the 4-week plan:**
> - Auto-send (Phase 2)
> - Multi-shipment (Phase 2)
> - Auto-language detection (Phase 2)
> - Refund logic (out of scope, full stop)
> - Slack/Teams plugin (Phase 3+)

### 6. Open questions

> *What don't you know yet that you need to know before week 2?*

**Why this section exists:** to make the unknowns *explicit*. An open question is better than a wrong assumption. The list is also the FDE's week-1 to-do list.

**PacificFreight content:**

> 1. **Where does the PHP tracker data actually live?** Database? API? Daily CSV dump? (need to ask Daniel in IT — affects whether `tracker_lookup` is a read-from-JSON-file or a read-from-API call)
> 2. **What is the style guide?** Sarah said "in our voice" but hasn't shown us the guide. We drafted a placeholder in `shared/style-guide.md` and will revise in week 2 once Mei reviews it.
> 3. **What languages are in scope?** We've seen Vietnamese, English, and one Bahasa email. Do we need the drafter to reply in the customer's language, or always in English? (Phase 1: English only, in the customer's language if explicitly asked. Phase 2: auto-detect.)
> 4. **What is the PII policy?** Are we allowed to send customer shipment details to OpenAI? (Need a yes/no from Daniel. If no, we self-host a model in week 1 of Phase 2.)
> 5. **Who owns the eval set?** Mei is the user, but she shouldn't grade her own tool. Does Sarah nominate someone from ops to be the "rater"? (Default: Mei rates, FDE reviews weekly.)

---

## The full PacificFreight solution outline (assembled)

```markdown
# PacificFreight Co. — Solution Outline (v0.1)

**Status:** draft, week 1
**Owner:** [FDE name]
**Companion doc:** pacificfreight-1pager.md

## 1. Components
1. email_reader   — .eml/stdin → body
2. id_extractor   — regex → shipment_id
3. tracker_lookup — shipments.json → shipment
4. reply_drafter  — system+user prompt → draft
5. output_formatter — draft → stdout or JSON

## 2. Data flow
[ASCII diagram from above]

## 3. Inputs/outputs
[Table from above]

## 4. Cost projection
~3,300 drafts/month × $0.00014 = ~$0.47/month at gpt-4o-mini.
Customer ceiling: $200/month. Headroom: 425x.

## 5. Build plan
- Week 1: foundations (1-pager + this outline) ✓
- Week 2: v0 CLI, Mei runs it manually
- Week 3: pilot with Mei, daily as-is ratio
- Week 4: pilot with all CS, go/no-go

## 6. Open questions
1. Tracker data source (DB? API? CSV?)
2. Real style guide from Sarah
3. Language scope (English only Phase 1?)
4. PII policy for OpenAI
5. Who rates the drafts?
```

---

## 🏛️ FDE Lens — the technical reality underneath

The 6 sections of the solution outline map to the 4 technical lessons in this phase:

| Outline section | Lesson that teaches it |
|---|---|
| 1. Components | Lesson 04 (`04-first-ai-tool.py` is the 5 components) |
| 2. Data flow | Lesson 04 (the CLI wiring) |
| 3. Inputs/outputs | Lesson 01 (`Shipment` dataclass, `--json` flag) |
| 4. Cost projection | Lesson 03 (`PRICING` dict, `_log_usage`) |
| 5. Build plan | Lessons 02 + 03 (what gets built when) |
| 6. Open questions | Lesson 01 (the discovery questions that didn't get answered) |

The solution outline is the **bridge** between the consulting track (the 1-pager, lesson 04) and the technical track (the working CLI, lesson 04 of technical). When the FDE finishes both, the customer has a document they signed (1-pager) and an engineer has a document they can build from (this outline).

## 🌙 Reflect

Write 3-5 sentences:

1. The 1-pager says "the tool never sends" but the solution outline doesn't have a "no-send" component. Where in the outline is that constraint enforced? Is it in code, in process, or in trust?
2. The cost projection has 425x headroom. Should the FDE propose a cheaper model to give the headroom back to the customer? Why or why not?
3. The open questions list has 5 items. What happens to the engagement if question #1 (tracker data source) can't be answered in week 1?
4. The build plan says "Mei uses the tool on 10 real emails per day" in week 3. Why 10 and not all 150?
5. You are an FDE 2 weeks into a different engagement. The customer says "the 1-pager is done, just start building." What's missing if you skip the solution outline?

**What's next** — Phase 1 is complete. You have:
- A **first working AI tool** (`technical/04-first-ai-tool.py`)
- A **clear problem statement** (`consulting/04-framing-an-ai-use-case.md` — the 1-pager)
- An **initial solution outline** (`consulting/05-solution-outline.md`)

The next phase, **Phase 2 — Production**, takes the same scenario deeper: real Gmail integration, the full eval harness, a small FastAPI service, and the move from CLI to web UI. The path from here is `course/practice/` (intermediate engineering) and `course/hardcode/` (advanced engineering) — both already exist in the repo.
