# QUICK REFERENCE - Day of Interview Cheat Sheet
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)

---

## 🎯 YOUR CORE NARRATIVE (Memorized)
> "I'm a Data & Analytics Lead with 7 years taking customers from legacy Hadoop/Teradata to modern GCP data platforms. I've led 100TB+ migrations saving 28%+ costs, managed SI partners across JAPAC, built and retained high-performing consultant teams, and created reusable assets that scale expertise. I want to bring this to Google Cloud Consulting Singapore to help enterprise customers unlock AI-ready data platforms."

---

## 📊 ROUND 1: RECRUITER (30 min) - KEY ANSWERS

| Question | 60-Second Answer Framework |
|----------|----------------------------|
| **Walk me through background** | 3-min: Current role → Migration expertise (140TB, 28% savings) → Partner mgmt (5 SIs, scorecards) → Team leadership (12 consultants, 95% retention) → Why Google Cloud Consulting Singapore |
| **Most complex migration** | **STAR**: 140TB Teradata→BQ, 500 SPs, 22 weeks. Challenge: NULL skew in shuffle. Solution: Classifier→5 patterns→80% auto. Result: 3 weeks early, $2.3M savings |
| **BQ Architecture (2 min)** | Colossus (storage) → Dremel (query) → Borg (compute). Partitioning (time/unit) + Clustering (filter cols). Slots = compute units. BI Engine for <1s dashboards. Streaming Write API for <1s ingestion |
| **Cost objection** | A.C.E.: **A**cknowledge → **C**ontext (TCO: storage+compute+people+ops) → **E**vidence (Pilot: 10TB showed 40% savings) → **Pilot close** |
| **Partner experience** | Governance model: Scorecards (delivery/quality/commercial), 4-level escalation (PM→Director→VP→C-suite), certification gates, co-creation IP model |
| **Why Singapore** | MAS-TRM wave, FinServ hub, partner ecosystem (Strategic/Select/Boutique), data residency expertise, cultural fluency (relationship/hierarchy/face) |

---

## 🔧 ROUND 2: TECHNICAL (60 min) - RAPID FIRE ANSWERS

### BigQuery (5 questions in 8 min)
| Topic | 30-Second Answer |
|-------|------------------|
| **Partition vs Cluster** | Partition = pruning (time/unit). Cluster = sort within partition (filter cols). Use both: PARTITION BY date CLUSTER BY customer_id |
| **Slot contention** | 1) Reservation (baseline+burst) 2) Fair scheduling (job priority) 3) Query optimization (reduce shuffle) 4) BI Engine offload |
| **Streaming Write API** | Direct to storage, bypass shuffle. Exactly-once via offset commit. <1s latency. Default stream + committed streams for transactions |
| **BQML → Vertex** | EXPORT MODEL → Vertex Model Registry → Vertex Endpoint (online) / Batch Prediction (offline). Feature Store for features |
| **Omni** | Multi-cloud query (AWS S3, Azure Blob). External tables + connection. No data movement. Same SQL dialect |

### Dataflow/Beam (5 questions in 8 min)
| Topic | 30-Second Answer |
|-------|------------------|
| **Exactly-once (3 layers)** | 1) Source: Pub/Sub exactly-once (ack deadlines) 2) Transform: Deterministic DoFn + stateful processing 3) Sink: BQ Streaming Write API with offset |
| **Windowing types** | Fixed (tumbling), Sliding (overlapping), Session (gap-based), Global. Trigger = Early/Firing/Accumulating/Retracting |
| **Shuffle skew (NULL keys)** | Salting: `key + "_" + hash(value) % N`. Custom Partitioner. CoGroupByKey with skewed keys separate |
| **Flex Templates** | Container-based. Build once, run anywhere. Parameters at runtime. CI/CD friendly. Replaces Classic templates |
| **Streaming → Batch backfill** | Same pipeline, bounded source. `--streaming=false`. Watermark = max timestamp. Handle late data with allowed_lateness |

### Migration (3 questions in 5 min)
| Topic | 30-Second Answer |
|-------|------------------|
| **4-Phase Methodology** | **Assess** (DMA, inventory, complexity) → **Pilot** (10TB, validate) → **Migrate** (dual-write, CDC, cutover) → **Optimize** (slots, partitioning, cost) |
| **500 SP Strategy** | Classifier → 5 categories (trivial/parameterized/complex/dynamic/dead). 80% auto via templates. 20% human. Validate: row counts + checksums + business logic |
| **Cutover (15-min RTO)** | 1) Freeze writes 2) Final CDC sync 3) Validate counts 4) Switch BI/consumers 5) Monitor 15 min 6) Rollback plan: dual-write reverse |

