# Best Practice Assets Portfolio
## Reusable Intellectual Property for Google Cloud Data & Analytics Delivery

---

## 📦 Asset Catalog Overview

| # | Asset | Type | Adoption | Your Role | Interview Story |
|---|-------|------|----------|-----------|-----------------|
| 1 | **Migration Runbook** | Playbook + Code | 3 partners, 15 projects, 60% faster delivery | Author & Maintainer | "Open-sourced internally, adopted by 3 SI firms" |
| 2 | **Terraform: GCP Data Foundation** | IaC Module | 8 customer engagements | Architect | "15 configs → 1 module, 10-min env spin-up" |
| 3 | **Dataflow Template Library** | Pipeline Patterns | 500+ deployments | Lead Developer | "Dead-letter, schema evolution, monitoring baked in" |
| 4 | **Dataplex Policy Packs** | Governance Configs | 3 industries (FinServ, Healthcare, Retail) | Product Owner | "Auto-applied via Terraform, DLP integration" |
| 5 | **Cost Governance Dashboard** | Looker + BQ | 12 customers | Designer | "Real-time + forecast + optimization recommendations" |

---

## 1️⃣ MIGRATION RUNBOOK: "TERADATA TO BIGQUERY PLAYBOOK"

### What It Is
A 50-page executable playbook covering the full migration lifecycle with checklists, runbooks, rollback procedures, and decision trees.

### Structure
```
MIGRATION_RUNBOOK/
├── 01_ASSESS/
│   ├── inventory_checklist.md
│   ├── query_analysis_notebook.ipynb
│   ├── tco_calculator.py
│   └── risk_register_template.xlsx
├── 02_PILOT/
│   ├── pilot_scope_template.md
│   ├── success_criteria.yaml
│   ├── validation_framework.py
│   └── go_nogo_checklist.md
├── 03_MIGRATE/
│   ├── wave_plan_template.xlsx
│   ├── historical_load_runbook.md
│   ├── cdc_sync_runbook.md
│   ├── dual_write_validation.py
│   └── cutover_runbook.md
├── 04_OPTIMIZE/
│   ├── partition_review.sql
│   ├── mv_candidates.sql
│   ├── bi_engine_setup.md
│   └── reservation_calculator.py
├── 05_SECURITY_GOVERNANCE/
│   ├── vpc_sc_terraform/
│   ├── cmek_setup.md
│   ├── policy_tags_taxonomy.csv
│   └── dlp_integration.py
└── 06_HANDOFF/
    ├── kt_plan_template.md
    ├── runbook_handoff.md
    └── hypercare_checklist.md
```

### Key Differentiators
- **Executable**: Every checklist has automation (Python/SQL/Terraform)
- **Validated**: 15 production migrations, zero data loss
- **Extensible**: Plugin architecture for Oracle, SQL Server, Netezza
- **Partner-Ready**: SI firms white-label and deliver independently

### Adoption Metrics
| Metric | Before Runbook | After Runbook | Improvement |
|--------|---------------|---------------|-------------|
| Assess Phase Duration | 4 weeks | 2 weeks | **50% faster** |
| Pilot Success Rate | 60% | 95% | **+35 pts** |
| Cutover Issues (P1) | 3.2/engagement | 0.1/engagement | **97% reduction** |
| Knowledge Transfer | Ad-hoc | Structured 30/60/90 | **Measurable** |
| Partner Ramp Time | 8 weeks | 3 weeks | **62% faster** |

### Interview Talking Points
> "I authored the Teradata→BigQuery Migration Runbook that's now used by 3 partner firms across 15 projects. It codifies 50+ migrations of learnings into executable checklists with automation. The key insight: migration isn't a lift-and-shift—it's a transformation opportunity. The runbook forces data quality assessment upfront, classifies workloads for the right migration pattern, and builds validation into every phase. Result: 60% faster assess, 95% pilot success, zero data loss cutovers."

---

## 2️⃣ TERRAFORM MODULE: "GCP DATA FOUNDATION"

### What It Is
A production-grade Terraform module that provisions the complete GCP data platform foundation in 10 minutes.

