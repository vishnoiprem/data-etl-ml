# Master Question Bank - All 200+ Questions Consolidated
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)

---

## 📋 ROUND 1: RECRUITER SCREEN (30-45 min)

### Core Questions (Every Mock)
1. **Why Google Cloud Consulting? Why Data & Analytics Lead?**
2. **Walk me through your background - 7 years troubleshooting for customers?**
3. **Experience managing partners - SIs, channel partners, third-party developers?**
4. **Experience with Hadoop, Spark, Hive, SQL - at what scale?**
5. **People management - how many engineers/architects managed?**
6. **Do you have current right to work in Singapore? (JD: no visa sponsorship)**
7. **Why are you looking for new position? What are you looking for?**

### Singapore-Specific
8. **Confirm: No sponsorship needed, right to work Singapore?**
9. **Experience working in Singapore/SEA market?**
10. **MAS-TRM / PDPA familiarity?**

### Mock Set Variations
| Mock Set | Additional Focus |
|----------|------------------|
| Set 1 | Hadoop to BigQuery migration experience |
| Set 2 | Biggest data platform delivered, open source distributed systems |
| Set 3 | Channel partners, SIs, third-party developers deep dive |
| Set 4 | People management - delivering technical data projects |
| Set 5 | Cloud AI experience (Vertex AI preferred) |
| Set 6 | Troubleshooting technical issues for partners - example |
| Set 7 | Most challenging troubleshooting in 7 years |
| Set 8 | Architecting distributed processing with Hadoop/Spark |
| Set 9 | Why Google Cloud Professional Services team? |
| Set 10 | Singapore retailer use cases, inventory real-time |

---

## 🔧 ROUND 2: TECHNICAL SCREEN (60 min) - Hiring Manager / Senior Consultant

### A. Migration Strategy (Top Priority)
1. **Migrate 100TB on-premise Teradata/Hadoop to GCP - walk through strategy and key GCP services**
2. **500-node Cloudera with Hive metastore, Oozie → Dataproc + BigQuery + Composer - cutover plan with dry runs**
3. **Customer: 100TB Teradata + Hadoop - tools (BMS, Data Transfer Service, Dataproc)**
4. **Migration phases: Assess → Pilot → Migrate → Optimize - your playbook**

### B. Pipeline Design
5. **Design batch pipeline: GCS landing → Dataflow validation → BigQuery partitioned/clustered → Composer orchestration**
6. **Design streaming pipeline: Pub/Sub → Dataflow → BigQuery - handle late data, duplicates, event-time vs processing-time**
7. **Streaming vs batch tradeoffs - Lambda vs Kappa architecture**
8. **How orchestrate and monitor data workflows on GCP? (Composer, retries, idempotency, audit)**

### C. BigQuery Mastery
9. **Optimize slow/expensive BigQuery query scanning 2TB → 90GB (partition pruning, clustering, materialized views, bytes scanned)**
10. **BigQuery architecture - storage vs compute separation, slots, BI Engine**
11. **Partitioning vs clustering - when to use each, max 4 clustering columns**
12. **BigQuery optimization: skew handling (one store 40% data), slot estimation, caching**

### D. Data Quality & Governance
13. **Data quality handling - dead-letter, audit table, versioned contracts, Great Expectations**
14. **Schema evolution - backward compatibility, Avro/Protobuf, Schema Registry**
15. **Data governance with Dataplex - lineage, quality scans, policy tags, glossary**
16. **Secure data in GCP - IAM least privilege, VPC-SC, CMEK, policy tags, row-level security**

### E. Database & Storage Decisions
17. **Design HA scalable database for global e-commerce: Cloud SQL vs Spanner vs Bigtable - decision matrix**
18. **Finance use case: MAS compliance - VPC-SC perimeter, CMEK, audit logs**
19. **Data storage location significance for MNCs - privacy laws, latency, DR**

### F. SQL & Programming
20. **Write Dataflow pipeline in Python for JSON logs processing**
21. **SQL subquery vs CTE - when use which?**
22. **Normalization in SQL (1NF, 2NF, 3NF, BCNF) - tradeoffs for analytics**
23. **Common joins - INNER, LEFT, RIGHT, FULL, CROSS, SEMI, ANTI - when each**
24. **Programming: Java/Python/Go/C++ - data processing code example**
25. **Python vs Go for data engineering - decision criteria**

### G. Differentiation & Architecture
26. **Differentiate BigQuery vs Redshift vs Snowflake - serverless, BQML, pricing, multi-cloud**
27. **Modern data platform for retailer: GCS + Dataproc + BigQuery + Vertex AI (real-time + AI)**
28. **Integrate Vertex AI into BigQuery ML pipeline - feature store, training, serving**
29. **Implement large-scale cloud project in corporate environment - steps**

