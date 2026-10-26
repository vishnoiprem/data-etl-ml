# Meta L6 Loop 2 - Tech Lead Review (100 Points + Q&A Addendum)

**Reviewer:** Sr Tech Lead (Meta L7 equivalent)
**Reviewed:** All 5 rounds of Loop 2 mock prep
**Validation:** 100 review points, simplified jargon, real interview Q&A added

---

## How to Use This Document

- **Part 1:** 100 review points (what tech lead validates, simplified)
- **Part 2:** Glossary (jargon -> plain English)
- **Part 3:** Real interview Q&A addendum (15 extra questions + L6 answers)

---

# PART 1: 100 TECH LEAD REVIEW POINTS

## Section A: Greet Round (15 min) - 20 Points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 1 | 2-min pitch length | Under 2 min, not 3 min | You stop at 2:00 |
| 2 | Metrics in pitch | Numbers: 400ms, 10 shards, 0.89 | At least 3 concrete numbers |
| 3 | No "um/uh" filler | Smooth delivery | Rehearse 5x out loud |
| 4 | AI-Native DE narrative | Why you switched from pure DE | Clear pivot story (4yr -> 2yr) |
| 5 | "I built X for 100M scale" | Scale keyword used | 100M or 1B mentioned |
| 6 | "Eval harness" mention | You measure AI quality | Recall@8 or grounded rate said |
| 7 | "Cursor pagination O(1)" | Senior DE signal | Once is enough, not 5x |
| 8 | "Dual-write shadow" | Production pattern | Mentioned once in pitch |
| 9 | No "I worked on a team" | Use "I" not "we" | 80% "I" statements |
| 10 | "Staff scope" asked | L6 wants L7 next | Mentioned once |
| 11 | Why Meta = Scale | 1B traces/day real here | Specific number |
| 12 | Why Meta = AI-native DE | New team, both skills | Unique angle |
| 13 | Hardest decision = Qdrant vs ES | Real tradeoff shown | Latency 1.2s vs 320ms |
| 14 | Weakness = over-own | Honest + growth | Now delegate |
| 15 | Weakness = real example | Latency spike story | Concrete metric |
| 16 | Growth in weakness | "Now I scale via delegation" | Forward-looking |
| 17 | Ask 2 smart questions | Recall@K or thumbs up? | Team quality metric |
| 18 | Question 2 = pain point | Freshness vs cost vs hallucination | Shows you think ahead |
| 19 | No salary question | Wait for recruiter | Save for later |
| 20 | Thank interviewer | Polite close | Always do this |

---

## Section B: AI-Native DE Full Stack (60 min) - 20 Points

### Data Modeling (0-15m) - 5 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 21 | gold_dataset table | PK gold_id, FK trace_id | Drawn on whiteboard |
| 22 | pii_scrub_log table | Audit trail | Original + scrubbed both kept |
| 23 | fine_tuning_jobs table | Versioning model | model_version field |
| 24 | fine_tuning_examples table | Prompt + completion | evidence_json in prompt |
| 25 | pii_types ARRAY | Multi-PII support | email, ssn, phone in array |

### Pipeline Design (15-30m) - 5 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 26 | Flink listens feedback | Real-time trigger | thumbs_down + corrected_answer |
| 27 | PII scrubber first | Before anything else | Presidio + regex named |
| 28 | LLM-as-judge for quality | Data quality check | Grounded rate >90% |
| 29 | 80/20 train/eval split | Standard ML split | Mentioned explicitly |
| 30 | Shadow 1% traffic | Safe rollout | dual-write pattern |

### SQL (30-45m) - 5 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 31 | Cost per job SQL | Aggregates correct | COUNT * 0.0042 |
| 32 | PII leak rate SQL | Regex check | ~* operator used |
| 33 | Hallucination detection SQL | LLM-as-judge function | grounded_score < 0.5 |
| 34 | JOIN fine_tuning_jobs | Correct foreign key | job_id join |
| 35 | ORDER BY created_at DESC | Recent first | Used in queries |

