---
name: Outbound sender identity is Alex Morgan <alex.morgan@avilx.com>, sent via Outlook SMTP AUTH
description: From header, body signature and Reply-To all derive from AVILX_FROM_*; Gmail strips the address so the transport is Microsoft 365 OAuth2, gated on a licensed mailbox and an SPF swap
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

## The fix is Outlook SMTP AUTH — and it is NOT live yet

`avilx.com` is **already a Microsoft 365 tenant**, so no third-party relay is
needed:

- MX → `avilx-com.mail.protection.outlook.com`
- DKIM selectors 1 and 2 are live
- DMARC → `v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:dmarc_rua@onsecureserver.net;`
- Autodiscover CNAME → `autodiscover.outlook.com`
- Tenant → `NETORGFT20933709.onmicrosoft.com`

The code was built on 2026-11-24:

- `lib/m365_auth.py` — device-code flow, refresh-token cache in
  `state/m365_token.json` (mode 0600), and `build_xoauth2_blob()` which produces
  the byte-exact XOAUTH2 SASL initial response
  (`base64("user=" + mailbox + \x01 + "auth=Bearer " + token + \x01\x01)` — the
  separator must be the byte `0x01`, not the literal `^A`).
- `lib/smtp_client.py` — the single transport used by both `autopilot.py` and
  `bin/send_followups.py` (they used to have divergent `SMTP_*` vs `AVILX_SMTP_*`
  namespaces and only one had a retry wrapper). `SMTP_AUTH=gmail|oauth2` selects
  the mechanism.
- `SETUP_OUTLOOK_SMTP.md` — the full setup guide.

**`.env` still has `SMTP_AUTH=gmail`.** Three things must all be true before it
can be flipped to `oauth2`:

1. `alex.morgan@avilx.com` must be a **licensed** Exchange Online mailbox.
   Outlook SMTP AUTH may only send as the authenticated mailbox or one it has
   Send As permission for. An alias is not enough.
2. **SPF must be replaced.** It is currently
   `v=spf1 include:secureserver.net -all` — GoDaddy parking, which does not
   authorize Microsoft 365, and `-all` makes it a hard fail for Outlook sends.
   The replacement is `v=spf1 include:spf.protection.outlook.com -all`. It must
   be an *edit* of the existing TXT record, not a second record — two records
   means receivers fail SPF entirely.
3. The device-code login must have run: `python -m lib.m365_auth --device-code`
   (needs `SMTP.Send` + `offline_access` as **application** permissions with
   admin consent).

**How to apply:** Never tell the user the avilx.com From address is live while
`SMTP_AUTH=gmail` is set. If they ask "is it sending as alex.morgan@avilx.com?",
the answer is: the name yes, the address no — until all three gates clear and a
test send's delivered headers show `From: Alex Morgan <alex.morgan@avilx.com>`
with `spf=pass` / `dkim=pass` / `dmarc=pass`.

Do not claim a send succeeded without a `send_log` row. Nothing has ever been sent
as of 2026-11-23 (`send_log` is empty, `DRY_RUN=true` is set). The three self-test
emails sent during verification were deleted from the inbox.

## Bounce scanning is still on Gmail IMAP

`check_bounces.py` reads `GMAIL_ADDRESS` + `GMAIL_APP_PASSWORD` and hardcodes
`imap.gmail.com:993`. The `AVILX_IMAP_*` vars in `.env.example` are dead. Moving
bounce scanning to Microsoft 365 IMAP XOAUTH2 is optional follow-up work and was
deliberately left out of the SMTP AUTH change — it is a separate credential
namespace and inbound scanning does not block sending.
