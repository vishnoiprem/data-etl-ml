# Apply Workflow — 2 paths (email + URL)

For each of the 10 leads, you have TWO ways to apply:

## Path A: Email (when you have a recruiter email)
Use `send_emails.py` to send a personalized email with resume attached.

```bash
# Send 1 lead
python3 send_emails.py --lead 0

# Send today's batch
python3 send_emails.py --daily --limit 3
```

**Best for:** A.Team, Lemon.io, Proxify (these have public `hello@` or `talent@` addresses that don't bounce).

## Path B: Apply URL (when no email is public, or the platform wants the application)
Use `open_urls.py` to open the apply URL in your browser, then sign in / apply.

```bash
# Open all 10 URLs
python3 open_urls.py

# Open just principal-track (LiveKit, A.Team, Tailscale, Dremio, Reef, Sticker Mule)
python3 open_urls.py --principal

# Open just one
python3 open_urls.py --lead 0
```

**Best for:** LiveKit (Ashby), Dremio (WWR), Tailscale (WWR), Sticker Mule (RemoteOK), Typeform (WWR), Toggl (WWR), Reef Tech (careers page).

## Which to do first?

**Do BOTH for the same lead.** Many of these companies prefer applicants via the platform (they have an ATS), but a personal email to the founder/recruiter can bypass the queue.

The recommended sequence:

1. **Open the URL** (via `open_urls.py --lead N`) → apply on the platform (5 min)
2. **Send a courtesy email** (via `send_emails.py --lead N`) → "Hi, just applied via [platform], would love to chat" (30 sec)

This puts you in front of the recruiter twice.

## Today's workflow (60-90 min)

```bash
# 1. Open the top 3 principal leads in your browser
python3 open_urls.py --lead 0   # LiveKit
python3 open_urls.py --lead 1   # A.Team
python3 open_urls.py --lead 2   # Tailscale

# Apply manually on each platform
# Sign in, paste the cover letter, attach resume, submit

# 2. Send a courtesy email to each (after you've applied on the platform)
python3 send_emails.py --lead 0
python3 send_emails.py --lead 1
python3 send_emails.py --lead 2

# 3. Mark them as sent
# Open leads.json, change "status": "pending" → "status": "sent"
# OR add new field "applied_via": "platform" or "email" or "both"

# 4. Repeat for next 3 leads
python3 open_urls.py --lead 3   # Dremio
python3 open_urls.py --lead 4   # Reef
python3 open_urls.py --lead 5   # Sticker Mule
# apply, then:
python3 send_emails.py --lead 3
python3 send_emails.py --lead 4
python3 send_emails.py --lead 5
```

## Tracking in leads.json

After you apply, edit `leads.json` to update status:

```json
{
  "company": "LiveKit",
  "status": "pending",  // change to: applied_url, applied_email, applied_both, replied, interviewed, offered
  "applied_via": "url",  // optional
  "applied_date": "2026-10-10",
  "response_date": null,
  "notes": "Applied via Ashby, sent follow-up email"
}
```

## When the recruiter-email agent finishes

I'll update `leads.json` with verified emails for each company. The leads with **High confidence email** will get an auto-send via `send_emails.py`. The leads with **no email** will only get the URL apply via `open_urls.py`.