### Coding (45-60m) - 5 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 36 | PII scrubber compiled | No syntax errors | Runs in interview |
| 37 | Tuple return type | (scrubbed, pii_found) | Both values returned |
| 38 | Regex patterns correct | Email, SSN, phone | Standard patterns |
| 39 | Semantic cache class | LRU eviction | OrderedDict used |
| 40 | Cache stats method | Hit rate tracked | hits/total returned |

---

## Section C: Sr Tech Design (60 min) - 20 Points

### Requirements (5m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 41 | 100M code files | Scale named | 100M or 1B chunks |
| 42 | 500M users | User scale | Mentioned once |
| 43 | ACL private repos | Privacy concern | "team only" said |
| 44 | Time-travel semantics | 3 use cases asked | training/debug/backfill |

### Data Model (10m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 45 | code_files SCD2 | valid_from/valid_to | Both columns |
| 46 | code_chunks with line numbers | start_line, end_line | For citations |
| 47 | repos with is_private | ACL starts here | BOOL field |
| 48 | repo_acl table | Per-user permission | read/write enum |

### Architecture (25m) - 8 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 49 | Git commit webhook | Event-driven ingest | Kafka commit_event |
| 50 | **AST parser chunking** | Not 512 tokens | Function/class chunks |
| 51 | Code embedding model | CodeBERT/StarCoder | Named model |
| 52 | 20 shards by hash | hash(repo_id) % 20 | 5M files per shard |
| 53 | ACL filter BEFORE LLM | Cost optimization | Said explicitly |
| 54 | evidence_json with file:line | Citations | Format shown |
| 55 | "Not found" fallback | No hallucination | If not in evidence |
| 56 | Time-travel via SCD2 | Replay snapshots | valid_from/to query |

### Scale (5m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 57 | 1B chunks math | 100M files * 10 chunks | Stated |
| 58 | 50M per shard | 1B / 20 shards | Math shown |
| 59 | ACL saves LLM cost | Filter before inference | Cost reason given |
| 60 | Team_id in Qdrant payload | Multi-tenant | tenant_id field |

---

## Section D: Sr Ownership (30 min) - 20 Points

### ES->Qdrant Migration Story - 12 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 61 | S: Cost problem | $50k/month ES | Number stated |
| 62 | S: Latency problem | 1.2s p95 | Number stated |
| 63 | T: Zero downtime | Constraint stated | Explicit |
| 64 | T: Zero data loss | Constraint stated | Explicit |
| 65 | A: Dual-write via Kafka | Real-time sync | docs_v2_shadow |
| 66 | A: Spark backfill | Batch catchup | 10M docs verified count |
| 67 | A: Shadow 1% read | Compare metrics | Recall@8 vs |
| 68 | A: Qdrant 0.89 vs ES 0.82 | Numbers | Stated |
| 69 | A: 7-day stability window | No flapping | Days stated |
| 70 | A: 2-week ES backup | Rollback window | 2 weeks |
| 71 | A: Feature flag rollback | 5 min rollback | prompt_version flag |
| 72 | R: Latency 1.2s -> 420ms | Win metric | 65% reduction |

### PM Disagreement Story - 8 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 73 | S: PM wanted Flink real-time | PM position stated | 5-min freshness |
| 74 | S: Cost 10x higher | $130k vs $12k | Numbers |
| 75 | T: Push back with data | Not opinion | Data-driven |
| 76 | A: Cost model built | Showed PM | 10x cost / 24hr vs 5min |
| 77 | A: 95% use case batch | Compromise | Premium tier Flink |
| 78 | A: Saved $118k/year | Real number | Calculated |
| 79 | R: PM thanked later | Outcome | Relationship intact |
| 80 | R: Shipped v1 batch | Speed to market | Done |

---

## Section E: Full Stack (60 min) - 20 Points