### H. Operations & Monitoring
30. **Backfill strategy - replay raw files, MERGE not APPEND, idempotency keys**
31. **Monitoring - Cloud Monitoring alerts for freshness, row counts, data quality**
32. **Pipeline failure RCA - Dataflow + Composer troubleshooting**

---

## 👥 ROUND 3: LEADERSHIP / PEOPLE & PARTNER MANAGEMENT (45 min)

### People Management
1. **Foster positive team culture - how hire, develop, retain? (JD responsibility)**
2. **Tell me about time you managed a low performer / difficult engineer in data team**
3. **Tell me about time you led team through tight deadline - how ensure success and manage client expectations?**
4. **How hire data consultants - what is your hiring bar?**
5. **How manage and grow team of data consultants focused on modern data platforms?**
6. **Tell me about time you coached struggling consultant to success**
7. **Foster positive team culture through performance management and career coaching - example**

### Partner Management (JD: Managing Partners)
8. **Tell me about time SI partner failed to deliver - how handled?**
9. **How do you manage partner failure - SI not delivering?**
10. **How enable Google Cloud partners? Enablement plan**
11. **Manage relationships with customer's key stakeholders?**
12. **Experience managing program with Global System Integrators across JAPAC - India, Japan, SEA**
13. **Experience working within ecosystem of technology partners - how influence?**

### Presales & Customer Outcomes
14. **Tell me about time you helped client significantly optimize GCP spend (example: 28% reduction)**
15. **How estimate customer outcomes and ensure accurate presales?**
16. **How prioritize 10 projects with not enough skilled consultants?**
17. **How anticipate customer needs before they arise? (JD preferred)**
18. **Tell me about time you said no to customer for long-term success**

### Technical Leadership
19. **Walk me through project where you addressed critical security/compliance challenge using GCP**
20. **Give example of challenging technical problem in GCP project and how you resolved it**
21. **Tell me about time you had to explain complex technical GCP solution to non-technical stakeholder / manage conflicting requirements**
22. **Tell me about time you dealt with inconsistent/poor-quality data from multiple sources on GCP**
23. **Tell me about complex data analysis project you led from start to finish on GCP**
24. **Time you addressed security/compliance - HIPAA/GDPR with CMEK, SCC**
25. **Experience leading IT implementations/deployments/BD?**
26. **How drive development of best practices and assets to scale expertise? (JD responsibility)**
27. **Tell me about time you migrated monolithic Oracle to GKE + Cloud SQL PostgreSQL**
28. **Oversee data portfolio delivery excellence - how measure?**
29. **Lead team under tight deadline - e-commerce holiday launch**

---

## 🎬 ROUND 4: PRESENTATION ROUND (30 min present + 15 Q&A)

### Required Artifacts (Bring Your Own)
1. **Architecture diagram** - Modern data platform you built (Hadoop → GCS + Dataproc + BigQuery + Dataplex + Vertex AI)
2. **Migration path doc** - Hadoop/Spark/Hive → BigQuery
3. **Best practices asset** - You created to scale expertise

### Presentation Topics by Mock Set
| Mock Set | Presentation Focus |
|----------|-------------------|
| Set 1 | Hadoop to GCP migration - architecture before/after, minimal downtime |
| Set 2 | Cost optimization case - Billing Reports, right-sizing, CUDs, lifecycle |
| Set 3 | Presales to delivery success story - customer satisfaction |
| Set 4 | Best practice asset created - migration runbook |
| Set 5 | AI-driven data platform - predictive insights enabled |
| Set 6 | Global e-commerce platform migration - <30 min downtime, 40% improvement |
| Set 7 | Compliance remediation - IAM least privilege, Policy Analyzer |
| Set 8 | Pipeline failure RCA and best practice created to prevent |
| Set 9 | End-to-end: discovery → assessment → POC → migration → optimization → handover (25% cost reduction, 40% performance gain) |
| Set 10 | Technical solutions + stakeholder management + enabling partners - all three in one story |

### Standard Q&A (Prepare for All)
1. **Walk us through migration of complex on-prem application/data warehouse to GCP - why chosen architecture?**
2. **What alternatives did you consider and why choose this architecture?**
3. **How did you handle data security/governance concerns (Dataplex, governance)?**
4. **Biggest technical challenges during POC?**
5. **How would you drive development of best practices and assets to scale expertise?**
6. **How did you ensure delivery excellence and customer satisfaction?**
7. **How does this solution enable AI use cases? (JD preferred: cloud AI experience)**

---

## 🧠 ROUND 5: COGNITIVE / GOOGLEYNESS / HYPOTHETICAL (45 min)

