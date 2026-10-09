# Lesson 03 — Communicating Scope, Choices, and Trade-offs (ADRs)

> **The decisions that would otherwise live in someone's head.** 35 minutes. No new code.

By the end of this lesson you can write an **ADR** (Architecture Decision Record) — a 1-page document that records *one* design decision, *why* it was made, and *what the alternatives were*. You have a template, three worked PacificFreight examples, and a checklist for when to write one.

The ADRs are the artifact that **survives the engagement**. The discovery deck gets archived, the PRD gets re-written, the design doc gets re-versioned — but the ADRs stay. When a new FDE joins the project 6 months later, the ADRs are how they learn why the system is the way it is.

---

## 🎯 Outcome

You produce **three artifacts** (one per worked example):

- `decisions/0001-choose-fastapi.md` — why FastAPI over Flask
- `decisions/0002-mock-vector-store.md` — why a mock vector store over Pinecone for Phase 2
- `decisions/0003-eval-regression-threshold.md` — why 0.05 (not 0.10, not 0.02) for the regression threshold

When you finish, you can write an ADR in 15 minutes for any new design decision, and a reviewer can tell within 30 seconds whether the reasoning is sound.

## 🧠 Mindset

An ADR is **one decision, one page, written once**. It is not a design doc (that's a 5-page system view). It is not a PR description (that's a 200-word "what changed"). It is the **artifact that records the "why"** so the next FDE doesn't have to guess.

The four properties of a good ADR:

1. **Scoped** — one decision per ADR. Not "the design," not "the architecture." One decision: FastAPI vs Flask, mock vs Pinecone, 0.05 vs 0.10.
2. **Atomic** — written at the moment the decision is made, not in retrospect. Retrospective ADRs are usually rationalizations.
3. **Immutable** — once written, the ADR is **not edited**. If the decision changes, write a NEW ADR that supersedes the old one. The old ADR is kept for the historical record.
4. **Lightweight** — 1 page, no diagrams required (a 5-line ASCII is fine), no review meeting (the team reads it async).

The traps:

1. **The retrospective trap.** The FDE writes the ADR 6 weeks after making the decision, when they've already forgotten the alternatives. The result is a rationalization, not a record. **Write the ADR at the moment of decision.**
2. **The "everything is an ADR" trap.** The FDE writes 40 ADRs in the first week, one for every line of code. The result is a wiki nobody reads. **Only ADRs for non-obvious choices that the next FDE would second-guess.**
3. **The "no ADR" trap.** The FDE makes a choice in a Slack thread and never writes it down. 6 months later, the next FDE reverses it. **If you can't write the ADR, the decision wasn't real.**

> **FDE rule:** if a choice would generate pushback in code review, it's an ADR. If nobody would push back, it's not.

## 🛠️ Practice — the ADR template