### API Design (0-10m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 81 | POST /compare endpoint | RESTful | Method + path |
| 82 | prompt_versions array | Multiple versions | []v1.2.0, v1.3.0-beta |
| 83 | Returns results array | Parallel results | Per version |
| 84 | Each result has grounded bool | Quality flag | true/false |

### Side-by-side UI (10-35m) - 8 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 85 | useState for versions | React state | versions array |
| 86 | Loading state | UX feedback | loading bool |
| 87 | Grid 2-column layout | Side-by-side | grid-cols-2 |
| 88 | v1.2.0 panel (left) | Control | "control" label |
| 89 | v1.3.0-beta panel (right) | Candidate | "candidate" label |
| 90 | Latency displayed | Metric shown | ms unit |
| 91 | Grounded shown | Quality flag | yes/no |
| 92 | Pick winner button | Action | per panel |

### Winner + Gold Dataset (35-50m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 93 | POST /api/feedback/compare | Save feedback | Method shown |
| 94 | winner_version + loser_version | Both stored | Both fields |
| 95 | comparison_id for tracking | Audit | UUID/link |
| 96 | Optimistic UI update | setWinner | No reload |

### Polish (50-60m) - 4 points

| # | Point | What TL Validates | Pass Criteria |
|---|-------|-------------------|---------------|
| 97 | Diff view between answers | Visual diff | Token diff |
| 98 | Stats footer | Aggregate metrics | satisfaction, p95, Recall |
| 99 | v1.3.0 wins shown | Conclusion | Decision support |
| 100 | Link to Round 2 gold dataset | Cross-round integration | "feeds fine-tuning" |

---

# PART 2: GLOSSARY (Jargon -> Plain English)

| Jargon | Plain English |
|--------|---------------|
| **SCD2** | A table that keeps every old version of data, so you can ask "what did this look like on Jan 15?" |
| **Dual-write** | Write the same data to two places (old system + new system) at the same time, so nothing breaks |
| **Shadow index** | A second copy of your data that you test on, without affecting real users |
| **1% canary** | Send 1% of users to the new version first, watch for errors, then roll out to everyone |
| **Bounded fanout** | Only look at a fixed number of friends (500), not ALL friends, to avoid running out of memory |
| **HNSW** | A fast way to search vectors (like Google search but for AI numbers), O(log N) instead of O(N) |
| **BM25** | Old-school keyword search (like Ctrl+F but smarter), used together with vector search |
| **Hybrid search** | Mix keyword search (BM25) + AI search (vectors) - get best of both |
| **Rerank** | Take top 50 results, use a smarter model to pick best 20 - like a second round of judging |
| **Grounded generation** | LLM only answers using facts you gave it, refuses to make stuff up |
| **evidence_json** | A box of source documents/citations passed to the LLM, so it can prove its answer |
| **LLM-as-judge** | Use one AI to grade another AI's answer (cheap quality check) |
| **Gold dataset** | Hand-picked examples that are "definitely correct", used to test your AI |
| **Recall@K** | Out of all correct answers, how many did we find in top K results? (0 to 1) |
| **nDCG@K** | Are the correct answers ranked higher? (0 to 1, higher = better) |
| **AST parser** | Reads code like a human, understands functions/classes, splits code by meaning not size |
| **ACL** | Access Control List - who is allowed to see this data (e.g., only your team) |
| **p95 latency** | 95% of requests finish in this time, 5% are slower (used as SLO) |
| **Shadow read** | 1% of queries also read from the new system to compare, but answer comes from old system |
| **Cutover** | Switch from old system to new system completely |
| **Recall@8 0.89** | 89% of correct answers found in top 8 results |
| **Runbook** | Step-by-step doc for fixing a problem (like a recipe) |
| **Qdrant** | Open-source vector database (stores AI embeddings for fast search) |
| **Flink CDC** | Real-time data pipeline that watches for changes (e.g., new doc added) and processes them in seconds |
| **Cursor pagination** | Get next page by saying "give me items after this last ID" - O(1), not slow like OFFSET |
| **OFFSET pagination** | Get next page by saying "skip first 1000 rows" - slow on big data, scans all skipped rows |
| **Optimistic UI** | Show result immediately, fix if it fails (faster UX) |
| **TAO** | Meta's internal database for social graph (friends, likes, etc.) - you don't use it directly, but know it exists |
| **PII** | Personally Identifiable Info (email, SSN, phone) - must scrub before training AI |
| **Presidio** | Microsoft's PII detection tool |
| **Inverse Propensity Scoring (IPS)** | Math to remove bias from logged data when you want to know "what if we showed X?" |

