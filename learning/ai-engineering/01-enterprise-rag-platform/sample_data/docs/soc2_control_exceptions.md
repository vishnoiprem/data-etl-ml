# SOC 2 Control Exception Process

## Purpose

This document describes how AcmeCorp handles deviations from documented
SOC 2 controls. The process ensures that all exceptions are approved,
time-bounded, compensated, and visible to auditors.

## When you need an exception

You need a documented control exception when, for a defined business
reason, you cannot meet a documented SOC 2 control. Common examples:

- A vendor cannot accept SAML SSO and requires a shared service account.
- A legacy system does not support 90-day password rotation.
- A maintenance change requires temporarily disabling production logging.

If the deviation is unintentional or a misconfiguration, this is **not** an
exception — it is an incident. Open a ticket with Security Operations.

## Who approves SOC 2 control exceptions

Approvals are tiered by the residual risk:

| Risk | Approver | SLA |
|---|---|---|
| Low | Engineering Manager + Security Officer | 5 business days |
| Medium | Director of Engineering + Head of Compliance | 10 business days |
| High | CISO + General Counsel | 15 business days |
| Critical | CISO + CEO | Case-by-case |

The Head of Compliance owns the master Exceptions Register. Every approved
exception lives there with: control ID, requester, business justification,
risk rating, compensating controls, expiry date, and approvers.

## How to request

1. Open a ticket in ComplianceHub with template "SOC 2 Exception".
2. Include:
   - The control ID being deviated from (e.g., `CC6.1.3`).
   - Why the standard control cannot be met.
   - The proposed compensating control.
   - The expiry date (max 12 months; longer requires CISO sign-off).
3. Route to the appropriate approver based on risk.

## Compensating controls

Every exception requires a compensating control that reduces residual risk
to an acceptable level. Examples:

- Cannot do SAML SSO → require monthly access review + alert on every login
  outside business hours.
- Cannot rotate password every 90 days → vault credential, log retrieval,
  rotate every 180 days.

## Review

The Compliance team reviews open exceptions monthly and reports to the
Audit Committee quarterly. Expired exceptions are escalated to the CISO
within 5 business days.

## Auditor visibility

The Exceptions Register is a primary artifact in the SOC 2 audit. Auditors
sample exceptions and verify:
- The approval chain
- The compensating control is operating
- The exception has not expired without renewal or remediation
