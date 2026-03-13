# CLP (Senior) Data Engineer – Data / AI Platform
## Interview Preparation Guide

---

**Date:** Monday, 9th March 2026, 5:00 PM  
**Duration:** 30 minutes – 1 hour  
**Format:** Online Video Conference  

---

## INTERVIEW PANEL

| Name | Role | Focus Areas |
|------|------|-------------|
| **Sudhir Bisht** | Principal, Data, Analytics & AI / GenAI | **Main Interviewer** – GenAI, RAG, LLMs, Data Architecture |
| **Patrik Forsstroem** | Associate Director, Data & Analytics | BI, ML, Data Delivery, 13+ years at CLP, MBA |
| **Panda Soonam** | Senior Manager, Technical Delivery | Project delivery, technical execution |
| **Eric Sze** | Senior Project Manager / Scrum | Agile, delivery methodology, stakeholder management |

---

## COMPANY CONTEXT: CLP

### Quick Facts
- **Founded:** 1901 in Hong Kong
- **Employees:** 8,000+
- **Coverage:** Powers 80% of Hong Kong's population
- **Regions:** Hong Kong, China Mainland, Australia, India, Taiwan, Thailand
- **Business:** Vertically integrated – generation, transmission, distribution, retail, smart energy
- **Mission:** "Power Brighter Tomorrows"

### Technology Stack (Confirmed)
- **Cloud:** Azure (primary)
- **Data Platform:** Azure Databricks, Data Lake, Data Factory
- **BI:** Power BI, enterprise dashboards
- **RPA:** Blue Prism
- **CRM:** Salesforce
- **IoT:** Smart Grid, Advanced Metering Infrastructure

### Strategic Priorities
- Decarbonisation & energy transition
- Digital transformation & AI adoption
- Smart grid & IoT analytics
- Customer engagement & personalisation
- Renewable energy forecasting

---

## QUESTION-BY-QUESTION PREPARATION

---

### SECTION 1: INTRODUCTION & BACKGROUND (5-10 min)

#### Q1: "Tell me about yourself and your background."

**Answer (60 seconds):**

> "I'm Prem Vishnoi, currently Head of Data Engineering at Makro, part of the CP Group – Thailand's largest retail conglomerate with $8 billion in revenue. I report directly to the Group CTO.
>
> Over the past 15 years, I've built data platforms at scale across retail, fintech, and banking. At Makro, I built our Databricks lakehouse from scratch, processing over 10 billion rows daily with 99.99% uptime across 3 countries. I grew my team from 8 to 25 engineers and manage a $2 million annual cloud budget.
>
> Before Makro, I was VP of Data Engineering at Lazada/Alibaba leading data infrastructure across 6 Southeast Asian countries. I've also worked at Xendit, Standard Chartered Bank, DBS, and PayPal – all in senior data engineering roles.
>
> I'm excited about CLP because the energy sector is at an inflection point with decarbonisation and smart grid technologies. The opportunity to build AI-powered data platforms that help power 80% of Hong Kong's population is exactly the kind of mission-driven impact I'm looking for."

---

#### Q2: "Why CLP? Why this role?"

**Answer:**

> "Three reasons:
>
> **First, the industry transformation.** Energy is becoming data-intensive – smart meters, IoT sensors, renewable forecasting, demand prediction. CLP is leading this transformation in Asia, and I want to be part of building the data infrastructure that enables it. The energy sector's data challenges are fascinating – real-time processing from thousands of assets, predictive maintenance, grid optimisation.
>
> **Second, the AI opportunity.** This role specifically mentions GenAI, RAG, and vector databases. I've been implementing RAG pipelines and working with LangChain for internal knowledge management. The chance to apply these at CLP – where you have decades of operational knowledge and documentation – is compelling.
>
> **Third, the mission.** 'Power Brighter Tomorrows' resonates with me. At Makro, I built platforms that helped feed millions of people across Southeast Asia. At CLP, I'd be powering the daily lives of millions more. That tangible impact matters to me."

---

#### Q3: "What do you know about CLP's digital transformation?"

