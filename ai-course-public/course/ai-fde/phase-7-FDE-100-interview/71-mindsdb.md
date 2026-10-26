# MindsDB — FDE (Open-Source AI Database)

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~20–40
- **Comp**: $150K–$210K; TC $230K–$380K
- **What they deploy**: Open-source AI-database FDEs (MindsDB + LLMs)
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium + SQL)
3. AI-database design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### AI-database case
**Q:** *"Customer wants to query their warehouse with natural language."*
**A (winner):** *"MindsDB + SQL generation against their warehouse schema (Snowflake / BigQuery). Schema-aware prompting + retrieval. Eval: 200 hand-labeled natural-language → SQL queries. Pilot: 1 team, 30 days."*
**Why it worked:** Right NL-to-SQL framing with MindsDB.

---

## ❌ REJECTION STORIES
### NL→SQL
**Q:** *"Query is wrong."*
**A (loser):** "Better prompt."
**What they should have said:** *"Add schema context, column descriptions, few-shot examples. Validate queries before running (dry run + EXPLAIN). Use semantic layer."*

---

## 📚 Reading List
1. MindsDB docs (mindsdb.com)
2. NL2SQL papers (Spider, BIRD)
3. r/dataengineering
4. levels.fyi MindsDB