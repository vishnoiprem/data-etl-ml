-- Migration 001 — role-aware unique index on leads
-- Date: 2026-10-11
--
-- Why: The previous UNIQUE INDEX leads_company_email_unique on
-- (LOWER(company), LOWER(contact_email)) was too strict. With the new
-- role-aware dedup in find_more_leads.insert_leads() (which keys on
-- (company, email, role)), the DB constraint was rejecting valid
-- inserts via ON CONFLICT DO NOTHING. Result: the curated 106 leads
-- from find_clients and the post-backfill refinement swaps all hit
-- the unique key and got silently dropped.
--
-- Safe to apply: the old constraint prevented any rows with
-- duplicate (company, email) and *different* roles from existing
-- in the first place, so the new constraint is trivially satisfied.
--
-- Before:
--   leads_company_email_unique ON (LOWER(company), LOWER(contact_email))
--     WHERE contact_email IS NOT NULL
--
-- After:
--   leads_company_email_role_unique
--     ON (LOWER(company), LOWER(contact_email), LOWER(role))
--     WHERE contact_email IS NOT NULL AND role IS NOT NULL AND role != ''

BEGIN;

DROP INDEX IF EXISTS leads_company_email_unique;

CREATE UNIQUE INDEX IF NOT EXISTS leads_company_email_role_unique
    ON leads (LOWER(company), LOWER(contact_email), LOWER(role))
    WHERE contact_email IS NOT NULL
      AND role IS NOT NULL
      AND role != '';

COMMIT;
