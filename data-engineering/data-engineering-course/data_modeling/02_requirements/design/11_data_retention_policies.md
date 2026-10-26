# Data Retention Policies & Historical Data Management

## Why this lesson

A data model that doesn't account for retention is a model that will fail an audit, a regulator, or a finance close. Retention is a non-functional requirement that determines partition strategy, archival cadence, and the right-hand side of every "delete after N days" question. A 7-year retention requirement (US financial audits) means the warehouse must keep `fact_invoices` for 7 years; a 30-day cookie-retention requirement (GDPR) means the warehouse must delete `fact_web_events` after 30 days for EU users. This lesson teaches the retention discovery questions, the regulatory and operational drivers, and the partitioning + cold-storage patterns that make retention enforceable rather than aspirational.

---

## Why retention matters

There are three reasons retention is a hard requirement, not a
nice-to-have:

1. **Regulatory.** GDPR, CCPA, HIPAA, SOX, and finance audit
   rules impose specific retention windows — sometimes minimum
   (SOX: 7 years for financial records), sometimes maximum
   (GDPR: data subject right to erasure).
2. **Operational.** Storage costs scale with retention. A
   fact table with 10B rows kept "forever" is a budget problem
   in 24 months. Archival to cold storage is a real
   optimization, not a hygiene task.
3. **Legal.** Litigation hold, right-to-be-forgotten, and
   audit-trail requirements impose *minimum* retention.
   Deleting data too early is a legal exposure.

The senior candidate treats retention as a *first-class*
non-functional requirement, alongside freshness and volume.

---

## The retention discovery questions

> Candidate: "Before I draw, I need to understand the retention
> requirements, because they drive partitioning, archival, and
> the data-deletion strategy."

1. **What are the minimum retention windows?**
   > "Are there regulatory or audit rules that require us to
   > keep certain data for a minimum period — e.g., 7 years for
   > financial records (SOX), 6 years for healthcare (HIPAA),
   > 10 years for tax records?"
2. **What are the maximum retention windows?**
   > "Are there regulations that require us to *delete* data
   > after a period — e.g., GDPR right-to-be-forgotten, CCPA
   > opt-out, cookie retention at 30/90/180 days?"
3. **Are there different retention windows by data type?**
   > "Do `fact_orders` need 7 years, while `fact_web_events`
   > need only 90 days? Do PII fields need separate handling
   > (e.g., tokenize, redact, or delete) on a different
   > schedule from the rest of the row?"
4. **Where does the data live in the retention lifecycle?**
   > "Do we have a hot/warm/cold tier — recent data in
   > Snowflake / BigQuery, older data in Parquet on S3, oldest
   > data in Glacier / coldline?"
5. **What happens to deletes and corrections?**
   > "If a user invokes GDPR right-to-be-forgotten, do we
   > delete from the warehouse, redact fields, or both? If a
   > financial record is corrected, do we keep the original
   > (audit trail) or overwrite?"
6. **Is there a litigation hold?**
   > "Are we under any active or anticipated legal hold that
   > freezes deletion? Does the warehouse need to be able to
   > *suspend* deletion on a subset of records?"
7. **Who owns retention policy?**
   > "Is retention defined by legal, security, finance, or the
   > data team? Who signs off on changes to the policy?"

---

## The retention tier pattern

Most warehouses implement retention as a three-tier lifecycle:

| Tier | Latency to query | Storage | Cost/GB | Typical use |
|---|---|---|---|---|
| **Hot** | < 1s | Snowflake / BigQuery / Redshift standard | $$$ | Last 30–90 days; live dashboards. |
| **Warm** | 5–60s | Snowflake / BigQuery / Redshift, lower-tier storage | $$ | 90 days – 2 years; ad-hoc analyst queries. |
| **Cold** | minutes | Parquet on S3 / GCS, queried via Athena or Spectrum | ¢ | 2+ years; finance / audit / compliance. |

The schema-level decision: partition the fact table by
`date_key` (or event-time), and let the warehouse's
*retention policy* (or a scheduled compaction job) move old
partitions to cold storage. This is enforceable; deleting
rows in-place is not.

---

## Retention patterns by data type

| Data type | Typical retention | Driver | Pattern |
|---|---|---|---|
| Financial records (invoices, payments) | 7 years | SOX, IRS | Hot 2y, cold 5y+; never delete. |
| Healthcare records (encounters, claims) | 6–10 years | HIPAA | Hot 1y, cold 5–9y+; audit-trail immutable. |
| Web events (clicks, page views) | 30–180 days | Cookie consent, GDPR | Hot 30d, then delete or aggregate. |
| User PII (name, email, address) | Until account deletion | GDPR, CCPA | Tokenize; delete on request. |
| Session logs (auth, API) | 90 days – 1 year | Security audit | Hot 90d, cold 1y. |
| ML feature tables | 1–2 years | Model reproducibility | Hot 1y, recompute or archive. |
| Derived / aggregated tables | 2–5 years | Ad-hoc analyst | Recompute from raw; no archival. |

