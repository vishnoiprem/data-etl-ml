# Lesson 6 — AI-Augmented Workflow

> **Type:** Article · Module 1 · AI-Powered DE Foundations
> The end-to-end flow: spec → draft → review → test → ship. The shape of a typical day.

---

## The five-step loop

Every task follows the same loop, whether it's a one-line SQL fix or a multi-week migration:

```
   ┌─────────┐
   │  SPEC   │   what + why + constraints
   └────┬────┘
        ▼
   ┌─────────┐
   │  DRAFT  │   AI produces candidate
   └────┬────┘
        ▼
   ┌─────────┐
   │ REVIEW  │   you + AI cross-check
   └────┬────┘
        ▼
   ┌─────────┐
   │  TEST   │   automated + manual
   └────┬────┘
        ▼
   ┌─────────┐
   │  SHIP   │   deploy + observe
   └─────────┘
        │
        └──────────────► back to SPEC
```

The mistake is treating AI as a replacement for one of these steps. It's a **force multiplier** for the draft step, and an **accelerant** for the review step. The other steps are yours.

---

## Step 1 — SPEC

The spec is the **single highest-leverage artifact** in the entire loop. A good spec turns an AI from a slot machine into a junior engineer.

A spec for a DE task needs:
1. **Goal** — what user/business question are we answering, or what system are we building.
2. **Inputs** — which tables, which fields, what grain.
3. **Outputs** — what shape, what tests, what docs.
4. **Constraints** — performance, cost, style, dependencies.
5. **Done definition** — how do we know we're done.

```
SPEC: Add lifetime-revenue column to dim_user

GOAL
  Analytics needs `lifetime_revenue` on dim_user for churn modelling.

INPUTS
  fct_orders: user_id, gross_amount, status, created_at
  dim_user: user_id (PK)

OUTPUTS
  New column `lifetime_revenue` on dim_user.
  Type: NUMERIC(18,2). USD.
  Updated by daily incremental job.

CONSTRAINTS
  Only count orders with status IN ('PAID','FULFILLED').
  No double-counting on refunds — net revenue only.
  Backfill must complete in <30 min.
  No PII may leave the warehouse in any log.

DONE WHEN
  - Column exists on dim_user, backfilled.
  - dbt test: matches `SUM(gross_amount) FROM fct_orders`
    grouped by user_id.
  - Schema.yml updated with description and tests.
  - Runbook updated.
```

That spec is now usable by **any** engineer (human or AI) with the same context.

---

## Step 2 — DRAFT

Pass the spec to the AI (Cursor, Claude Code, Aider, etc.) with the appropriate prompt template (Lesson 4).

The AI's job: produce the SQL, the dbt model, the dbt schema.yml, the runbook update.

Your job: **don't touch the draft yet**. Save it to a branch. Move to review.

---

## Step 3 — REVIEW

You review the AI draft with the same rigor you'd apply to a junior's PR. Three passes:

### Pass 1 — Logic
Read every line. Does it match the spec? Are the joins right? Are the filters right? Are NULLs handled?

### Pass 2 — Style
Does it match the `.cursorrules`? Naming conventions? Macro usage? CTE style?

### Pass 3 — Verification
Does the AI's "verification block" actually verify what you need? If it's weak, rewrite it. Don't ship a draft whose verification you don't trust.

AI-assisted review (Cursor, Copilot PR review) is good at the first pass for boilerplate. You are the senior reviewer for the **business logic**.

---

## Step 4 — TEST

Every AI-generated artifact gets:
1. **Unit tests** — dbt tests, pytest, whatever your stack uses.
2. **Integration test** — run on real data in dev, compare to expected counts.
3. **Manual test** — sample 10 rows by hand.

The AI can write the tests. You confirm they actually fail when they should.

```sql
-- Intentional break: confirm the not_null test fires
UPDATE fct_orders SET user_id = NULL WHERE order_id = 'test';
```

---

## Step 5 — SHIP

Deploy, monitor, sleep.

The new habit: **after every AI-assisted deploy, check the dashboards for 24 hours.** Anything anomalous gets a postmortem, not a shrug. AI-assisted work is not exempt from the same scrutiny as human-written work — in fact, it deserves **more** scrutiny for the first 30 days you're using it.

---

## The loop in practice — 90-minute example

```
00:00 — Open ticket "Add lifetime_revenue to dim_user"
00:05 — Write the spec (you, 5 min)
00:10 — Prompt Cursor with spec → get SQL + schema.yml + runbook draft
        (AI, ~30 sec, you skim)
00:15 — Review pass 1: logic. You find one missing filter
        (refunds not excluded). Edit. 5 min.
00:20 — Review pass 2: style. Matches conventions. Pass. 2 min.
00:25 — Review pass 3: verification. AI's row-count check is wrong
        (off by refunds). You rewrite it. 3 min.
00:30 — Run dbt run in dev. 1 min.
00:32 — Run dbt test. 1 test fails — null user_id (10 rows in
        fct_orders). You log a ticket for upstream fix, add an
        `is_valid_user` filter to the model. 8 min.
00:40 — Re-run. Tests pass. 1 min.
00:45 — Sample 10 rows by hand. Looks good. 5 min.
00:50 — Open PR. Use AI to draft the PR description. 2 min.
00:55 — CI green. Reviewer approves.
01:00 — Merge. CI deploys. Backfill job scheduled.
01:05 — Verify dashboard. All numbers tie. 5 min.
01:10 — Close ticket. Update team dashboard.

Total: 70 minutes for a feature that would have taken 3+ hours
without AI, with higher test coverage.
```

---

## Common workflow anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Skip the spec, prompt directly | AI guesses the missing context, you re-do work | Always write the spec first, even 5 lines |
| Trust the AI's first draft | It looks right, ships wrong | Always run the verification block you wrote |
| Skip code review because "AI wrote it" | Plausible-but-wrong propagates | AI is a junior. You are the senior. Always. |
| Paste the AI output straight into Slack | Looks authoritative, may be wrong | Run it first, then share |
| Use AI for the spec itself | Spec is where your judgment lives | AI can offer a checklist; the spec is yours |

---

## What Comes Next

> Lesson 7 — **Ethics & Risks** — the things you cannot delegate to AI: PII handling, hallucination, bias, IP, model-supply risk, and the ethics of automating decisions.
