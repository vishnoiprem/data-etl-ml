# Meta L6 Onsite Mock - Round 1 (Greet) & Round 2 (Sr Ownership)

**Role:** L6 AI-Native Data Engineer (Full Stack) - Meta
**Total Time:** 45 mins (15 + 30)
**Focus:** Pitch, L6 signals, ownership beyond scope, STAR stories

---

## ROUND 1: Greet (15 mins) - HM / Recruiter

**Goal:** Can you pitch in 2 mins? Are you L6? Do you want this team?

---

### Q1: Tell me about yourself in 2 mins (They time you)

**BAD Answer (E5 - Rejected):**

> "I have 6 years DE, worked on pipelines, Spark, Python, did RAG project..."

**L6 HIRE Answer (Use this exact):**

> "I'm a DE with 6 years, last 2 years focused on AI-native data platforms. I built APEX-RAG Omni - sovereign RAG platform designed for 100M docs, not demo. Frontend: Next.js with virtualized 1k-row trace reviewer, cursor pagination O(1) not OFFSET, optimistic feedback. Backend: 10-shard Qdrant cluster, hybrid BM25+vector, Flink CDC 5-min freshness, dual-write shadow index for embedding model upgrades. Omni layer: one API serves 3 domains HR/Tech/Product with separate prompt templates and grounded evidence_json to prevent hallucination. I built eval harness Recall@8 0.89, nDCG 0.91, LLM-as-judge grounded rate 96%. Last role I owned latency spike 400ms->2.5s after model upgrade, built dashboard by model_version+shard, added alert, wrote runbook. Looking for Staff scope where I own data + AI quality end-to-end."

**Why Hire:** 2 mins, metrics, ownership, Staff keywords: sovereign, cursor O(1), dual-write, grounded, eval harness.

---

### Q2: Why Meta? Why this AI-Native DE Full Stack team?

**L6 Answer:**

> "Two reasons: 1. Scale - Meta has 1B traces/day, 100M docs is real here, not toy. My APEX-RAG design with 10 shards and cursor pagination was built for this scale, tutorial OFFSET would OOM. 2. AI-native DE is new - DE + AI eval together. Most companies treat RAG as LLM call, I treat as data platform with traces table partitioned by day, feedback gold dataset, prompts versioned SCD2. This team owns both."

---

### Q3: Walk me through APEX-RAG Omni in 3 mins - what was hardest?

**L6 Answer:**

> "Hardest was 100M scale + freshness. 100M docs = 1B chunks. I did 3 things: SHA256 dedup check Postgres before embedding - saved 30% cost $130k. 10-shard Qdrant by hash(doc_id)%10, 10M/shard. Freshness: Flink CDC listens doc_updated, only re-embeds changed chunks, not full doc, 5-min SLA. Second hardest was eval - how to know RAG is good? I built traces table + feedback with thumbs up/down, corrected_answer where thumbs_down becomes gold dataset for LLM-as-judge checking groundedness. Satisfaction 73.2% to 89% after fixing chunk_strategy per collection."

---

### Q4: What are you looking for in next role?

**L6 Answer:**

> "Staff scope: own data + AI quality end-to-end, not just pipelines. I want to own latency, cost, satisfaction. In APEX-RAG I owned p95 420ms, cost $0.0042/query, Recall@8. Looking for team where I can define metrics, build runbooks, influence ML + DE together."

---

### Q5: Do you have questions for me? (Ask this - L6 signal)

> "Two: 1. How does team measure RAG quality today - Recall@K or just thumbs up? 2. What is biggest pain - freshness, hallucination, or cost at 100M scale?"

---

### Greet Score: If you pitched under 2 mins with metrics = pass.

---

## ROUND 2: Sr Ownership (30 mins) - Most important for L6

**Goal:** Did you own something WITHOUT being asked? Did you prevent recurrence? L6 = ownership beyond your team.

**Format:** 2-3 stories, STAR, 10 mins each. Interviewer probes.

---

### Q1: Tell me about time you owned a broken system no one owned. (They WILL ask this)

**STAR - Use Latency Spike Story:**

**S - Situation (30 sec):**

> "In APEX-RAG Omni, after embedding model upgrade v1->v2, p95 latency 400ms->2.5s, satisfaction 73%->45%, cost $0.0042-> $0.012. Oncall page. No owner - ML said infra, infra said model. 500 users impacted, trace reviewer timing out."

**T - Task (15 sec):**

> "I was DE, not oncall, but I owned. No one asked. My task: bring latency back to <500ms and prevent recurrence."

**A - Action (4 mins - This is what they score):**

