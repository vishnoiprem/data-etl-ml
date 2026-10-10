-- Avilx leads tracking schema
-- Stores every email we send with phone/contact info for dedup + tracking.

CREATE TABLE IF NOT EXISTS leads (
    id              SERIAL PRIMARY KEY,
    tracking_id     TEXT UNIQUE NOT NULL,           -- short public ID for the email link
    company         TEXT NOT NULL,
    role            TEXT,
    contact_email   TEXT,                            -- nullable for URL-apply leads
    contact_phone   TEXT,
    apply_method    TEXT NOT NULL DEFAULT 'email',  -- email | url
    stack           TEXT,
    rate            TEXT,
    resume_file     TEXT,
    source_url      TEXT,
    source          TEXT,                            -- 'linkedin_dm', 'jd_inbox', 'auto_replenish', etc
    cover_letter_subject TEXT,
    cover_letter_body    TEXT,
    jd_text         TEXT,
    status          TEXT NOT NULL DEFAULT 'pending', -- pending | sent_email | failed | replied | bounced | unsubscribed
    sent_at         TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    last_error      TEXT,
    send_count      INTEGER NOT NULL DEFAULT 0,      -- how many times we sent to this email
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique only when contact_email is present (URL-apply leads can repeat company)
CREATE UNIQUE INDEX IF NOT EXISTS leads_company_email_unique
    ON leads (LOWER(company), LOWER(contact_email))
    WHERE contact_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS leads_status_idx ON leads(status);
CREATE INDEX IF NOT EXISTS leads_email_idx ON leads(contact_email);
CREATE INDEX IF NOT EXISTS leads_company_idx ON leads(company);
CREATE INDEX IF NOT EXISTS leads_tracking_idx ON leads(tracking_id);

-- Send log: every email attempt
CREATE TABLE IF NOT EXISTS send_log (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    to_email        TEXT NOT NULL,
    subject         TEXT,
    status          TEXT NOT NULL,                  -- success | fail
    error           TEXT,
    smtp_message_id TEXT
);

CREATE INDEX IF NOT EXISTS send_log_lead_idx ON send_log(lead_id);

-- Phone number directory — easy lookup for dedup by phone
CREATE TABLE IF NOT EXISTS phones (
    id          SERIAL PRIMARY KEY,
    phone       TEXT UNIQUE NOT NULL,
    company     TEXT,
    contact_email TEXT,
    lead_id     INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Track unsubscribe / opt-out (anti-spam compliance)
CREATE TABLE IF NOT EXISTS opt_outs (
    email       TEXT PRIMARY KEY,
    opted_out_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- updated_at trigger
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS leads_updated_at ON leads;
CREATE TRIGGER leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =============================================
-- LinkedIn DM tracking (cold outreach to clients)
-- =============================================
CREATE TABLE IF NOT EXISTS linkedin_dms (
    id              SERIAL PRIMARY KEY,
    linkedin_url    TEXT,
    handle          TEXT NOT NULL,                  -- @theirstyle
    name            TEXT,
    company         TEXT,
    title           TEXT,                            -- CTO, VP Eng, etc
    region          TEXT,                            -- US, EU, APAC, China
    template_used   TEXT,                            -- 'Template 1: Hiring signal', etc
    dm_text         TEXT,                            -- exact text sent
    status          TEXT NOT NULL DEFAULT 'sent',    -- sent | replied | intro | meeting | won | lost | bounced
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    replied_at      TIMESTAMPTZ,
    last_touch_at   TIMESTAMPTZ,
    touch_count     INTEGER NOT NULL DEFAULT 1,     -- 1 = initial DM, 2+ = follow-ups
    notes           TEXT,
    lead_id         INTEGER REFERENCES leads(id) ON DELETE SET NULL,  -- if they became a real lead

    CONSTRAINT linkedin_dms_handle_unique UNIQUE (handle)
);

CREATE INDEX IF NOT EXISTS linkedin_dms_status_idx ON linkedin_dms(status);
CREATE INDEX IF NOT EXISTS linkedin_dms_handle_idx ON linkedin_dms(handle);
CREATE INDEX IF NOT EXISTS linkedin_dms_company_idx ON linkedin_dms(company);
CREATE INDEX IF NOT EXISTS linkedin_dms_sent_idx ON linkedin_dms(sent_at DESC);

-- follow-ups: every bump (day 3, day 7, day 14)
CREATE TABLE IF NOT EXISTS linkedin_followups (
    id          SERIAL PRIMARY KEY,
    dm_id       INTEGER NOT NULL REFERENCES linkedin_dms(id) ON DELETE CASCADE,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message     TEXT,
    reply_seen  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS linkedin_followups_dm_idx ON linkedin_followups(dm_id);
