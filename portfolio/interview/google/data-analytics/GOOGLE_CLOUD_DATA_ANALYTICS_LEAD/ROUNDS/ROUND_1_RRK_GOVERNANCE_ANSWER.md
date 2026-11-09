# RRK: Governance and Security Answer (Singapore, PII, PDPA + MAS)

**Question:** Singapore enterprise, PII, data must stay in Singapore, PDPA and MAS apply, multiple teams need access. Design the governance for the data platform.
**Follow-up:** A team wants to copy prod to dev for testing.
**Time:** about 5 minutes, then 1 minute for the follow-up.
**Pass signal:** you name VPC Service Controls, IAM, masking, Dataplex and residency, **and** decision rights and an operating model. Encryption alone is a fail.

> Legal and regulatory statements below are for interview reasoning, not legal advice. Verify against the current PDPA and MAS texts before quoting them to a client.

---

## 1. Short answer (the version that was supplied, kept for reference)

Dataset in `asia-southeast1`; VPC Service Controls around Pub/Sub, Dataflow and BigQuery; IAM least privilege with a service account per workload and no broad access; BigQuery column masking and Dataplex policies for PII, tokenise email; audit logs, Dataplex lineage, data quality checks; decision rights for schema change and PII access; residency; retention of 30 days for traces, then anonymise. Follow-up: do not copy prod to dev; use masked synthetic data.

That is a correct skeleton. The sections below make it a Lead-level answer.

---

## 2. Improved answer

**Frame (20 s):** "Governance has four jobs: *classify* what we have, *control* who can reach it, *prove* what happened, and *own* the decisions. I'd design in that order, and treat residency as a structural boundary, not a setting."

### 2.1 Classify
- A short data-classification taxonomy (public, internal, confidential, restricted-PII), agreed with the data protection officer.
- Classification applied as **policy tags** (Dataplex Universal Catalog / BigQuery policy tags), discovered with **Sensitive Data Protection (DLP)** scans, so protection follows the tag rather than a developer's memory.

### 2.2 Control
| Layer | Control |
|---|---|
| **Residency** | Org policy **resource locations** restricted to Singapore (`asia-southeast1`). Datasets, Pub/Sub message storage policy, Dataflow regional endpoint, Cloud Storage buckets, **log buckets** (default is `global`), KMS keys and Dataplex all in Singapore. |
| **Perimeter** | **VPC Service Controls** around BigQuery, Cloud Storage, Pub/Sub, Dataflow, KMS, Logging and Dataplex, with ingress and egress rules written explicitly. |
| **Identity** | **Least-privilege IAM**, groups not individuals, a **service account per workload** with no keys (Workload Identity), IAM conditions, time-bound access for sensitive roles, and a break-glass process with alerts. |
| **Data-level** | **Column-level security** by policy tag; **dynamic data masking** for most roles; **row-level security** where needed; **authorised views** for sharing across domains. |
| **Protection of the sensitive field** | **Tokenise email** with Sensitive Data Protection deterministic encryption (or format-preserving) using a Cloud KMS-wrapped key, so joins still work but raw email isn't exposed. **CMEK** for restricted datasets. |
| **Network** | Private Google Access / Private Service Connect, no public IPs on workers. |

### 2.3 Prove
- **Cloud Audit Logs** with **Data Access logs enabled** for BigQuery, exported to a Singapore log bucket with its own retention.
- **Lineage** and quality: Dataplex lineage, data-quality scans as publication gates, freshness SLOs.
- Evidence mapped to named requirements (control, artefact, owner), because regulators ask for proof.

### 2.4 Own (decision rights)
| Decision | Who decides | Who is consulted |
|---|---|---|
| Access to restricted PII | **Data owner** (business), via a ticket with purpose and expiry | Data protection officer, security |
| Schema change on a data product | **Data product owner**, with consumer sign-off for breaking changes | Platform, governance |
| New external data transfer | Data owner **and** DPO | Legal, security |
| Perimeter or org-policy change | Platform security, with change approval | Risk, audit |
| Retention rule | DPO and legal | Data owner |

