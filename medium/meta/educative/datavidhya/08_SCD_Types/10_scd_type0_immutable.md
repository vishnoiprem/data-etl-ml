# SCD Type 0: Immutable / No Changes Allowed

## Problem
Regulatory dimensions where the value at the time of event must never be modified.

## How to Think
1. Once inserted, rows never change.
2. "Corrections" are new rows (audit trail).
3. Strict INSERT-only discipline.

## How to Remember
- **Pattern**: "Type 0: append-only. No UPDATE."
- Use for compliance / audit.

## SQL (Presto / Hive)
```sql
-- Insert only; never UPDATE.
INSERT INTO dim_transaction (transaction_id, currency, event_date)
VALUES (1, 'EUR', '2025-01-02');
```

## Common Mistakes
- Running UPDATE statements — violates immutability.
- Confusing with Type 1 (which DOES allow in-place updates).

## AI Use Cases
- Regulatory reporting (SOX, GDPR).
- Audit logs.
- Immutable event streams.
