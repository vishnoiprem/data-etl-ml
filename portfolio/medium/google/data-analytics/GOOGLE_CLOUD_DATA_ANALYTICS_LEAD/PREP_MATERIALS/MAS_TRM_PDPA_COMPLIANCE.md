# MAS-TRM 2025 & PDPA Compliance — GCP Control Mapping
## Google Cloud Data & Analytics Lead, Cloud Consulting (Singapore)

---

## 🎯 Purpose
**Interview-ready reference** mapping MAS Technology Risk Management (TRM) 2025 guidelines and Singapore PDPA to Google Cloud Platform controls. Demonstrates regulatory fluency for Singapore FSI/GovTech clients.

---

## 📋 MAS-TRM 2025 — Control Domains & GCP Mapping

> **Source:** MAS Notice 655 (Banks) / MAS Notice 1014 (Insurers) / MAS TRM Guidelines 2025
> **Scope:** Technology risk governance, cyber resilience, data protection, third-party risk

---

### Domain 6: Technology Risk Governance

| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **6.1** | Board oversight of technology risk | Org policies at folder level; SCC findings exported to BigQuery for board dashboards | Org policy configs, SCC export logs, board deck templates |
| **6.2** | Risk management framework | Risk register in Jira/Smartsheet; Dataplex data quality scans as control tests | Risk register, scan results, control test evidence |
| **6.3** | Independent assurance (internal audit) | Cloud Audit Logs → Log Analytics → Audit dashboards; Data Access logs for all admin activity | Audit log sinks, IAM recommender reports, Policy Analyzer |
| **6.4** | Technology risk appetite & limits | Quota limits, budget alerts, VPC-SC perimeter boundaries, CMEK key rotation policies | Budget alerts, VPC-SC config, KMS rotation schedules |

---

### Domain 7: Cyber Resilience

#### 7.1 Network Security
| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **7.1.1** | Network segmentation | **Shared VPC** (hub-spoke); Subnets per tier (mgmt, data, DMZ); **Firewall rules** default deny; **Cloud Armor** WAF | VPC topology diagram, firewall rules export, Cloud Armor policies |
| **7.1.2** | Secure connectivity | **Cloud Interconnect** (Dedicated 10Gbps×2, HA); **Private Service Connect** for APIs; **Cloud VPN** backup | Interconnect configs, PSC endpoints, VPN tunnels |
| **7.1.3** | Network monitoring | **VPC Flow Logs** → Cloud Logging → Chronicle; **Network Intelligence Center** topology | Flow log sinks, Chronicle rules, NIC dashboards |
| **7.1.4** | DDoS protection | **Cloud Armor** (Standard/Adaptive); **Cloud CDN** caching; **Load Balancing** anycast | Armor policies, CDN configs, LB health checks |

#### 7.2 Endpoint Security
| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **7.2.1** | Hardened compute | **Shielded VMs** (vTPM, integrity monitoring); **Confidential Computing** (AMD SEV/Intel TDX); **OS Config** patch management | Shielded VM configs, Confidential VM attestations, patch compliance reports |
| **7.2.2** | Container security | **GKE Autopilot** (hardened nodes); **Binary Authorization** (attestation); **Artifact Registry** vulnerability scanning | GKE configs, Binary Auth policies, AR scan results |
| **7.2.3** | Secrets management | **Secret Manager** (auto-rotation, CMEK); **Workload Identity** (no SA keys); **Parameter Manager** | Secret versions, WI bindings, rotation schedules |

#### 7.3 Identity & Access Management
| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **7.3.1** | Least privilege access | **Custom IAM roles**; **IAM Conditions** (time, resource tags, IP); **Principal Access Boundary** | Role definitions, condition expressions, PAB policies |
| **7.3.2** | Privileged access management | **Privileged Access Manager** (PAM); **Break-glass** with approval workflow; **Service Account impersonation** | PAM entitlements, break-glass logs, SA impersonation grants |
| **7.3.3** | Workforce identity | **Workforce Identity Federation** (Okta/Azure AD → GCP); **MFA enforcement**; **Context-aware access** | WIF configs, MFA policies, CAA levels |
| **7.3.4** | Access reviews | **IAM Recommender** (lateral movement, excess permissions); **Policy Analyzer** (effective access); Quarterly certifications | Recommender insights, Policy Analyzer exports, certification records |

