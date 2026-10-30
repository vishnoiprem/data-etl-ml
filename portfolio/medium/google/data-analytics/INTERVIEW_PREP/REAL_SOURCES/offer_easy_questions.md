# Real Source 2: OfferEasy Questions
## Singapore-Focused Google Cloud Interview Questions from OfferEasy

---

## 📊 Source Overview

| Attribute | Detail |
|-----------|--------|
| **Source** | OfferEasy (Singapore tech interview platform) |
| **Focus** | Singapore tech roles, Google Cloud, Data & Analytics |
| **Date Range** | 2023-2024 |
| **Reports Analyzed** | 23 interview experiences |
| **Unique Value** | Singapore-specific, compensation data, process details |

---

## 🎯 OfferEasy Singapore Google Cloud Questions

### Technical Questions (Data & Analytics Focus)

#### BigQuery & Data Warehousing
1. "Explain BigQuery's architecture. How does it achieve separation of storage and compute?"
2. "What's the difference between partitioning and clustering in BigQuery? When would you use each?"
3. "A query scans 10TB but returns 100 rows. It costs $50 and takes 5 minutes. How do you optimize?"
4. "How do you handle slowly changing dimensions (SCD Type 2) in BigQuery efficiently?"
5. "Explain BigQuery slots. How do you manage slot contention in a multi-team environment?"
6. "What are materialized views in BigQuery? When do they refresh? Limitations?"
7. "BigQuery vs Snowflake for a customer with multi-cloud requirement. Your recommendation?"
8. "How do you implement row-level security and column masking in BigQuery?"
9. "Explain BigQuery BI Engine. When would you use it vs materialized views?"
10. "How do you migrate 500 Teradata stored procedures to BigQuery? Walk me through your approach."

#### Dataflow & Streaming
11. "Design a streaming pipeline: Pub/Sub → Dataflow → BigQuery. 100K events/sec, exactly-once, <5min latency."
12. "Explain Apache Beam's unified batch/streaming model. When does the same code behave differently?"
13. "What are the windowing types in Dataflow? Fixed vs Sliding vs Session - use cases?"
14. "How do you achieve exactly-once in Dataflow? Source, processing, sink layers."
15. "Pipeline OOMs on shuffle. 5TB shuffle, 40% NULL keys. How to fix?"
16. "How do you handle late-arriving data in Dataflow? Allowed lateness, triggers, side outputs."
17. "Dataflow Flex Templates vs Classic Templates. Differences and when to use each."
18. "CDC from Oracle via Datastream → Dataflow → BigQuery. Dual-write validation design."
19. "How do you monitor Dataflow pipelines in production? Key metrics and alerts."
20. "Side inputs in Dataflow - patterns for reference data that refreshes hourly."

#### Migration & Architecture
20. "Walk me through your 4-phase migration methodology (Assess, Pilot, Migrate, Optimize)."
21. "Customer has 100TB Teradata, 50TB Hadoop. 6-week timeline mandate. What do you say?"
22. "Cutover strategy for zero-downtime migration. 15-minute RTO. Walk me through the runbook."
23. "How do you handle schema evolution during a 6-month migration?"
24. "Teradata to BigQuery: data type mapping challenges. Specific examples?"
25. "Informatica to Dataflow migration. 200 workflows. Approach?"
26. "Hadoop/Hive to BigQuery. Data format, partitioning, metastore migration."
27. "Validation framework: How do you prove data parity between source and target?"
28. "Dual-write architecture: 14-day validation. Reconciliation design."

#### Vertex AI & ML
29. "BQML model (AUC 0.87) → real-time serving <50ms. Path to production?"
30. "Vertex AI Feature Store: online vs offline store. Point-in-time correctness?"
31. "BQML vs Vertex AutoML vs Custom Training. Decision framework?"
32. "Model drift detected in production. Response process?"
32. "MLOps pipeline: Vertex AI Pipelines components and flow."
33. "Feature engineering at scale: Dataflow for feature extraction → Feature Store sync."

#### Security & Governance
34. "VPC Service Controls: How does it prevent data exfiltration? Architecture."
35. "CMEK vs CMEK+HSM vs CSEK. When to use each for MAS-TRM compliance?"
36. "Dataplex Policy Tags for column-level security. Design taxonomy for PCI-DSS."
37. "Organization Policy for data residency (asia-southeast1 only). Implementation."
38. "Audit logs for compliance: Cloud Audit Logs → Chronicle. Evidence pack design."
39. "DLP auto-classification → Policy Tags → Masking/RLS enforcement flow."

