# Technical Scenarios — Solutions & Frameworks
## Google Cloud Data & Analytics Lead, Cloud Consulting

---

## 🎯 Scenario 5: AI-Enabled Data Platform (L7 Differentiator)
> **Context:** Enterprise client wants to embed GenAI/ML into their data platform. They have 50TB in BigQuery, siloed ML experiments, no MLOps, and a mandate from the CEO: "AI in production in 6 months."
> **Your Role:** Google Cloud Lead Architect + Practice Lead — own technical strategy, delivery governance, and practice asset creation.

---

### 📋 DISCOVER (Weeks 1-3)

#### Stakeholder Map
| Role | Name | Influence | Interest | Pain Point | Success Metric |
|------|------|-----------|----------|------------|----------------|
| CEO / CDO | | High | High | "AI is a black box, no ROI visibility" | $XM revenue from AI use cases |
| CTO / VP Engineering | | High | High | "ML models don't reach production" | 5+ models serving, <2 week deploy |
| Head of Data Science | | Med | High | "Feature engineering duplicated, no governance" | Feature store adoption 80% |
| Data Engineering Lead | | High | High | "Pipeline breaks when DS changes features" | Zero training-serving skew incidents |
| CISO / Compliance | | High | Med | "PII in training data, model explainability" | 100% model cards, audit trail |
| SI Partner (Delivery) | | Med | High | "Scope unclear, skills gap" | Certified team, on-time delivery |

#### Current State Assessment
```
DATA LANDSCAPE:
├── BigQuery: 50TB, 2000+ tables, 500+ daily queries
├── ML Experiments: 50+ notebooks, 10 models in Vertex AI (unmanaged)
├── Feature Engineering: Ad-hoc SQL in notebooks, no versioning
├── Serving: 2 models on Vertex AI Endpoints (manual deploy)
├── Governance: None — no lineage, no model cards, no drift monitoring
├── Team: 15 DE, 8 DS, 3 MLOps (new hires)
└── Skills Gap: 0 Vertex AI certifications, 20% BQML knowledge
```

#### Business Drivers & KPIs
| Driver | Target | Measurement |
|--------|--------|-------------|
| **Revenue from AI** | $5M ARR in 18 months | Attributed revenue per use case |
| **Model Velocity** | Idea → Production in 2 weeks | Cycle time (commit → serving) |
| **Governance** | 100% models with cards | Model Registry compliance |
| **Cost Control** | <$50K/mo ML platform | Vertex AI + BQML spend tracking |
| **Team Enablement** | 100% certified | Vertex AI, MLOps certifications |

---

### 🏗️ DESIGN (Weeks 3-6)

#### Architecture Decision Records (ADRs)

**ADR-001: Unified Feature Store on Vertex AI Feature Store (Online + Offline)**
- **Context:** DS teams recreate features; training-serving skew caused 3 incidents
- **Decision:** Vertex AI Feature Store (BigQuery backend for offline, Bigtable for online)
- **Alternatives:** 
  - Feast (self-managed) — more control, but ops burden on 3-person MLOps team
  - BigQuery only — no online serving <10ms
- **Consequences:** +Managed, +BQ integration, -Bigtable cost, -Learning curve
- **Mitigation:** Partner enables Feast migration path if needed later

**ADR-002: MLOps Pipeline on Vertex AI Pipelines (Kubeflow)**
- **Context:** Manual notebook → model → deploy; no reproducibility
- **Decision:** Vertex AI Pipelines with Dataform for feature materialization
- **Alternatives:**
  - Composer (Airflow) — team knows it, but no ML-native components
  - Custom Kubernetes — too much infra for current team
- **Consequences:** +ML-native, +Model Registry, +Traffic splitting, -Less flexible than Airflow
- **Mitigation:** Composer for data prep, Vertex AI Pipelines for training/serving

**ADR-003: Model Governance — Model Cards + Drift Monitoring + Approval Gates**
- **Context:** CISO requires audit trail; CEO wants ROI visibility
- **Decision:** 
  - Model Cards (auto-generated from pipeline metadata)
  - Vertex AI Model Monitoring (drift, skew, explanation)
  - Approval gate: DS Lead → MLOps Lead → CISO (automated via Pipeline)
- **Alternatives:** Manual review — doesn't scale
- **Consequences:** +Compliance, +Velocity (automated), -Pipeline complexity

**ADR-004: GenAI Integration — RAG on Vertex AI Search + Conversation**
- **Context:** CEO wants "Chat with Data" for business users
- **Decision:** Vertex AI Search (unstructured) + Vertex AI Conversation + BQ structured data via NL2SQL
- **Alternatives:** Custom LangChain — faster POC, no enterprise governance
- **Consequences:** +Managed, +IAM integration, -Less customization

