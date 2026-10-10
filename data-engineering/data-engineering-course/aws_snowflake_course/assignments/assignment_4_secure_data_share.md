# Assignment 4 — Secure Data Share with Masking & Reader Account

> **Duration:** 3 hours.  Combines sections 16, 18, 20.

## Goal

Publish a `PRODUCT_CATALOG` dataset to two downstream audiences
(an internal team via Direct Share, and an external partner via a
**Reader Account**) while enforcing:

- row-level filters,
- column-level masking for PII,
- a **secure view** that hides internal IDs and prices,
- and a custom role hierarchy on the consumer side.

## Steps

1. In the provider account: create a `PROVIDER_CATALOG` database with
   a `PRODUCTS` table and a `CUSTOMERS` table (PII columns).
2. Build a `SECURE VIEW V_CATALOG_PUBLIC` that joins them but exposes
   only the columns the consumer is allowed to see.
3. Add a **row-access policy** that limits consumers to the `EU` and
   `APAC` regions.
4. Add **masking policies** on `email` and `phone` so even authorised
   consumers see `e***@example.com` and `+** *** 1234`.
5. `CREATE SHARE PRODUCT_CATALOG_SHARE` and grant the right USAGE/SELECT.
6. `ALTER SHARE ADD ACCOUNTS = (<your internal consumer locator>);`.
7. Provision a **Reader Account**, grant the role to it, and add it to
   the share.
8. From the consumer account, `CREATE DATABASE CONSUMER_DB FROM SHARE
   <provider>.PRODUCT_CATALOG_SHARE;` and run a `SELECT` — confirm the
   masking and row policies fire as expected.

## Deliverable

A PR that adds:
- `18_data_sharing/code/create_share.sql` (extended with row policy +
  Reader Account)
- `20_extra_topics/code/masking_policy.sql` (column-level PII masking)
- `20_extra_topics/code/rbac_grants.sql` (consumer-side role hierarchy)
- `tests/test_secure_share.py` (≥ 6 tests, FakeConnection-based)
- A `SECURITY.md` describing one threat model you engineered against.

## Bonus

- Add a **network policy** that restricts the Reader Account to a
  specific IP range (e.g. a partner VPN).
- Add a **future-grant** on all new tables in the catalog so any
  new product is auto-shared.
- Demonstrate **time-travel on the share** (consumer can query the
  shared view as of 1 h ago — no extra cost).

## Author

Prem Vishnoi <pvishnoi@avilx.com>