One page, one owner per row. Without named decision rights, controls decay.

### 2.5 Retention and the legal basis
- Retention is set **per data class**, by the DPO and legal, not by engineering. PDPA has a retention-limitation principle: do not keep personal data longer than needed for the purpose or legal need. MAS and the bank's records policy may require longer for certain records.
- Implement with table or partition expiry, lifecycle rules, and an anonymisation job after the retention date.
- "30 days for traces, then anonymise" is a reasonable **example** for debug traces. Present it as a policy to confirm, not as a fixed rule.

### 2.6 Residency versus resilience (say this; it shows depth)
Singapore has one Google Cloud region (`asia-southeast1`). Strict in-country residency means **no cross-region replica outside Singapore**. So disaster recovery relies on **multi-zone** design within the region, backups in Singapore, and a documented, regulator-aligned position on any out-of-country failover. If the bank accepts it, cross-region DR needs a legal basis and de-identified or encrypted data. Raise it as a decision for the CIO, risk and DPO.

### 2.7 Incident and regulatory obligations (verify wording)
Have a runbook for a data incident: contain, assess, and notify the regulators within their deadlines. PDPA has a mandatory data-breach notification regime (notify the PDPC and affected individuals when a breach is notifiable, with a short deadline once assessed). MAS technology-risk expectations include prompt reporting of relevant incidents. Name the deadlines with counsel, and rehearse the runbook.

### 2.8 Operating model (the enterprise-scope part)
- A **governance council** (data, security, risk, platform) meeting monthly; a named **data steward per domain**.
- **Self-service request workflow** with expiry and automatic revocation.
- **Guardrails as code:** Terraform for perimeter and policies, CI checks that reject an unclassified or non-Singapore resource.
- Metrics: percent of PII columns tagged, access requests fulfilled in under [N] days, stale access revoked, policy violations (target zero), audit findings closed.

---

## 3. Follow-up: "The team wants to copy prod to dev for testing."

**Answer:** "No. Production PII doesn't go to dev. I'd give them one of three things, in order: **synthetic data** with realistic shape and edge cases; a **de-identified subset** produced by Sensitive Data Protection (tokenised keys so joins work) in a controlled, approved pipeline; or, for rare cases that truly need real data, a **time-boxed, approved, access-logged** environment inside the same perimeter and region as prod, with the same controls. Dev stays in Singapore, inside the perimeter, and has no path to prod credentials. The test of success is that the team can reproduce a prod bug without ever seeing a customer's email."

---

## 4. Pass checklist (say each at least once)

- [ ] Residency as structure: org policy resource locations, Singapore region for every component including logs
- [ ] VPC Service Controls (and what's inside the perimeter)
- [ ] IAM least privilege, service account per workload, no keys
- [ ] Policy tags, column-level security, dynamic masking, tokenisation of email
- [ ] Dataplex: catalogue, lineage, data quality
- [ ] Audit logs, with data-access logging enabled
- [ ] Decision rights and an operating model
- [ ] Retention set by policy and legal basis, not by engineering
- [ ] The residency-versus-DR trade-off
- [ ] A direct "no" to prod PII in dev, with the alternatives

## 5. Likely probes

| Probe | One-line answer |
|---|---|
| "Encryption at rest is on, isn't that enough?" | It's table stakes and always on. The question is who can read the data, from where, and whether it can leave. That is IAM, perimeter, masking and audit. |
| "Two teams want the same PII for different purposes." | Purpose limitation: each purpose is a separate, approved access with its own expiry, via a policy-tagged view. |
| "A data scientist needs raw email." | Almost never. Provide the token; if raw is truly needed, use an approved, time-boxed exception with logging. |
| "How do you stop someone creating a US bucket?" | Org policy resource-location constraint, enforced by guardrails-as-code, so it is blocked rather than detected. |
| "How do you prove compliance?" | A control-to-requirement map with artefacts: policies, audit logs, scan results, approvals. |