> "Action 1 - Immediate: Rolled back to v1, latency back to 400ms in 10 mins.
>
> Action 2 - Root cause: Found HNSW ef_search 128->16 misconfigured in Qdrant, plus hot shard - 3M docs in shard 0 vs 10M avg because hash imbalance. I queried ClickHouse traces partitioned by day, GROUP BY shard_id, found skew.
>
> Action 3 - Fix: Fixed HNSW config, rebalanced shards by hash, added Flink job to monitor shard size.
>
> Action 4 - Prevent recurrence (L6 bar): Built dashboard tracking latency by model_version + shard + collection, alert p95>600ms. Wrote runbook for model upgrade: 1. Create shadow collection, 2. Spark backfill dual-write, 3. Dual-read 1% for eval Recall@8 + nDCG, 4. Cutover only if satisfaction >70%. Added gold dataset check with LLM-as-judge grounded rate."

**R - Result (30 sec):**

> "Result: Latency 420ms p95, satisfaction back to 73%, cost $0.0042. Dashboard caught 2 future regressions before users. Runbook used by 3 teams. I presented in eng review, made it standard for embedding upgrades."

**Probe they will ask:** "What would you do differently?"

> "Add canary - 1% traffic to shadow index first, not 100% cutover. I learned."

**Hire Signal:** You owned without being asked, rolled back, root caused, prevented with dashboard + runbook + dual-write.

---

### Q2: Tell me about time you had to make decision with incomplete data / ambiguous problem "Make RAG better"

**STAR:**

**S:** "PM said 'Make RAG better' - no metric, no definition of better."

**T:** "Define what better means and build eval first, not code."

**A:** "I defined 3 metrics before coding:
1. Business: satisfaction thumbs_up rate from feedback table
2. Retrieval: Recall@8 + nDCG@8
3. Generation: LLM-as-judge grounded rate using evidence_json

Built traces table day-partitioned, feedback table with corrected_answer. Ran eval: Recall 0.71, satisfaction 52%. Found root cause: chunk_strategy 256 tokens too small for tech docs that need code context. Changed per collection: hr 256, tech 512+50 overlap, product 1024. Added hybrid BM25+vector + Cohere rerank Top8. Added grounded generation with evidence_json - if not in evidence, say 'Not found'."

**R:** "Recall 0.71->0.89, satisfaction 52%->73%, grounded rate 96%. Defined gold dataset = feedback where thumbs_down + corrected_answer. Now team uses same metrics."

**L6 Signal:** You defined metrics before solution, built eval harness.

---

### Q3: Tell me about conflict - DE says ML embeddings bad, ML says DE chunks bad

**STAR:**

**S:** "DE team said chunks bad, ML said embeddings bad, 2 weeks blame, Recall stuck 0.71."

**T:** "Break deadlock with data, not opinion."

**A:** "I built eval harness that isolates: Tested same chunks with 3 embedding models - Recall same 0.71, so not embedding. Tested same embedding with 3 chunk strategies 256/512/1024 - Recall 0.71/0.89/0.84. Proved chunks. Then influenced both teams to adopt per-collection chunk_strategy. Built dashboard showing Recall@8 by collection + chunk_strategy, made it visible."

**R:** "Conflict resolved, Recall 0.89, adopted as standard. I facilitated joint review, not escalation."

---

### Q4: Tell me about time you influenced without authority

**Answer:** Use same story - you had no authority over ML team but influenced with eval data dashboard.

---

### Q5: Tell me about failure

**STAR:**

**S:** "First version of APEX-RAG I used OFFSET pagination for traces."

**T:** "Failed at 100k traces - query timed out 30 sec."

**A:** "Learned OFFSET scans N rows O(N) OOMs on 1B rows. Fixed to cursor pagination WHERE trace_id < :cursor using index (day, trace_id) O(1). Added virtualized list react-window. Wrote ADR doc why cursor."

**R:** "Now handles 1B traces, p95 420ms. Failure taught me to design for 100M scale day 1."

---

## Final Checklist

### Greet 15m

- [ ] 2-min pitch with metrics (400ms, 10 shards, Recall@8 0.89) - no rambling
- [ ] Say "cursor O(1) not OFFSET O(N)" once
- [ ] Ask 2 smart questions about team metrics

### Ownership 30m

- [ ] 3 STAR stories ready: Latency spike (ownership), Make RAG better (ambiguity), Chunk vs embedding conflict (influence)
- [ ] Each story has metrics: latency 400->2500->420ms, Recall 0.71->0.89, satisfaction 73%
- [ ] Each story ends with "prevented recurrence with dashboard + runbook + gold dataset"
- [ ] Say "owned without being asked" - L6 keyword

**Mistake that fails L6:** Saying "I was asked to fix" - must be "No owner, I owned without being asked"

---

## Up Next: Round 3 - Sr Tech Design 60m (PYMK + time-travel + bounded fanout)

Ready when you are.
