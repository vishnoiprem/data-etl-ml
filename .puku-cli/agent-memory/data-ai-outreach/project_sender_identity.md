---
name: Outbound sender identity is Alex Morgan <alex.morgan@avilx.com>
description: From header, body signature and Reply-To all derive from AVILX_FROM_NAME/AVILX_FROM_EMAIL; Gmail login constraint on whether the avilx.com address can actually send
type: project
---

Outbound email sends as **Alex Morgan** `<alex.morgan@avilx.com>`. The From header
(`autopilot.py`), the body signature (`cover_letter.py`), the follow-up sign-off
(`bin/send_followups.py`), the HTML signature block, and `Reply-To` all derive from
`AVILX_FROM_NAME` / `AVILX_FROM_EMAIL` in the pipeline's `.env`. `AVILX_REPLY_TO`
overrides where replies land; `AVILX_ENVELOPE_FROM` overrides MAIL FROM and is only
needed when a provider uses its own bounce domain.

The one-click unsubscribe link stays on `hello@avilx.com` regardless of sender.

**Why:** The user asked for the sender to be `alex.morgan@avilx.com` (2026-11-23).
Before this the pipeline sent as "Prem Vishnoi" with the Gmail login
(`premvishnoisoft@gmail.com`) as the From address, and the body sign-off disagreed
with the From header in `cover_letter.py` vs `autopilot.py`.

**How to apply:** Never hardcode a sender name or address in a new module — import
`SIGNER` / `SIGNER_EMAIL` from `cover_letter`, or read the `AVILX_FROM_*` vars.
If the From header and the body signature ever disagree, that is a bug, not a
config choice.

## The Gmail constraint

Gmail only accepts a From address the authenticated account owns or has aliased.
The SMTP login is `premvishnoisoft@gmail.com`, so `alex.morgan@avilx.com` only
sends if that address is aliased on the Gmail account. Otherwise a real sending
provider is needed — `SETUP_MAILGUN.md` documents that path.

Do not claim a send succeeded without a `send_log` row. Nothing has ever been sent
as of 2026-11-23 (`send_log` is empty, `DRY_RUN=true` is set).