**Answer:**

> "CLP has made digitalisation a core strategic priority. From my research:
>
> **Data & Analytics:** You're using Azure Databricks as your data platform, implementing advanced analytics and ML across power generation and distribution. Patrik's team has been leading the delivery of these capabilities aligned with enterprise data governance.
>
> **Smart Grid:** CLP deployed smart meters with advanced metering infrastructure in partnership with Itron and Cisco. This generates massive IoT data streams that need real-time processing.
>
> **AI Adoption:** CLP is actively implementing GenAI across the business – customer service, operational efficiency, knowledge management. Hong Kong's regulatory environment with HKMA's GenAI sandbox creates opportunities for responsible AI innovation.
>
> **Decarbonisation:** Your investments in renewable energy through Apraava Energy require sophisticated forecasting models – wind, solar, demand prediction.
>
> The combination of IoT scale, AI ambition, and energy transition makes this a technically rich environment. I'm particularly interested in how GenAI can accelerate insights from the vast operational data you've accumulated."

---

### SECTION 2: TECHNICAL DEEP DIVE (15-25 min)

---

#### Q4: "Describe your experience building end-to-end data pipelines."

**Answer:**

> "At Makro, I built our entire data platform from scratch using Databricks on AWS:
>
> **Architecture:**
> - **Bronze Layer:** Raw ingestion from 50+ sources – POS systems, ERP (SAP), e-commerce, logistics, IoT sensors
> - **Silver Layer:** Cleansed, normalised data with quality checks using Delta Lake
> - **Gold Layer:** Business-ready aggregates for analytics and ML
>
> **Scale:**
> - 10 billion+ rows/day processed
> - 500+ Delta tables in production
> - Sub-minute latency for critical pipelines
> - 99.99% uptime SLA
>
> **Key Patterns:**
> - Change Data Capture from SQL Server and Oracle using Debezium
> - Structured Streaming for real-time inventory and pricing
> - Unity Catalog for governance and access control
> - dbt for transformation orchestration
>
> **For CLP specifically**, I'd apply similar patterns to energy data – meter readings, grid sensor data, asset telemetry. The medallion architecture works well for IoT scale where you need both historical analysis and real-time monitoring."

---

#### Q5: "How would you design a data pipeline for smart meter data at scale?"

**Answer:**

> "Let me walk through how I'd architect this for CLP's smart meter infrastructure:
>
> **Ingestion Layer:**
> - Meter readings arriving via Azure IoT Hub or Event Hubs
> - Schema registry for versioned message formats
> - Dead letter queue for malformed data
> - Expected volume: millions of readings per hour
>
> **Processing Layer (Azure Databricks):**
> ```
> IoT Hub → Auto Loader → Bronze (raw) → Streaming ETL → Silver (cleaned)
>                                                              ↓
>                                          Batch aggregation → Gold (analytics)
> ```
>
> **Bronze:** Raw meter readings with full audit trail, partitioned by date and meter_id
>
> **Silver:** 
> - Validated readings (outlier detection, missing value handling)
> - Enriched with customer and tariff metadata
> - Delta Lake with time travel for corrections
>
> **Gold:**
> - Hourly/daily consumption aggregates
> - Peak demand calculations
> - Anomaly flags for billing disputes
>
> **Real-Time Requirements:**
> - Structured Streaming with Auto Loader for continuous ingestion
> - Watermarking for late-arriving data
> - Checkpointing for exactly-once guarantees
>
> **Governance:**
> - Unity Catalog for access control (customer data is sensitive)
> - Data masking for PII in non-production environments
> - Lineage tracking for audit compliance"

---

#### Q6: "What's your experience with Azure cloud technologies?"

**Answer:**