#### 7.4 Data Protection
| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **7.4.1** | Data classification | **Dataplex** policy tags (PII, PCI, SOX, MAS-TRM); **DLP API** automated scanning; **Data Catalog** glossary | Policy tag taxonomy, DLP scan results, Catalog entries |
| **7.4.2** | Encryption at rest | **CMEK** (Cloud KMS, 90-day rotation); **Default encryption** (AES-256); **External Key Manager** (EKM) option | KMS key rings, rotation schedules, EKM configs |
| **7.4.3** | Encryption in transit | **TLS 1.2+** enforced (ALB, Cloud SQL, Spanner); **mTLS** for service-to-service (GKE, Cloud Run) | SSL policies, mTLS configs, cert transparency logs |
| **7.4.4** | Data loss prevention | **DLP API** (inspect, de-identify, re-identify); **Dataplex quality rules** for PII; **VPC-SC** egress controls | DLP job templates, quality rule configs, VPC-SC perimeters |
| **7.4.5** | Data retention & disposal | **Cloud Storage lifecycle** (retention locks); **BigQuery table expiration**; **Dataproc TTL**; **Secure deletion** (CMEK destruction = data destruction) | Lifecycle policies, table expiration, key destruction procedures |

#### 7.5 Application Security
| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **7.5.1** | Secure SDLC | **Cloud Build** (private pools); **Binary Authorization**; **Artifact Registry** (SBOM, vuln scanning); **Cloud Deploy** (canary, rollback) | Build triggers, Binary Auth attestations, AR vuln reports, Deploy pipelines |
| **7.5.2** | API security | **Apigee** (OAuth2, rate limiting, threat protection); **Cloud Endpoints** (ESPv2); **API Gateway** | Apigee proxies, Endpoints configs, Gateway routes |
| **7.5.3** | Vulnerability management | **Container Analysis** (OS + language vulns); **Web Security Scanner**; **SCC vulnerability findings** | Scan schedules, finding remediation SLAs, exception process |

---

### Domain 8: Third-Party Risk Management

| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **8.1** | Vendor risk assessment | **Partner Scorecard** (5 dimensions); **SCC** for partner project access; **Data Sharing Agreements** with DLP | Scorecard templates, SCC partner findings, DSA templates |
| **8.2** | Contractual controls | **Partner contracts**: quality gates, SLAs, audit rights, data processing addenda | Contract templates, SLA definitions, DPA clauses |
| **8.3** | Ongoing monitoring | **Quarterly Business Reviews**; **Partner certifications**; **Joint incident response** | QBR decks, cert tracking, IR runbooks |
| **8.4** | Concentration risk | **Multi-partner strategy** (Strategic/Select/Registered tiers); **No single partner >40% revenue** | Partner tier matrix, revenue concentration reports |

---

### Domain 9: Incident Management

| TRM Ref | Control Requirement | GCP Implementation | Evidence Artifacts |
|---------|---------------------|-------------------|-------------------|
| **9.1** | Detection & alerting | **Cloud Monitoring** (SLO-based alerts); **Chronicle** (SIEM); **SCC** (threat detection); **Error Reporting** | Alert policies, Chronicle rules, SCC findings, Error Reporting groups |
| **9.2** | Response & recovery | **Runbooks** (Git/Confluence); **Cloud Deploy** rollback; **BigQuery time travel**; **Dataproc backup/restore** | Runbook library, deploy rollback logs, BQ snapshot schedules |
| **9.3** | Communication & reporting | **Incident command structure**; **Stakeholder notification** (PagerDuty, Slack); **Postmortem template** (blameless) | Org chart, notification configs, postmortem database |
| **9.4** | Lessons learned | **Postmortem action items** → Jira; **Reliability review** (quarterly); **SLO recalibration** | Action tracker, review minutes, SLO dashboards |

---

## 📋 PDPA (Personal Data Protection Act) 2012/2020 — GCP Mapping