### Module Structure
```
terraform-google-data-foundation/
├── main.tf                 # Root module composition
├── variables.tf            # 47 variables with validation
├── outputs.tf              # 23 outputs for downstream
├── versions.tf             # Provider versions pinned
├── modules/
│   ├── network/            # VPC, subnets, PSC, DNS, NAT
│   ├── iam/                # Custom roles, conditions, deny policies
│   ├── bigquery/           # Datasets, reservations, BI Engine, MVs
│   ├── dataplex/           # Lake, zones, assets, policy tags
│   ├── composer/           # Airflow env, service account, configs
│   ├── dataflow/           # Service account, network, templates
│   ├── vertex_ai/          # Feature Store, Model Registry, Pipelines
│   ├── monitoring/         # Dashboards, alerts, SLOs, log routing
│   └── security/           # VPC-SC, CMEK, KMS, DLP, Binary Auth
├── examples/
│   ├── minimal/            # Dev environment (5 resources)
│   ├── standard/           # Standard prod (47 resources)
│   └── enterprise/         # Full MAS-TRM compliant (127 resources)
├── test/
│   ├── integration/        # Terratest + Go
│   └── unit/               # OPA policies
└── docs/
    ├── architecture.md
    ├── security_model.md
    └── migration_guide.md
```

### Key Features
| Feature | Implementation |
|---------|----------------|
| **Multi-environment** | Workspaces + tfvars (dev/staging/prod) |
| **Policy-as-Code** | OPA policies for security, naming, cost |
| **Drift Detection** | Cloud Build pipeline + driftctl |
| **Progressive Rollout** | Canary → Staging → Prod with approval gates |
| **Documentation** | Auto-generated via terraform-docs |

### Example: Enterprise Configuration (127 resources in 1 apply)
```hcl
module "data_foundation" {
  source  = "git::https://github.com/.../terraform-google-data-foundation.git//examples/enterprise"
  
  project_id       = "my-data-platform-prod"
  region           = "asia-southeast1"
  org_id           = "123456789"
  billing_account  = "ABCDEF-GHIJKL-MNOPQR"
  
  # Network
  vpc_cidr                    = "10.0.0.0/16"
  private_subnets             = ["10.0.1.0/24", "10.0.2.0/24"]
  psc_enabled                 = true
  dns_zone                    = "data-platform.internal"
  
  # Security
  vpc_sc_enabled              = true
  cmek_enabled                = true
  kms_key_rotation_days       = 90
  policy_tags_taxonomy        = "projects/123/locations/asia-southeast1/taxonomies/456"
  dlp_deidentify_templates    = ["pii-template", "financial-template"]
  
  # BigQuery
  bq_edition                  = "ENTERPRISE"
  slot_commitment_plan        = "THREE_YEAR"
  baseline_slots              = 2000
  bi_engine_reservation_gb    = 100
  
  # Dataplex
  lake_name                   = "enterprise-data-lake"
  raw_zone_gcs_bucket         = "gs://my-raw-zone"
  curated_zone_bq_datasets    = ["raw", "staging", "serving"]
  
  # Governance
  data_quality_schedule       = "0 2 * * *"
  lineage_enabled             = true
  
  labels = {
    environment = "production"
    team        = "data-platform"
    cost_center = "cc-12345"
  }
}
```

### Adoption Metrics
- **8 customer engagements** using this module
- **10 minutes** from `terraform apply` to running platform
- **127 resources** managed, **zero manual steps**
- **3 partner firms** certified to deliver with this module

### Interview Talking Points
> "I architected the GCP Data Foundation Terraform module that provisions a MAS-TRM compliant data platform in 10 minutes—127 resources including VPC-SC, CMEK, Dataplex, BigQuery Enterprise, Composer, Vertex AI, and monitoring. The key design principle: infrastructure as a product. We treat IaC like software—versioned, tested (Terratest + OPA), documented, with semantic versioning. Partners deliver with it, customers inherit it. It's the foundation that lets us spend Week 1 on business logic, not plumbing."

---

## 3️⃣ DATAFLOW TEMPLATE LIBRARY

### What It Is
12 production-hardened Dataflow templates covering the 80% of ingestion patterns, with dead-letter handling, schema evolution, and monitoring built-in.

