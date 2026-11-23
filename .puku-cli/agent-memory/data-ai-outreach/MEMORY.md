# Agent Memory — data-ai-outreach

- [Avilex offer and positioning](project_avilex_offer.md) — what Avilex sells; `pitch_pod` vs `apply_personal` must never be mixed.
- [Canonical pipeline location and the stale duplicate](project_pipeline_layout.md) — canonical is `projects/leads-pipeline/draft-cron/`; repo-root copy is stale and untracked.
- [Pipeline commands and guard behaviour](reference_pipeline_commands.md) — exact CLI entry points; what `can_send_to()` and the cron lock enforce.
- [Local Postgres setup for the leads pipeline](reference_local_postgres.md) — starting Postgres on :5433 without Docker; the `LC_ALL` requirement.
- [Cover letter word budget and template fixes](project_cover_letter_word_budget.md) — the 120-word limit, template bugs fixed, and how to render a draft.
- [Outbound sender identity](project_sender_identity.md) — sends as Alex Morgan <alex.morgan@avilx.com>; env-driven, and the Gmail aliasing constraint.
- [Hard rules for outbound email](feedback_hard_rules.md) — draft-first, no guessed addresses, never bypass the guards.