---

# PART 3: REAL INTERVIEW Q&A ADDENDUM (15 Extra Questions)

These are questions interviewers ACTUALLY ask in L6 loops, not covered in your 5 rounds.

---

### Q1: "How would you reduce hallucination in a RAG system by 50%?"

**L6 Answer:**

> "Three things, in order of cost:
>
> 1. **Grounded generation with evidence_json** (free): LLM only answers from passed chunks, refuses if not in evidence. Reduced hallucination 30% in my APEX-RAG.
>
> 2. **Better retrieval = fewer hallucinations** (medium cost): Hybrid BM25+vector, rerank with Cohere, per-collection chunk_strategy. If you retrieve the right chunks, LLM can't hallucinate. Reduced 40%.
>
> 3. **LLM-as-judge guardrail** (high cost): After LLM answers, second LLM checks "is answer in evidence_json?" If no, return "Not found". Reduced 50%+ when combined.
>
> I'd ship 1+3 first (low cost, high win), then 2."

---

### Q2: "Design a rate limiter for 100K QPS"

**L6 Answer:**

> "Token bucket per user, Redis-backed.
>
> - **Algorithm:** Token bucket, 100 tokens/min refill, burst 200.
> - **Storage:** Redis with TTL, key = `rate:{user_id}`, value = tokens_left + last_refill_ts.
> - **Atomicity:** Lua script for `get + decrement` (no race).
> - **Failure mode:** If Redis down, fail open (allow request) - rate limit should never break the product.
> - **Scale:** 100K QPS, Redis cluster 10 shards, ~10K QPS per shard, well within limits.
> - **Edge case:** Bot users get 10 tokens/min, premium users 1000/min."

---

### Q3: "Your pipeline is 6 hours late. Walk me through debugging."

**L6 Answer:**

> "Step 1: Check Spark UI - is it slow shuffle, GC, or data skew?
> Step 2: ClickHouse query: `SELECT stage, AVG(duration) FROM pipeline_runs WHERE date=today GROUP BY stage` - find the slow stage.
> Step 3: Check upstream - did input data grow 10x? `SELECT COUNT(*) FROM input_today vs input_yesterday`.
> Step 4: Check downstream - is consumer backpressure causing backoff?
> Step 5: Fix root cause, not symptom. Add alert `pipeline_lag > 4h` to catch earlier next time."

---

### Q4: "Design a feature store from scratch"

**L6 Answer:**

> "Two tables:
>
> 1. **Online (low latency):** Key-value store, MyRocks/TAO, feature = latest value. Read p99 <5ms.
> 2. **Offline (training):** SCD2 in Hive/Iceberg, partition by day, as-of queries for time-travel.
>
> **Write path:** Stream (Kafka) -> Flink job writes to both online + offline atomically (with version).
>
> **Read path:** Online = get(user_id, feature_name) -> latest. Offline = SELECT FROM features_scd2 WHERE user_id=X AND valid_from <= T AND valid_to > T.
>
> **Schema evolution:** Each feature has feature_version. Old features kept for 1 year for backfill."

---

### Q5: "Tell me about a time you said NO to your manager"

**L6 Answer (PM disagreement story):**

> "PM wanted real-time Flink CDC for v1 RAG freshness 5 min. I said no - cost $130k/month vs $12k batch, 10x for 1% premium use case. Showed cost model, PM agreed, we shipped batch v1 + premium tier Flink. Saved $118k/year, PM later thanked me. Lesson: data > opinion, even with managers."