> "I hold AWS certifications but have significant Azure experience as well:
>
> **Azure Data Factory:**
> - Built hybrid pipelines connecting on-premise Oracle to Azure Data Lake
> - Copy activities with parameterised datasets
> - Integration runtime for secure data movement
>
> **Azure Databricks:**
> - Databricks certified (Delta Lake, Generative AI)
> - Production experience with Unity Catalog, Delta Live Tables
> - Cluster policies for cost optimisation
>
> **Azure Data Lake Storage Gen2:**
> - Hierarchical namespace for efficient data organisation
> - ABAC for fine-grained access control
> - Lifecycle policies for tiered storage
>
> **Azure Synapse:**
> - Serverless SQL pools for ad-hoc analysis
> - Dedicated pools for BI serving layer
> - Integration with Power BI
>
> **At Makro, we're on AWS, but the principles transfer directly.** Azure's integration with Power BI and Microsoft ecosystem makes it ideal for enterprise environments like CLP. I'm also familiar with Azure DevOps for CI/CD pipelines."

---

#### Q7: "Describe your experience with Spark and Python."

**Answer:**

> "Spark is my primary tool for large-scale data processing:
>
> **PySpark:**
> - 5+ years of production experience
> - Optimisation: broadcast joins, partition tuning, caching strategies
> - Structured Streaming for real-time pipelines
> - UDFs when necessary, though I prefer native Spark functions
>
> **Example optimisation at Makro:**
> A sales aggregation job was running 4 hours. I:
> 1. Replaced `groupBy().collect_list()` with window functions
> 2. Increased shuffle partitions for the skewed customer dimension
> 3. Used Delta Lake Z-ORDER on frequently filtered columns
> 4. Result: 4 hours → 25 minutes (90% improvement)
>
> **Python beyond Spark:**
> - Airflow DAGs for orchestration
> - FastAPI for serving ML models
> - Great Expectations for data quality
> - pandas for ad-hoc analysis
>
> **Scala:**
> - Read and maintain Scala Spark code
> - Prefer PySpark for team velocity and ML integration
>
> **SQL:**
> - Expert level – complex window functions, CTEs, query optimisation
> - Spark SQL and PostgreSQL"

---

#### Q8: "What's your experience with GenAI – RAG, LangChain, vector databases?"

**Answer:**

> "This is directly relevant to what I've been building at Makro:
>
> **RAG Implementation:**
> I built an internal knowledge assistant for our data team:
>
> ```
> Documents (Confluence, Runbooks) 
>       ↓ 
> Embedding Model (OpenAI text-embedding-3-large)
>       ↓
> Vector Store (Pinecone)
>       ↓
> Retrieval + LLM (GPT-4)
>       ↓
> Answer with source citations
> ```
>
> **LangChain Experience:**
> - Document loaders for various formats (PDF, Confluence, Slack)
> - Text splitters with semantic chunking
> - Chain composition for complex workflows
> - Memory management for conversational context
>
> **Vector Databases:**
> - Production: Pinecone (managed, good for POCs)
> - Evaluated: Weaviate, Milvus, Chroma
> - Interested in: pgvector for PostgreSQL integration
>
> **Use Cases for CLP:**
> - **Operations Knowledge Base:** Decades of maintenance procedures, incident reports – RAG can make this searchable
> - **Customer Service:** FAQ automation with source grounding
> - **Document Q&A:** Engineering specifications, regulatory compliance
> - **Code Assistant:** Helping engineers navigate legacy systems
>
> **LlamaIndex:**
> - Used for structured data querying (SQL + natural language)
> - Index types: VectorStoreIndex, TreeIndex, KnowledgeGraphIndex
>
> **I've also experimented with fine-tuning smaller models for domain-specific terminology.**"

---

#### Q9: "How do you use coding assistants like GitHub Copilot?"

**Answer:**

> "I've integrated Copilot into my team's daily workflow:
>
> **My Personal Usage:**
> - Daily coding with Copilot enabled
> - 40-50% of boilerplate code suggested by Copilot
> - Most valuable for: test generation, docstrings, SQL queries
>
> **Team Adoption at Makro:**
> - Rolled out to 15 engineers
> - Created internal guidelines for effective prompting
> - Measured 25% productivity improvement for routine tasks
>
> **Best Practices I Follow:**
> 1. Write clear function signatures – Copilot uses them as context
> 2. Add comments describing intent before complex logic
> 3. Review suggestions critically – especially for security
> 4. Use Copilot Chat for explaining unfamiliar code
>
> **Limitations I'm Aware Of:**
> - Can suggest outdated patterns
> - Security-sensitive code needs careful review
> - Not a replacement for understanding fundamentals
>
> **For CLP:** I'd help establish governance around AI coding assistants – approved tools, security review processes, training for engineers to use them effectively while maintaining code quality."

