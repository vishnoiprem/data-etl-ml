# Security & Governance - GCP Data Platform
## VPC-SC, CMEK, Dataplex, IAM, Compliance - Interview Ready

---

## 🏰 Defense-in-Depth Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GCP DATA PLATFORM SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 1: NETWORK PERIMETER                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    VPC Service Controls                      │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │   │
│  │  │  │ Project A    │  │ Project B    │  │ Project C    │       │   │   │
│  │  │  │ (Analytics)  │  │ (ML)         │  │ (Raw Data)   │       │   │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘       │   │   │
│  │  │         │                │                │                  │   │   │
│  │  │         └────────────────┼────────────────┘                  │   │   │
│  │  │                          ▼                                   │   │   │
│  │  │              ┌─────────────────────┐                         │   │   │
│  │  │              │  Service Perimeter  │                         │   │   │
│  │  │              │  (BigQuery, GCS,    │                         │   │   │
│  │  │              │   Dataproc, etc.)   │                         │   │   │
│  │  │              └─────────────────────┘                         │   │   │
│  │  │                          │                                   │   │   │
│  │  │         ┌────────────────┼────────────────┐                  │   │   │
│  │  │         ▼                ▼                ▼                  │   │   │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐                │   │   │
│  │  │  │ PSC to    │  │ PSC to    │  │ PSC to    │                │   │   │
│  │  │  │ BigQuery  │  │ GCS       │  │ Vertex AI │                │   │   │
│  │  │  └───────────┘  └───────────┘  └───────────┘                │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 2: ENCRYPTION                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │ CMEK (Cloud KMS)│  │ CMEK + Cloud HSM│  │ Google Default  │     │   │
│  │  │ Customer manages│  │ FIPS 140-2 L3   │  │ Encryption      │     │   │
│  │  │ key rotation    │  │ (Regulated)     │  │ (Default)       │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │ BigQuery tables │  │ BigQuery tables │  │ All services    │     │   │
│  │  │ GCS buckets     │  │ GCS buckets     │  │ by default      │     │   │
│  │  │ Dataproc disks  │  │ Dataproc disks  │  │                 │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 3: IDENTITY & ACCESS                        │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  IAM: Least Privilege + Conditions + Deny Policies          │   │   │
│  │  │                                                              │   │   │
│  │  │  Custom Roles (not primitive):                              │   │   │
│  │  │  • roles/dataplex.dataReader  • roles/bigquery.dataViewer  │   │   │
│  │  │  • roles/dataflow.developer   • roles/dataproc.editor      │   │   │
│  │  │                                                              │   │   │
│  │  │  IAM Conditions (Context-Aware):                            │   │   │
│  │  │  • time: access only 9am-6pm weekdays                       │   │   │
│  │  │  • resource.tag: only "env=prod" resources                  │   │   │
│  │  │  • ip: only from corporate CIDR                             │   │   │
│  │  │                                                              │   │   │
│  │  │  Deny Policies (Guardrails):                                │   │   │
│  │  │  • deny BigQuery *.DELETE on prod datasets                  │   │   │
│  │  │  • deny GCS bucket deletion                                 │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 4: DATA-LEVEL SECURITY                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │ Policy Tags     │  │ Row-Level       │  │ Column-Level    │     │   │
│  │  │ (Dataplex)      │  │ Security (BQ)   │  │ Masking (DLP)   │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │ Taxonomy:       │  │ CREATE ROW      │  │ DLP Inspection  │     │   │
│  │  │ PII → MASKED    │  │ ACCESS POLICY   │  │ → Auto-tag      │     │   │
│  │  │ PCI → ENCRYPTED │  │ ON table        │  │ → Policy tag    │     │   │
│  │  │ PHI → RESTRICTED│  │ USING FILTER    │  │ → Masking rule  │     │   │
│  │  │                 │  │ (tenant_id =    │  │                 │     │   │
│  │  │ Data Catalog    │  │  current_user)  │  │ SSN: ***-**-1234│     │   │
│  │  │ auto-enrichment │  │                 │  │ Email: u***@d.com│     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 5: GOVERNANCE & AUDIT                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │ Dataplex        │  │ Cloud Audit     │  │ Data Quality    │     │   │
│  │  │ Lineage/Glossary│  │ Logs → Chronicle│  │ (Great Expect.) │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │ • Column-level  │  │ • Data Access   │  │ • Freshness     │     │   │
│  │  │   lineage       │  │ • Admin Activity│  │ • Completeness  │     │   │
│  │  │ • Business      │  │ • System Event  │  │ • Validity      │     │   │
│  │  │   glossary      │  │ • Policy Denied │  │ • Consistency   │     │   │
│  │  │ • Quality scans │  │                 │  │ • Accuracy      │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 VPC Service Controls (VPC-SC) - Deep Dive

