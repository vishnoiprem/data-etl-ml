# Lesson 22: Data quality

> **Week 5 · Day 22 · 90 min**
> **Deliverable:** A data quality scorecard per domain and per source.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Data quality is the most-claimed and least-measured property in enterprise data. The CDO who can measure it — and show the trend — is the CDO who earns trust.

The 6 dimensions of data quality:

| Dimension | Question | Example metric |
|---|---|---|
| **Accuracy** | Is the value correct? | % of rows that match a known source of truth |
| **Completeness** | Are all expected values present? | % null in required columns |
| **Consistency** | Do values agree across systems? | % of customers with the same email in CRM and orders |
| **Freshness** | Is the data current? | Hours since last update |
| **Uniqueness** | Are there unintended duplicates? | Duplicate key rate |
| **Validity** | Do values conform to the schema? | % of rows passing schema validation |

The data quality scorecard is the operational artifact. It has:

- 1 row per source system (or per dataset)
- 1 column per dimension
- A trend (week-over-week, month-over-month)
- An owner (the BU head or source-system owner)
- A threshold (the SLO)

The single biggest mistake is to **measure without a threshold**. "We have 99% completeness" is meaningless without "the SLO is 99.5%." A scorecard without thresholds is a thermometer without a fever line.

The second biggest mistake is to **not have an owner**. A scorecard row with no owner is a row that nobody fixes. The scorecard is an accountability tool, not just a measurement tool.

The third biggest mistake is to **set thresholds too high at the start**. 99.99% is unachievable for most data. Set the SLO at the level the business needs (e.g., 99.5% for the financial close), then tighten over time.

## 🛠️ Build It

**Spec:** Build a data quality scorecard for the retailer's top 10 source systems.

**Acceptance:**
- 10 source systems × 6 dimensions
- Threshold (SLO) per dimension per source
- Owner per source
- Trend (current vs. last month)
- 1 paragraph on the scorecard cadence

**Starter:** Start with the 5 most-critical sources (orders, customers, inventory, payments, products). Add the next 5 after.

**Solution (data quality scorecard, abridged):**

| Source | Accuracy | Completeness | Consistency | Freshness | Uniqueness | Validity | Owner |
|---|---|---|---|---|---|---|---|
| Orders | 99.5% | 99.9% | 99.0% | <1h | 99.99% | 99.9% | VP Merch |
| Customers | 99.0% | 99.5% | 98.0% | <4h | 99.5% | 99.5% | CMO |
| Inventory | 99.9% | 99.9% | 99.5% | <15m | 99.99% | 99.9% | COO |
| Payments | 99.99% | 99.99% | 99.9% | <5m | 99.99% | 99.99% | CFO |
| Products | 99.9% | 99.9% | 99.5% | <24h | 99.99% | 99.9% | VP Merch |
| ... 5 more | | | | | | | |

**Cadence:** Daily automated checks (dbt tests + Monte Carlo). Weekly review with data engineering. Monthly review with the data council.

**SLOs:** Tighten by 0.1-0.5% per quarter. Track on a single dashboard.

## 🏛️ Architect Notes

- **Trade-off:** Coverage vs. depth. 100 sources × 6 dimensions = 600 cells. Prioritize: 5 critical sources × 6 dimensions = 30 cells done well beats 600 cells half-done.
- **Capacity / cost:** Data quality tooling (Monte Carlo, Soda, Great Expectations) costs $50-300K/year for mid-market. Below that, build in-house.
- **When NOT to use:** Don't measure quality on data the business doesn't use. The scorecard should be the data the BU relies on for decisions.
- **Production checklist:**
  - [ ] 6 dimensions named
  - [ ] Source systems × dimensions
  - [ ] Threshold (SLO) per cell
  - [ ] Owner per source
  - [ ] Trend
  - [ ] Cadence named

## 🌙 Reflect

- Which source would the CISO push hardest on? Pre-write the answer.
- Which dimension is the weakest in your current org? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 23 — Security and privacy.