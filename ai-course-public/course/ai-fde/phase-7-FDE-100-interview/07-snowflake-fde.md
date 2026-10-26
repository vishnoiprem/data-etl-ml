# Snowflake — Field CTO / Solution Engineering FDE

## Company Snapshot
- **HQ**: Bozeman, MT / SF
- **Team Size**: ~400+ Field CTO / Solution Engineering FDEs
- **Comp**: Base $180K–$230K; TC $280K–$500K
- **What they deploy**: AI Data Cloud; Cortex AI integrations
- **Travel**: 30–50%

## Interview Process
1. Recruiter screen
2. SQL screen (Snowflake-flavored — VARIANT, semi-structured, window fns)
3. Data engineering design
4. Loop
   - Coding (SQL + Python)
   - Snowflake architecture
   - AI deployment scenario with Cortex
   - Customer scenario (sales / business)
   - Bar-raiser

---

## ✅ SUCCESS STORIES

### Snowflake SQL
**Q:** *"Given a `raw_logs` table with VARIANT column `payload`, write a query that finds the 10 users with the highest LTV in the last quarter, where LTV is `SUM(payload:totals:revenue)` over customers who paid ≥ 3 times."*
**A (winner):**
```sql
WITH p AS (
  SELECT
    payload:user_id::STRING AS user_id,
    payload:totals:revenue::NUMBER(18,2) AS revenue,
    DATE_TRUNC('quarter', ts) AS qtr
  FROM raw_logs
  WHERE ts >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
),
paid_users AS (
  SELECT user_id, COUNT(*) AS n_payments, SUM(revenue) AS ltv
  FROM p GROUP BY user_id HAVING COUNT(*) >= 3
)
SELECT user_id, ltv FROM paid_users ORDER BY ltv DESC LIMIT 10;
```
Then: *"I'd add `_RESERVED` micro-partitions + clustering on `ts` for scan efficiency on bigger scales. Also Cortex Search would let customer ask LLM-y follow-ups on this."*
**Why it worked:** Comfortable with Snowflake-isms (VARIANT, ::cast, DATE_TRUNC), then production concerns + product cross-sell.

---

### Architecture
**Q:** *"A retailer wants to consolidate 4 BI tools onto Snowflake + Cortex. Design the data share + governance model."*
**A (winner):**
- **Data layers**: raw → curated → consumption.
- **Snowflake features**:
  - Secure Data Sharing for the supply-chain partner (no ETL, no copy).
  - Row Access Policies + Dynamic Data Masking for PII.
  - Horizon Catalog for governance.
  - Cortex for natural-language BI.
- **Network**: a single account with multiple databases, or per-BU accounts with data shares between them.
- **Rollout**: 4-week PoC on 1 BI tool, expand in 12-week phases.
**Why it worked:** Knows Snowflake-native primitives (Secure Shares, Horizon Catalog), structured rollout, knows where Cortex fits.

---

## ❌ REJECTION STORIES

### SQL
**Q:** *"Find the second-highest salary per department."*
**A (loser):** `SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1` — global second, not per department.
**Why it failed:** Missed the "per department" part; classic interview trap.
**What they should have said:** Use DENSE_RANK() window function partitioned by department, filter rnk = 2.

---

### Architecture
**Q:** *"Customer complains Cortex is hallucinating."*
**A (loser):** *"Switch to a different LLM."*
**Why it failed:** Same mistake as Scale AI rejection — didn't root-cause.
**What they should have said:** Build an eval set, categorize the misses, ship a retrieval/citation fix, add a guardrail, iterate.

---

## 📚 Reading List
1. Snowflake docs — Cortex AI, Snowpark, Secure Data Sharing
2. *"The Snowflake Cookbook"* (O'Reilly, free excerpts)
3. Snowflake Summit session recordings (YouTube)
4. r/snowflake threads
5. levels.fyi Snowflake FCTO debriefs