### Perimeter Design
```hcl
# Terraform: VPC-SC Perimeter for Data Analytics
resource "google_access_context_manager_service_perimeter" "data_analytics" {
  name        = "data-analytics-perimeter"
  title       = "Data Analytics Perimeter"
  description = "Perimeter for BigQuery, GCS, Dataproc, Vertex AI"
  
  status {
    resources = [
      "projects/analytics-prod",
      "projects/ml-prod",
      "projects/raw-data-prod"
    ]
    
    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "dataproc.googleapis.com",
      "aiplatform.googleapis.com",
      "dataplex.googleapis.com",
      "composer.googleapis.com"
    ]
    
    # Allow specific egress (e.g., to approved partner APIs)
    egress_policies = [{
      egress_from = [{
        identities = ["user:service-account@analytics-prod.iam.gserviceaccount.com"]
      }]
      egress_to = [{
        operations = [{
          service_name = "bigquery.googleapis.com",
          method_selectors = [{
            method = "jobs.create"
          }]
        }]
      }]
    }]
    
    # Allow ingress from corporate network
    ingress_policies = [{
      ingress_from = [{
        sources = [{
          access_level = "accessPolicies/123/accessLevels/corporate-network"
        }]
      }]
      ingress_to = [{
        operations = [{
          service_name = "bigquery.googleapis.com"
        }]
      }]
    }]
  }
  
  # Dry run first!
  # Then enforce with: use_explicit_dry_run_spec = false
}
```

### Key Concepts
| Concept | Description | Interview Talking Point |
|---------|-------------|------------------------|
| **Perimeter** | Logical boundary around projects/services | "I design perimeters per environment (dev/staging/prod) with bridge perimeters for shared services" |
| **Dry Run** | Test mode - logs violations but allows | "Always deploy in dry-run first, analyze logs for 2 weeks, then enforce" |
| **Ingress/Egress** | Control what enters/leaves perimeter | "Ingress from corporate CIDR only; egress to approved partner APIs only" |
| **Bridge Perimeter** | Share services across perimeters | "Shared VPC host project in bridge perimeter for DNS, NAT, logging" |
| **Service Accounts** | Must be inside perimeter to access | "All service accounts for Dataflow/Dataproc must be in perimeter projects" |

---

## 🔑 CMEK (Customer-Managed Encryption Keys)

### Key Hierarchy
```
Organization
└── Folder: Security
    └── Project: kms-project
        └── Key Ring: data-analytics
            ├── Key: bigquery-prod (rotation: 90 days)
            ├── Key: gcs-prod (rotation: 90 days)
            ├── Key: dataproc-prod (rotation: 90 days)
            └── Key: vertex-ai-prod (rotation: 90 days)
```

### Implementation
```python
# BigQuery table with CMEK
from google.cloud import bigquery

client = bigquery.Client()
table_id = "project.dataset.secure_table"

table = bigquery.Table(table_id)
table.encryption_configuration = bigquery.EncryptionConfiguration(
    kms_key_name="projects/kms-project/locations/us/keyRings/data-analytics/cryptoKeys/bigquery-prod"
)

# Time travel & fail-safe still work with CMEK!
table = client.create_table(table, exists_ok=True)
```

