# Submission Status Tracker

> **Update this as you go.** After each submission, mark the status. The pattern is: ⬜ → 📤 Sent → 📩 Replied → 🎤 Interview → 💰 Offer / ❌ Rejected

## Today's 27 leads (2026-10-10)

### Section 1: Email Apply (18)

| # | Company | Date sent | Status | Notes |
|---|---------|-----------|--------|-------|
| 1 | Sticker Mule | | ⬜ | AI Agent Engineer, $200k |
| 2 | A.Team AI Architect | | ⬜ | $90-170/hr top fit |
| 3 | A.Team Software Dev | | ⬜ | $90-170/hr |
| 4 | Toggl | | ⬜ | Senior Full Stack |
| 5 | Typeform | | ⬜ | Full Stack |
| 6 | Dremio Query | | ⬜ | Senior Staff SWE |
| 7 | Tailscale Data | | ⬜ | Analytics Eng |
| 8 | Tailscale Backend | | ⬜ | Go distributed |
| 9 | Dremio DX | | ⬜ | Developer Exp |
| 10 | Mastra | | ⬜ | TS agents framework |
| 11 | Curai | | ⬜ | Agentic AI |
| 12 | Runway | | ⬜ | Backend, media |
| 13 | Close | | ⬜ | LLM + MCP |
| 14 | Footprint | | ⬜ | ⚠️ verify onsite |
| 15 | Flowstate | | ⬜ | ⚠️ hybrid London |
| 16 | RINSE | | ⬜ | Python+React |
| 17 | City Detect | | ⬜ | Geo+Python |
| 18 | Meeru AI | | ⬜ | Sr Staff Data Eng |

### Section 2: X DM (5)

| # | Handle | Date DM'd | Status | Notes |
|---|--------|-----------|--------|-------|
| 19 | @mastra_ai | | ⬜ | Verify DMs open |
| 20 | @curai_health | | ⬜ | Verify DMs open |
| 21 | @flowstate | | ⬜ | Verify DMs open |
| 22 | @footprint | | ⬜ | Verify DMs open |
| 23 | @bjak_official | | ⬜ | APAC AI |

### Section 3: APAC-Direct (4)

| # | Company | Date sent | Status | Notes |
|---|---------|-----------|--------|-------|
| 24 | Perform.AI | | ⬜ | HCMC, same timezone |
| 25 | Bjak | | ⬜ | APAC remote |
| 26 | SalesNow | | ⬜ | VN-eligible |
| 27 | Touchpoints Health | | ⬜ | UK/Portugal |

## Daily cadence tracker

| Date | Emails sent | X DMs sent | Platform submits | Replies | Interviews | Offers |
|------|-------------|------------|------------------|---------|------------|--------|
| 2026-10-10 | / 18 | / 5 | / 5 | | | |
| 2026-10-11 | | | | | | |
| 2026-10-12 | | | | | | |
| ... | | | | | | |

## Weekly KPI targets

- **Submissions:** 100+ / week
- **Replies:** 5-10 / week (5-10% reply rate)
- **Interviews:** 2-3 / week (20-30% reply → interview)
- **Offers:** 1-2 / week (50% interview → offer)
- **Contracts signed:** 1-2 / month

## Follow-up rules

- **No reply in 3 days:** Send 1-line follow-up ("Hi, just bumping this in case it got buried.")
- **No reply in 7 days:** Move to backup, re-apply in 30 days.
- **Replied but no interview:** Ask 1 question about the role to re-engage.
- **Interview scheduled:** Send 3-bullet pre-call note (1 line per bullet).
- **Rejection:** Ask "what would have made this a yes?" — feedback loop.

## Status legend

- ⬜ Not started
- 📤 Sent
- 📩 Replied
- 🎤 Interview scheduled
- 💰 Offer received
- ✅ Contract signed
- ❌ Rejected
- ⏸️ On hold (waiting for them to reply)

---

## Reply tracking (the columns that answer "which template converts")

`leads-pipeline/<date>/leads-tracker.csv` now has four reply-tracking columns
appended to the right of the original 14:

| Column | Meaning | Example |
|---|---|---|
| `replied` | `yes` once they respond (any channel). Empty = no reply yet. | `yes` |
| `replied_at` | Date of the reply (UTC, `YYYY-MM-DD`). | `2026-10-14` |
| `reply_channel` | Where the reply came in. One of: `email`, `x_dm`, `linkedin`, `platform`, `inbound`, `other`. | `email` |
| `meeting_booked` | Date of the booked meeting (UTC). Empty until scheduled. | `2026-10-17` |

### How to record a reply

The `draft-cron/` directory ships a CLI that mutates the latest
`leads-tracker.csv` in place. From `leads-pipeline/draft-cron/`:

```bash
# Mark a reply
make reply Q="Tailscale" REPLIED=1 AT=2026-10-12 VIA=email
# Or directly:
python3 bin/mark_reply.py "Tailscale" --replied --at 2026-10-12 --via email

# Mark a meeting (without marking replied — assumes already replied)
make reply Q="Perform.AI" MEETING=1 AT=2026-10-14

# Record both in one shot
python3 bin/mark_reply.py "A.Team" --replied --meeting --at 2026-10-13 --via email --notes "asked for case studies"

# See the current state of every lead
make reply-list
# or:
python3 bin/mark_reply.py --list

# Misclick? Revert
python3 bin/mark_reply.py "Acme Co" --revert
```

The CLI:
- **Idempotently migrates** any older CSV: if the four reply columns
  are missing, they're appended. Safe to run on the 2026-10-10 drop
  or any future drop.
- **Searches by company substring** (case-insensitive). If "Tailscale"
  matches two rows, the first one wins — fix by using a more specific
  query or a numeric index.
- **Validates `--via`** against the channel whitelist above. Anything
  else is rejected by argparse before the CSV is touched.
- **Does not delete the row** — it only updates columns 15–18.

### How to read the weekly KPIs

After a few replies are logged, the metrics CLI answers the questions
that drive the next 7 days of outreach:

```bash
# Default: last 7 days
make metrics
# Last 30 days
make metrics DAYS=30
# With per-channel breakdown
make metrics CHANNEL=1 DAYS=30
# JSON for a dashboard
make metrics DAYS=30 JSON=1 > /tmp/metrics.json
# Or directly:
python3 bin/reply_metrics.py --days 30 --by-channel
```

Output (example):

```
# Reply metrics — last 30d
  sent     = 87
  replied  = 6   (6.9% reply rate)
  meetings = 2   (33.3% meeting rate from replies)

## By channel
  channel         sent  replied   reply%   meetings
  --------------------------------------------------
  email             62        5     8.1%          2
  x_dm              18        1     5.6%          0
  platform           7        0     0.0%          0
```

### Why this matters (the close-the-loop part)

The previous tracker stopped at "📤 Sent". Sent is a vanity metric.
The four new columns turn the tracker from a *send log* into a
*conversion funnel* — the data you need to answer:

- **"Which email template converts?"** → correlate `reply_channel=email`
  + the row's `cover_letter` content with `meeting_booked` dates.
- **"Does X DM work better than email for tier-1 leads?"** → group by
  `channel` and `tier`.
- **"What day of the week gets replies?"** → group by `replied_at`
  weekday.
- **"Am I improving?"** → run `make metrics` weekly, watch the
  reply-rate line trend.

The target (from this README's KPI section above): 5–10% reply rate,
20–30% of replies become interviews, 50% of interviews become offers.
If your numbers are below these after 50 sends, the bottleneck is
*the template* (rewrite the opener), not the channel or the volume.

---


---

## CI status — local verification (2026-10-13)

`leads-ci` only triggers on pushes to `main`, `feature/agent-coding-11oct`,
or `feature/auto-pilot-ai-leads-loop` — not on this branch
(`feature/add-business-plan-13-oct`). `pip-audit` only triggers on
changes to `requirements*.txt` files, which the reply-tracking
work didn't touch. With no `gh` CLI on this machine and no PR
open against `main`, the live CI cannot be re-run from here.

**What we did instead** — ran the full CI test matrix locally
against the exact Python 3.10 + `requirements.txt` from the
workflows, plus every test module added by steps 1–3 of the
30-day plan. Result:

| Suite | Modules | Result |
|---|---|---|
| `leads-ci` test job (matches `make test` + `test_hnhiring_parse`) | 8 | ✅ all pass |
| `test_mark_reply.py` (step 1 — reply-tracking) | 6 | ✅ all pass |
| `test_mark_supplier_reply.py` (step 2 — first supplier RFQ) | 8 | ✅ all pass |
| `test_no_hardcoded_aws_keys.py` (step 3 — key rotation regression) | 7 | ✅ all pass |
| **Total new tests added in the 30-day plan** | **21** | **21/21 ✅** |
| **Total including pre-existing CI modules** | **27** | **27/27 ✅** |

**To exercise the actual remote CI** (recommended before the
next regulated-industry client conversation):

1. Open a PR from `feature/add-business-plan-13-oct` → `main`.
   `leads-ci` fires on `pull_request: branches: [main]`. Green
   PR = green CI.
2. After merge, `pip-audit` will fire on the next push to `main`
   that touches a `requirements*.txt` file — or on Monday morning
   via its weekly cron.

The local run above is the same code path the CI executes; the
PR gate is the only thing that changes.


**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
