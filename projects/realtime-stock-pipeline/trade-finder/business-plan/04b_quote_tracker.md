# Supplier Quote Tracker — Top 3 RFQ

> **Purpose.** Track the RFQ sent to each of the top 3 shortlisted
> suppliers and the quotes that come back. The data below feeds
> directly into the financial model (`03_financial_model.csv`,
> untracked) — when you fill in the quote cells, the model becomes
> accurate enough to commit capital.
>
> **Companion CLI:** `python3 mark_supplier_reply.py "Gold Star" --replied --at 2026-10-15 --via email --notes "Quoted $8.50/500u"`
>
> **Window:** Sent on 2026-10-13. Follow-up on Day 3 (2026-10-16)
> if no reply. Final decision by Day 7 (2026-10-20).

## Summary

| # | Supplier | Alibaba ID | RFQ Sent | Replied | Samples | Verdict |
|---|---|---|:---:|:---:|:---:|---|
| 1 | Shenzhen Gold Star Technology | `goldstar_2010` | 2026-10-13 | — | — | ⏳ Awaiting reply |
| 2 | Shenzhen OCOM Technology | `ocom_2007` | 2026-10-13 | — | — | ⏳ Awaiting reply |
| 3 | Shenzhen Qiyang Technology | `qytech_2014` | 2026-10-13 | — | — | ⏳ Awaiting reply |

## Detail per supplier

### 1. Shenzhen Gold Star Technology Co., Ltd.  (`goldstar_2010`)

- **Composite score:** 8.81 / 10 (rank #1, 86% top-1 finishes)
- **Baseline data:** 500u FOB $8.75, 1000u FOB $7.95, 19-day lead, 100u MOQ, free sample + $30 DHL

| Item | Value (when received) |
|---|---|
| Date sent | 2026-10-13 |
| Date replied | — |
| Reply channel | — |
| Sample policy confirmed | — |
| Quote 100u FOB | — |
| Quote 500u FOB | — |
| Quote 1000u FOB | — |
| Quote 5000u FOB | — |
| Lead time (500u) | — |
| Payment terms | — |
| OEM/ODM MOQ + tooling | — |
| CE / RoHS / UKCA certs | — |
| Trade references | — |
| Sample ordered | — |
| Sample received | — |
| QC test result (7d) | — |
| Notes | — |

### 2. Shenzhen OCOM Technology Co., Ltd.  (`ocom_2007`)

- **Composite score:** 8.62 / 10 (rank #2, 11% top-1 finishes — best response time + biggest team)
- **Baseline data:** 500u FOB $9.10, 1000u FOB $8.40, 18-day lead, 100u MOQ, free sample

| Item | Value (when received) |
|---|---|
| Date sent | 2026-10-13 |
| Date replied | — |
| Reply channel | — |
| Sample policy confirmed | — |
| Quote 100u FOB | — |
| Quote 500u FOB | — |
| Quote 1000u FOB | — |
| Quote 5000u FOB | — |
| Lead time (500u) | — |
| Payment terms | — |
| OEM/ODM MOQ + tooling | — |
| CE / RoHS / UKCA certs | — |
| Trade references | — |
| Sample ordered | — |
| Sample received | — |
| QC test result (7d) | — |
| Notes | — |

### 3. Shenzhen Qiyang Technology Co., Ltd.  (`qytech_2014`)

- **Composite score:** 8.47 / 10 (rank #3, 2.9% top-1 finishes — large factory, strong OEM/ODM)
- **Baseline data:** 500u FOB $8.80, 1000u FOB $7.90, 18-day lead, 100u MOQ, free sample + $25-40 DHL

| Item | Value (when received) |
|---|---|
| Date sent | 2026-10-13 |
| Date replied | — |
| Reply channel | — |
| Sample policy confirmed | — |
| Quote 100u FOB | — |
| Quote 500u FOB | — |
| Quote 1000u FOB | — |
| Quote 5000u FOB | — |
| Lead time (500u) | — |
| Payment terms | — |
| OEM/ODM MOQ + tooling | — |
| CE / RoHS / UKCA certs | — |
| Trade references | — |
| Sample ordered | — |
| Sample received | — |
| QC test result (7d) | — |
| Notes | — |

## Decision rules (after all 3 quote back)

1. **Sample quality is the tiebreaker.** The 5-axis weighted score
   treats sample quality as 25% of the total. If two suppliers are
   within 0.5 points on the composite, choose the one with the
   better sample.
2. **Never pay 100% upfront.** T/T 30% deposit, 70% on B/L copy is
   the floor. Trade Assurance on Alibaba adds a layer of protection.
3. **OEM/ODM tooling cost is a hidden capex.** A $500-1,000 tooling
   fee is fine; $5,000+ on a $7,700 starting capital kills the unit
   economics — negotiate or pass.
4. **Lead time > 25 days = rejected.** Every extra day of lead time
   is a day of stockout risk on Amazon UK. 18-21 days is the band.
5. **If all 3 quotes are within 5%, choose OCOM** (best response
   time + biggest team = lowest long-term risk even at a 3-4%
   higher price).

## Cost-matrix aggregation (for the financial model)

When all 3 quotes are in, summarize here:

| Metric | Gold Star | OCOM | Qiyang | Best |
|---|---|---|---|---|
| 500u FOB (USD) | — | — | — | — |
| 1000u FOB (USD) | — | — | — | — |
| 5000u FOB (USD) | — | — | — | — |
| Lead time (days) | — | — | — | — |
| OEM tooling (USD) | — | — | — | — |
| Sample cost (USD) | — | — | — | — |
| CE / RoHS / UKCA | — | — | — | — |
| Payment terms | — | — | — | — |
| **Weighted score (post-quote)** | — | — | — | **—** |

The financial model (`03_financial_model.csv`, gitignored) reads
this table. Don't commit the CSV — keep this `.md` in git as the
canonical source of truth.