### Key Rotation Strategy
| Rotation Period | Use Case | Automation |
|-----------------|----------|------------|
| 30 days | Highly sensitive (PCI, PHI) | Cloud Scheduler + Cloud Function |
| 90 days | Standard enterprise | KMS auto-rotation (native) |
| 365 days | Low sensitivity | Manual with approval workflow |

**Critical:** Key destruction = data destruction. Always:
1. Disable key first (30-day grace)
2. Verify no active resources using key
3. Schedule destruction with approvals

---

## 🏷️ Dataplex Governance (The Modern Way)

### Lake/Zone/Asset Hierarchy
```
Dataplex Lake: enterprise-data-lake
│
├── Zone: raw-zone (type: RAW)
│   ├── Asset: gcs://landing-bucket (Cloud Storage)
│   └── Asset: projects/raw-data/topics/* (Pub/Sub)
│
├── Zone: curated-zone (type: CURATED)
│   ├── Asset: projects/analytics/datasets/staging (BigQuery)
│   └── Asset: projects/analytics/datasets/serving (BigQuery)
│
└── Zone: analytics-zone (type: CURATED)
    └── Asset: projects/ml/datasets/features (BigQuery)
```

### Policy Tags Taxonomy
```
Taxonomy: data-classification (location: us)
├── PII
│   ├── NAME
│   ├── EMAIL
│   ├── PHONE
│   ├── SSN
│   └── ADDRESS
├── PCI
│   ├── CREDIT_CARD
│   ├── CARD_EXPIRY
│   └── CVV
├── PHI
│   ├── PATIENT_ID
│   ├── DIAGNOSIS
│   └── TREATMENT
├── INTERNAL
│   ├── EMPLOYEE_ID
│   └── SALARY
└── PUBLIC
    └── NON_SENSITIVE
```

### Applying Policy Tags
```sql
-- BigQuery: Apply policy tag to column
ALTER TABLE `project.dataset.customers`
ALTER COLUMN email SET OPTIONS (
  description="Customer email - PII",
  tags=[("data-classification", "PII/EMAIL")]
);

-- Dataplex: Data quality scan with policy tag awareness
-- Console: Dataplex → Data Quality → Create Scan
-- Rules automatically suggest based on policy tags
```

### Dataplex Data Quality (Built-in)
```yaml
# Data quality scan spec (YAML for version control)
name: projects/123/locations/us/dataScans/daily-customer-quality
description: "Daily customer data quality scan"
data:
  entity: projects/analytics/datasets/serving/tables/customers
  sampling_percent: 100
spec:
  rules:
    - column: customer_id
      dimension: COMPLETENESS
      non_null_expectation: {}
    - column: email
      dimension: VALIDITY
      regex_expectation:
        regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    - column: tier
      dimension: CONSISTENCY
      set_expectation:
        values: ["bronze", "silver", "gold", "platinum"]
    - row_condition: "signup_date <= CURRENT_DATE()"
      dimension: ACCURACY
execution_spec:
  trigger:
    schedule: "0 2 * * *"  # Daily 2 AM UTC
```

---

## 👁️ Row-Level Security (BigQuery)

### Multi-Tenant Pattern
```sql
-- 1. Create authorized view per tenant (legacy approach - don't use)
-- 2. Modern: Row-level security policy

-- Create policy
CREATE ROW ACCESS POLICY tenant_isolation
ON `project.dataset.orders`
GRANT TO ("role:tenant-viewer")
FILTER USING (tenant_id = SESSION_USER());

-- Or using custom function for complex logic
CREATE ROW ACCESS POLICY regional_access
ON `project.dataset.orders`
GRANT TO ("group:apac-analysts@company.com")
FILTER USING (region IN ('SG', 'JP', 'AU', 'IN')
              AND has_region_access(SESSION_USER(), region));
```

### Session User Context
```python
# Application sets session user for RLS
from google.cloud import bigquery

client = bigquery.Client()
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("tenant_id", "STRING", "tenant_123")
    ],
    # Impersonate service account with tenant context
    # Or use Cloud SQL proxy with tenant header
)

# In practice: Use Identity-Aware Proxy (IAP) + JWT claims
# BigQuery reads X-Goog-IAP-JWT-Assertion header for SESSION_USER()
```