| PDPA Obligation | Requirement | GCP Implementation | Evidence |
|-----------------|-------------|-------------------|----------|
| **Consent** (S13-17) | Obtain/manage consent | **Cloud Functions** consent API; **Firestore** consent records; **Apigee** consent enforcement | Consent logs, API specs, data model |
| **Purpose Limitation** (S18) | Use only for stated purpose | **Dataplex policy tags** (purpose labels); **IAM Conditions** (purpose-based access); **Data Catalog** purpose metadata | Policy tags, IAM conditions, Catalog entries |
| **Notification** (S20) | Notify at collection | **Cloud Run** notification service; **Pub/Sub** event-driven notifications | Notification templates, Pub/Sub topics |
| **Access & Correction** (S21-22) | Data subject rights | **Cloud Functions** DSAR portal; **BigQuery** row-level deletion; **Cloud Storage** object versioning | DSAR workflow, BQ DML logs, versioning config |
| **Accuracy** (S23) | Keep data accurate | **Dataplex quality rules** (completeness, validity); **Dataflow** reconciliation pipelines | Quality scan results, reconciliation reports |
| **Protection** (S24) | Reasonable security | **All Domain 7 controls** (above); **CMEK** for PDPA data; **VPC-SC** for data residency | CMEK keys, VPC-SC perimeter, security configs |
| **Retention Limitation** (S25) | Retain only as needed | **Cloud Storage retention policies** (lock); **BigQuery TTL**; **Cloud Scheduler** automated purge | Retention locks, TTL configs, Scheduler jobs |
| **Transfer Limitation** (S26) | Cross-border controls | **Resource Location Restriction** org policy (asia-southeast1); **VPC-SC** egress; **DLP** scanning before transfer | Org policy, VPC-SC egress logs, DLP transfer scans |
| **Accountability** (S11-12) | Demonstrate compliance | **Cloud Audit Logs** (all access); **Dataplex lineage**; **SCC** compliance reports; **Policy Analyzer** | Audit log exports, lineage graphs, SCC reports |

---

## 🏗️ Reference Architecture: MAS-TRM Compliant Data Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MAS-TRM / PDPA COMPLIANT DATA PLATFORM                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ORG POLICIES (Folder: platforms/data-analytics)                           │
│  ├── constraints/gcp.resourceLocations = asia-southeast1, asia-south1      │
│  ├── constraints/iam.disableServiceAccountKeyCreation = TRUE               │
│  ├── constraints/iam.allowedPolicyMemberDomains = fsi-corp.com             │
│  ├── constraints/compute.vmExternalIpAccess = DENY                         │
│  ├── constraints/sql.restrictPublicIp = TRUE                               │
│  └── constraints/bigquery.restrictCrossRegionQueries = TRUE                │
│                                                                             │
│  NETWORK (Shared VPC: network-host-prod)                                   │
│  ├── Subnet: mgmt (10.0.0/24) — bastion, monitoring                        │
│  ├── Subnet: data-prod (10.0.1/24) — Dataproc, Dataflow, BQ               │
│  ├── Subnet: dmz (10.0.2/24) — Apigee, Load Balancers                     │
│  ├── Cloud Interconnect (2×10Gbps Dedicated, HA) → On-prem DC1/DC2        │
│  ├── Private Service Connect → BigQuery, Vertex AI, Storage, Pub/Sub      │
│  ├── Cloud Armor (WAF, geo-block, rate limit)                             │
│  └── VPC Flow Logs → Cloud Logging → Chronicle SIEM                        │
│                                                                             │
│  IDENTITY & ACCESS                                                         │
│  ├── Workforce Identity Federation (Okta → GCP)                            │
│  ├── Custom Roles: dataEngineer.builder, dataScientist.builder, auditor   │
│  ├── IAM Conditions: time-bound, resource-tag, IP-based                   │
│  ├── Privileged Access Manager (break-glass, approval)                    │
│  └── Service Accounts: Workload Identity (no keys), impersonation         │
│                                                                             │
│  ENCRYPTION & KEY MANAGEMENT                                               │
│  ├── KMS (security-central project)                                        │
│  │   ├── Key Ring: data-platform-prod (auto-rotation 90d)                 │
│  │   │   ├── bigquery-prod, storage-prod, dataproc-prod, vertex-ai-prod  │
│  │   │   └── pubsub-prod                                                   │
│  │   └── Key Ring: data-platform-dr (asia-south1, manual failover)        │
│  └── External Key Manager (Thales/Luna) option for FIPS 140-2 Level 3    │
│                                                                             │
│  DATA GOVERNANCE (Dataplex: fsi-data-lake)                                 │
│  ├── Zone: raw (Cloud Storage, immutable, 7-yr retention lock)            │
│  │   └── Assets: landing-bucket (DLP scan on write), cdc-bucket           │
│  ├── Zone: curated (BigQuery, partitioned, clustered)                      │
│  │   └── Assets: fin-reporting (PII tags, RLS), risk-models, mkt-analytics│
│  ├── Zone: consumed (Looker, Vertex AI Feature Store)                     │
│  ├── Quality: 50+ rules (freshness, completeness, validity, consistency)  │
│  ├── Lineage: Column-level, cross-system (Datastream → BQ → Looker)       │
│  ├── Policy Tags: PII, PCI, SOX, MAS-TRM — enforced via IAM Conditions   │
│  └── Glossary: 200+ business terms, stewards per LOB                      │
│                                                                             │
│  COMPLIANCE AUTOMATION                                                     │
│  ├── DLP Inspection Jobs (daily, template-based) → Findings in BQ         │
│  ├── Dataplex Quality Scans (scheduled) → Results in BQ, alerts in CM     │
│  ├── Policy Analyzer (daily) → IAM drift detection → Jira tickets         │
│  ├── SCC Continuous Export → BigQuery → Compliance Dashboards             │
│  └── Org Policy Compliance (daily) → Violations → Security team           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Interview Talking Points