### Security/Governance (4 questions in 6 min)
| Topic | 30-Second Answer |
|-------|------------------|
| **VPC-SC** | Perimeter around projects. Ingress/Egress rules. Bridge for cross-perimeter. Dry-run mode first. MAS-TRM 7.2/8.1 |
| **CMEK vs CMEK+HSM vs CSEK** | CMEK: Cloud KMS key. CMEK+HSM: Cloud HSM (FIPS 140-2 L3). CSEK: Customer supplies key (no rotation). MAS-TRM 6.3 requires CMEK+HSM |
| **Dataplex Policy Tags** | Taxonomy → Policy Tags → Column-level → DLP auto-tag → Dynamic masking/RLS via IAM conditions. Governance unified |
| **Org Policy Data Residency** | `constraints/gcp.resourceLocations` = `in:asia-southeast1`. Inheritance. Dry-run audit. Exception process documented |

### Vertex AI (3 questions in 5 min)
| Topic | 30-Second Answer |
|-------|------------------|
| **Feature Store (Online/Offline)** | Online: Low-latency serving (Redis), <10ms. Offline: BigQuery/Parquet for training. Sync via ingestion jobs. Entity + Feature View |
| **BQML → Vertex Promotion** | `EXPORT MODEL` → Vertex Model Registry → `gcloud ai endpoints deploy`. Monitoring: drift, skew, latency. Auto-retrain pipeline |
| **GenAI on Data Platform** | Vertex AI Search (RAG) → Grounding in BQ → Agent Builder for SQL gen → Custom models on Vertex Training → MLOps pipeline |

---

## 🤝 ROUND 3: CONSULTING SIM (45 min) - FRAMEWORKS

### Executive Presentation (10 min, 3 slides)
```
SLIDE 1: Business Problem + Impact ($)
SLIDE 2: Approach (Phases, Timeline, Team)
SLIDE 3: Investment + ROI + Risk Mitigation
```
**Key**: Outcomes first. Technical depth in appendix. Address CFO skepticism with Pilot.

### Scope Creep Negotiation
```
MoSCoW Workshop (2 hrs):
M - Must have (in scope)
S - Should have (defer to Phase 2, costed)
C - Could have (nice to have, not committed)
W - Won't have (explicitly out)
```
**Partner accountability**: "You committed to SoW. New scope = change order."

### Technical Disagreement (Dataflow vs Kafka)
1. Seek to understand their constraints
2. Tradeoff table: Latency, ops burden, cost, team skills, ecosystem
3. Pilot both on same workload
4. Data-driven decision

---

## 🎨 ROUND 4: PRESENTATION (30+15 min) - WHITEBOARD SCRIPT

### Architecture Diagram (<4:30)
```
1. Title + Context (15s): "Teradata→BigQuery, 140TB, FinServ Singapore"
2. Current State (45s): On-prem Teradata, ETL, BI, Security gaps
3. Target State (90s): 
   - Ingestion: Datastream/CDC → Pub/Sub
   - Processing: Dataflow (batch + streaming)
   - Storage: BQ (partitioned/clustered)
   - ML: Vertex AI (Feature Store, Endpoints)
   - Governance: Dataplex, VPC-SC, CMEK+HSM
   - BI: Looker + BI Engine
4. Migration Flow (45s): Assess→Pilot→Migrate→Optimize with dual-write
5. Security/Compliance (30s): MAS-TRM controls mapped, PDPA residency
6. Cost/Ops (30s): Slot reservations, autoscaling, monitoring, runbooks
```
**Draw order**: Ingestion → Processing → Storage → ML → Governance → Migration → Security

### Top 10 Q&A (A.C.E. Framework)
| Question | A.C.E. Response |
|----------|-----------------|
| Why not Snowflake? | A: Valid choice. C: Customer needs unified AI (BQML→Vertex), Omni, MAS-TRM native. E: Pilot showed 30% faster ML time-to-prod |
| 100TB initial load? | A: Large volume. C: Datastream backfill + parallel Dataflow. E: 140TB done in 3 weeks with validation |
| Rollback plan? | A: Critical. C: Dual-write reverse, CDC replay, BI switchback tested. E: 15-min RTO achieved in Pilot |
| Scale for 10 migrations? | A: Scale challenge. C: Reusable IP (Runbook, Terraform, Templates). E: 15 projects, 80% faster delivery |
| Biggest mistake? | A: Underestimated SP complexity. C: Built classifier after. E: Now 80% auto, 3-week acceleration |
| Multi-cloud strategy? | A: Reality. C: BQ Omni for query, Anthos for compute. E: Customer X querying AWS S3 from BQ |
| Schema evolution? | A: Inevitable. C: Avro/Protobuf schemas, compatibility checks in CI/CD, BQ schema evolution rules. E: Zero downtime deploys |
| Team composition? | A: Right sizing. C: 1 Lead, 2 Architects, 4 Engineers, 1 QA, 1 PM per migration. E: 12 consultants, 95% utilization |
| CTO cost objection? | A: Understood. C: TCO = infra + people + ops + risk. Pilot proves 40% savings. E: Bank Y saved $2.3M/yr |
| Partner not technical? | A: Common. C: Fast-track cert (6 mo, 3 gates), co-delivery model, quality scorecards. E: Partner Z now Specialized |

---

## 🧠 ROUND 5: COGNITIVE/BEHAVIORAL (60 min) - 5 STAR STORIES

