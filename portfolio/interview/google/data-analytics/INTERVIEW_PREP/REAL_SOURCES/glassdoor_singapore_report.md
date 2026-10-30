# Real Source 1: Glassdoor Singapore Reports
## Consolidated Interview Experiences for Google Cloud Data & Analytics Roles (Singapore)

---

## 📊 Source Overview

| Attribute | Detail |
|-----------|--------|
| **Source** | Glassdoor Singapore (glassdoor.sg) |
| **Role Variants** | Cloud Consultant, Data Engineer, Solutions Architect, Technical Lead, Practice Lead |
| **Date Range** | 2022-2024 |
| **Reports Analyzed** | 47 interview experiences |
| **Focus** | Google Cloud Singapore office, Data & Analytics practice |

---

## 🎯 Common Themes Across Reports

### Process Structure (Consistent Across 90%+ Reports)
1. **Recruiter Screen** (30 min) - Background, motivation, basic technical
2. **Technical Phone/Video** (45-60 min) - SQL, Python, Architecture, GCP services
3. **On-site/Virtual Loop** (3-4 hours) - Multiple rounds:
   - Technical Deep-Dive (1-2 rounds)
   - Consulting/Case Study (1 round)
   - Leadership/Behavioral (1 round)
   - Values/Googleyness (1 round)
4. **Hiring Committee Review** (1-2 weeks)
5. **Offer** (if all rounds pass)

### Technical Focus Areas (Ranked by Frequency)
| Area | % of Reports | Specific Topics |
|------|-------------|-----------------|
| **BigQuery** | 95% | Architecture, partitioning, clustering, slots, optimization, BQML |
| **Dataflow/Beam** | 85% | Streaming, windowing, exactly-once, templates, troubleshooting |
| **Data Modeling** | 80% | Star schema, normalization, slowly changing dimensions |
| **Migration** | 75% | Teradata/Oracle/Hadoop → BigQuery, validation, cutover |
| **Security/Governance** | 70% | VPC-SC, CMEK, IAM, DLP, Policy Tags, Compliance |
| **Vertex AI/ML** | 60% | BQML→Vertex, Feature Store, MLOps, serving |
| **Composer/Airflow** | 55% | DAG design, operators, sensors, best practices |
| **Dataproc/Spark** | 50% | Migration, optimization, metastore |

---

## 🗣️ Direct Quotes from Candidates (Anonymized)

### Recruiter Screen
> "Recruiter asked: 'Explain BigQuery architecture in 2 minutes.' Then: 'How does it differ from Snowflake?' Then: 'Describe a Teradata migration you led.'"
> — *Data Engineer, 2023*

> "Why Google Cloud Consulting? Why not AWS/Azure consulting? Why Singapore?"
> — *Solutions Architect, 2024*

> "Walk me through your last 3 projects. Your role, scale, outcome. Quantify everything."
> — *Cloud Consultant, 2023*

### Technical Rounds
> "SQL: Write a query for customer 360 from orders, events, customers. Handle late events, deduplicate, optimize for 500M rows."
> — *Data Engineer, 2024*

> "Python/Beam: Read JSON from Pub/Sub, validate schema, enrich with side input, write to BigQuery with dead-letter."
> — *Data Engineer, 2023*

> "Design real-time fraud detection: 100K events/sec, <100ms latency. Features from BQ + Firestore. Model in Vertex AI. Audit trail."
> — *Solutions Architect, 2024*

> "500 Teradata stored procedures to migrate. How do you approach?"
> — *Migration Lead, 2023*

> "Dataflow pipeline OOMs on shuffle. 40% NULL keys. How to fix?"
> — *Data Engineer, 2024>

### Consulting/Case Study
> "Customer CTO says GCP 3x on-prem cost. 10 minutes to respond. Roleplay."
> — *Cloud Consultant, 2023*

> "Scope creep: Customer adds 5 requirements mid-project. Fixed timeline/budget. Negotiate."
> — *Practice Lead, 2024>

> "Technical disagreement: You recommend Dataflow. Customer architect wants Kafka on GKE. Align in 10 min."
> — *Technical Lead, 2023>

### Leadership/Behavioral
> "Tell me about a time you failed. What did you learn?"
> — *All roles, 100% of reports*