### "How do you map MAS-TRM to GCP for a bank client?"

> "**I use a control-by-control mapping** — 47 MAS-TRM controls → GCP configurations → automated evidence collection.
> 
> **Example for 7.4 Data Protection:**
> - **Classification** → Dataplex policy tags (PII, PCI, MAS-TRM) + DLP auto-scan
> - **Encryption at rest** → CMEK with Cloud KMS (90-day rotation, key destruction = data destruction)
> - **Encryption in transit** → TLS 1.2+ enforced via SSL policies, mTLS for service mesh
> - **DLP** → DLP API inspection jobs (daily), de-identification for non-prod
> - **Retention** → Cloud Storage retention locks (WORM), BigQuery table expiration, CMEK destruction procedure
> - **Cross-border** → Org policy `gcp.resourceLocations = asia-southeast1`, VPC-SC egress controls
> 
> **Evidence automation:** SCC continuous export → BigQuery → Looker compliance dashboards. Audit = query dashboard, not manual screenshots."

### "How do you handle PDPA cross-border transfer for MNC client?"

> "**Three-layer approach:**
> 1. **Technical:** Org policy restricts resources to `asia-southeast1` (Singapore) + `asia-south1` (Mumbai DR). VPC-SC perimeter blocks egress. Private Service Connect for all API access — no public internet.
> 2. **Process:** DLP scan before any data export. Transfer request → DLP job → findings review → approval workflow → controlled egress via PSC.
> 3. **Contractual:** Data Processing Addendum (DPA) with subprocessors. Standard Contractual Clauses (SCC) for EU data. Binding Corporate Rules (BCR) for intra-group.
> 
> **For DR to Mumbai:** Synchronous replication (Filestore/Cloud SQL) within VPC-SC. Async (BigQuery, Storage) via scheduled jobs with DLP pre-scan. Failover tested quarterly."

### "What's your DLP strategy for a 500TB data estate?"

> "**Tiered scanning, not full scans:**
> - **Tier 1 (Critical - PII/PCI):** Daily incremental scans on new/changed partitions (Dataplex quality rules + DLP)
> - **Tier 2 (Sensitive - Internal):** Weekly sample scans (10% TABLESAMPLE)
> - **Tier 3 (Public/Internal):** Monthly full scans
> - **Findings:** Auto-tagged in Data Catalog, routed to Jira for remediation, dashboarded in Looker
> - **Cost control:** DLP API pricing ~$0.10/GB inspected. Sampling + partitioning keeps monthly cost <$5K for 500TB"

### "How do you prove compliance to auditors without manual evidence gathering?"

