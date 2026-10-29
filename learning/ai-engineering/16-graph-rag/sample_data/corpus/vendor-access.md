# Third-Party Vendor Access

Any third-party vendor that touches AcmeCorp systems or data must be reviewed
and onboarded through this process.

## Requirements

- A signed **Data Processing Agreement (DPA)** is required before any access.
- A **security review** is required for any vendor that handles customer data
  or production systems.
- The vendor's IAM role is **least-privilege** and time-boxed (default 90 days,
  renewable).

## Approval Path

1. The requesting team files a vendor-access ticket.
2. Security reviews the ticket (3 business days).
3. Legal reviews the DPA (5 business days, can run in parallel).
4. IT provisions the IAM role.
5. The vendor accesses only what they need; access is revoked at the end of
   the engagement.

## Renewals

Reviews are renewed **annually**. Security may re-review sooner if there is a
material change in the vendor's data handling.
