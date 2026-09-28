# Lesson 5 — AI Testing & Validation

> **Type:** Article · Module 3 · AI for Pipeline Development
> Generating dbt tests, pytest suites, and end-to-end data contracts using AI as a test-generation partner.

---

## The asymmetry

Writing tests is the **least-fun, highest-ROI** activity in DE. AI makes it cheap.

```
   Manual test authoring: 4 hours per model
   AI-assisted test authoring: 15 minutes per model
   Coverage improvement: 30% → 85%

   The AI doesn't replace the test. It removes the cost barrier
   to writing the test in the first place.
```

---

## The four test layers

```
   ┌──────────────────────────────────────────────────────────┐
   │  TEST PYRAMID for AI-DATA PIPELINES                     │
   │                                                          │
   │                              ┌──────────┐                │
   │                              │  E2E     │  dbt build     │
   │                              │  tests   │  full project  │
   │                              └─────┬────┘                │
   │                          ┌────────┴────────┐             │
   │                          │  Contract tests │  producer/   │
   │                          │                 │  consumer    │
   │                          └────────┬────────┘             │
   │                  ┌────────────────┴────────────────┐    │
   │                  │  Integration tests                │    │
   │                  │  pipeline runs against real data  │    │
   │                  └────────────────┬────────────────┘    │
   │      ┌────────────────────────────┴──────────────────┐ │
   │      │  Unit tests                                    │ │
   │      │  extract function, validator, transform       │ │
   │      └────────────────────────────────────────────────┘ │
   └──────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Unit tests (pytest)

```text
Given the function:

  def normalise_currency(amount: int, from_ccy: str, to_ccy: str) -> Decimal:
      ...

Generate pytest tests covering:
- happy path (USD → USD)
- conversion (EUR → USD)
- same currency (no-op)
- negative amount (raises ValueError)
- unknown currency (raises ValueError)
- zero amount (returns 0)
- rounding to 2 dp
- large amount near Decimal precision limits
- non-integer input (raises TypeError)

CONSTRAINTS:
- parametrize where useful
- one assert per test
- no fixtures that hide what's being tested
```

AI generates ~20 test cases in 30 seconds. Without it, you'd write 4 in an hour.

---

## Layer 2 — Integration tests (pipeline runs against real data)

```text
For the pipeline dags/stripe_payments.py:

Generate integration tests that:
- run against the dev environment
- use a 1-day window from {{ ds }}
- assert: extract returns >0 rows; validate accepts all; load completes
- assert: second run produces no duplicates (idempotency)
- assert: rows match SUM from the source system

CONSTRAINTS:
- tests are run by `make test-integration`
- use Airflow's `airflow tasks test` not `airflow dags trigger`
- clean up any test data inserted
```

---

## Layer 3 — dbt tests (`schema.yml`)

```text
Given the model marts.fct_orders with columns:
- order_id (varchar, PK)
- customer_id (varchar, FK dim_customers)
- order_amount (decimal(18,2))
- order_status (varchar)
- placed_at (timestamp)

Generate schema.yml with:
- not_null + unique on order_id
- relationships on customer_id → dim_customers.customer_id
- accepted_values on order_status: ['placed', 'paid', 'shipped', 'delivered', 'returned', 'cancelled']
- dbt_utils.expression_is_true on order_amount >= 0
- freshness on placed_at (warn at 24h, error at 48h)
- column descriptions

CONSTRAINTS:
- don't over-test (5-8 tests is right for this table)
- use accepted_values, not custom SQL, where possible
```

---

## Layer 4 — Contract tests (producer / consumer)

Producer (e.g. the API ingestion team) and consumer (e.g. the analytics team) agree:

```yaml
# contracts/stripe_payments.yml
producer: data-platform
consumer: analytics
model: raw.stripe.payments_v2
columns:
  - name: payment_id
    type: varchar
    nullable: false
    description: Stripe's unique payment identifier
  - name: amount_cents
    type: integer
    nullable: false
  - name: created_at
    type: timestamp_ntz
    nullable: false
freshness:
  sla: 6h
```

Both sides run a contract test in CI:

```python
def test_stripe_payments_contract():
    """Verify the producer's contract is honoured."""
    columns = get_table_columns("raw.stripe.payments_v2")
    assert columns["payment_id"].nullable is False
    assert columns["amount_cents"].type == "integer"
    assert max_loaded_age_hours("raw.stripe.payments_v2") < 6
```

AI generates the contract test from the YAML.

---

## The "generate tests for legacy code" workflow

Most legacy code has **zero tests**. AI fixes this fast:

```
   Pick a legacy module
        │
        ▼
   AI: "Here is module X. Generate pytest tests covering:
       - every public function
       - every error path in the docstring
       - the edge cases I list: [...]"
        │
        ▼
   You: review, fix the tests, ship
        │
        ▼
   Next module
```

A team of 3 DEs can take a project from 30% to 80% coverage in **a single sprint** using this pattern. Without AI, it's a quarter.

---

## The "what to test" decision matrix

| Test type | When | Effort | AI helps? |
|---|---|---|---|
| **dbt schema tests** | Every model | Low | ✅ Very |
| **dbt custom SQL tests** | Business rules | Medium | ✅ Yes |
| **pytest unit** | Reusable functions | Medium | ✅ Very |
| **Pipeline integration** | End-to-end | High | ⚠️ Some |
| **Contract tests** | Producer/consumer | Medium | ✅ Yes |
| **Data-diff tests** | Cross-env | High | ⚠️ Some |

---

## The "AI test failure mode" honesty

- **Tests that always pass.** AI sometimes writes a test that doesn't actually exercise the code (e.g. asserts the wrong thing).
- **Tests that test the framework.** AI sometimes writes a test that tests `pytest`, not your code.
- **Over-mocking.** AI mocks too aggressively, hiding real bugs.

**Defense:**
1. **Mutation test the tests.** Deliberately break the code; the test must fail.
2. **Coverage report.** If a test has 100% coverage but doesn't fail when the code is wrong, it's worthless.
3. **Periodic manual review.** Once a sprint, review AI-generated tests for "is this actually testing anything?"

---

## The validation pipeline

```
   AI generates test
        │
        ▼
   Run the test against current code         → does it pass?
        │
        ├─ pass: ship
        │
        └─ fail: investigate
                │
                ▼
   Deliberately break the production code   → does the test fail?
                │
                ├─ fail: ship
                │
                └─ pass: the test is broken — fix it
```

This is **mutation testing**. Without it, AI-generated tests are decoration.

---

## What Comes Next

> Lesson 6 — **AI Documentation & Catalogs** — generating schema.yml, docstrings, lineage notes, and column-level descriptions at >85% coverage.
