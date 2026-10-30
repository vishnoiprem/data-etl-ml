# Mock Interview Sets 6-10 - Specialized Scenarios
## Edge Cases, Curveballs, and Advanced Simulations

---

## 🎯 Mock Set 6: Curveball & Stress Test
### "The interview goes sideways" scenarios

---

### Scenario 1: Hostile Interviewer
**Setup:** Interviewer challenges everything, interrupts, dismisses your answers
**Your Response:**
- Stay calm. "I hear your concern. Let me address that directly."
- Don't match energy. Slow down. Structure more.
- "May I finish the thought?" (polite, firm)
- If truly abusive: "I want to have a productive conversation. Can we reset?"

### Scenario 2: "We've already decided not to hire you" (Pressure Test)
**Setup:** Interviewer says this mid-interview
**Your Response:**
- "I appreciate the candor. May I ask what drove that - so I can address it or learn?"
- If they share: Address specifically with evidence
- If they don't: "I'd still like to use our time well. What would be most valuable to discuss?"
- Never beg. Professional to the end.

### Scenario 3: Technical Question You Truly Don't Know
**Setup:** "What's the exact BigQuery slot millisecond calculation for DML with partitioned tables?"
**Your Response:**
- "I don't have the exact formula memorized."
- "Here's how I'd find out: 1) BigQuery pricing doc section 4.2, 2) Run test query with EXPLAIN ANALYZE, 3) Confirm with our BQ specialist."
- "Can I follow up by EOD with the precise answer?"
- **Never:** Guess, deflect, or "it depends"

### Scenario 4: Ethical Dilemma
**Setup:** "Customer wants to use ML to deny loans based on zip code (proxy for race). Legal but unethical. You're the architect."
**Your Response:**
- "This raises fairness concerns. Zip code as proxy for protected class = regulatory risk (MAS, PDPA) and reputational risk."
- "I'd recommend: 1) Fairness assessment (Vertex AI Model Monitoring), 2) Alternative features, 3) Legal/compliance review, 4) Document decision."
- "If they proceed against advice: Escalate to Practice Lead, document objection, consider engagement withdrawal."
- **Google Value:** "Focus on the user" = society, not just customer

### Scenario 5: "Your competitor (AWS/Azure) does this better."
**Setup:** Direct competitive challenge
**Your Response:**
- "They have strengths. Here's where they win: [specific]. Here's where we win: [specific]."
- "For YOUR use case [reference their context], here's why GCP: [evidence]."
- "Happy to do a technical bake-off on your workload. Pilot proves it."
- Never trash competitors. Confident differentiation.

---

## 🎯 Mock Set 7: Industry-Specific Deep-Dives
### FinServ, Healthcare, Retail, Telco, Public Sector variations

---

### 7A: FinServ (MAS-TRM, PCI-DSS, SOX)
**Key Differences:** Regulatory evidence, data residency, audit trails, vendor mgmt
**Must Know:** MAS-TRM control mapping, PCI-DSS scope reduction via tokenization, SOX ITGCs

### 7B: Healthcare (HIPAA, FHIR, PHI)
**Key Differences:** De-identification, consent management, interoperability, BAA
**Must Know:** Cloud Healthcare API, FHIR stores, DLP de-id templates, audit logs

### 7C: Retail (PCI, PII, Customer 360, Real-time)
**Key Differences:** Seasonal scale, personalization, inventory optimization, omnichannel
**Must Know:** Vertex AI Recommendations, Feature Store for real-time, Dataflow for clickstream

### 7D: Telco (Network data, IoT, Edge, 5G)
**Key Differences:** Petabyte-scale time-series, edge processing, network topology, GIS
**Must Know:** BigQuery GIS, Dataflow for streaming IoT, Vertex AI for network optimization

### 7E: Public Sector (GovTech, SingPass, Data.gov.sg, Smart Nation)
**Key Differences:** Data sovereignty, citizen consent, open data, inter-agency sharing
**Must Know:** NCS/ST Engineering partnerships, SingPass integration, data.gov.sg APIs

---

## 🎯 Mock Set 8: Role-Play Intensive
### Full consulting simulations with professional actors (or skilled peers)

---

### 8A: Discovery Workshop (2 hours → 30 min simulation)
**Scenario:** "Run a 30-min Art of Possible workshop for a CTO who thinks they know better."
**Structure:**
1. Context setting (2 min): "You're here to explore, not be sold"
2. Current state rapid-fire (5 min): Pain points ranked
3. Art of Possible (10 min): 3 GCP capabilities mapped to their pains
4. Prioritization (8 min): Quick wins vs Strategic vs Transform
5. Next Steps (5 min): Pilot scope, success criteria, timeline

### 8B: Executive Presentation (10 min → 10 min)
**Scenario:** "Present $3M migration to CFO who sees only cost."
**Structure:**
1. One-slide executive summary (Business problem → Solution → Investment → ROI → Risk)
2. 3 objection handling (Security, Cost, Timeline) - preempted in slides
3. Clear ask: "4-week Pilot. Go/No-Go. Your risk: 4 weeks."

### 8C: Technical Dispute Mediation (15 min)
**Scenario:** "Your architect says Dataflow. Customer architect says Kafka on GKE. Mediate."
**Structure:**
1. Seek to understand (3 min): "Help me understand your constraints..."
2. Tradeoff table (5 min): Objective comparison on THEIR criteria
3. Pilot proposal (4 min): "Let's test both on your workload. Data decides."
4. Decision framework (3 min): "If tie, here's how we decide: [criteria]"