The interview move: the candidate names the *driver* (SOX,
GDPR, etc.), the *window*, and the *pattern* (hot/cold,
delete, tokenize). Three sentences that show end-to-end
fluency.

---

## GDPR / CCPA — the right-to-be-forgotten pattern

GDPR Article 17 and CCPA both give users the right to have
their personal data erased. The schema-level pattern:

1. **Tokenize PII at ingest.** Replace `email`, `name`, and
   `phone` with opaque tokens. The token is the same in every
   fact and dim, so joins still work.
2. **Maintain a deletion registry.** A `dim_user_deletion_log`
   table records `user_id`, `deletion_request_date`,
   `redaction_complete_date`.
3. **Re-derive fact tables.** When a user is deleted, re-derive
   their fact rows (or re-tokenize their `customer_key` in
   every fact). Aggregate tables are unaffected (the user is
   already counted anonymously).
4. **Audit-trail immutable.** The original PII is *gone* from
   the warehouse. The audit log records *that* a deletion
   happened, not the deleted data.

> "For GDPR, I'd tokenize PII at ingest and re-derive fact
> rows on deletion. The user becomes a token, joins still
> work, and the original PII is unrecoverable."

---

## The audit-trail pattern

Some data *cannot* be deleted — financial corrections, security
incidents, healthcare records. The pattern:

1. **Append-only fact table.** No UPDATEs. Corrections are
   new rows with a `correction_of` FK back to the original.
2. **Immutable storage tier.** The fact table is on a
   write-once-read-many (WORM) tier — S3 Object Lock, GCS
   Bucket Lock, or a vendor equivalent.
3. **Audit metadata.** Every row carries `created_at`,
   `created_by`, `source_system`, and (for corrections)
   `correction_of`.

> "For financial records under SOX, I'd put the fact table on
> a WORM tier with no UPDATEs. Corrections are new rows
> pointing back to the original."

---

## Cold storage and recompute

The senior candidate's pattern for cold storage:

1. **Hot tier:** last 90 days in the warehouse, queried live.
2. **Cold tier:** > 90 days in Parquet on S3, queried via
   Athena / Spectrum.
3. **Recompute path:** derived tables (aggregates, rollups) are
   *not* archived — they are recomputed from raw when needed.

The cost optimization: $23/TB-month in standard warehouse
storage vs $0.04/GB-month in S3. A 100TB historical archive
is $2,300/month vs $4/month. The numbers matter.

---

## The retention-driven requirements doc

```markdown
# Requirements — Subscription SaaS (with retention)

## Retention
- **Financial records** (invoices, payments): 7 years, hot 2y +
  cold 5y+, immutable WORM tier
- **Subscription events**: 5 years, hot 1y + cold 4y
- **Customer PII**: until account deletion, tokenized at ingest
- **Auth logs**: 1 year, hot 90d + cold 9m
- **GDPR right-to-be-forgotten**: tokenize at ingest, re-derive
  on deletion, audit-trail immutable
- **CCPA opt-out**: same pattern as GDPR; aggregate tables
  unaffected

## Tiering
- **Hot:** Snowflake, last 1 year
- **Cold:** Parquet on S3 + Athena, 1–7 years
- **WORM:** invoices and corrections, 7 years

## Deletion pattern
- GDPR/CCPA: tokenize, re-derive, audit
- Cookie consent expiry: 30/90/180 days per consent
- Litigation hold: warehouse supports hold flag on subset
```

---

## Try it

Take any prompt from the canonical modeling questions. Write a
retention section for the requirements doc, with explicit
windows for: financial records, user PII, raw events, derived
tables, and any regulatory drivers (GDPR, CCPA, HIPAA, SOX).
Time yourself: 10 minutes.

---

## In the interview, you would say...

> "Retention is a first-class non-functional requirement. I'm
> going to ask about **minimum retention** (regulatory, audit),
> **maximum retention** (GDPR, cookie), **per-data-type windows**,
> and the **tiering strategy** (hot/warm/cold). For PII, the
> pattern is tokenize-at-ingest + re-derive-on-deletion; for
> financial records, immutable WORM with corrections as new
> rows. Naming the driver, the window, and the pattern is what
> the interview is testing."

---

*Author: Prem Vishnoi <pvishnoi@avilx.com>*