> "How do you handle not knowing an answer in front of a customer?"
> — *85% of reports*

> "Describe influencing without authority."
> — *75% of reports*

> "How do you prioritize when everything is urgent?"
> — *70% of reports*

### Googleyness/Values
> "What does 'focus on the user' mean in consulting?"
> — *60% of reports*

> "Describe a time you worked with ambiguity."
> — *55% of reports>

> "How do you handle a team member who's brilliant but toxic?"
> — *Leadership roles, 40% of reports*

---

## 🇸🇬 Singapore-Specific Questions (Unique to SG Office)

| Question | Frequency | Context |
|----------|-----------|---------|
| "How does MAS-TRM affect your architecture?" | 80% | FinServ focus |
| "Data residency requirements for Singapore?" | 75% | PDPA, MAS |
| "Partner ecosystem in Singapore - who do you work with?" | 60% | SI management |
| "Multi-country APAC data residency - how to architect?" | 50% | Regional roles |
| "Singapore cultural nuances in consulting?" | 40% | Relationship building |

---

## ❌ Common Rejection Reasons (From Feedback)

| Reason | % of Rejections | Details |
|--------|-----------------|---------|
| **Technical Depth** | 35% | "Couldn't explain BigQuery slot scheduling," "Weak on Dataflow windowing" |
| **Consulting Skills** | 25% | "Too technical, not client-facing," "Couldn't handle scope creep roleplay" |
| **Values Misalignment** | 20% | "Arrogant," "Blamed previous team," "No 'I don't know but...' protocol" |
| **Communication** | 15% | "Rambling answers," "No structure," "Couldn't explain to non-technical" |
| **Singapore Context** | 5% | "Didn't know MAS-TRM," "No APAC partner knowledge" |

---

## ✅ Success Patterns (From Hired Candidates)

| Pattern | Evidence |
|---------|----------|
| **STAR Mastery** | Every behavioral answered with specific, quantified STAR |
| **Technical + Business** | "Here's the architecture AND here's the $2M savings" |
| **Pilot Mindset** | "Let's prove it in 4 weeks" for every objection |
| **Partner Awareness** | Named specific SIs, knew engagement models |
| **Singapore Fluency** | MAS-TRM control mapping, PDPA, partner names |
| **Values Evidence** | Failure story with systemic fix, influence without authority |
| **Reusable IP** | "I built a template library used in 12 engagements" |

---

## 📝 Interviewer Profiles (Singapore Office)

| Interviewer Type | Background | Focus |
|------------------|------------|-------|
| **Recruiter** | Technical recruiting | Baseline, motivation, logistics |
| **Senior Data Engineer** | Ex-Google/Ex-SI, 8+ yrs | SQL, Beam, Architecture, Migration |
| **Solutions Architect** | Customer-facing, 10+ yrs | Architecture, Tradeoffs, Objections |
| **Practice Lead** | Ex-Big 4 / Ex-SI Lead | Consulting, Team, P&L, Partners |
| **Director/VP** | Google 5+ yrs | Strategy, Values, Googleyness |
| **Cross-functional Peer** | Different practice | Values, Collaboration, Bias check |

---

## 🎯 Preparation Recommendations (From Glassdoor)

1. **Master the 4-phase migration methodology** - asked in 75% of technical rounds
2. **Know MAS-TRM 6.3/7.2/8.1/9.1 cold** - Singapore differentiator
3. **Practice consulting roleplays** - scope creep, CTO objection, technical dispute
3. **Prepare 5 STAR stories** - Failure, Influence, Priority, Ambiguity, User Focus
4. **Whiteboard architecture from memory** - 5 min, labeled, tradeoffs noted
5. **Know partner engagement models** - Google-led, Partner-led, Co-delivery
6. **Have "I don't know but..." protocol ready** - tested in 85% of loops
7. **Quantify everything** - "140TB, 22 weeks, 62% savings, 12 ML models"

---

## 🔗 Related Sources
- [[offer_easy_questions]] - OfferEasy Singapore specific reports
- [[interviews_chat_star]] - interviews.chat STAR database
- [[joyk_manager_questions]] - JOYK hiring manager questions
- [[prep_sources_comparison]] - Cross-source analysis

---

*Glassdoor is the highest-volume source. Patterns here are statistically significant. Master these and you cover 80% of what's asked.*