# Lesson 34 — Design a Data Warehouse Schema for Stripe

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the *money type* lesson, the
> *charge state machine*, and the *payout
> reconciliation* problem.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

## Why this lesson

Stripe is a *payments* warehouse, and payments are
where modeling mistakes become financial losses. The
interviewer is testing whether you know that *money
is never a float*, that a *charge* is a state machine
with seven states, and that *payouts do not equal
charges* (the reconciliation problem). Strong
candidates walk in knowing the difference between
`gross`, `net`, `fee`, and `available`; the difference
between *authorization*, *capture*, and *settlement*;
and the difference between *transaction-time FX* and
*settlement-time FX*. This is a finance-flavored
system-design round.

---

## The prompt

> Design a data warehouse for Stripe. 10T
> transactions, 4M merchants, 50B events/year across
> 100+ countries. Finance needs: MRR, gross payment
> volume, dispute rates, payout reconciliation, fraud
> detection.

---

## Step 1: Requirements gathering

Five clarifying questions:

1. **What is a "transaction"?** A *charge* (the
   buyer's payment attempt), a *transfer* (movement
   between Stripe accounts), or a *payment* (the
   final settled amount)? I assume the *charge* is
   the headline event, with transfers and payments as
   downstream facts.
2. **What is "MRR"?** Monthly recurring revenue, but
   over what — subscriptions, all charges, or net of
   refunds? I assume the sum of *subscription
   invoice* amounts, separate from one-off charges.
3. **What is a "dispute"?** A chargeback filed by the
   buyer's bank, with a 7-15 day window to respond.
   Do we model the dispute lifecycle (opened →
   under_review → won/lost) as a state machine?
4. **Multi-currency.** A charge in EUR settled to a
   USD-paying merchant. What is the "revenue" — the
   EUR amount, the USD-converted amount at charge
   time, or the USD-converted amount at payout time?
   These can differ by 1-3%.
5. **Payouts.** Stripe holds balances for 2-7 days
   (the "rolling reserve"), then pays out in a batch.
   A $1000 charge does not produce a $1000 payout;
   it produces a $1000 charge that eventually
   contributes to a payout net of fees. How do we
   model that?

---

## Step 2: High-level architecture

Three fact tables:

```mermaid
fact_charge_events  (grain: 1 row per charge *lifecycle event*)
   ├── charge_event_key  (PK)
   ├── charge_key        → dim_charge
   ├── merchant_key      → dim_merchant
   ├── customer_key      → dim_customer
   ├── currency_key      → dim_currency
   ├── country_key       → dim_country
   ├── event_type        (TEXT: created/authorized/captured/
   │                       settled/refunded/failed/disputed)
   ├── event_date_key    → dim_date
   ├── event_ts          (TIMESTAMP)
   ├── amount_minor      (BIGINT, e.g. cents)
   ├── amount_usd_minor  (BIGINT, FX-converted at event time)
   ├── fee_minor         (BIGINT, Stripe's fee)
   ├── net_minor         (BIGINT, amount - fee)
   └── is_successful     (BOOLEAN)

fact_payouts  (grain: 1 row per payout *leg*)
   ├── payout_leg_key    (PK)
   ├── payout_key        → dim_payout
   ├── merchant_key      → dim_merchant
   ├── currency_key      → dim_currency
   ├── arrival_date_key  → dim_date
   ├── amount_minor      (BIGINT)
   ├── amount_usd_minor  (BIGINT)
   ├── status            (TEXT: pending/in_transit/paid/failed)
   ├── bank_account_key  → dim_bank_account
   └── payout_ts         (TIMESTAMP)

fact_disputes  (grain: 1 row per dispute *lifecycle event*)
   ├── dispute_event_key (PK)
   ├── dispute_key       → dim_dispute
   ├── charge_key        → dim_charge
   ├── merchant_key      → dim_merchant
   ├── event_type        (TEXT: opened/under_review/won/lost/
   │                       evidence_submitted/withdrawn)
   ├── event_date_key    → dim_date
   ├── event_ts          (TIMESTAMP)
   ├── amount_minor      (BIGINT, disputed amount)
   ├── evidence_due_by   (TIMESTAMP)
   └── reason            (TEXT: fraud/product_not_received/etc.)
```

Dimensions:

- `dim_charge` — SCD 1. charge_id, merchant_key,
  customer_key, payment_method_key, description,
  created_at, statement_descriptor.
- `dim_merchant` — SCD 2. merchant_id, business_name,
  country_key, default_currency_key, mcc (merchant
  category code), plan (standard/custom), is_active,
  created_at.
- `dim_customer` — SCD 1. customer_id, merchant_key
  (customers are scoped to a merchant in Stripe),
  email, country_key, default_currency_key, created_at.
- `dim_currency` — small dim. currency_code (ISO 4217),
  name, symbol, decimal_places.
- `dim_country` — small dim. iso_code, name, region.
- `dim_bank_account` — SCD 2. account_id, merchant_key,
  bank_name, last4, currency_key, country_key.
- `dim_payout` — small dim. payout_id, merchant_key,
  status (current only), arrival_date.
- `dim_date` — conformed, role-played.
- `dim_dispute` — small dim. dispute_id, charge_key,
  status (current), reason (current).

---

## Step 3: The 3 hardest parts

### 3.1 Money type — never use float for currency

This is the *first* thing a strong candidate says
when asked to design a payments warehouse. Float
arithmetic accumulates rounding errors: 0.1 + 0.2 =
0.30000000000000004 in IEEE 754. Over 10T
transactions, that error becomes millions of dollars
in mismatched ledgers.

The right model is **integer minor units** (cents,
pence, fen). A $30.00 charge is `3000`, not `30.00`.
SQLite and most warehouses support `BIGINT`, which
holds up to 9.2 × 10^18 — way more than any single
amount. Aggregations (`SUM`) are exact. Conversions
to decimal for display are done at query time, never
at storage time.

The "decimal" type in some warehouses (DECIMAL(18,4))
is acceptable but slower than `BIGINT` for
aggregations. For high-volume payment warehouses,
`BIGINT` minor units is the standard.

A second rule: **always store the currency code** on
the same row as the amount. A column
`amount_minor` without a `currency_code` is
meaningless — 1000 yen is not 1000 USD. The dim
`dim_currency` enforces this; the FK on
`currency_key` is non-nullable.

### 3.2 Charge state machine

A Stripe charge goes through up to seven states:

```
created → authorized → captured → settled → (refunded | disputed)
   ↓          ↓           ↓
 failed    failed      failed
```

The state is not a column on `dim_charge`; it is a
*trail of events* in `fact_charge_events`. The
`event_type` column records the transition. The
"current status" of a charge is the `event_type` of
the most recent event for that `charge_key`.

This matters because:

- **Authorization holds** can expire (a 7-day auth
  on a hotel booking that never captures). The
  fact records the `authorized` event; the analyst
  computes "uncaptured authorizations" as
  `authorized` events with no subsequent `captured`
  event within 7 days.
- **Partial refunds.** A $100 charge can be
  refunded $30, then $20 more, then $50 more. Each
  is a separate `refunded` event with a negative
  `amount_minor`. The fact has multiple rows per
  charge. The total refunded is
  `SUM(amount_minor) WHERE event_type = 'refunded'`.
- **Disputed charges** are *also* in a state machine
  (see §3.4).

A common error: candidates model `status` as an SCD 1
column on `dim_charge` and overwrite it on each
event. This loses the event history and makes it
impossible to answer "what was the status of this
charge on day X?"

### 3.3 Payout reconciliation

This is the *hardest* sub-problem. A charge and a
payout are *not* one-to-one. The flow:

```
Charge $1000 on day 1
  → fee $32
  → net $968 added to merchant balance
  → balance held for 2-7 days ("rolling reserve")
  → payout of $5000 (sum of many charges) on day 7
```

The merchant's daily balance is a *running sum* of
charge-net minus refund-net minus dispute-net. The
payout is a *batch event* that drains the balance.

To reconcile, the warehouse needs a fact that
records the *balance* after each event:

```sql
CREATE TABLE fact_balance_ledger (
  ledger_key        BIGINT PRIMARY KEY,
  merchant_key      INTEGER NOT NULL REFERENCES dim_merchant,
  event_date_key    INTEGER NOT NULL REFERENCES dim_date,
  event_ts          TIMESTAMP NOT NULL,
  event_type        TEXT NOT NULL,  -- 'charge', 'refund',
                                    -- 'dispute_hold',
                                    -- 'payout', 'adjustment'
  amount_minor      BIGINT NOT NULL,  -- signed
  balance_after_minor BIGINT NOT NULL,
  charge_key        INTEGER REFERENCES dim_charge,
  payout_key        INTEGER REFERENCES dim_payout
);
```

