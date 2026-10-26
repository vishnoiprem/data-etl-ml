-- Reference SQL for Postgres Row-Level Security tenant isolation.
-- Run as a superuser; the app connects as a non-superuser.

CREATE TABLE accounts (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    name        TEXT NOT NULL,
    balance     INT  NOT NULL
);

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON accounts
    USING (tenant_id = current_setting('app.current_tenant', true));

-- Per-tenant encryption key (real impl: AWS KMS / Vault)
CREATE TABLE tenant_keys (
    tenant_id  TEXT PRIMARY KEY,
    kek_id     TEXT NOT NULL,           -- KMS key id
    wrapped_dek BYTEA NOT NULL          -- data encryption key, wrapped by KEK
);

-- Audit every cross-tenant attempt
CREATE TABLE tenant_access_audit (
    ts          TIMESTAMPTZ DEFAULT now(),
    actor       TEXT,
    tenant_set  TEXT,
    rows_read   INT
);
