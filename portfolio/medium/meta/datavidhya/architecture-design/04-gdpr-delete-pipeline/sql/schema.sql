-- =====================================================================
-- GDPR Delete Pipeline — Schema
-- =====================================================================

-- 1) Deletion requests (append-only)
CREATE TABLE IF NOT EXISTS deletion_requests (
    request_id      STRING          NOT NULL,
    user_id         STRING          NOT NULL,
    requested_at    TIMESTAMP       NOT NULL,
    requested_by    STRING,                       -- 'self' | 'legal_hold' | 'admin'
    verification_method STRING,                    -- 'email_otp', 'gov_id', 'sso'
    sla_deadline    TIMESTAMP       NOT NULL,      -- requested_at + 30 days
    status          STRING          NOT NULL,      -- RECEIVED | DISCOVERED | DELETING | VERIFIED | FAILED
    completed_at    TIMESTAMP,
    PRIMARY KEY (request_id)
) PARTITIONED BY (days(requested_at));

-- 2) Per-system per-request receipt
CREATE TABLE IF NOT EXISTS deletion_receipts (
    receipt_id      STRING          NOT NULL,
    request_id      STRING          NOT NULL,
    user_id         STRING          NOT NULL,
    system_name     STRING          NOT NULL,      -- iceberg, warehouse, redis, s3, es, ...
    system_id       STRING,                       -- DB/table identifier
    rows_deleted    BIGINT,
    objects_deleted BIGINT,
    method          STRING,                       -- 'direct' | 'crypto_shred' | 'soft_delete'
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    receipt_hash    STRING,                       -- SHA-256 of all receipt fields
    signature       STRING,                       -- HSM-signed
    status          STRING,                       -- OK | FAILED | RETRY
    PRIMARY KEY (receipt_id)
) PARTITIONED BY (days(completed_at));

-- 3) Compliance certificate (final artifact for auditor)
CREATE TABLE IF NOT EXISTS compliance_certificates (
    certificate_id  STRING          NOT NULL,
    request_id      STRING          NOT NULL,
    user_id         STRING          NOT NULL,
    systems_covered INT,
    total_rows      BIGINT,
    total_objects   BIGINT,
    methods_used    ARRAY<STRING>,
    merkle_root     STRING,                       -- root hash of all receipts
    signature       STRING,                       -- HSM-signed
    issued_at       TIMESTAMP       NOT NULL,
    PRIMARY KEY (certificate_id)
);

-- 4) Crypto-shredding key registry (per-user encryption keys)
CREATE TABLE IF NOT EXISTS crypto_keys (
    key_id          STRING          NOT NULL,
    user_id         STRING          NOT NULL,
    alias           STRING,                       -- KMS alias
    status          STRING          NOT NULL,      -- ACTIVE | SCHEDULED_DELETION | DELETED
    created_at      TIMESTAMP,
    deletion_scheduled_at TIMESTAMP,
    deleted_at      TIMESTAMP,
    PRIMARY KEY (key_id)
);