### Google's 4 Attributes → Your STARs

| Attribute | STAR Title | 2-Min Delivery |
|-----------|------------|----------------|
| **Humility** | Schema Assumption Failure | Assumed static schema → pipeline broke → built auto-detection + profiling in Assess phase → now standard in Runbook |
| **User Focus** | Said No to Lift-and-Shift | Customer wanted 1:1 Teradata→BQ. Pushed for modernization. $800k vs $2M, better performance, AI-ready |
| **Ambiguity** | Ambiguous Requirements → Pilot | "Just migrate" → Designed 10TB Pilot to discover requirements → Defined scope, saved 6 months rework |
| **Influence** | Dataflow vs Kafka Partner | Partner pushed Kafka. Built tradeoff table. Piloted both. Partner adopted Dataflow, co-delivered 3 migrations |
| **Leadership** | Retention Crisis Fix | 2 seniors left (no growth, burnout). Launched dual ladder, 20% protected time, asset royalties, practice council. Retention 95% |

### Singapore Cold Knowledge
| Topic | Key Points |
|-------|------------|
| **MAS-TRM** | 6.3 (Encryption), 7.2 (Network), 8.1 (Access), 9.1 (Audit) → Map to VPC-SC, CMEK+HSM, IAM Conditions, Cloud Audit Logs |
| **PDPA** | Consent, Purpose Limitation, Access/Correction, Retention, Transfer → BQ column masking, DLP, Org Policy residency, Data Catalog lineage |
| **Partners** | Strategic: Accenture, Deloitte, NCS | Select: Cloud Ace, SADA | Boutique: Local SG specialists |
| **Culture** | Relationship first, hierarchy respected, face preserved, indirect communication, consensus-driven |

### Objection Handling (A.C.E. + Pilot Close)
| Objection | A.C.E. + Pilot |
|-----------|----------------|
| "3x Teradata cost" | Acknowledge → TCO decomposition (storage+compute+people+ops+risk) → Pilot 10TB proves 40% savings → "Let's Pilot" |
| "MAS-TRM = On-prem" | Acknowledge → VPC-SC + CMEK+HSM + Org Policy = compliant → MAS-TRM 6.3/7.2/8.1/9.1 mapped → "Pilot validates" |
| "Proprietary = Lock-in" | Acknowledge → Open formats (Parquet, Avro, Iceberg), Omni, SQL standard, Terraform portable → "Pilot proves portability" |
| "22 weeks impossible" | Acknowledge → Classifier + automation = 80% faster SP migration → Pilot proved 3-week acceleration → "Pilot de-risks timeline" |

---

## 📋 DAY-OF CHECKLIST

### Materials (Pack Night Before)
- [ ] Presentation PDF: Phone + Laptop + USB
- [ ] Whiteboard markers: Black, Blue, Red, Green (tested)
- [ ] Architecture diagram: Drawn from memory <4 min (5x practiced)
- [ ] Migration path doc: Printed A3 color
- [ ] Best practice asset demo: GitHub/Terraform/Notebook ready
- [ ] Appendix slides: Accessible

### Logistics
- [ ] Interview time confirmed (Singapore = UTC+8)
- [ ] Video link tested, backup hotspot ready
- [ ] Camera, mic, lighting, professional background
- [ ] Clothes ready (worn in Mock 10)

### Mental
- [ ] 3 questions for them prepared
- [ ] Values stories feel authentic (not memorized)
- [ ] "I don't know but..." protocol automatic
- [ ] Sleep: 8 hours, no screens 1hr before

### Emergency Kit
- [ ] Recruiter contact for technical issues
- [ ] Backup presentation on phone
- [ ] "I don't know but..." phrases on sticky
- [ ] 4-7-8 breathing for anxiety

---

## 🚫 VALUES VETO - NEVER DO THESE

| Veto Trigger | Instead |
|--------------|---------|
| Blame others for failure | Own it, systemic fix, applied since |
| "I don't know" without plan | "I don't know but here's how I'd find out" |
| Can't explain tech to non-tech | Analogies, business outcomes, no jargon |
| Arrogance / solo heroics | "We" language, team credit, humility |
| Inflated ownership | Precise scope, verifyable in ref check |

---

## 🎯 FINAL REMINDERS

1. **Business judgment > Technical cleverness**
2. **Customer outcomes > Architectural purity**
3. **Team success > Individual heroics**
4. **Reusable IP > Custom solutions**
5. **Humility > Certainty**
6. **Every answer ladders to**: "How does this help the customer succeed? How does this scale the practice? How does this embody Google's values?"

---

## 📞 YOUR 3 QUESTIONS FOR THEM

1. "How does the Singapore practice measure success beyond revenue - customer outcomes, partner enablement, consultant development?"
2. "What's the biggest challenge the Data & Analytics practice faces in APAC this year, and how would this role help solve it?"
3. "How does Google Cloud Consulting balance reusable IP development with custom delivery in the Singapore market?"

---

*Last Review: Morning of Interview | You're Prepared. Trust the Process. 🚀*