The "payout reconciliation report" is then:

```sql
SELECT p.payout_id,
       p.amount_minor AS payout_amount,
       SUM(l.amount_minor) AS ledger_sum
FROM fact_payouts p
JOIN fact_balance_ledger l
  ON l.merchant_key = p.merchant_key
 AND l.event_ts <= p.payout_ts
 AND l.event_ts >  COALESCE(prev_payout.payout_ts, '1970-01-01')
WHERE p.payout_id = ?
GROUP BY p.payout_id;
```

If `payout_amount != ledger_sum`, the payout is
*unreconciled* — and finance needs to investigate.
This is a real audit trail, not a star-schema
report. The star schema is the foundation; the
ledger is the audit.

### 3.4 FX conversion

Money in three currencies: charge currency, merchant
payout currency, and the warehouse's reporting
currency (typically USD). A €100 charge to a US
merchant produces:

- `amount_minor = 10000` (€100.00 in euro cents)
- `amount_usd_minor = 10800` (€100 → $108 at
  charge-time FX)
- `payout_usd_minor = 10500` (€100 → $105 at
  payout-time FX, after a 1% FX margin)

The FX rate *changes daily*. The query "what was Q1
GMV?" must specify which FX rate:

- **Charge-time FX** — accurate at the moment of sale.
  Used for "GMV" reports.
- **Settlement-time FX** — accurate at the moment
  Stripe paid out. Used for "cash collected" reports.
- **Payout-time FX** — accurate at the moment the
  money hit the merchant's bank. Used for "cash
  available to merchant" reports.

A strong candidate says: "I'd store *all three* —
`amount_minor` in the original currency, plus
`amount_usd_charge_time_minor`, plus
`amount_usd_payout_time_minor`. Each report picks
the column that matches its definition."

The FX rate itself is a small dim: `dim_fx_rate`
with `currency_code`, `rate_date`, `rate_to_usd`.
One row per (currency, day). Joins to
`fact_charge_events` on `currency_code` and
`event_date_key`.

---

## Step 4: Common failure modes

1. **Float for money.** The #1 mistake. Use `BIGINT`
   minor units. Always.
2. **Storing charge `status` on the dim.** The
   status is a *trail*, not a *value*. The state
   machine lives in `fact_charge_events`.
3. **One fact for charges and refunds.** A refund
   is not a "negative charge" — it is a *separate
   event* with its own `event_type`. Mixing them
   loses the ability to compute "uncaptured
   authorizations" or "disputed refunds."
4. **No FX columns.** A warehouse that stores only
   the local-currency amount cannot answer "what
   was our USD revenue?" without an external FX
   lookup at query time, which is slow and
   non-reproducible.
5. **One fact for the payout, none for the
   reconciliation.** The payout fact is fine for
   the *payout* report, but the *reconciliation*
   report needs a ledger fact that records every
   balance change. Candidates who forget the ledger
   get a follow-up question and stumble.

---

## Step 5: Scoring against the rubric

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about transaction definition, MRR scope, dispute lifecycle, multi-currency, payouts. |
| **Picks a grain** | 5/5 | `fact_charge_events` (events), `fact_payouts` (legs), `fact_disputes` (events), plus the ledger. Defended each. |
| **Makes and defends tradeoffs** | 5/5 | BIGINT for money, state machine in events, separate ledger fact for reconciliation, three FX columns. |
| **Talks while drawing** | 5/5 | Narrated every dim, every FK, every measure, every money column. |

---

## In the interview, you would say...

> "Money is `BIGINT` minor units, never float. The
> charge is a state machine that lives in
> `fact_charge_events`, not as a column on
> `dim_charge` — every transition is a row, and the
> current status is the most recent event. A charge
> and a payout are not one-to-one; payouts are
> *batches* of charges net of fees, and
> reconciliation needs a separate ledger fact
> `fact_balance_ledger` that records every balance
> change. For multi-currency, I store the original
> amount *and* two USD conversions — one at
> charge-time FX, one at payout-time FX — so GMV
> reports and cash-collected reports pick the
> column that matches their definition."

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