---

## 📋 Compliance Mapping (MAS-TRM, GDPR, HIPAA)

### MAS-TRM (Singapore) Controls → GCP Implementation

| MAS-TRM Control | GCP Implementation | Evidence |
|-----------------|-------------------|----------|
| **6.1 Network Segmentation** | VPC-SC perimeter, Private Service Connect | Perimeter config export, PSC endpoints |
| **6.2 Encryption** | CMEK with Cloud HSM (FIPS 140-2 L3) | Key ring config, HSM attestation |
| **6.3 Access Control** | IAM conditions, deny policies, RLS | IAM policy export, deny policy list |
| **6.4 Audit Logging** | Cloud Audit Logs → Chronicle SIEM | Log sink config, Chronicle dashboards |
| **6.5 Data Residency** | Dual-region BQ (SG+JP), org policies | Resource location policy, BQ location |
| **6.6 Incident Response** | Cloud Monitoring alerts, runbooks | Alert policies, runbook docs |
| **6.7 Vendor Management** | Partner scorecards, SI attestations | Scorecard templates, SOC2 reports |

### Automated Evidence Collection
```python
# Cloud Function: Daily compliance evidence package
def collect_compliance_evidence(request):
    """Generate daily compliance evidence for auditors."""
    from google.cloud import logging, asset_v1, bigquery
    
    evidence = {
        "timestamp": datetime.utcnow().isoformat(),
        "vpc_sc_config": export_vpc_sc_config(),
        "kms_key_status": list_kms_keys(),
        "iam_policies": export_iam_policies(),
        "audit_logs_sample": query_audit_logs("last_24h"),
        "dataplex_scan_results": get_latest_dq_results(),
        "bq_rls_policies": list_rls_policies(),
    }
    
    # Store in evidence bucket with retention lock
    store_evidence(evidence)
    return {"status": "collected", "items": len(evidence)}
```

---

## 🎯 Interview Talking Points

### "How do you secure data in GCP?" (Structured 3-min Answer)
1. **Network:** VPC-SC perimeter around all data projects, PSC for private access, no public IPs
2. **Encryption:** CMEK with 90-day rotation, Cloud HSM for regulated data, key hierarchy per environment
3. **Identity:** Custom roles (not primitive), IAM conditions (time/IP/resource tags), deny policies as guardrails
4. **Data-Level:** Dataplex policy tags → DLP auto-classification → column masking + row-level security
5. **Governance:** Dataplex lineage/quality/glossary, Cloud Audit Logs → Chronicle, automated evidence
6. **Compliance:** MAS-TRM/GDPR/HIPAA mapped to controls, daily evidence collection, audit-ready

### "VPC-SC vs Firewall Rules?"
- **VPC-SC:** Service-level perimeter (API calls), protects data exfiltration via APIs
- **Firewall:** Network-level (IP/port), protects VM-to-VM traffic
- **Both needed:** VPC-SC for data services, firewall for compute

### "CMEK vs Default Encryption?"
- **Default:** Google manages keys, rotation, access - zero ops
- **CMEK:** You control key lifecycle, rotation, access - compliance requirement
- **Trade-off:** CMEK adds cost (~$0.06/key/month) and operational complexity

### "How do you handle GDPR right to deletion in BigQuery?"
1. **Partition by user_id** → DROP PARTITION (instant, no scan cost)
2. **Or:** MERGE with DELETE condition (scans affected partitions)
3. **Time travel:** 7-day recovery window if mistake
4. **Audit:** Log all deletions to compliance bucket

---

## 📝 Related Files
- `code/dataplex_policies.py` - Dataplex policy management
- `code/vpc_sc_setup.py` - VPC-SC perimeter automation
- `code/cmek_rotation.py` - Key rotation automation
- `notebooks/security_audit_demo.ipynb` - Compliance evidence demo

---

*Last Updated: 2026-10-30 | For: Google Cloud Data & Analytics Lead Technical Screen*