---

### SECTION 3: DATA QUALITY & GOVERNANCE (5-10 min)

---

#### Q10: "How do you ensure data quality in your pipelines?"

**Answer:**

> "Data quality is built into every layer of my pipeline design:
>
> **Framework at Makro (Great Expectations + Custom):**
>
> | Layer | Quality Checks |
> |-------|----------------|
> | **Ingestion** | Schema validation, null checks, freshness SLA |
> | **Bronze** | Row counts, duplicate detection |
> | **Silver** | Business rules, referential integrity, outlier detection |
> | **Gold** | Reconciliation with source systems, trend analysis |
>
> **Implementation:**
> ```python
> # Great Expectations in Databricks
> expectation_suite = context.create_expectation_suite('sales_data')
> expectations = [
>     expect_column_values_to_not_be_null('transaction_id'),
>     expect_column_values_to_be_between('amount', 0, 1000000),
>     expect_column_values_to_be_in_set('currency', ['THB', 'USD']),
> ]
> ```
>
> **For Energy Data (CLP context):**
> - **Meter readings:** Range validation (negative consumption is an error)
> - **Time series:** Gap detection (missing readings need flagging)
> - **Sensor data:** Anomaly detection (sudden spikes may indicate faults)
>
> **Alerting:**
> - Slack notifications for quality failures
> - PagerDuty for critical pipeline SLA breaches
> - Daily data quality scorecards for stakeholders
>
> **Governance:**
> - Data lineage tracked in Unity Catalog
> - Data dictionary maintained in collaboration with business
> - Quality metrics published to data catalog"

---

#### Q11: "Describe your experience with data governance and cataloguing."

**Answer:**

> "At Makro, I implemented enterprise data governance:
>
> **Unity Catalog (Databricks):**
> - Centralised metastore across workspaces
> - 3-level namespace: catalog.schema.table
> - Fine-grained access control per table/column
> - Data lineage automatically tracked
>
> **Data Classification:**
> - PII tagged and masked in non-production
> - Sensitive columns (pricing, customer data) restricted
> - Audit logging for all data access
>
> **Data Catalog:**
> - Business glossary with term definitions
> - Data owners assigned per domain
> - Quality metrics visible in catalog
>
> **For CLP:**
> - **Customer data:** PDPO compliance (Hong Kong privacy ordinance)
> - **Grid operations:** Safety-critical data needs strict access control
> - **Regulatory:** Audit trail for tariff calculations, billing accuracy
>
> **I'd work with the Data Office (Patrik's team) to ensure our pipeline implementations align with CLP's governance framework.**"

---

### SECTION 4: LEADERSHIP & COLLABORATION (5-10 min)

---

#### Q12: "How do you collaborate with data scientists and ML engineers?"

**Answer:**

> "Close collaboration is essential for successful AI projects:
>
> **Current Model at Makro:**
>
> | Role | Responsibility |
> |------|----------------|
> | **Data Engineers (my team)** | Feature pipelines, data quality, infrastructure |
> | **Data Scientists** | Model development, experimentation |
> | **ML Engineers** | Model serving, MLOps |
>
> **How We Work Together:**
>
> 1. **Feature Store:** I built a shared feature store in Databricks. Scientists define features; engineers productionise them.
>
> 2. **Development Environment:** Scientists have sandbox clusters with access to production data (read-only, sampled).
>
> 3. **Model Handoff:** Clear contract – input schema, output format, latency requirements.
>
> 4. **MLflow:** Shared experiment tracking and model registry.
>
> **Specific Example:**
> Our demand forecasting model needed inventory and weather data. I:
> - Built automated feature pipeline with 6-hour freshness
> - Implemented point-in-time joins to prevent data leakage
> - Created monitoring for feature drift
> - Scientists focused on model; my team handled data reliability
>
> **For CLP's AI Use Cases:**
> - **Renewable forecasting:** I'd build reliable weather and generation data pipelines
> - **Predictive maintenance:** Asset telemetry ingestion and feature engineering
> - **Customer analytics:** Consumption pattern features for segmentation"