### Hypothetical Scenarios
1. **Skeptical CIO concerned about security/governance in public cloud - how address? (VPC-SC, CMEK, Dataplex)**
2. **Customer CTO says GCP cost 3x vs on-prem Hadoop - how handle objection? (TCO math)**
3. **Your team has 10 projects, not enough skilled consultants - how prioritize demand and provide technical leadership?**
4. **Your team estimates 6 months, sales promised 3 months to win deal - what do you do?**
5. **Imagine presenting to board - how communicate technical risk in business terms?**

### Googleyness / Behavioral
6. **Why Google? Why you?**
7. **Tell me about time you had to lead without authority**
8. **Tell me about time you had to lead without authority - different example**
9. **What is normalization in SQL? (Singapore filter question)**
10. **Data Cleaning Challenges - not all data arrives perfect - how identify errors?**
11. **Data Storage Location Significance - why geographical location matters for MNCs?**
12. **Joining Data Sets - common joins**
13. **SQL Subquery explanation**
14. **Presentation Review for Data Visualizations - final review steps**
15. **Programming Language Selection - when R vs spreadsheets vs SQL?**
16. **Focus Groups vs Surveys - suitable questions**
17. **Handling Data Entry Variations - phone number formats etc**
18. **Mean Age Calculation returns N/A - troubleshoot**
19. **Visualization Selection - scatterplots vs heatmaps**
20. **Identifying Bias Sources**
21. **Reports vs Dashboards - when dashboard preferable?**
22. **Sample Size and Bias misconception**
23. **Importance of Keys in Database Management**
24. **Understanding Metadata**

### Singapore Context
25. **MAS-TRM / PDPA / Data residency requirements**
26. **Multi-cultural team leadership in SEA**
27. **Cross-border data transfer regulations**

---

## 📊 QUESTION FREQUENCY ANALYSIS

### Must-Know (Appear in 8+ Mock Sets)
| Question | Frequency | Priority |
|----------|-----------|----------|
| 100TB Teradata/Hadoop → BigQuery migration | 10/10 | 🔴 CRITICAL |
| BigQuery optimization (partition, cluster, MV) | 10/10 | 🔴 CRITICAL |
| SI partner failure management | 9/10 | 🔴 CRITICAL |
| GCP cost optimization with metrics | 9/10 | 🔴 CRITICAL |
| Team culture: hire/develop/retain | 8/10 | 🔴 CRITICAL |
| Architecture diagram + presentation | 10/10 | 🔴 CRITICAL |
| Lead without authority | 8/10 | 🔴 CRITICAL |
| Security: VPC-SC, CMEK, Dataplex | 8/10 | 🔴 CRITICAL |

### High Priority (5-7 Mock Sets)
| Question | Frequency |
|----------|-----------|
| Streaming pipeline design (Pub/Sub → Dataflow) | 7/10 |
| Low performer management | 7/10 |
| Presales estimation methodology | 6/10 |
| Data quality framework | 6/10 |
| Compliance (MAS-TRM, GDPR, HIPAA) | 5/10 |
| Skeptical CIO/CTO objection handling | 7/10 |

### Singapore-Specific (3-4 Mock Sets)
| Question | Frequency |
|----------|-----------|
| Right to work Singapore confirmation | 4/10 |
| MAS-TRM / PDPA knowledge | 3/10 |
| Data residency for MNCs | 4/10 |
| JAPAC partner management | 3/10 |

---

## 🎯 L7-SPECIFIC QUESTIONS (Round 3, 5, 6 — Differentiators)

### Practice Building & P&L Ownership
| # | Question | Your Framework |
|---|----------|----------------|
| L7-1 | **"How do you scale a consulting practice across SEA?"** | Partner tiering + asset factory + certification pipeline + joint GTM + P&L discipline |
| L7-2 | **"Customer wants GenAI but has messy data. Your move?"** | Data readiness assessment → quick win (RAG on clean subset) → platform modernization roadmap |
| L7-3 | **"Partner delivers poor quality. Google sales wants to protect revenue. You?"** | Quality gates in contract → joint war room → probation framework → escalate with data |
| L7-4 | **"Build a 3-year practice strategy for Data & Analytics in Singapore"** | Market sizing → partner gaps → specialization bets (FinServ, Telco, Public Sector) → hiring plan → asset roadmap |
| L7-5 | **"How do you balance Google IP vs Partner IP?"** | Clear demarcation: Google owns architecture/methodology; Partner owns delivery/industry templates; Joint IP = shared repo |
| L7-6 | **"Sales promised 3 months, your team says 6. What do you do?"** | Data-driven pushback: pilot in 4 weeks proves scope → re-baseline → fixed-fee milestones with contingency |
| L7-7 | **"How do you measure practice health beyond revenue?"** | Utilization, NPS, asset reuse rate, partner certification velocity, consultant retention, pipeline quality |