The standard template (Michael Nygard's, adapted):

```markdown
# ADR-NNNN: <Title>

- **Status:** Proposed | Accepted | Superseded by ADR-XXXX
- **Date:** YYYY-MM-DD
- **Authors:** <name>

## Context
<2-3 sentences: what is the situation? what forces are at play?>

## Decision
<1-2 sentences: what did we decide?>

## Consequences
<2-4 bullets: what becomes easier? what becomes harder?>

## Alternatives considered
<2-3 options, each with 1 sentence on why we didn't pick it.>
```

That's it. **One page, four sections.** Most ADRs are 30-50 lines.

---

## ADR-0001 — FastAPI over Flask

- **Status:** Accepted
- **Date:** 2026-10-01
- **Authors:** [FDE name]

### Context

The PacificFreight Phase 2 service needs an HTTP layer. The team is familiar with both Flask (Phase 1 used a CLI, but the org has a Flask app elsewhere) and FastAPI (none of the team has shipped to production with it). The service will grow into a multi-endpoint, async-friendly LLM application in Phase 3.

### Decision

We will use **FastAPI** for the HTTP layer.

### Consequences

- (+) OpenAPI spec generated automatically — the customer can browse the API at `/docs` during the demo
- (+) Pydantic validation means bad requests return 422, not 500
- (+) Async-native — Phase 3's streaming responses don't require a rewrite
- (-) The team needs to learn Pydantic conventions (~half a day)
- (-) FastAPI's `Depends` injection is overkill for Phase 2 (we use module-level state); Phase 3 will need to refactor

### Alternatives considered

- **Flask** — familiar, but no built-in async, no built-in OpenAPI, no built-in Pydantic. Would need 3 extra libraries to match FastAPI's out-of-the-box story.
- **Django** — too heavy for a single-purpose service. Better for multi-app monorepos.

---

## ADR-0002 — Mock vector store over Pinecone for Phase 2

- **Status:** Accepted
- **Date:** 2026-10-01
- **Authors:** [FDE name]

### Context

The drafter needs to retrieve the right policy chunk + the right shipment for each email. Options: (a) a real vector DB (Pinecone, Qdrant, pgvector) with real embeddings, or (b) an in-process mock with token-overlap scoring. The corpus is 7 policy chunks + 15 shipments today.

### Decision

We will use an **in-process mock** for Phase 2, and migrate to a real vector DB in Phase 3.

### Consequences

- (+) Zero ops — no API key, no rate limit, no cost, no "is it up?"
- (+) Deterministic — the same query returns the same chunks every time. Customer demos are reproducible; tests are reliable.
- (+) Ships in 1 day (the mock is ~100 lines of Python)
- (+) Same interface as a real vector DB (`retrieve(query, k) -> list[Chunk]`) — Phase 3 migration is a 1-function change in `service/rag.py`
- (-) The mock uses token overlap, not semantic similarity. Phrases like "stuck" vs "held" might not match well.
- (-) At 10K+ chunks the mock is too slow (O(N) per query) and the recall degrades (token overlap misses paraphrases).

### Migration trigger

We will replace the mock when **any** of these become true:
- Policy docs > 50 chunks (the mock's F1 score drops below 0.5 on the eval set)
- Tracker > 10K shipments (recall is unacceptable for the 80% as-is target)
- Customer asks "why did the drafter retrieve this chunk?" (no explainability in a mock)

### Alternatives considered

- **Pinecone** — free tier (100K vectors), well-documented, easy to swap in. But: another vendor, another API key, another thing to be down. Worth it in Phase 3, not in Phase 2.
- **pgvector** — would require a Postgres instance. Daniel doesn't have one running, and standing one up is a 2-week side quest.
- **In-memory FAISS** — fast, but the API is different from a real vector DB, so the Phase 3 migration isn't a 1-function change.

---

## ADR-0003 — Eval regression threshold = 0.05

- **Status:** Accepted
- **Date:** 2026-10-01
- **Authors:** [FDE name]

### Context

The CI pipeline runs the 30-row eval set on every PR. If any of the 4 metrics (faithfulness, answer relevance, context precision, context recall) drops by more than a threshold, the deploy is blocked. Too loose and we ship regressions; too tight and CI breaks on noise.

### Decision

We will set the **regression threshold to 0.05** (5 percentage points) for Phase 2.

### Consequences

- (+) A 5pp drop is large enough to be a real regression, not noise (the eval set's row-to-row variance is ~0.02 on context_precision)
- (+) Tight enough to catch the regressions that matter (a 10pp drop on faithfulness = the model is making stuff up)
- (-) False positives: ~1 in 20 PRs will trip on a real but unimportant change. We'll add a "waiver" comment in the PR to bypass.
- (-) Doesn't catch all regressions — a prompt change that improves 2 rows and breaks 1 row by 6pp will not trip. Phase 3 swaps in per-row significance testing.

### Alternatives considered

- **0.10 (loose)** — too loose. A 10pp drop means we shipped 1 in 4 drafts that got worse. Customer notices.
- **0.02 (tight)** — too tight. The eval set's natural variance is 0.02-0.03. CI breaks on noise; team stops trusting the check.
- **Per-row significance test (statistical)** — the right answer in Phase 3 when the eval set is bigger (100+ rows). For Phase 2's 30 rows, the per-row test is underpowered.

### When to revisit

Phase 3, when the eval set grows to 100+ rows. The 0.05 number will probably tighten to 0.02 once we have the statistical power to back it up.

---

## How to write an ADR in 15 minutes

1. **Pick the title.** "ADR-NNNN: <verb> <thing>". Examples: "0001: choose FastAPI", "0002: mock vector store over Pinecone", "0003: regression threshold = 0.05". The verb makes the decision searchable.

2. **Write Context (5 min).** Two or three sentences: what's the situation? What forces are at play? *No preamble, no marketing.* If you find yourself writing a 4th sentence, you're writing a blog post, not an ADR.

3. **Write Decision (2 min).** One or two sentences: what did you decide? Use the active voice. "We will use X" not "X was chosen."

4. **Write Consequences (5 min).** Two to four bullets. Start each with `(+)`, `(-)`, or `(neutral)`. The (+) and (-) are the trade-offs. The (neutral) bullets are "this doesn't change much" — drop them if you have nothing to say.

5. **Write Alternatives (3 min).** Two or three options you considered. For each, one sentence on why you didn't pick it. If you can't write the "why we didn't pick it" sentence, you didn't seriously consider the alternative — go back and consider it.

6. **Set Status.** `Proposed` while the team is reviewing, `Accepted` after the first reviewer agrees, `Superseded by ADR-XXXX` when a later ADR reverses it. Don't agonize over the wording.

> **FDE tip:** the *easiest* way to write an ADR is to write it **before** you write the code. The act of writing forces you to think about the alternatives. If you can't write the Alternatives section, you don't actually know why you chose this option.

## When to write an ADR (the checklist)

Write one when:
- The choice would generate pushback in code review ("why not Flask?")
- The choice is hard to reverse later (migrating off FastAPI is 1 week; migrating off Pinecone is 4 weeks)
- The choice has a non-obvious trade-off the next FDE would second-guess
- The choice is being made across multiple teams (so the ADR is the reference for "we already decided this")

Don't write one when:
- The choice is obvious from the code (e.g., "we use Python 3.11")
- The choice is reversible in < 1 hour (e.g., "we use `pathlib` not `os.path`")
- The choice is a personal preference (e.g., "I prefer spaces over tabs")

For the PacificFreight Phase 2 service, the 3 ADRs above are the *only* ones worth writing. Everything else is in the code.

## 🏛️ FDE Lens — the technical reality underneath

The ADRs are how the **decisions** survive the **turnover**. The next FDE who joins PacificFreight in 6 months will:

1. Read the 1-pager (what we're building)
2. Read the discovery deck (what we heard)
3. Read the design doc (how it's built)
4. Read the ADRs (why each choice was made)

If the ADRs don't exist, the next FDE re-debates every choice. "Should we use Flask?" is a 2-hour meeting. "Why FastAPI? The ADR says async-native + OpenAPI + Pydantic. OK, moving on."

The cost of an ADR is 15 minutes. The cost of NOT writing one is 2 hours of re-debate, every time someone new joins.

## 🌙 Reflect

Write 3-5 sentences:

1. ADR-0001 is "FastAPI over Flask." A new FDE joins and says "I prefer Flask, let's migrate." What does the ADR let you say in 30 seconds?
2. ADR-0002 says "migrate to a real vector DB when policy > 50 chunks." Today the policy is 7 chunks. Why write the migration trigger in the ADR now, not when the trigger fires?
3. ADR-0003 says "threshold = 0.05." A new FDE says "I prefer 0.02, it's tighter." What do you say?
4. The ADR template has 4 sections. A new FDE writes a 6-section ADR with "Background" and "Open Questions" and "References." What do you push back on?
5. The customer asks "why did you pick FastAPI?" You point at the ADR. The customer says "but I want Flask." What do you say?

**What's next** — Phase 2 is complete. You have the **deployable AI system** (the FastAPI service), the **architecture view** (the solution-design doc), and the **record of key design decisions** (the 3 ADRs). The next phase, **Phase 3 — Production**, takes the same service deeper: real auth, rate limiting, observability with LangSmith, streaming responses, a hosted vector DB, and a production rollout runbook. The path from here: **`course/hardcode/level-6-production-systems/`** (production patterns) and **`course/hardcode/level-8-evaluation-testing/`** (the 1000-line eval harnesses).
