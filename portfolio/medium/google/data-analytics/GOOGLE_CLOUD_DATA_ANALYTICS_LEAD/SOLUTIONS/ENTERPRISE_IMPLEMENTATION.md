# Enterprise Cloud Implementation — Landing Zone, Governance & Change Management
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)

---

## 🎯 Context
> **Client:** Multinational Financial Services Institution (FSI), HQ Singapore, operations in 12 countries
> **Trigger:** Regulatory mandate (MAS-TRM 2025) + contract expiration on-prem (Teradata, Oracle, Hadoop)
> **Scope:** 500TB data estate, 2000+ pipelines, 300+ users, 5 LOBs, 8-month deadline
> **Your Role:** Google Cloud Lead Architect + Program Lead — own landing zone, governance framework, and delivery across 3 SI partners

---

## 🏗️ 1. LANDING ZONE ARCHITECTURE (Weeks 1-4)

### Organizational Hierarchy
```
Organization: fsi-corp.com
├── Folder: platforms
│   ├── Folder: data-analytics
│   │   ├── Project: data-platform-prod (Shared VPC host)
│   │   ├── Project: data-platform-nonprod
│   │   ├── Project: bigquery-prod (Analytics hub)
│   │   ├── Project: vertex-ai-prod (ML platform)
│   │   └── Project: dataplex-prod (Governance)
│   ├── Folder: networking
│   │   ├── Project: network-host-prod (Shared VPC, Cloud Interconnect)
│   │   └── Project: network-host-nonprod
│   └── Folder: security
│       ├── Project: security-central (SCC, Log sink, KMS)
│       └── Project: identity (Workforce Identity Federation)
├── Folder: lob-finance
│   ├── Project: fin-reporting-prod
│   └── Project: fin-risk-prod
├── Folder: lob-risk
│   └── Project: risk-models-prod
├── Folder: lob-marketing
│   └── Project: mkt-analytics-prod
└── Folder: sandbox
    └── Project: *-sandbox-* (Auto-expire 30 days)
```

### Network Topology (Hub-and-Spoke)
```
┌─────────────────────────────────────────────────────────────────┐
│                     SHARED VPC (network-host-prod)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Subnet:    │  │  Subnet:    │  │  Subnet:    │             │
│  │  mgmt       │  │  data-prod  │  │  dmz        │             │
│  │  10.0.0/24  │  │  10.0.1/24  │  │  10.0.2/24  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
│  ┌──────▼────────────────▼────────────────▼──────┐              │
│  │         CLOUD INTERCONNECT (Dedicated)        │              │
│  │  2x 10Gbps → Singapore DC1 + DC2 (Active/Active)│              │
│  └────────────────────────┬──────────────────────┘              │
└───────────────────────────│─────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │  DC1     │       │  DC2     │       │  Cloud   │
   │ On-prem  │       │ On-prem  │       │ Region   │
   │ (Prod)   │       │ (DR)     │       │ (Backup) │
   └──────────┘       └──────────┘       └──────────┘
```

### Connectivity & Security
| Component | Configuration | MAS-TRM Mapping |
|-----------|---------------|-----------------|
| **Interconnect** | 2x 10Gbps, Dedicated, 99.99% SLA | TRM 6.2 (Resilient connectivity) |
| **Cloud Armor** | WAF rules, Geo-blocking, Rate limiting | TRM 7.1 (Network security) |
| **Cloud NAT** | Regional, HA, no public IPs on workloads | TRM 7.2 (Network segmentation) |
| **Private Service Connect** | APIs (BigQuery, Vertex AI, Storage) no internet | TRM 7.3 (Private access) |
| **Firewall Rules** | Default deny, allow by tag, logging enabled | TRM 7.1, 7.4 |

---

## 🔐 2. SECURITY & COMPLIANCE FRAMEWORK (Weeks 2-6)

### IAM Architecture (Least Privilege + Blast Radius Control)
```
ORG POLICIES (Enforced at Folder: platforms/data-analytics)
├── constraints/iam.disableServiceAccountKeyCreation = TRUE
├── constraints/iam.allowedPolicyMemberDomains = fsi-corp.com
├── constraints/gcp.resourceLocations = asia-southeast1, asia-south1 (DR)
├── constraints/compute.vmExternalIpAccess = DENY (except DMZ)
├── constraints/sql.restrictPublicIp = TRUE
└── constraints/bigquery.restrictCrossRegionQueries = TRUE
```