---

### Q6: "How do you handle PII in a RAG system?"

**L6 Answer:**

> "Three layers:
>
> 1. **Ingestion:** Presidio scrubs email/SSN/phone before embedding. Original kept in secure vault, scrubbed goes to Qdrant.
> 2. **Retrieval:** Don't return chunks with PII markers (Qdrant payload filter `pii_found = false`).
> 3. **Generation:** Prompt template says 'Never include PII in response, even if in evidence'. LLM-as-judge scans for PII in answer, blocks if found.
>
> **Audit:** pii_scrub_log keeps who/when/what was scrubbed, scrubber_version. SOC2 compliant."

---

### Q7: "Design a dead letter queue for failed pipeline tasks"

**L6 Answer:**

> "Kafka topic `dlq.pipelines`, partition by task_id (so retries stay ordered).
>
> - **Payload:** original message + error + retry_count + first_failure_ts.
> - **Retry logic:** Exponential backoff, max 5 retries, then move to `dlq.parked` for manual review.
> - **Alerting:** DLQ depth > 100 in 5 min -> page oncall.
> - **Replay tool:** CLI to redrive from DLQ to original topic after fix.
> - **Schema:** `original_message, error_class, error_msg, retry_count, first_failure_ts, last_failure_ts`"

---

### Q8: "How do you test a data pipeline?"

**L6 Answer:**

> "Four layers:
>
> 1. **Unit:** Test transform functions with sample input/output.
> 2. **Integration:** Test Kafka -> Flink -> sink end-to-end with testcontainers.
> 3. **Data quality:** Great Expectations or Deequ checks - row count, null %, schema, value distributions.
> 4. **Backfill:** Replay historical data, compare output to known-good (golden dataset).
>
> **On production:** Daily DQ report emailed, alert if row count drops >20% or null rate >5%."

---

### Q9: "Design a system to deduplicate 100M documents"

**L6 Answer:**

> "Two-pass:
>
> 1. **Exact dedup:** SHA256(content) -> Postgres unique index. INSERT ON CONFLICT DO NOTHING. Saves 30% in my APEX-RAG ($130k).
> 2. **Near dedup:** MinHash or SimHash on content, LSH (locality-sensitive hashing) to find similar, threshold 0.95 Jaccard. Spark job nightly.
>
> **Storage:** Dedup table `(sha256 PK, doc_id, first_seen, is_exact_dup)`. Near-dup pairs in `near_dup_pairs(from_id, to_id, jaccard)`."

---

### Q10: "Your model went from 0.89 to 0.85 Recall overnight. Debug."

**L6 Answer:**

> "1. Check if dataset changed: `SELECT COUNT(*), COUNT(DISTINCT doc_id) FROM gold_dataset WHERE created_at > yesterday` - new data added?
> 2. Check if embedding model version changed: feature_store.model_version - did someone deploy?
> 3. Check query distribution: `SELECT query, COUNT(*) FROM traces WHERE ts > yesterday GROUP BY query` - new query type?
> 4. Check infra: Qdrant shard health, any shard > 12M docs (skew)?
> 5. Run eval harness against yesterday's model on today's data - if Recall drops, it's data drift.
> 6. If model_version changed, rollback + dual-write shadow for new version."

---

### Q11: "How do you prioritize tech debt vs features?"

**L6 Answer:**

> "Two-bucket prioritization:
>
> 1. **Tech debt that blocks features** = P0 (fix now). E.g., schema migration needed for new feature.
> 2. **Tech debt that slows team** = P2 (next quarter). E.g., refactor Spark job to faster framework.
>
> I use 80/20 rule: 80% features, 20% tech debt. If team velocity drops 2 sprints in a row, swap to 50/50.
>
> **Communication:** Write ADR (Architecture Decision Record) for each tech debt item: cost of fixing now vs cost of delaying. Show PM the data."

---

### Q12: "Design a notification system at Meta scale (1B users)"