### 8D: Partner Conflict Resolution (15 min)
**Scenario:** "Partner missed milestone, blames your architecture. Customer angry. Mediate."
**Structure:**
1. De-escalate (2 min): "Let's focus on solution, not blame."
2. Root cause (5 min): Joint war room - specific technical gap
3. Remediation (5 min): Specific actions, owners, dates, Google support
4. Prevention (3 min): Process change so it doesn't recur

---

## 🎯 Mock Set 9: Technical Whiteboard Challenges
### Draw/Design under time pressure

---

### 9A: "Design this in 5 minutes" Series

| Challenge | Time | Key Elements Required |
|-----------|------|----------------------|
| **Real-time fraud detection** | 5 min | Pub/Sub→Dataflow→Feature Store→Vertex→BQ→Alerting, exactly-once, <100ms |
| **Multi-country data residency** | 5 min | Hub-spoke, Org Policy, Omni, VPC-SC per country, Dataplex lineage |
| **Teradata→BigQuery migration** | 5 min | 4 phases, Assess/Pilot/Migrate/Optimize, dual-write, validation, cutover |
| **ML Feature Platform** | 5 min | BQ offline → Feature Store online/offline → Vertex training/serving → Monitoring |
| **Cost Governance Dashboard** | 5 min | Billing Export→Dataflow→BQ→Looker, Forecast, Anomaly, Optimization recs |
| **Disaster Recovery** | 5 min | Multi-region GCS, BQ multi-region, Composer DR, Dataflow snapshots, RTO/RPO |

### 9B: "Fix This Architecture" (Red Team)
**Given:** Flawed architecture diagram
**Find:** 5+ issues in 5 min
**Common Flaws:**
- Public IPs on Dataflow workers
- No VPC-SC, CMEK missing
- Single-region for FinServ
- No partitioning/clustering shown
- No dead letter, no monitoring
- No partition pruning in queries
- Direct BQ access from internet
- No policy tags, no DLP
- No KT plan, no runbooks

---

## 🎯 Mock Set 10: Final Integration Mock
### Full 5-Round Simulation (3 hours) - Dress Rehearsal

---

### Schedule (Simulated Interview Day)

| Time | Round | Interviewer | Focus | Duration |
|------|-------|-------------|-------|----------|
| 09:00 | 1 | Recruiter | Baseline, motivation | 30 min |
| 09:45 | 2 | Senior Architect | Technical deep-dive | 60 min |
| 11:00 | 3 | Practice Lead | Consulting simulation | 45 min |
| 11:55 | **Lunch/Break** | | | 60 min |
| 13:00 | 4 | Panel (3) | Presentation + Q&A | 45 min |
| 13:55 | 5 | Cross-functional (3) | Cognitive/Behavioral | 60 min |
| 15:00 | **Debrief** | Self | Score, notes, action items | 30 min |

---

### Round 1: Recruiter (30 min)
- [ ] 3-min background narrative
- [ ] Most complex migration (STAR)
- [ ] BigQuery architecture (2 min)
- [ ] Cost objection handling
- [ ] Partner experience
- [ ] Why Google Cloud Consulting Singapore
- [ ] Logistics (salary, notice, location)

### Round 2: Technical (60 min)
- [ ] SQL: Customer 360 with late data handling
- [ ] Beam: Pub/Sub→BQ with validation, DLQ, side input
- [ ] System Design: Real-time fraud (100K eps, <100ms)
- [ ] Tradeoffs: BQ vs Snowflake, Dataflow vs Kafka, Dataproc vs EMR

### Round 3: Consulting (45 min)
- [ ] Executive presentation (10 min, 3 slides)
- [ ] Scope creep negotiation (roleplay)
- [ ] Technical disagreement (roleplay)

### Round 4: Presentation (45 min)
- [ ] 20-min presentation (slides + whiteboard)
- [ ] 5-min whiteboard architecture
- [ ] 15-min Q&A (top 10 questions)

### Round 5: Cognitive (60 min)
- [ ] Googleyness: 5 STARs (Failure, Learning, Influence, Priority, User Focus)
- [ ] Leadership: Team build, P&L, Partner scale, Hiring
- [ ] Singapore: MAS-TRM, PDPA, Residency, Partners, Culture
- [ ] Technical: 10 rapid-fire + 1 deep-dive
- [ ] Objections: 2 roleplays (Cost, Security/Lock-in/Timeline)

---

### Scoring Sheet (Post-Mock)

| Round | Score (1-4) | Pass? | Key Strength | Key Gap |
|-------|-------------|-------|--------------|---------|
| 1: Recruiter | | Y/N | | |
| 2: Technical | | Y/N | | |
| 3: Consulting | | Y/N | | |
| 4: Presentation | | Y/N | | |
| 5: Cognitive | | Y/N | | |
| **OVERALL** | | **HIRE/NO HIRE** | | |

### Values Veto Check
- [ ] Humility/Learning Agility: PASS/FAIL
- [ ] User Focus: PASS/FAIL
- [ ] Comfort with Ambiguity: PASS/FAIL
- [ ] Influence Without Authority: PASS/FAIL

**ANY FAIL = NO HIRE (regardless of scores)**

---

### Post-Mock Action Items
1. ________________________________________ (Due: _____)
2. ________________________________________ (Due: _____)
3. ________________________________________ (Due: _____)

### Next Mock Date: _______________ Focus: _______________

---

*Run Mock Set 10 exactly once, 3 days before real interview. Treat it as the real thing. Same clothes, same setup, same breakfast. The dress rehearsal reveals what the practice runs miss.*