### Role Design (Custom Roles + Predefined)
| Persona | Custom Role | Predefined Roles | Projects |
|---------|-------------|------------------|----------|
| **Platform Admin** | `dataPlatform.admin` | `roles/owner` (project) | data-platform-* |
| **Data Engineer** | `dataEngineer.builder` | `roles/bigquery.dataEditor`, `roles/dataflow.developer`, `roles/dataproc.editor` | Assigned via group |
| **Data Scientist** | `dataScientist.builder` | `roles/vertexai.user`, `roles/bigquery.dataViewer`, `roles/dataplex.viewer` | Assigned via group |
| **Data Analyst** | `dataAnalyst.reader` | `roles/bigquery.dataViewer`, `roles/looker.viewer` | bigquery-prod |
| **Security Auditor** | — | `roles/securitycenter.findingsViewer`, `roles/logging.viewer` | security-central |
| **SI Partner** | `partner.delivery` | `roles/dataproc.worker`, `roles/dataflow.worker`, `roles/storage.objectCreator` | Time-bound, project-scoped |

### Encryption & Key Management (CMEK)
```
KMS Hierarchy (security-central project):
├── Key Ring: data-platform-prod
│   ├── Key: bigquery-prod (rotation: 90 days, auto)
│   ├── Key: cloud-storage-prod (rotation: 90 days)
│   ├── Key: dataproc-prod (rotation: 90 days)
│   ├── Key: vertex-ai-prod (rotation: 90 days)
│   └── Key: pubsub-prod (rotation: 90 days)
├── Key Ring: data-platform-dr (asia-south1)
│   └── Keys: mirror of prod (manual failover)
└── Key Ring: external-sharing
    └── Key: partner-delivery (external key access via IAM conditions)
```

**Key Access Policy:**
- Service accounts: `cloudkms.cryptoKeyEncrypterDecrypter` on specific key
- Humans: `cloudkms.cryptoKeyViewer` only (via break-glass process)
- **Key destruction = data destruction** — documented, tested, approved by CISO

### Data Governance (Dataplex)
```
LAKE: fsi-data-lake (asia-southeast1)
├── ZONE: raw (Cloud Storage buckets, immutable, 7-yr retention)
│   ├── ASSET: landing-bucket (ingest, DLP scan on write)
│   └── ASSET: cdc-bucket (Datastream output)
├── ZONE: curated (BigQuery datasets, partitioned, clustered)
│   ├── ASSET: fin-reporting (PII tagged, RLS policies)
│   ├── ASSET: risk-models (model features, lineage tracked)
│   └── ASSET: mkt-analytics (aggregated, no PII)
├── ZONE: consumed (Looker models, Vertex AI Feature Store)
│   ├── ASSET: looker-prod (semantic layer, certified)
│   └── ASSET: feature-store-prod (online/offline, monitored)
└── GOVERNANCE:
    ├── DATA QUALITY: 50+ rules (freshness, completeness, validity, consistency)
    ├── DATA LINEAGE: Column-level, cross-system (Datastream → BQ → Looker)
    ├── POLICY TAGS: PII, PCI, SOX, MAS-TRM — enforced via IAM conditions
    └── GLOSSARY: 200+ business terms, stewards per LOB
```

### MAS-TRM 2025 Control Mapping
| MAS-TRM Domain | Control | GCP Implementation | Evidence |
|----------------|---------|-------------------|----------|
| **6.1 Technology Risk Governance** | Risk framework, board oversight | Org policies, folder structure, audit logs | Policy configs, SCC findings |
| **6.2 Resilience** | RTO/RPO, DR testing | Dual-region BQ, Interconnect HA, backup | DR test reports (quarterly) |
| **7.1 Network Security** | Segmentation, monitoring | Shared VPC, Cloud Armor, Private SC | Firewall configs, flow logs |
| **7.2 Endpoint Security** | Hardening, patching | OS Config, Shielded VMs, Confidential Computing | Patch compliance reports |
| **7.3 Identity & Access** | Least privilege, MFA | Workforce Identity Federation, conditional IAM | IAM recommender, access reviews |
| **7.4 Data Protection** | Classification, encryption, DLP | Dataplex policy tags, CMEK, DLP API | Scan reports, key rotation logs |
| **7.5 Application Security** | Secure SDLC, secrets | Secret Manager, Binary Authorization, Cloud Build | Pipeline configs, attestations |
| **8.1 Third Party Risk** | Vendor assessment, contracts | Partner scorecards, contract clauses | Quarterly partner reviews |
| **9.1 Incident Management** | Detection, response, reporting | Cloud Monitoring, Chronicle, runbooks | MTTD/MTTR metrics, postmortems |

