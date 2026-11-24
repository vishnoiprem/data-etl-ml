# Outlook SMTP AUTH Setup — send as `alex.morgan@avilx.com`

> **Why not Gmail?** Gmail accepts `MAIL FROM:<alex.morgan@avilx.com>` with
> `250 2.1.0 OK` but **rewrites the delivered `From:` header** to the Gmail
> login address. The original survives only in `X-Google-Original-From:`.
> Verified empirically on 2026-11-23 with three test sends.
>
> `avilx.com` is already a Microsoft 365 tenant (MX → `avilx-com.mail.protection.outlook.com`,
> DKIM selectors 1 and 2 live, DMARC `p=quarantine`). So Outlook **SMTP AUTH**
> — OAuth2 with the XOAUTH2 SASL mechanism — is the right path. No new
> provider, no third-party relay, no deliverability surcharge.

**Time:** ~20 minutes. **Cost:** $0 (the mailbox license is the only cost, and
you already have the tenant).

---

## Before you start — two hard prerequisites

Both must be true before a single real send, or mail will fail or land in junk.

### 1. `alex.morgan@avilx.com` must be a licensed mailbox

Outlook SMTP AUTH may only send as **the authenticated mailbox**, or an address
that mailbox has explicit **Send As** permission for. An alias is not enough.

Check in the Microsoft 365 admin center:

> <https://admin.microsoft.com> → **Users** → **All users** → click
> `alex.morgan@avilx.com` → **Licenses** tab → check that **Exchange Online
> (Plan 2)** is assigned.

If the box is unchecked, assign it. A license that isn't assigned gives you a
user object with no mailbox, and every send fails with:

```
550 5.7.1 Sender not authorized for alex.morgan@avilx.com
```

### 2. The SPF record must be replaced — this is the important one

The current SPF record at `avilx.com` is:

```
v=spf1 include:secureserver.net -all
```

`secureserver.net` is **GoDaddy domain parking**. It does not authorize
Microsoft 365, and the trailing `-all` makes the record a hard fail for any
sender it doesn't cover. Outlook sends would fail SPF at every receiver and
land straight in junk.

---

## Step 1 — Register the Entra app