---

#### Q13: "How do you handle project delivery and stakeholder management?"

**Answer:**

> "I've delivered large-scale data projects with multiple stakeholders:
>
> **Stakeholder Engagement:**
> - **Business:** Regular demos, SLA transparency, clear escalation paths
> - **Technical:** Architecture reviews, knowledge sharing, documentation
> - **Leadership:** Monthly metrics, risk updates, roadmap alignment
>
> **Delivery Approach (Agile):**
> - 2-week sprints with defined acceptance criteria
> - Daily standups for team alignment
> - Sprint demos to stakeholders
> - Retrospectives for continuous improvement
>
> **Example – Lakehouse Migration at Makro:**
>
> | Phase | Duration | Outcome |
> |-------|----------|---------|
> | Discovery | 1 month | Mapped 200+ data sources, prioritised by business impact |
> | Foundation | 2 months | Databricks setup, governance, first 10 pipelines |
> | Migration | 6 months | Incremental migration, parallel running |
> | Optimisation | Ongoing | Performance tuning, cost reduction (40% savings) |
>
> **Risk Management:**
> - Identified dependencies early (data quality from source systems)
> - Maintained fallback to legacy systems during migration
> - Communicated blockers transparently
>
> **For CLP:**
> Given the panel includes Technical Delivery and Scrum PM, I'd expect strong delivery discipline. I'm comfortable with structured project governance while maintaining engineering velocity."

---

### SECTION 5: SCENARIO-BASED QUESTIONS

---

#### Q14: "You discover a data quality issue affecting customer billing. What do you do?"

**Answer:**

> "This is critical for a utility company. Here's my structured response:
>
> **Immediate (First Hour):**
> 1. **Assess Impact:** How many customers? What's the financial exposure? Is it over-billing or under-billing?
> 2. **Contain:** Stop downstream processes from propagating bad data
> 3. **Notify:** Alert the Data Office and relevant business stakeholders immediately
>
> **Investigation (First Day):**
> 4. **Root Cause:** Use data lineage to trace where the issue originated
> 5. **Scope:** Determine the timeframe affected
> 6. **Evidence:** Preserve logs and snapshots for audit
>
> **Resolution (Days 2-3):**
> 7. **Fix:** Correct the source issue
> 8. **Reprocess:** Recalculate affected records using Delta Lake time travel
> 9. **Validate:** Confirm accuracy with business reconciliation
>
> **Prevention (Following Week):**
> 10. **RCA Document:** Full root cause analysis shared with stakeholders
> 11. **Controls:** Add data quality checks to prevent recurrence
> 12. **Monitor:** Enhanced alerting for similar patterns
>
> **Communication:**
> - Technical: Detailed timeline and fix in RCA
> - Business: Plain language summary with customer impact
> - Leadership: Risk assessment and prevention measures
>
> **At Makro, I handled a similar issue with promotional pricing affecting 50,000 transactions. We resolved it within 48 hours with zero customer complaints.**"

---

#### Q15: "How would you approach building a GenAI solution for CLP's operations knowledge base?"

**Answer:**