---

## 👥 3. CHANGE MANAGEMENT & TEAM ENABLEMENT (Weeks 4-12)

### Stakeholder Engagement Model
```
EXECUTIVE STEERING COMMITTEE (Monthly)
├── Chair: CDO
├── Members: CTO, CISO, CFO, LOB Heads, Google Practice Lead, SI Leads
├── Decisions: Scope changes >$100K, timeline >2 weeks, risk acceptance
└── Output: Go/No-Go per wave, budget reallocation, escalation resolution

TECHNICAL ARCHITECTURE BOARD (Bi-weekly)
├── Chair: Google Lead Architect
├── Members: Client Enterprise Architect, SI Lead Architects, Security Lead
├── Decisions: ADRs, technology selection, pattern approval
└── Output: Architecture decision records, pattern library updates

LOB WORKING GROUPS (Weekly per LOB)
├── Finance: Reporting, regulatory, risk
├── Risk: Models, stress testing, compliance
├── Marketing: Customer analytics, personalization
└── Operations: Supply chain, fraud, operations
```

### Skills Transformation Program
| Cohort | Target | Curriculum | Duration | Certification Target |
|--------|--------|------------|----------|---------------------|
| **Wave 1: Platform Team** | 15 DE + 5 MLOps | GCP Fundamentals → Data Engineering → Architect | 12 weeks | Professional Data Engineer (100%) |
| **Wave 2: Data Science** | 12 DS + 3 MLOps | Vertex AI → MLOps → Feature Store | 10 weeks | Professional ML Engineer (80%) |
| **Wave 3: Analysts** | 50+ Analysts | Looker → BigQuery SQL → Self-service | 6 weeks | Looker Business Analyst (60%) |
| **Wave 4: LOB SMEs** | 30 SMEs | Domain data ownership, Data Mesh principles | 4 weeks | Internal: Data Product Owner |

**Enablement Mechanics:**
- **Google-led:** Architecture workshops (2 days/wave), office hours (weekly)
- **Partner-led:** Hands-on labs (Qwiklabs credits), migration execution
- **Client-led:** Internal hackathons, community of practice (monthly)
- **Measurement:** Pre/post assessment, certification rate, project contribution

### Communication Plan
| Audience | Channel | Cadence | Content |
|----------|---------|---------|---------|
| **Executive** | Steering deck + 1-pager | Monthly | ROI, risk, timeline, decisions needed |
| **Technical** | Architecture decisions (Confluence) | Per ADR | Context, decision, alternatives, consequences |
| **Delivery** | Sprint demo + retro | Bi-weekly | Working software, blockers, metrics |
| **All Hands** | Town hall | Quarterly | Vision, progress, recognition, Q&A |
| **Partner** | Joint business review | Quarterly | Pipeline, utilization, certifications, assets |

---

## 🤝 4. MULTI-PARTNER DELIVERY MODEL (3 SIs)

### Partner Allocation
| Partner | Tier | Scope | Team Size | Commercial Model |
|---------|------|-------|-----------|------------------|
| **Accenture** | Strategic | Finance LOB migration, reporting | 40 | Co-delivery (Google 30% arch / SI 70% delivery) |
| **TCS** | Strategic | Risk LOB, ML platform, Vertex AI | 35 | Google-led (Google arch + quality, SI delivery) |
| **Local SI (SEA)** | Select | Marketing LOB, Data Mesh pilots | 20 | Partner-led (Google quality gates only) |

