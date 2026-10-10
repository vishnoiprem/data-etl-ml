# Assignment 3 — dbt Unit Tests

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Estimated time:** 2 hours
> **Sections tested:** 6, 19

## Goal

Write 3 dbt unit tests for the `fraud_score` Python model.

## Steps

1. **Read** `dbt_project/tests/unit/test_fraud_score_unit.yml` for the pattern.

2. **Add 3 new unit tests** in
   `dbt_project/tests/unit/test_fraud_score_extra.yml`:
   - `test_zero_risk_address`: an address with 0 transactions should
     not appear in the output.
   - `test_score_calculation`: verify the exact score formula
     `distinct_counterparties * 0.6 + tx_count * 0.4`.
   - `test_handles_null_to_address`: a contract-creation transaction
     (to_address = null) should still be included.

3. **Run `dbt test --select test_type:unit`** to verify.

## Acceptance criteria

- [ ] 3 new test cases in `test_fraud_score_extra.yml`
- [ ] All 5 unit tests pass (2 original + 3 new)
- [ ] `dbt test` exit code 0
