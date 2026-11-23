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

The one-click unsubscribe link stays on `hello@avilx.com` regardless of sender
(`AVILX_UNSUB_EMAIL` overrides it). It must not point at a person's inbox — an
unsubscribe request that lands in one person's mailbox is not monitored.

**Why:** The user asked for the sender to be `alex.morgan@avilx.com` (2026-11-23).
Before this the pipeline sent as "Prem Vishnoi" with the Gmail login
(`premvishnoisoft@gmail.com`) as the From address, and the body sign-off disagreed
with the From header in `cover_letter.py` vs `autopilot.py`.

**How to apply:** Never hardcode a sender name or address in a new module — import
`SIGNER` / `SIGNER_EMAIL` from `cover_letter`, or read the `AVILX_FROM_*` vars.
If the From header and the body signature ever disagree, that is a bug, not a
config choice. The legacy `YOUR_NAME` / `YOUR_EMAIL` aliases in `.env` are wired
to `AVILX_FROM_NAME` / `AVILX_FROM_EMAIL` so old scripts cannot drift back to the
founder record.

## Gmail strips the avilx.com address from the visible From header

Verified empirically on 2026-11-23 by sending three test messages to the account
itself and reading back the delivered headers:

- SMTP accepts `MAIL FROM:<alex.morgan@avilx.com>` → `250 2.1.0 OK`
- The delivered `From:` is **`Alex Morgan <premvishnoisoft@gmail.com>`**
- The original survives only in `X-Google-Original-From:`
- `Reply-To: alex.morgan@avilx.com` passes through untouched

So the display name "Alex Morgan" reaches the recipient, but the address is the
Gmail one. The pipeline currently sends from `premvishnoisoft@gmail.com` wearing
the Alex Morgan name.

To genuinely send as `alex.morgan@avilx.com` a provider with the avilx.com domain
verified is required — `SETUP_MAILGUN.md` documents that path.

**How to apply:** Never tell the user the avilx.com From address is live while the
Gmail SMTP login is in use. If they ask "is it sending as alex.morgan@avilx.com?",
the answer is: the name yes, the address no — until a provider is configured.

Do not claim a send succeeded without a `send_log` row. Nothing has ever been sent
as of 2026-11-23 (`send_log` is empty, `DRY_RUN=true` is set). The three self-test
emails sent during verification were deleted from the inbox.