### Template Catalog
| # | Template | Pattern | Use Case | Key Features |
|---|----------|---------|----------|--------------|
| 1 | **gcs-to-bq-batch** | Batch | Daily/hourly file loads | Partition pruning, schema validation, DML merge |
| 2 | **pubsub-to-bq-streaming** | Streaming | Real-time events | Exactly-once, windowing, late data, side inputs |
| 3 | **datastream-to-bq** | CDC | Database replication | Schema evolution, UPSERT, transaction grouping |
| 4 | **bq-to-bq-transform** | ELT | dbt-style transforms | SQL-based, incremental, testable |
| 5 | **multi-source-union** | Converge | Merge CRM + ERP + Web | Deduplication, source tracking, SCD2 |
| 6 | **ml-feature-extract** | Feature Eng | Vertex AI Feature Store | Point-in-time, time-travel, backfill |
| 7 | **reverse-etl** | Activation | BQ → SaaS (SF, Braze) | Batch + streaming, idempotent writes |
| 8 | **data-quality-scan** | Governance | Great Expectations in Beam | Expectation suites, quarantine, metrics |
| 9 | **schema-evolution** | Migration | Avro/Protobuf evolution | Backward compat, auto-migration, alerts |
| 10 | **change-data-capture** | CDC Custom | Legacy DB without Datastream | Debezium + custom transformers |
| 11 | **streaming-join** | Enrichment | Stream + Reference join | Side input refresh, TTL, cache warming |
| 12 | **dead-letter-reprocess** | Operations | DLQ inspection + replay | Automated classification, one-click replay |

### Template Architecture (All Templates Share)
```python
# Base template structure (simplified)
class DataflowTemplate:
    # 1. PARAMETERIZATION (via ValueProvider)
    params = {
        'input_location': ValueProvider,
        'output_table': ValueProvider,
        'schema_path': ValueProvider,
        'dead_letter_table': ValueProvider,
        'monitoring_topic': ValueProvider,
    }
    
    # 2. VALIDATION (First transform)
    def validate(element):
        result = schema_validator.validate(element)
        if not result.valid:
            yield DeadLetter(element, result.errors)
        else:
            yield ValidElement(element)
    
    # 3. TRANSFORMATION (Core logic)
    def transform(element):
        enriched = enrich_with_side_input(element)
        normalized = normalize(enriched)
        yield normalized
    
    # 4. SINK (Exactly-once to BQ)
    def write_to_bq(element):
        # Uses Storage Write API with stream-level exactly-once
        # Partitioned by date, clustered by high-cardinality key
        pass
    
    # 5. OBSERVABILITY (Built-in)
    metrics = {
        'records_in': Counter,
        'records_valid': Counter,
        'records_dlq': Counter,
        'processing_latency': Distribution,
        'watermark_lag': Gauge,
    }
```

### Adoption Metrics
- **500+ pipeline deployments** across 12 customers
- **Zero data loss** incidents in production
- **40% reduction** in pipeline development time
- **Standardized monitoring** across all pipelines

### Interview Talking Points
> "I built a Dataflow Template Library—12 patterns covering batch, streaming, CDC, ML features, reverse ETL. Every template has dead-letter handling, schema evolution, and monitoring baked in. The key insight: don't write pipelines, write *templates*. We parameterize everything via ValueProviders so the same template runs in dev/staging/prod with different configs. 500+ deployments, zero data loss. This is how you scale delivery: invest in the 20% of patterns that handle 80% of workloads."

---

## 4️⃣ DATAPLEX POLICY PACKS

### What It Is
Industry-specific governance configurations (Policy Tags, DQ Rules, DLP Templates) that auto-apply via Terraform.

### Pack Catalog
| Pack | Industry | Compliance | Contents |
|------|----------|------------|----------|
| **FinServ Pack** | Banking, Insurance | MAS-TRM, PCI-DSS, SOX | 47 Policy Tags, 23 DQ Rules, 8 DLP Templates |
| **Healthcare Pack** | Hospitals, Pharma | HIPAA, FHIR, GDPR | 38 Policy Tags, 19 DQ Rules, 6 DLP Templates |
| **Retail Pack** | E-commerce, Retail | PCI-DSS, CCPA, PDPA | 32 Policy Tags, 15 DQ Rules, 5 DLP Templates |