> "CLP has decades of operational knowledge – maintenance procedures, incident reports, engineering specs. Here's how I'd approach it:
>
> **Phase 1: Discovery (Week 1-2)**
> - Inventory knowledge sources: Confluence, SharePoint, PDFs, legacy systems
> - Interview domain experts to understand search pain points
> - Identify high-value use cases (e.g., 'How do we respond to transformer fault X?')
>
> **Phase 2: Data Pipeline (Week 3-6)**
> - Build ingestion pipelines for each document type
> - Chunking strategy: semantic chunking for technical documents
> - Embedding model: Start with OpenAI, evaluate Azure OpenAI for enterprise
> - Vector store: Azure Cognitive Search (native Azure integration) or Databricks Vector Search
>
> **Phase 3: RAG Implementation (Week 7-10)**
> ```
> User Query
>     ↓
> Query Embedding
>     ↓
> Vector Search (top-k retrieval)
>     ↓
> Reranking (optional)
>     ↓
> LLM with context + citations
>     ↓
> Response with source documents
> ```
>
> **Phase 4: Evaluation & Iteration (Week 11-12)**
> - Human evaluation of response quality
> - Feedback loop for continuous improvement
> - Metrics: answer accuracy, source relevance, user satisfaction
>
> **CLP-Specific Considerations:**
> - **Safety-critical content:** Human review for procedures affecting safety
> - **Access control:** Respect document-level permissions
> - **Regulatory compliance:** Audit trail for AI-generated answers
> - **Hallucination mitigation:** Always require source citation; flag low-confidence answers
>
> **I'd start with a pilot focused on one high-value domain (e.g., substation maintenance) before scaling.**"

---

### SECTION 6: QUESTIONS FOR THE PANEL

**Prepare 3-4 thoughtful questions:**

1. **For Sudhir (GenAI focus):**
   > "What GenAI use cases are you most excited about for CLP? Are you seeing more interest in operational efficiency or customer-facing applications?"

2. **For Patrik (Data & Analytics):**
   > "How mature is CLP's data platform today? What are the biggest opportunities for improvement in the next 12 months?"

3. **For Panda (Technical Delivery):**
   > "How does CLP balance delivery velocity with the reliability requirements of critical infrastructure?"

4. **For Eric (Scrum/PM):**
   > "How are data engineering teams organised – by business function or as a platform team?"

5. **General:**
   > "What does success look like for this role in the first 90 days?"

---

## KEY MESSAGES TO LAND

| Topic | Your Message |
|-------|--------------|
| **Scale** | "10 billion rows/day at Makro, 99.99% uptime" |
| **Databricks** | "Built lakehouse from scratch, Databricks certified" |
| **GenAI** | "Production RAG implementation, LangChain, vector databases" |
| **Leadership** | "Grew team 8→25, $2M budget, report to Group CTO" |
| **Energy fit** | "Excited about smart grid, IoT at scale, decarbonisation" |
| **Azure** | "Experienced with Azure ecosystem; Databricks transfers directly" |

---

## FINAL PREPARATION CHECKLIST

### Technical Prep
- [ ] Review Azure Databricks vs AWS Databricks differences
- [ ] Brush up on Azure Data Factory concepts
- [ ] Prepare RAG/LangChain code examples to discuss
- [ ] Review Delta Lake features (time travel, Z-ORDER, OPTIMIZE)

### Company Research
- [ ] Read CLP's latest annual report (sustainability section)
- [ ] Check CLP news for recent digital transformation updates
- [ ] Review Hong Kong's AI governance framework

### Logistics
- [ ] Test video/audio setup
- [ ] Quiet environment secured
- [ ] Keep JD and notes accessible (but off-camera)
- [ ] Join 5 minutes early

### Mindset
- [ ] This is a conversation, not an interrogation
- [ ] You have exactly what they need: scale + Databricks + GenAI
- [ ] Show enthusiasm for energy sector transformation
- [ ] Listen carefully – adapt answers to what they're really asking

---

## CLOSING STATEMENT

**When they ask "Any final thoughts?":**

> "I want to emphasise my genuine excitement about this opportunity. The energy sector is at an inflection point – smart grids, decarbonisation, AI-driven operations. CLP is leading this transformation in Asia, and I want to be part of building the data infrastructure that makes it possible.
>
> I bring proven experience scaling data platforms to billions of events daily, hands-on GenAI implementation, and the leadership skills to build and grow high-performing teams. I'm confident I can make an immediate impact while learning the unique challenges of the energy domain.
>
> Thank you for your time today. I look forward to the possibility of joining CLP."

---

**Good luck tomorrow! You've got this.** 🚀