### Governance Across Partners
```
JOINT DELIVERY OFFICE (JDO) — Weekly Sync
├── Google: Practice Lead, Lead Architect, Delivery Lead, PM
├── Accenture: Delivery Lead, Tech Lead, PM
├── TCS: Delivery Lead, Tech Lead, PM
├── Local SI: Delivery Lead, PM
└── Client: Program Manager, Enterprise Architect

SHARED ARTIFACTS (Single Source of Truth):
├── Migration Wave Plan (Smartsheet) — all partners update
├── Risk Register (Jira) — auto-escalation >48hr
├── Quality Dashboard (Looker) — automated from CI/CD
├── Architecture Decision Log (Confluence) — all ADRs
└── Knowledge Base (GitBook) — runbooks, patterns, FAQs
```

### Quality Gates (Enforced by Google)
| Gate | Criteria | Tool | Blocker? |
|------|----------|------|----------|
| **Code Review** | 2 approvals (1 Google, 1 SI), security scan | GitHub + SCA | Yes |
| **Unit Test** | >80% coverage, mutation testing | pytest/JUnit | Yes |
| **Integration Test** | End-to-end data flow validated | Custom framework | Yes |
| **Data Validation** | Row count ±0.1%, checksum match, business rules | Great Expectations | Yes |
| **Performance** | Query latency < SLA, cost within model | BQ slots, Dataflow metrics | Yes |
| **Security** | VPC-SC, CMEK, IAM conditions, DLP scan | Policy Analyzer, SCC | Yes |
| **Documentation** | Runbook, architecture diagram, data dictionary | Confluence | Soft (warn) |

---

## 📊 5. PROGRAM METRICS & REPORTING

### Executive Dashboard (Monthly)
| KPI | Target | Current | Trend | Owner |
|-----|--------|---------|-------|-------|
| **Migration Progress** | 100% in 8 months | 65% | ↗ | Program Lead |
| **Data Fidelity** | 99.99% | 99.97% | → | QA Lead |
| **Cost vs Budget** | ≤$1.2M/yr (BQ) | $1.15M | ↘ | FinOps Lead |
| **Query Performance** | 80% faster | 72% | ↗ | Arch Lead |
| **User Adoption** | 90% reports migrated | 68% | ↗ | Change Lead |
| **Team Certification** | 100% Prof. Data Eng | 78% | ↗ | Enablement Lead |
| **Partner Utilization** | 85% | 82% | → | Partner Lead |
| **Open Risks (High)** | 0 | 2 | ↘ | Risk Owner |

### Financial Model (P&L View)
```
REVENUE (Google Cloud Consulting)
├── Architecture & Advisory: $1.2M (Fixed fee, milestone-based)
├── Co-delivery (Accenture): $2.4M (T&M, capped)
├── Quality Governance (TCS): $800K (Fixed fee)
├── Enablement & Assets: $600K (Fixed fee)
└── Managed Services (Year 1): $400K (Monthly retainer)
TOTAL REVENUE: $5.4M

COSTS
├── Google Consultants (8 FTE): $2.4M
├── Partner Enablement: $300K
├── Asset Development: $200K
├── Travel/Events: $150K
└── Overhead: $450K
TOTAL COST: $3.5M

MARGIN: 35% ($1.9M)
TARGET: >30% (Consulting benchmark)
```

---

## 🚀 6. CUTOVER & HYPERCARE STRATEGY

### Cutover Approach: Phased Dual-Write + CDC
```
PHASE 1: Historical Load (Weeks 1-16, 4 waves)
├── Extract → Transform → Load (Dataproc/Dataflow)
├── Validation: Row count, checksum, business reconciliation
├── Sign-off: Business UAT + Automated validation report

PHASE 2: CDC Sync (Weeks 17-28, parallel)
├── Datastream (Oracle/Teradata) → Pub/Sub → Dataflow → BigQuery
├── Dual-write: Application writes to both old + new
├── Reconciliation: Daily automated diff, weekly business review
├── Target: <0.1% discrepancy for 14 consecutive days

PHASE 3: Cutover Weekend (Week 29)
├── Friday 18:00: Freeze on-prem writes
├── Saturday: Final CDC catch-up, validation, smoke tests
├── Sunday: DNS switch, application cutover, monitoring
├── Monday 08:00: Go-live, hypercare begins

PHASE 4: Hypercare (Weeks 30-34, 5 weeks)
├── Dedicated war room: Google + SI + Client SMEs
├── P1: 30min response, P2: 2hr, P3: 8hr
├── Daily issue triage, weekly executive update
├── Performance tuning sprints (Week 1, 3)
└── Knowledge transfer sign-off (Week 5)
```