1. Go to <https://portal.azure.com>
2. Left rail → **Microsoft Entra ID** → **App registrations** → **New registration**
3. Fill in:
   - **Name:** `Avilx Outbound Mail`
   - **Supported account types:** *Accounts in this organizational directory only*
     (single tenant — you don't need multi-tenant for your own domain)
   - Leave the redirect URI blank (the device-code flow needs none)
4. Click **Register**
5. On the Overview page, copy two values:
   - **Application (client) ID** → `AVILX_M365_CLIENT_ID`
   - **Directory (tenant) ID** → `AVILX_M365_TENANT_ID`
     (for this tenant it is `NETORGFT20933709.onmicrosoft.com`)

## Step 2 — API permissions + admin consent

1. Still on the app → **API permissions** → **Add a permission**
2. Choose **Microsoft Graph** → **Application permissions**
3. Search for and add **both**:
   - `SMTP.Send`
   - `offline_access`
     (`offline_access` is what produces a **refresh token**. Without it the
     cached token dies after ~1 hour and the pipeline can no longer send
     unattended — which, in practice, means it stops overnight.)
4. Click **Grant admin consent** on each permission (the blue "Grant admin
   consent" button at the top of the list).

   Admin consent is **required**. A self-granted delegated `SMTP.Send` does
   not work for SMTP AUTH, and the token request will fail with
   `invalid_scope` or `unauthorized_client`.

5. Click **Grant admin consent** again and confirm the status shows
   **Granted** for both permissions.

## Step 3 — Client secret

1. Left rail → **Certificates & secrets** → **New client secret**
2. **Name:** `avilx-outbound` · **Expires:** 6 months (or 24 months)
3. Click **Create** and **copy the secret value immediately** — Microsoft only
   shows it once. → `AVILX_M365_CLIENT_SECRET`

> Set a calendar reminder for the expiry date. When it lapses, sends start
> failing with `invalid_client`; the refresh path clears the dead cache and
> tells you to re-run the device-code login.

## Step 4 — DNS: replace the SPF record

This is the record to paste. In your DNS provider (GoDaddy, Cloudflare,
whatever hosts `avilx.com`):

**Type:** TXT
**Name/Host:** `@`
**Value:**

```
v=spf1 include:spf.protection.outlook.com -all
```

Notes on the edit:

- **You must *edit* the existing TXT record, not add a second one.** SPF
  allows only one record per domain. Two records means receivers fail SPF
  entirely with "multiple SPF records" — worse than the current state.
- **Remove `include:secureserver.net`.** It authorized GoDaddy parking, which
  the pipeline does not use, and it consumed one of the 10 DNS lookups SPF
  allows. The new record uses exactly one lookup, so the limit is not a
  concern.
- **Do not flatten Microsoft.** `spf.protection.outlook.com` resolves to
  Microsoft's dynamically-managed IP ranges; hardcoding them breaks the
  moment they change.
- **DKIM needs no change.** Selectors `1` and `2` are already CNAME'd to
  Microsoft and Outlook will sign with them automatically.
- **DMARC needs no change.** `v=DMARC1; p=quarantine; adkim=r; aspf=r` already
  aligns with `avilx.com` and Outlook's DKIM signature.

Verify the change (DNS propagation can take up to an hour):

```bash
dig +short TXT avilx.com
# expect: "v=spf1 include:spf.protection.outlook.com -all"
```

## Step 5 — Configure `.env`

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/projects/leads-pipeline/draft-cron
```

Add or uncomment:

```bash
# ── Outbound transport ────────────────────────────────────────────────
SMTP_AUTH=oauth2
AVILX_SMTP_HOST=smtp-mail.outlook.com
AVILX_SMTP_PORT=587
AVILX_SMTP_USE_SSL=false

# ── Microsoft 365 / Outlook SMTP AUTH ──────────────────────────────────
AVILX_M365_CLIENT_ID=<paste from Step 1>
AVILX_M365_CLIENT_SECRET=<paste from Step 3>
AVILX_M365_TENANT_ID=NETORGFT20933709.onmicrosoft.com
AVILX_M365_SENDER=alex.morgan@avilx.com
AVILX_M365_TOKEN_PATH=./state/m365_token.json
```

Leave `AVILX_FROM_NAME=Alex Morgan` and `AVILX_FROM_EMAIL=alex.morgan@avilx.com`
exactly as they are — those are the visible sender identity, and they stay the
same across both auth modes.

## Step 6 — Get the OAuth token

```bash
.venv/bin/python -m lib.m365_auth --device-code
```

You get a URL and a code:

```
  Open this URL and sign in as the sending mailbox:

      https://microsoft.com/devicelogin

  Enter the code: ABC-DEF123

  Waiting for consent (expires in 15 min)...
```

1. Open the URL in a browser
2. Sign in as **`alex.morgan@avilx.com`**
3. Enter the code
4. Accept the consent prompt

The token is written to `state/m365_token.json` with mode `0600`.

Check it:

```bash
.venv/bin/python -m lib.m365_auth --status
# tenant: NETORGFT20933709.onmicrosoft.com
# client: <your client id>
# sender: alex.morgan@avilx.com
# cache:  .../state/m365_token.json
# token cached, valid for another 59 min
```

> `state/m365_token.json` contains a live bearer token. It is gitignored —
> confirm it never shows up in `git status`.

## Step 7 — Verify with a test send

Send one message to yourself and read the delivered headers.

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/projects/leads-pipeline/draft-cron
.venv/bin/python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv(Path(".env"))
from email.mime.text import MIMEText
import lib.smtp_client as sc

to = "premvishnoisoft@gmail.com"   # your own inbox
msg = MIMEText("Outlook SMTP AUTH test — ignore.\n")
msg["From"] = "Alex Morgan <alex.morgan@avilx.com>"
msg["To"] = to
msg["Subject"] = "Avilx SMTP AUTH test"

cfg = sc.smtp_config()
print("sending via:", sc.describe(cfg))
sc.send_with_retry(msg, envelope_from="alex.morgan@avilx.com", envelope_to=to, cfg=cfg)
print("sent")
PY
```

Then check the received headers. **All three of these must hold:**

| Header | Expected |
|---|---|
| `From:` | `Alex Morgan <alex.morgan@avilx.com>` — **not** the Gmail address |
| `Authentication-Results:` | `spf=pass` … `dkim=pass` … `dmarc=pass` |
| `Return-Path:` | `alex.morgan@avilx.com` |

If `From:` still shows the Gmail address, `SMTP_AUTH` didn't switch — check
`.env` was loaded (the script above calls `load_dotenv` explicitly).

If SPF fails, the DNS record hasn't propagated yet. Wait and re-check with
`dig +short TXT avilx.com`.

If you get `550 5.7.1 Sender not authorized`, the mailbox isn't licensed (see
the prerequisite at the top) or `AVILX_M365_SENDER` doesn't match the mailbox
you signed in with.

## Step 8 — Run the pipeline

```bash
# preview only — renders drafts, sends nothing
.venv/bin/python autopilot.py --email --dry

# real send (still subject to the pipeline's own approval rules)
.venv/bin/python autopilot.py --email --mode pitch_pod --max-emails 1
```

Confirm a row landed in `send_log`:

```bash
.venv/bin/python db_cli.py --help   # or: SELECT * FROM send_log ORDER BY id DESC LIMIT 5;
```

---

## Rollback

Set `SMTP_AUTH=gmail` in `.env`. The Gmail path is unchanged code — the
pipeline keeps working, mail just arrives from `premvishnoisoft@gmail.com`.

If you'd rather not use your own Microsoft 365 mailbox at all,
`SETUP_MAILGUN.md` documents the third-party relay path (costs money, needs
its own domain verification).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `535` on AUTH | Bad token, revoked consent, or `SMTP.Send` not admin-consented | Re-run `--device-code`; check the permission status in Step 2 |
| `invalid_client` | Client secret expired or wrong | Rotate the secret (Step 3), update `.env`, re-run `--device-code` |
| `invalid_grant` | Refresh token revoked (password changed, consent revoked) | Re-run `--device-code` |
| `550 5.7.1 Sender not authorized` | Mailbox not licensed for the From address | Assign Exchange Online (Plan 2); check `AVILX_M365_SENDER` |
| `550 5.7.1 Access denied` | `SMTP.Send` permission missing | Add the application permission and grant admin consent |
| `535 ... Invalid XOAUTH2 format` | Blob separator wrong | Should be impossible with `lib/m365_auth.py`; it is unit-tested byte-exact |
| Mail arrives but lands in junk | SPF/DKIM/DMARC failing | `dig +short TXT avilx.com`; wait for DNS propagation |
| `no Microsoft 365 token cached` | Device-code login never ran | Run `--device-code` |
| Sends stopped after ~1 hour | `offline_access` scope missing | Add the permission, re-consent, re-run `--device-code` |

## Reference

- Microsoft: [Authenticate an SMTP session using OAuth](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- Microsoft: [Configure SPF for Microsoft 365](https://learn.microsoft.com/en-us/defender-office-365/email-authentication-spf-configure)
- Microsoft: [DNS records for Microsoft 365](https://learn.microsoft.com/en-us/microsoft-365/enterprise/external-domain-name-system-records?view=o365-worldwide)
- RFC: [XOAUTH2 SASL mechanism](https://tools.ietf.org/html/rfc7628)