### FinServ Pack Detail (Example)
```yaml
# policy_tags_taxonomy.yaml
taxonomy: "projects/123/locations/asia-southeast1/taxonomies/finserv"
policy_tags:
  - id: "pii.ssn"
    display_name: "SSN"
    description: "Social Security Number - MAS-TRM restricted"
    parents: ["pii"]
    dlp_info_type: "US_SOCIAL_SECURITY_NUMBER"
    masking: "HASH_SHA256"
    
  - id: "financial.credit_card"
    display_name: "Credit Card"
    description: "PCI-DSS Cardholder Data"
    parents: ["financial"]
    dlp_info_type: "CREDIT_CARD_NUMBER"
    masking: "PARTIAL_MASK_LAST4"
    
  - id: "financial.account_number"
    display_name: "Bank Account"
    description: "MAS-TRM Account Information"
    parents: ["financial"]
    masking: "PARTIAL_MASK_LAST4"

# data_quality_rules.yaml
rules:
  - table: "serving.transactions"
    rule: "NOT_NULL(transaction_id)"
    dimension: "COMPLETENESS"
    threshold: 1.0
    schedule: "0 2 * * *"
    
  - table: "serving.customers"
    rule: "EMAIL_FORMAT(email)"
    dimension: "VALIDITY"
    threshold: 0.99
    schedule: "0 2 * * *"
    
  - table: "serving.accounts"
    rule: "REFERENTIAL_INTEGRITY(customer_id, serving.customers.customer_id)"
    dimension: "CONSISTENCY"
    threshold: 1.0
    schedule: "0 2 * * *"

# dlp_templates.yaml
deidentify_templates:
  - name: "pci-tokenize"
    config:
      info_type_transformations:
        - info_types: ["CREDIT_CARD_NUMBER"]
          primitive_transformation:
            crypto_replace_ffx_fpe_config:
              crypto_key: "projects/123/locations/global/keyRings/dlp/cryptoKeys/tokenize"
              common_alphanumeric: {}
```

### Auto-Application via Terraform
```hcl
module "dataplex_governance" {
  source = "./modules/dataplex-governance"
  
  lake_name        = "enterprise-data-lake"
  policy_pack      = "finserv"  # or healthcare, retail
  taxonomy_project = "governance-project"
  
  # Auto-apply to all zones/assets
  apply_to_raw_zone     = true
  apply_to_curated_zone = true
  
  # DLP Integration
  dlp_scan_schedule     = "0 3 * * *"
  auto_tag_on_dlp_match = true
}
```

### Adoption Metrics
- **3 industries** covered, **15+ customers** using packs
- **100% auto-application** via Terraform (no manual tagging)
- **DLP auto-classification** reduces manual tagging by 85%
- **Audit-ready** evidence generated automatically

### Interview Talking Points
> "I created Dataplex Policy Packs for FinServ, Healthcare, and Retail—pre-built governance configurations that auto-apply via Terraform. FinServ pack has 47 policy tags mapped to MAS-TRM and PCI-DSS, 23 data quality rules, 8 DLP templates. The key innovation: DLP auto-classification tags data at ingestion, policy tags enforce masking/RLS at query time, and lineage shows the full chain. Auditors love it—evidence is generated automatically. 3 partner firms now lead with these packs."

---

## 5️⃣ COST GOVERNANCE DASHBOARD

### What It Is
A Looker dashboard + BigQuery backend providing real-time cost visibility, forecasting, and optimization recommendations.

### Architecture
```
COST GOVERNANCE PIPELINE
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Billing     │───▶│ Dataflow    │───▶│ BigQuery    │───▶│ Looker      │
│ Export      │    │ Enrichment  │    │ Partitioned │    │ Dashboard   │
│ (GCS)       │    │ + Labels    │    │ by day      │    │ (Real-time) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  Daily CSV         Add: project,     Cluster by:       Visualize:
  per project       team, env,        project, team,    - Daily/MTD/YTD
  + labels          service, SKU      env, service      - Forecast (Prophet)
                                          + partitioning   - Anomaly detection
                                                          - Optimization recs
                                                          - Chargeback reports
```

### Dashboard Panels
| Panel | Description | Actionability |
|-------|-------------|---------------|
| **Executive Summary** | MTD spend vs budget, trend, top 5 drivers | CFO-level view |
| **Service Breakdown** | BigQuery, Dataflow, Dataproc, Storage, Network | Identify optimization targets |
| **Project/Team Chargeback** | Allocated cost per label (team, env, app) | Showback/chargeback |
| **BigQuery Deep Dive** | Slot usage, storage, query costs, reservation utilization | Right-size reservations |
| **Anomaly Detection** | Prophet-based forecast + actual, alerts at 2σ | Catch runaway jobs early |
| **Optimization Recommendations** | Recommender API: idle slots, partition candidates, storage class | One-click savings |
| **Reservation ROI** | Committed vs on-demand, break-even analysis | Renewal decisions |
| **Trend & Forecast** | 90-day forecast with confidence intervals | Capacity planning |

