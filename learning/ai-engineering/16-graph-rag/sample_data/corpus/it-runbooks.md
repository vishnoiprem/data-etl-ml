# IT Runbooks

This document covers the day-1 IT setup and the common recurring tasks.

## Day-1 Setup

1. **Laptop provisioning** — pick up from IT, image with the standard corp build.
2. **SSO enrollment** — Okta SSO, with hardware-key MFA (YubiKey) preferred.
3. **Password manager** — 1Password, with the team vault joined on day 2.
4. **Accounts** — Slack, Email, Calendar, GitHub, AWS SSO.

## Travel IT Prep

If you are traveling for AcmeCorp — especially internationally — see
`expense-policy.md` §3 for the approval path. The IT side mirrors it:

- **Domestic travel**: laptop full-disk encryption, no extra action.
- **International travel**: VPN profile, hardware key, encrypted backup drive.

## Common Tasks

- **Password reset**: self-service via Okta. If locked out, page #it-helpdesk.
- **New account for a contractor**: 30-day expiry by default. See
  `vendor-access.md` for the full workflow.
- **Lost laptop**: page Security immediately. We do not wait.

## Paging

IT uses PagerDuty for SEV1 and SEV2 issues only. For everything else, open a
ticket in the helpdesk queue.
