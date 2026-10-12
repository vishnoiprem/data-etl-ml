-- Migration 002 — apply_mode column on leads
-- Date: 2026-10-13
--
-- Why: autopilot.py now supports two outreach modes:
--   'pod'  — Avilx sells a senior engineering pod (default, unchanged)
--   'solo' — Prem Vishnoi personally applies for the role
--
-- Track which mode each lead was generated under so the analytics
-- dashboard + future weekly reports can split replies/conversions
-- by mode. New column is NOT NULL with a default so the migration
-- is safe on existing rows.

BEGIN;

ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS apply_mode TEXT NOT NULL DEFAULT 'pod'
        CHECK (apply_mode IN ('pod', 'solo'));

-- Index for splitting daily/weekly reports by mode.
CREATE INDEX IF NOT EXISTS leads_apply_mode_idx ON leads(apply_mode);

COMMIT;