### Key Queries (BigQuery)
```sql
-- Daily cost by service with labels
SELECT
  DATE(usage_start_time) AS day,
  service.description AS service,
  sku.description AS sku,
  labels.key AS label_key,
  labels.value AS label_value,
  SUM(cost) AS cost_usd,
  SUM(usage.amount) AS usage_quantity,
  usage.unit AS usage_unit
FROM `project.billing_export.gcp_billing_export_v1`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY 1,2,3,4,5,7,8
ORDER BY day DESC, cost_usd DESC;

-- BigQuery slot utilization vs reservation
WITH slot_usage AS (
  SELECT
    TIMESTAMP_TRUNC(period_start, HOUR) AS hour,
    SUM(period_slot_ms) / (1000 * 60 * 60) AS slots_used
  FROM `region-asia-southeast1`.INFORMATION_SCHEMA.JOBS_TIMELINE
  WHERE project_id = 'my-project'
    AND period_start >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY 1
)
SELECT
  hour,
  slots_used,
  2000 AS reserved_slots,  -- From reservation
  SAFE_DIVIDE(slots_used, 2000) * 100 AS utilization_pct
FROM slot_usage
ORDER BY hour DESC;
```

### Adoption Metrics
- **12 customers** using dashboard
- **Average 15% cost reduction** identified in first month
- **Real-time alerts** catch 90% of anomalies before month-end
- **Chargeback adoption** drives team accountability

### Interview Talking Points
> "I designed a Cost Governance Dashboard that 12 customers use—real-time billing ingestion, Prophet-based forecasting, anomaly detection, and Recommender API integration. The key insight: cost governance isn't a report, it's a workflow. Teams get daily Slack alerts when their project exceeds 80% budget, with one-click optimization recommendations (partition this table, cluster that column, delete stale storage). Average 15% savings in month one. It turns FinOps from reactive to proactive."

---

## 🎯 Choosing Which Asset to Present

### Decision Matrix
| If Asked About... | Present This Asset |
|-------------------|-------------------|
| **Migration methodology** | Migration Runbook |
| **Infrastructure/DevOps** | Terraform GCP Data Foundation |
| **Pipeline engineering** | Dataflow Template Library |
| **Governance/Compliance** | Dataplex Policy Packs |
| **Business acumen/Cost** | Cost Governance Dashboard |
| **Scaling delivery/Partners** | Runbook + Terraform (partner enablement) |
| **Technical depth** | Dataflow Templates (show code) |
| **Security focus** | Terraform (VPC-SC, CMEK) + Policy Packs |

### My Recommendation: **Present the Migration Runbook + Terraform Module Together**
**Why:** Shows end-to-end thinking (methodology + automation), partner enablement (both adopted by SIs), and business impact (metrics). Can demo Terraform apply in 2 min, then walk through runbook phases.

---

## 📝 Asset Presentation Script (3 Minutes)

### Minute 1: The Problem
> "Every migration had the same problems: incomplete inventory, surprise data quality, manual validation, knowledge transfer gaps. Partners reinvented the wheel. Customers got inconsistent delivery."

### Minute 2: The Solution (Show Artifact)
> "I codified 50+ migrations into two assets. **Runbook**: 50 pages of executable checklists with automation—assess, pilot, migrate, optimize, security, handoff. **Terraform Module**: 127 resources in 10 minutes—VPC-SC, CMEK, Dataplex, BigQuery Enterprise, Composer, Vertex AI, monitoring. Both versioned, tested, documented."

### Minute 3: The Impact
> "3 partner firms deliver with these. 15 projects. 60% faster assess. 95% pilot success. Zero data loss. 10-minute platform spin-up. But the real value: we spend Week 1 on *business logic*, not plumbing. That's how Google Cloud Consulting scales—reusable IP that partners and customers inherit."

---

*All assets are version-controlled, documented, and actively maintained. Ready to demo in interview.*