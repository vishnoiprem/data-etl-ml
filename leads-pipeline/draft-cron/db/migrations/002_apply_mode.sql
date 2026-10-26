-- Migration 002 — apply_mode column on leads
-- Date: 2026-10-13
--
-- Why: autopilot.py now supports two distinct outreach modes:
--   'pitch_pod'       — Avilx pitches a senior engineering pod to the company
--                        ("We can build your team 10x faster with our 6-20 senior
--                        engineers, 7+ clouds, Databricks Champion...")
--   'apply_personal'  — Prem Vishnoi personally applies for the role
--                        ("I'm Prem, 15+ yrs shipping AI/data/cloud systems,
--                        here's my resume, can we talk?")
--
-- Default is 'pitch_pod' (preserves prior autopilot behavior).
--
-- Track which mode each lead was generated under so the analytics
-- dashboard + future weekly reports can split replies/conversions
-- by mode. New column is NOT NULL with a default so the migration
-- is safe on existing rows.

BEGIN;

ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS apply_mode TEXT NOT NULL DEFAULT 'pitch_pod'
        CHECK (apply_mode IN ('pitch_pod', 'apply_personal'));

-- Index for splitting daily/weekly reports by mode.
CREATE INDEX IF NOT EXISTS leads_apply_mode_idx ON leads(apply_mode);

COMMIT;