### AI/ML Leadership
| # | Question | Your Framework |
|---|----------|----------------|
| L7-8 | **"Build vs Buy for AI platform components?"** | Capability maturity model: Commodity (Feature Store, Monitoring) → Buy; Differentiating (Custom features, Domain models) → Build; Experimental (GenAI agents) → POC on managed |
| L7-9 | **"Govern AI at scale without slowing innovation?"** | Governance as code: Model Cards auto-generated, Drift alerts → auto-JIRA → auto-rollback, Approval gates in pipeline (async, <4hr) |
| L7-10 | **"GenAI hype vs reality conversation with executives?"** | Use case classification: Quick Win (NL2SQL, 4 wks) → Strategic (RAG, 8 wks) → Transformational (Agents, 6+ mo). Show TCO each. Pilot Quick Win first. |

### Enterprise Implementation & Change Management
| # | Question | Your Framework |
|---|----------|----------------|
| L7-11 | **"Landing zone design for regulated enterprise (MAS-TRM)?"** | Org hierarchy (folders/projects), Shared VPC + Interconnect, CMEK + VPC-SC + Dataplex policy tags, Org policies (resource locations, no external IPs), Workforce Identity Federation |
| L7-12 | **"Multi-partner delivery governance at scale?"** | Joint Delivery Office (weekly), Shared artifacts (Smartsheet/Jira/Looker), Quality gates enforced by Google (code review, data validation, security scan), 4-level escalation |
| L7-13 | **"300+ user change management across 5 LOBs?"** | Cohort-based enablement (Platform 12w, DS 10w, Analysts 6w, SMEs 4w), Certification targets, Internal hackathons, Data Mesh adoption, eNPS tracking |

### Commercial & Strategic Thinking
| # | Question | Your Framework |
|---|----------|----------------|
| L7-14 | **"Pricing model for migration: T&M vs Fixed vs Outcome-based?"** | T&M for discovery/pilot; Fixed-fee milestones for execution (Assess→Pilot→Migrate→Cutover→Hypercare); Outcome-based for strategic (Base + bonus tied to customer metrics) |
| L7-15 | **"How do you handle scope creep without damaging relationship?"** | MoSCoW in contract, change control board (weekly), alternative proposals (defer/descope/pay), data-driven impact assessment, executive sponsor alignment |
| L7-16 | **"Build business case for new practice investment (hiring/assets)?"** | ROI model: Asset dev cost vs reuse savings × engagements; Hiring cost vs utilization revenue; Payback period <6 months; NPV 3-year |

---

## 📋 ROUND 6: EXECUTIVE / HIRING COMMITTEE (30-45 min)

### Strategic Vision Questions
1. **Where is the Data & Analytics consulting market in SEA heading in 3 years?**
2. **How does Google differentiate vs AWS/Azure in data + AI consulting?**
3. **What's your 90-day plan if hired?**
4. **How do you build a practice that outlasts your tenure?**
5. **Describe a time you made an unpopular decision that was right for the business.**
6. **How do you develop the next generation of practice leads?**
7. **What's your take on Data Mesh vs centralized platform for enterprise clients?**

---

## ✅ YOUR PREPARATION CHECKLIST

### Content to Create (Fill in YOUR experience)
- [ ] 15 STAR stories (Round 3) - each with metrics
- [ ] 1 architecture diagram (draw from memory in 5 min)
- [ ] 1 migration path document (1 page)
- [ ] 1 best practice asset description
- [ ] 1 flagship case study narrative (10 min)
- [ ] TCO calculator spreadsheet (on-prem vs GCP)
- [ ] BQ optimization checklist (memorized)
- [ ] Partner escalation matrix
- [ ] Hiring rubric with scoring

### Technical to Master
- [ ] BigQuery architecture: storage/compute, slots, BI Engine
- [ ] Dataflow patterns: batch, streaming, windowing, late data
- [ ] Migration tools: DMS, Dataproc, Dataflow, Transfer Service, BMS
- [ ] Security: VPC-SC, CMEK, IAM conditions, policy tags, RLS
- [ ] Dataplex: lineage, quality, governance, glossary
- [ ] Composer vs Workflows vs Dataform
- [ ] Database selection: Cloud SQL vs Spanner vs Bigtable

### Practice Targets
- [ ] Round 1: <15 min, confident pitch
- [ ] Round 2: Draw architecture <10 min, code syntax correct
- [ ] Round 3: STAR <3 min each, every Result has metrics
- [ ] Round 4: 20 min presentation, diagrams drawn live
- [ ] Round 5: Structured frameworks, Google values, Singapore context

---

*Last Updated: 2026-01-15 | Source: 10 Mock Sets + Glassdoor + OfferEasy + Interviews.chat + JOYK + Google Warmup*