> "**Compliance as Code:**
> - **Infrastructure:** Terraform for all GCP configs → Git → plan/apply logs = evidence
> - **Policies:** Org policies as code (Terraform) → drift detection via Policy Analyzer
> - **Data:** Dataplex quality scans + DLP jobs → results in BigQuery → Looker dashboards
> - **Access:** IAM Recommender + Policy Analyzer → daily export → quarterly access certification workflow
> - **Incidents:** Chronicle rules → auto-ticket → SLA tracking → postmortem database
> - **Auditor portal:** Read-only Looker dashboard with pre-built MAS-TRM/PDPA control mapping
> 
> **Result:** Audit prep = 2 days (vs 4 weeks manual). Zero findings on last MAS audit."

---

## 📋 Quick Reference: MAS-TRM Control → GCP Service Matrix

| MAS-TRM Domain | Primary GCP Services | Secondary Services |
|----------------|---------------------|-------------------|
| **6. Governance** | Organization Policies, SCC, Cloud Audit Logs, IAM Recommender | Policy Analyzer, Cloud Asset Inventory |
| **7.1 Network** | Shared VPC, Cloud Interconnect, Private Service Connect, Cloud Armor, Cloud NAT | VPC Flow Logs, Network Intelligence Center, Cloud VPN |
| **7.2 Endpoint** | Shielded VMs, Confidential Computing, GKE Autopilot, Binary Authorization, OS Config, Secret Manager | Artifact Registry, Workload Identity |
| **7.3 IAM** | Custom Roles, IAM Conditions, Workforce Identity Federation, Privileged Access Manager | Principal Access Boundary, Context-Aware Access |
| **7.4 Data Protection** | Dataplex, Cloud DLP, Cloud KMS (CMEK), VPC Service Controls, Cloud Storage Lifecycle | Data Catalog, Cloud Storage Retention Locks |
| **7.5 Application** | Cloud Build, Binary Authorization, Artifact Registry, Cloud Deploy, Apigee | Container Analysis, Web Security Scanner |
| **8. Third Party** | Partner Scorecards (custom), SCC, Data Sharing Agreements | IAM Conditions for partner access, VPC-SC |
| **9. Incident** | Cloud Monitoring, Chronicle, Error Reporting, Cloud Deploy, BigQuery Time Travel | PagerDuty/Slack integration, Runbook automation |

---

## 🔴 Red Flags to Avoid

- ❌ "We encrypt everything" — no distinction between default/CMEK/EKM, no key rotation policy
- ❌ "VPC-SC is too complex" — it's mandatory for MAS-TRM regulated workloads
- ❌ "DLP scans everything daily" — cost-prohibitive at scale; tiered approach required
- ❌ "Partners have full project access" — violates least privilege; use IAM Conditions + VPC-SC
- ❌ "We don't have break-glass" — required for PAM; must have approval workflow + audit trail
- ❌ "PDPA = just consent" — it's 9 obligations; technical controls needed for each

---

## 📋 Compliance Artifact Checklist (Per Engagement)

| Artifact | Owner | Cadence | Storage |
|----------|-------|---------|---------|
| **MAS-TRM Control Mapping** | Google Lead Architect | Per engagement, update on change | Confluence + Git |
| **VPC-SC Perimeter Config** | Network Lead | Version-controlled | Terraform + Git |
| **CMEK Key Inventory** | Security Lead | Quarterly review | KMS + Sheet |
| **DLP Scan Results** | Data Governance Lead | Daily (auto) | BigQuery + Looker |
| **Dataplex Quality Reports** | Data Governance Lead | Per scan (scheduled) | BigQuery + Looker |
| **IAM Recommender Export** | Security Lead | Daily (auto) | BigQuery + Looker |
| **Partner Scorecards** | Partner Lead | Monthly | Smartsheet |
| **Incident Postmortems** | Delivery Lead | Per incident | Confluence + Jira |
| **Access Certification** | Security Lead | Quarterly | Workflow tool |
| **DR Test Report** | Platform Lead | Quarterly | Confluence |

---

*This mapping demonstrates L7 regulatory fluency: technical depth (GCP services) + compliance knowledge (MAS-TRM/PDPA) + automation mindset (evidence as code) + client-facing communication (talking points).*