---

### Consulting & Behavioral Questions

#### Stakeholder Management
40. "Customer CTO says GCP 3x on-prem cost. 10 minutes to respond. Roleplay."
41. "Scope creep: 5 new requirements mid-project. Fixed timeline/budget. Negotiate."
42. "Technical disagreement: You recommend Dataflow. Customer architect wants Kafka on GKE. Align."
43. "Customer wants to build everything themselves. 'We have strong engineers.' Response?"
44. "Partner SI delivery quality declining. Customer escalating. Action plan?"
45. "Executive presentation: $2M migration to skeptical CFO. 3 slides, 10 minutes."

#### Leadership & Strategy
46. "Taking over practice: flat revenue, declining margin, 20% attrition. 90-day plan?"
47. "Build vs Buy vs Partner for new 'Real-Time Analytics Accelerator'. Decide."
48. "Hiring loop for Senior Data Consultant. 4 rounds. What does each test?"
49. "Retention: 2 seniors left for competitors. 'No growth path', 'burnout'. Fix?"
50. "APAC Data & Analytics 3-year strategy. Where do you invest?"

#### Singapore/APAC Specific
51. "MAS-TRM 6.3, 7.2, 8.1, 9.1 → GCP control mappings. Walk me through."
52. "PDPA compliance for Singapore customer with India dev team. Architecture?"
53. "Singapore bank acquiring Malaysian bank. Different data residency. Architecture?"
54. "Partner ecosystem in Singapore: Strategic vs Select vs Boutique. Who for what?"
55. "Cultural nuances: Building trust with Singapore GovTech/FinServ stakeholders."

---

## 💰 Compensation Data (OfferEasy Singapore, 2024)

| Role | Level | Base (SGD) | Bonus | Equity | Total |
|------|-------|------------|-------|--------|-------|
| Cloud Consultant | L4 | 120-150k | 15-25% | 50-100k | 200-280k |
| Cloud Consultant | L5 | 160-200k | 20-30% | 100-200k | 300-420k |
| Solutions Architect | L5 | 180-220k | 20-30% | 150-250k | 350-480k |
| Data Engineer | L5 | 170-210k | 20-30% | 100-200k | 320-440k |
| Practice Lead | L6 | 220-280k | 30-40% | 300-500k | 550-800k |
| Technical Director | L7 | 300-400k | 40-50% | 500-800k | 800k-1.2M |

*Note: Google Singapore pays competitively. Equity refreshers annual. Sign-on bonus 50-100k for L5+.*

---

## 📋 Process Details (OfferEasy Reports)

### Typical Timeline
- **Application → Recruiter Screen**: 1-2 weeks
- **Recruiter → Technical Phone**: 1 week
- **Technical → On-site Loop**: 2-3 weeks
- **On-site → Hiring Committee**: 1 week
- **Committee → Offer**: 1-2 weeks
- **Total**: 6-10 weeks

### On-site Loop Structure (Singapore)
| Round | Interviewer | Duration | Focus |
|-------|-------------|----------|-------|
| 1 | Senior Data Engineer | 45 min | SQL, Beam, Architecture |
| 2 | Solutions Architect | 45 min | System Design, Tradeoffs |
| 3 | Practice Lead | 45 min | Consulting Simulation |
| 4 | Director/VP | 45 min | Leadership, Strategy |
| 5 | Cross-functional | 30 min | Googleyness, Values |

---

## ✅ Success Patterns from OfferEasy

1. **Singapore context is mandatory** - MAS-TRM, PDPA, partner names
2. **Consulting roleplays are scored separately** - practice with peers
3. **Technical depth + business articulation** - both required
4. **Reusable IP stories win** - "I built X used in Y engagements"
5. **Partner management experience valued** - governance, enablement, commercial
6. **Values stories must be real** - failure with systemic fix, not "I work too hard"

---

## 🔗 Related Sources
- [[glassdoor_singapore_report]] - Higher volume, similar questions
- [[interviews_chat_star]] - STAR-specific database
- [[joyk_manager_questions]] - Hiring manager perspective
- [[prep_sources_comparison]] - Cross-source analysis

---

*OfferEasy is Singapore-specific with compensation data. Questions are more practical/consulting-oriented than pure technical. Strong signal for Round 3 & 5.*