#### Target Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI-ENABLED DATA PLATFORM                             │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│   INGEST     │  PROCESSING  │   FEATURES   │   TRAINING   │    SERVING     │
├──────────────┼──────────────┼──────────────┼──────────────┼────────────────┤
│ Pub/Sub      │ Dataflow     │ Vertex AI    │ Vertex AI    │ Vertex AI      │
│ Datastream   │ (feature     │ Feature      │ Pipelines    │ Endpoints      │
│ CDC          │  engineering)│ Store        │ (Kubeflow)   │ (online)       │
│              │ Dataform     │ (BigQuery +  │ Model        │ BQML           │
│              │ (SQL trans-  │  Bigtable)   │ Registry     │ (batch)        │
│              │  formations) │              │              │ Vertex AI      │
│              │              │              │              │ Search/Conv    │
├──────────────┼──────────────┼──────────────┼──────────────┼────────────────┤
│ GOVERNANCE   │   ORCHESTRATION                  │   MONITORING             │
├──────────────┼──────────────────────────────────┼──────────────────────────┤
│ Dataplex     │ Composer (data)                  │ Vertex AI Model          │
│ (lineage,    │ + Vertex AI Pipelines (ML)       │ Monitoring               │
│  quality,    │ Cloud Scheduler (triggers)       │ Cloud Monitoring         │
│  policy)     │                                  │ (drift, skew, latency)   │
│ Model Cards  │                                  │ Looker (ML metrics)      │
│ (auto-gen)   │                                  │                          │
└──────────────┴──────────────────────────────────┴──────────────────────────┘
```

#### Migration / Build Wave Plan
| Wave | Scope | Duration | Team | Success Criteria |
|------|-------|----------|------|------------------|
| **0: Foundation** | Landing zone, Feature Store, Model Registry, IAM | 3 weeks | 2 Google Arch + 4 Partner + 2 Client | Feature Store ready, 1 pilot feature |
| **1: Batch ML** | Migrate 3 highest-value batch models (churn, LTV, demand) | 6 weeks | 2 Google + 6 Partner + 4 Client | 3 models in Registry, drift monitoring, <2 week deploy |
| **2: Real-time ML** | Fraud detection <100ms, Feature Store online | 8 weeks | 3 Google + 8 Partner + 4 Client | Online serving <50ms, 99.9% uptime |
| **3: GenAI** | Vertex AI Search (docs) + Conversation (NL2SQL) | 6 weeks | 2 Google + 4 Partner + 3 Client | 50 pilot users, 80% query accuracy |
| **4: Platform Hardening** | Cost optimization, auto-retraining, disaster recovery | 4 weeks | 1 Google + 2 Partner + 2 Client | Cost <$50K/mo, RTO <4hr, RPO <1hr |

---

### 🚀 DELIVER (Weeks 6-30)

#### Governance Model
```
Steering Committee (Monthly): CDO, CTO, CISO, Google Practice Lead, SI Practice Lead
    │
    ├── Technical Architecture Review (Bi-weekly): Google Lead Arch ↔ SI Lead Arch
    ├── MLOps Working Group (Weekly): MLOps leads, DS Lead, DE Lead
    ├── Model Approval Board (Per model): DS Lead → MLOps Lead → CISO (automated)
    └── Cost Review (Monthly): FinOps lead, Practice Lead, CFO delegate
