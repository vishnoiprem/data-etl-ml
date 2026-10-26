# Databricks — Mosaic AI FDE / Solutions Architect

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~600+ FDEs/SAs in Mosaic AI team
- **Comp**: Mid $180K–$220K; Sr $230K–$280K; TC $300K–$500K
- **What they deploy**: Mosaic AI / Lakehouse for F500; on-prem GenAI
- **Travel**: 25–50%

## Interview Process
1. Recruiter
2. SQL + Python coding screen (Databricks flavored)
3. Data engineering system design
4. On-site / loop
   - Coding 2
   - Lakehouse / data architecture case
   - GenAI deployment scenario
   - Customer scenario (with GTM SE)
   - Bar-raiser

---

## ✅ SUCCESS STORIES

### SQL round
**Q:** *"Given event logs table (user_id, event, ts), find the top-3 pages by conversion rate from page_view → purchase in the last 30 days."*
**A (winner):**
```sql
WITH pv AS (
  SELECT user_id, ts, JSON_EXTRACT(properties, '$.page') AS page
  FROM events WHERE event = 'page_view' AND ts > current_date - INTERVAL 30 DAYS
),
p AS (
  SELECT user_id, MIN(ts) AS first_buy_ts FROM events
  WHERE event = 'purchase' AND ts > current_date - INTERVAL 30 DAYS
  GROUP BY user_id
)
SELECT pv.page,
       COUNT(DISTINCT pv.user_id) AS viewers,
       COUNT(DISTINCT p.user_id) AS buyers,
       COUNT(DISTINCT p.user_id) * 1.0 / COUNT(DISTINCT pv.user_id) AS conv
FROM pv LEFT JOIN p ON pv.user_id = p.user_id
GROUP BY pv.page ORDER BY conv DESC LIMIT 3;
```
Then: *"In a real customer scenario I'd also segment by traffic source and bot-filter. Also 'conversion' here is naive — we'd usually use an attribution window."*
**Why it worked:** Working SQL with proper window logic, then production caveats. Databricks interviewers love "this is what I'd actually ship."

---

### Data architecture case
**Q:** *"A bank wants to deploy an AI risk model on top of Databricks. Their data lives in 12 systems. Design the medallion architecture."*
**A (winner):**
- **Bronze**: raw ingestion via Auto Loader from each system, schema-on-read, full history.
- **Silver**: conformed entities (Customer, Account, Transaction), PII tokenized, change-data-capture applied.
- **Gold**: feature tables for the model, with Unity Catalog governing access.
- **Model serving**: registered in MLflow, deployed via Mosaic AI Model Serving, monitored with Lakehouse Monitoring.
- **Governance**: row-level + column-level access by line of business.
**Why it worked:** Used Databricks-native concepts (Unity Catalog, Auto Loader, MLflow, Mosaic AI Model Serving). Showed they actually use the product.

---

### GenAI deployment
**Q:** *"Customer wants a RAG chatbot on their 5M contracts."*
**A (winner):** *"I'd propose: ingest contracts into a Delta table, chunk + embed with a Databricks-hosted embedding model, store vectors in Mosaic AI Vector Search, retrieve top-K per query, prompt-engineer the LLM with a strict citation requirement. Then I'd ship an evaluation notebook in week 1 with 50 hand-labeled Q&A so we can measure retrieval recall + answer correctness."*
**Why it worked:** Used the Databricks-native stack end-to-end.

---

## ❌ REJECTION STORIES

### SQL
**Q:** *"Write a query to detect duplicates."*
**A (loser):** `SELECT col, COUNT(*) FROM t GROUP BY col HAVING COUNT(*) > 1` — without addressing *which* rows to keep, no concept of dedup strategy.
**Why it failed:** Surface answer, no depth on dedup windows, deterministic tiebreakers, or merge logic.
**What they should have said:** Use ROW_NUMBER() with a PARTITION BY + ORDER BY tiebreaker; discuss fuzzy vs exact deduplication; discuss CDF (Change Data Feed) for downstream.

---

### GenAI scenario
**Q:** *"Customer wants to fine-tune Llama on their internal docs."*
**A (loser):** "Sure, we'll use the fine-tuning API."
**Why it failed:** Didn't address data prep, eval-first, instruction format, model selection (full FT vs LoRA vs continued pretraining), cost, hosting.
**What they should have said:** I'd start with retrieval-only RAG, ship, measure, *then* fine-tune as a phase 2 if retrieval is the bottleneck. Fine-tuning last.

---

## 📚 Reading List
1. Databricks docs — Lakehouse, Unity Catalog, Mosaic AI
2. *"Production RAG on Databricks"* (Databricks blog)
3. MLflow + Mosaic AI deployment guides
4. *"Lakehouse Architecture in 2025"* (free Databricks ebook)
5. r/dataengineering threads
6. levels.fyi Databricks Solutions Architect reviews