**L6 Answer:**

> "**Push (mobile):** 1B devices, batched by APNs/FCM, max 1 push/user/day to avoid spam.
> **In-app:** Kafka topic `notifications`, partitioned by user_id, consumer pushes to TAO, user fetches on app open.
> **Personalization:** Flink job ranks notifications by `user_interest_score`, top 5 shown.
> **Dedup:** Bloom filter on `(user_id, notification_type, day)` to avoid duplicate.
> **Scale:** 1B events/day, ~12K QPS avg, 100K peak. Kafka 100 partitions, consumer group 50 workers.
> **Failure mode:** If push fails, fall back to in-app badge. If all fails, log to `notifications_dropped` for replay."

---

### Q13: "Tell me about a time you mentored someone"

**L6 Answer:**

> "I mentored a junior DE on the APEX-RAG team. I delegated the shadow index backfill Spark job (I owned alone originally, learned to scale). I did pair-programming 2x/week, reviewed their PRs, and gave them ownership of the eval dashboard.
>
> Result: They shipped the backfill in 3 weeks, 0 errors. They grew from 'writes Spark' to 'designs eval harness' in 6 months. Now they own a sub-system.
>
> Lesson: ownership is not hoarding, it's multiplying."

---

### Q14: "How do you handle disagreement with senior engineer?"

**L6 Answer (Chunk vs Embedding story):**

> "DE said chunks bad, ML said embeddings bad, 2 weeks blame.
>
> I built an eval harness that isolated variables: same chunks, 3 embedding models -> Recall same 0.71 (not embeddings). Same embedding, 3 chunk strategies -> Recall 0.71/0.89/0.84 (chunks matter).
>
> Showed both teams the data. Conflict resolved in 1 day, not 2 weeks. Adopted per-collection chunk_strategy as standard.
>
> Lesson: data beats opinion, especially with senior engineers who respect evidence."

---

### Q15: "Why should we hire you over other candidates?"

**L6 Answer (30 sec):**

> "Three reasons:
>
> 1. **AI-Native DE is rare:** Most DEs do pipelines, most MLEs do models. I do both - I built APEX-RAG with traces table, eval harness, feedback loop, PII scrubbing, fine-tuning pipeline. Full stack.
>
> 2. **I leave systems, not just code:** Dashboard + runbook + gold dataset + ADR for every project. 3 teams use my embedding upgrade runbook.
>
> 3. **I scale via delegation:** Over-owning is my weakness, I learned to delegate. I can own a data+AI platform and grow the team.
>
> Bottom line: I ship production AI with quality metrics, not demos."

---

## TL Review Score Summary

| Section | Points | Your Target |
|---------|--------|-------------|
| A. Greet (15m) | 20 | 18+ (90%) |
| B. AI-Native DE (60m) | 20 | 18+ (90%) |
| C. Tech Design (60m) | 20 | 17+ (85%) |
| D. Ownership (30m) | 20 | 18+ (90%) |
| E. Full Stack (60m) | 20 | 17+ (85%) |
| **Total** | **100** | **88+ (88%)** |

**L6 Hire Threshold:** 85+ = strong hire, 90+ = strong hire + bar-raiser.

---

## How to Study This

1. **Day 1:** Read Part 1 (100 points), check off what you have ready. Aim for 80+ on first pass.
2. **Day 2:** Read Part 2 (glossary), make sure you can explain each term in plain English to a junior.
3. **Day 3:** Practice Part 3 (15 Q&A) out loud, 3 min per answer, recorded for self-review.
4. **Day 4 (mock day):** Do full loop 2 with another person, score yourself against the 100-point checklist.

---

## Cross-References

- See `mock_2_LOOP2_FULL_PREP.md` for the 5 rounds in detail
- See `META_ROUND1_GREET_OWNERSHIP.md` for Loop 1 Greet + Ownership
- See `META_ROUND3_TECH_DESIGN.md` for Loop 1 Tech Design (PYMK)

**You're ready. Good luck.**