### Rollback Plan
| Trigger | Action | RTO | RPO |
|-------|--------|-----|-----|
| **Data fidelity <99.9%** | Re-enable on-prem reads, pause CDC | 2 hours | 0 (CDC replay) |
| **Performance regression >50%** | Route critical queries to on-prem | 30 min | 0 |
| **Security incident** | Isolate affected project, forensic | 1 hour | N/A |
| **Mass user rejection** | Parallel run extended 2 weeks | 4 hours | 0 |

---

## 📦 7. REUSABLE ASSETS CREATED (Practice Scaling)

| Asset | Description | Reuse Count | Revenue Impact |
|-------|-------------|-------------|----------------|
| **Landing Zone Terraform** | Org policies, projects, networking, IAM, KMS | 5 engagements | $200K saved/setup |
| **MAS-TRM Control Map** | 47 controls → GCP config, evidence automation | 3 FSI clients | $150K saved/audit |
| **Migration Wave Template** | Assessment → Pilot → Waves → Cutover → Operate | 7 migrations | 40% faster planning |
| **Dataplex Governance Pack** | Zones, assets, quality rules, policy tags, glossary | 4 clients | $100K saved/setup |
| **Partner Scorecard Framework** | 5-dimension scorecard, escalation, probation | Practice-wide | 30% defect reduction |
| **FinOps Dashboard** | BQ cost attribution, slot optimization, alerts | 10+ projects | 25% avg cost reduction |
| **Certification Curriculum** | 12-week program, labs, assessments, mentorship | 200+ consultants | 92% pass rate |

---

## 🎯 L7 Interview Evidence (STAR Format)

### S: Situation
"Multinational FSI in Singapore, 500TB migration, MAS-TRM regulatory deadline, 3 SI partners, 8-month timeline, $5.4M engagement."

### T: Task
"Design landing zone, governance framework, and delivery model that satisfies MAS-TRM, enables 300+ users across 5 LOBs, and builds reusable practice assets."

### A: Action
1. **Architected org hierarchy + Shared VPC + Interconnect** meeting MAS-TRM network segmentation
2. **Built CMEK + Dataplex governance** with policy tags for PII/PCI/SOX/MAS-TRM, column-level lineage
3. **Created 3-tier partner model** with quality gates enforced by Google, joint delivery office
4. **Launched 12-week certification program** — 100% platform team certified, 80% DS certified
5. **Codified 7 reusable assets** (Terraform, governance packs, wave templates) now used across practice

### R: Result
- **Delivered on time, on budget** — 500TB migrated, 99.99% fidelity, 8 months
- **MAS-TRM audit passed** — zero findings, evidence automated via Dataplex + SCC
- **Practice margin 35%** — assets reduced setup effort 40% on subsequent engagements
- **Team outcomes** — 100% retention, 12 promotions, 3 partners achieved Specialization
- **Client expansion** — $3M follow-on for AI platform (Vertex AI + GenAI)

---

## 🔴 L7 Differentiators Demonstrated

| Dimension | Evidence in This Engagement |
|-----------|----------------------------|
| **Strategic Architecture** | Landing zone + governance as reusable platform, not one-off project |
| **Commercial Ownership** | $5.4M P&L, 35% margin, $3M expansion pipeline |
| **Partner Ecosystem** | 3 SIs governed via JDO, quality gates, tiered commercial models |
| **Organizational Change** | 300+ users transformed, certification program, Data Mesh adoption |
| **Regulatory Expertise** | MAS-TRM mapped to GCP controls, automated evidence, audit passed |
| **Asset-First Mindset** | 7 assets created, reused across 5+ engagements, practice scaling |
| **Technical + Business Fluency** | CISO conversations (CMEK, VPC-SC) + CFO conversations (TCO, margin) |

---

*This artifact demonstrates L7 scope: enterprise architecture + regulatory compliance + multi-partner governance + P&L ownership + practice building + team transformation.*