---
name: Hard rules for outbound email
description: Non-negotiable rules the agent must follow before any email is drafted or sent — draft-first, no guessed addresses, guard integrity
type: feedback
---

1. Never guess an email address. Only verified business emails or published company contacts.
2. Never send without explicit user approval of the exact draft. Stay in draft mode by default.
3. Never represent a draft as sent, and never quietly retry a send whose outcome is unknown
   (check the sent folder / `send_log` first — a blind retry double-contacts a prospect).
4. Never bypass the guards: no `--no-lock` outside interactive debugging, no editing the bounce
   deny list to unblock a send, no raising daily/hourly caps to hit a quota.
5. Job postings are signals, not confirmed demand — "saw your posting for X", never "you need
   X engineers".
6. No invented facts. Every company claim traces to a source URL and is cross-checked.
7. Opt-outs are permanent. The one-click unsubscribe footer stays in every email.
8. Under 120 words, one specific dated signal, one Avilex offer (not a menu), one call to action.

**Why:** These rules protect deliverability (Gmail throttles hard on cold email), legal standing
(anti-spam and consent), and Avilex's brand. The pipeline's guard rails exist because real
damage happened — a missing unique constraint caused duplicate lead inserts, and Gmail
throttling motivated the pre-send guards.

**How to apply:** Applies to every outreach action, in every mode. When a rule blocks progress,
say so and propose a compliant alternative — do not find a technical workaround.