```

#### Quality Gates per Wave
1. **Architecture Review** — ADR sign-off, security review, cost model
2. **Code Complete** — Unit tests >80%, integration tests pass
3. **Automated Validation** — Data diff, model metric thresholds, latency benchmarks
4. **Model Card Review** — Auto-generated, DS Lead approves, CISO acknowledges
5. **Staging Deploy** — Canary 10%, monitoring 48hr, rollback <5min
6. **Production Go/No-Go** — All gates green, Steering Committee sign-off

#### Partner Management (SI: 18 consultants)
| Workstream | Google Owns | SI Owns | Shared |
|------------|-------------|---------|--------|
| Feature Engineering | Architecture, Feature Store design | Implementation, testing | Code review, quality gates |
| MLOps Pipelines | Pipeline templates, Model Registry config | DAG development, custom components | CI/CD, testing |
| Model Training | Hyperparameter strategy, evaluation | Experiment tracking, training runs | Model selection |
| Serving/Monitoring | Endpoint architecture, alerting | Deployment, runbooks | Incident response |
| GenAI | Search/Conversation architecture | Indexing, prompt engineering | UAT, feedback loop |

---

### 📊 OPERATE (Week 30+)

#### Hypercare (8 weeks)
- **Support Model:** Google (L2/L3) + SI (L1) rotation
- **SLAs:** P1=30min, P2=2hr, P3=8hr (model serving); P1=4hr (batch)
- **Dashboards:** Model latency, drift score, feature freshness, cost/endpoint

#### Knowledge Transfer & Asset Creation
| Asset | Description | Reusability |
|-------|-------------|-------------|
| **AI Platform Blueprint** | Terraform modules: Feature Store, Pipelines, Endpoints, Monitoring | 100% — deploy to new project in 2 hours |
| **MLOps Pipeline Templates** | Vertex AI Pipeline templates: training, evaluation, deployment | 90% — parameterize per model |
| **Model Card Generator** | Auto-generates from pipeline metadata + evaluation metrics | 100% |
| **GenAI Starter Kit** | Vertex AI Search index config + Conversation agent template | 80% — customize corpus |
| **Cost Optimization Playbook** | Slot reservations, endpoint autoscaling, Bigtable sizing | 100% |
| **Certification Program** | 12-week curriculum: Vertex AI, MLOps, Feature Store | 100% — partner + client teams |

#### Expansion Scoping (Quarterly Business Review)
| Opportunity | Estimated Value | Timeline | Investment |
|-------------|----------------|----------|------------|
| **Real-time Personalization** | $2M ARR | 6 months | +4 DE, +2 DS |
| **Supply Chain Optimization** | $3M ARR | 9 months | +3 DE, +1 DS |
| **Document Intelligence (GenAI)** | $1.5M ARR | 4 months | +2 DE, GenAI specialization |
| **Partner Enablement** | $500K services | Ongoing | Train 20 partner consultants |

---

### 🎯 L7 Talking Points (Use in Round 3, 5, 6)

#### "How do you decide build vs buy for AI platform components?"
> "I use a **capability maturity model**: 
> 1. **Commodity** (Feature Store, Model Registry, Monitoring) → Buy managed (Vertex AI)
> 2. **Differentiating** (Custom features, domain models, business logic) → Build with managed primitives
> 3. **Experimental** (GenAI agents, novel architectures) → POC on managed, evaluate build if scale demands
> 
> This saved the client $200K/yr vs self-managed Feast + Kubeflow, while keeping 90% flexibility."

#### "How do you govern AI at scale without slowing innovation?"
> "**Governance as code, not process.** 
> - Model Cards auto-generated from pipeline metadata (no manual docs)
> - Drift alerts → auto-create JIRA → auto-rollback if threshold breached
> - Approval gates in pipeline: DS Lead (technical) → MLOps (operational) → CISO (compliance) — all async, <4hr total
> - Result: 5 models deployed in month 1, zero governance violations, CISO confidence increased"

#### "What's your AI practice building strategy?"
> "**Asset-first, not project-first.** Every engagement produces:
> 1. **Reusable Terraform module** (infrastructure)
> 2. **Pipeline template** (MLOps)
> 3. **Governance config** (Model Cards, monitoring)
> 4. **Certification path** (partner + client)
> 
> After 3 engagements, new AI platform deployment = 2 weeks vs 3 months. Practice margin improved from 18% → 32%."

#### "How do you handle the 'GenAI hype vs reality' conversation with executives?"
> "**Lead with use case classification, not technology:**
> | Category | Example | Approach | Timeline |
> |----------|---------|----------|----------|
> | **Quick Win** | NL2SQL for analysts | Vertex AI Conversation + BQ | 4 weeks |
> | **Strategic** | RAG for knowledge base | Vertex AI Search + custom embeddings | 8 weeks |
> | **Transformational** | Autonomous agents | Custom + Vertex AI | 6+ months |
> 
> I show TCO for each, pilot the Quick Win first, build credibility, then fund Strategic."

---

### 📈 Metrics That Matter (L7 Scorecard)
| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Practice Revenue (AI)** | $0 | $3M ARR | Quarterly |
| **Asset Reuse Rate** | 0% | 70% | Per engagement |
| **Partner Certification** | 0 | 15 Vertex AI certified | Quarterly |
| **Model Deployment Velocity** | 6 months | 2 weeks | Per model |
| **Training-Serving Skew Incidents** | 3/quarter | 0 | Real-time monitoring |
| **Client AI Maturity Score** | 1.2/5 | 3.5/5 | Annual assessment |

---

### 🔴 Red Flags to Avoid (L7 Interview)
- ❌ "I'd use Vertex AI for everything" — no nuance on build/buy
- ❌ "MLOps is just CI/CD for models" — misses feature store, drift, governance
- ❌ "GenAI is just prompt engineering" — misses RAG, evaluation, guardrails, cost
- ❌ "Data scientists should manage their own models" — misses MLOps separation of concerns
- ❌ No cost model for AI — endpoints, training, Feature Store Bigtable add up fast

---

*This scenario demonstrates L7 scope: technical strategy + delivery governance + practice asset creation + commercial outcomes + partner enablement + team development.*