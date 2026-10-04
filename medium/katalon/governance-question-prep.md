# Governance Question Prep — "Establish Enterprise-Wide Data Governance, Quality, Security, Privacy, and Compliance Standards"

> **Purpose:** Full preparation file for the governance line on the role's responsibility list. Completes the trio with `strategy-question-prep.md` and `platform-architecture-question-prep.md`.

---

## The Question

- **Round:** Onsite 2 (Duke Nguyen, VP Engineering) or Onsite 3 (Rajesh Krishnan, SVP Engineering); can also surface in Onsite 1 with the technical panel if a SQL/data-quality probe is included
- **Source:** Job posting, line 3 of "Your Responsibilities" (`README.md`)
- **Verbatim:** *"Establish enterprise-wide data governance, quality, security, privacy, and compliance standards (including GDPR, CCPA/CPRA)."*
- **Likely probes:**
  - "How do you build governance without slowing teams down?"
  - "A user asks to be deleted under GDPR. How does it work in a data lake?"
  - "How do you protect PII while still enabling analysis?"
  - "How do you measure and improve data quality?"
  - "What is a data contract?"
  - "Security of customer data when customers are Fortune 500?"

---

## Framework Used

- **Strategic / governance:** **C-O-Q-S-P-L** (6 pillars of governance) + **Govern to enable, not to block** as the anchor sentence
- **Tactical:** **Find → Delete → Prove** for DSAR/GDPR

🔵 **Hook: "Govern to enable, not to block. Good governance makes the right data easy to find and safe to use. Bad governance is a ticket queue."**

---

## 60–90 Second Spoken Answer (lead with this)

> I'd govern to **enable**, not to block. Six pillars: **catalog, ownership, quality, security, privacy, lifecycle** — all made executable in the platform, not in tickets.
>
> I'd start with the **20% of datasets that carries 80% of the risk and value** — customer PII, revenue, executive KPIs — and put real controls there first: named owners, lineage, PII classification, masking policies, quality SLOs, deletion workflows. Everything else gets best-effort until it's Tier 1.
>
> For GDPR and CCPA/CPRA: I'd translate legal requirements into **technical controls and audit evidence** — not policy documents. A DSAR becomes a workflow: find → delete → prove. Find via subject identifier in a registry; delete from operational stores, then from the lake with ACID row deletes + compaction, from the warehouse, from caches, from vector indexes, from backups on rotation, with a signed completion record. Privacy ≠ just legal's job — I'm the engineer who makes it real.
>
> For Katalon specifically: customer test artifacts can contain secrets, PII, and proprietary business logic. Default to **customer-confidential** classification. Tenant-scoped keys, row-level security, no use for analytics or model training beyond explicit opt-in.
>
> **NIST AI RMF** (Govern / Map / Measure / Manage) for AI governance, aligned to enterprise procurement language. The success measure is audit findings, DSAR turnaround, and incident recurrence — not "we have a governance program."

⏱️ ~95 seconds. Trim if rushed.

---

## The 6 Pillars: **C-O-Q-S-P-L**

| Pillar | What it means | Concrete mechanism |
|---|---|---|
| **C**atalog | Everyone can find + understand data | Catalog, business glossary, lineage, owners |
| **O**wnership | Every dataset has an owner + steward | Domain owners, data contracts |
| **Q**uality | Fit for use, with tests | dbt/Great Expectations/Soda, SLOs, anomaly monitors, incident process |
| **S**ecurity | Only the right people access | RBAC/ABAC, encryption, masking, audit |
| **P**rivacy | Lawful, minimal, deletable | Classification, consent, DSAR process, retention |
| **L**ifecycle | Keep only what's needed | Retention + deletion policies, archival |

Memorize as a single breath: *"Catalog, Ownership, Quality, Security, Privacy, Lifecycle."*

---

## Data Quality Dimensions: **C-V-U-T-C-A**

| Letter | Dimension | How to test |
|---|---|---|
| **C**ompleteness | % non-null | `not_null` test on critical columns |
| **V**alidity | Conforms to type/format | `regex` / `accepted_values` tests |
| **U**niqueness | No duplicates on the key | `unique` test on PK |
| **T**imeliness | Fresh enough | Freshness check vs SLO |
| **C**onsistency | Reconciles across systems | Cross-source reconciliation jobs |
| **A**ccuracy | Reflects reality | Sample audits + business owner sign-off |

🔵 **Hook: "Detection should come from us, not from an executive spotting a wrong number."**

---

## Tiering Model (govern what's Tier 1 first)

| Tier | What | Controls | On-call |
|---|---|---|---|
| **Tier 1** | Exec KPIs, finance, customer PII, customer-facing AI | SLOs, owners, lineage, masking, audit, incident review | Yes |
| **Tier 2** | Team metrics, internal ML | Owner + dbt tests | No |
| **Tier 3** | Exploratory, sandbox | Best-effort | No |

🔵 **Hook: "Name an owner for each Tier-1 dataset. Publish a glossary. Automate PII → masking. Run quality tests in CI."**

---

## GDPR vs CCPA/CPRA (quick contrast — the interviewer wants it)

| | **GDPR (EU/UK)** | **CCPA/CPRA (California)** |
|---|---|---|
| Model | **Opt-in**: lawful basis (consent, contract, legitimate interest) | **Opt-out**: notice + right to opt out of "sale/sharing" |
| Key principles | Lawfulness, purpose limitation, data minimisation, accuracy, storage limitation, integrity, accountability | Notice at collection, purpose limitation, data minimisation, security |
| Rights | Access, rectification, **erasure**, restriction, portability, objection, rights on automated decisions | Know, delete, **correct**, opt-out of sale/sharing, limit use of **sensitive PI**, non-discrimination |
| Response time | **1 month** (extendable by 2) | **45 days** (extendable by 45) |
| Other | **DPIA** for high-risk; **DPA** with processors; SCCs for non-EU transfers; breach notice to authority within **72h** | Honour **Global Privacy Control** opt-out; service-provider contracts; "Do Not Sell or Share" link |

🔵 **Hook: "GDPR = permission first; CCPA = notice and opt-out."**

🟡 You are not the lawyer. Always say: *"I translate legal requirements into controls and evidence; Legal confirms interpretation. Verify thresholds with counsel before quoting them."*

---

## GDPR Deletion Flow (DSAR) — **Find → Delete → Prove**

```
Verified request (legal intake)
    │
    ▼
Identity-to-subject resolution   (PII registry / subject graph)
    │
    ▼
Deletion plan from lineage + retention registry
    │
    ▼
┌─────────────────┬────────────────┬─────────────────┬─────────────────┬─────────────┐
│ Operational DBs │ Lake (Iceberg) │ Warehouse       │ Vector index    │ Backups    │
│ tombstone /     │ row-level      │ DELETE +        │ doc delete +    │ roll-off │
│ Object.delete   │ delete +       │ VACUUM          │              │ retention  │
│                 │ VACUUM        │                 │              │            │
└─────────────────┴────────────────┴─────────────────┴─────────────────┴─────────────┘
    │
    ▼
Rebuild derived data (features, embeddings, aggregates) so deleted subjects don't resurrect
    │
    ▼
Signed completion record →  exception ledger → audit evidence
```

**Interview points to make:**
- Backups need an approved expiry strategy; deletion may be **logical** until backup rotation completes.
- **Legal holds** override normal deletion only through an auditable policy.
- Rebuilt derived data, features, embeddings, caches **must not resurrect deleted subjects**.
- Trained models: if deletion from a trained model isn't technically guaranteed, document the legal/product policy rather than bluffing.

🔵 **Hook: "Three steps. Find. Delete. Prove."**

---

## Erasure in a Data Lake — three options

| Technique | When | Trade-off |
|---|---|---|
| **ACID row delete + VACUUM** (Iceberg/Delta) | Default | Works on most modern table formats; physical removal on compaction |
| **Rewrite affected partitions** | Legacy Parquet without ACID | Heavy if partition is large |
| **Crypto-shredding** | Raw files you can't rewrite | Encrypt per-person keys at ingest; "delete the key" to forget |

---

## Data Quality SLO Template

```yaml
data_product: gold.test_result_daily
owner: quality-analytics
consumers: [project-dashboard, executive-quality, flakiness-features]
freshness: 15m product / 7am daily certification
completeness: ">= 99.99% accepted terminal events"
uniqueness_key: [tenant_id, execution_id, test_case_id, attempt_id]
reconciliation: execution manifest count
severity_1: cross-tenant exposure or material executive metric error
runbook: catalog://gold.test_result_daily/runbook
```

---

## Incident Response (when a Tier-1 metric breaks)

1. **Stop** or label downstream publication
2. **Scope** affected tenants / dates / products / models / decisions via lineage
3. **Preserve** evidence; identify first-bad data/code version
4. **Roll back or replay** from immutable inputs
5. **Communicate** in business language
6. **Reconcile** corrected output
7. **Add** a prevention control + owner (don't just add an alert)

🔵 **Hook: "Detection, containment, correction. Add a prevention control, not just an alert."**

**Measure:** detection time, containment time, correction time, recurrence, decision impact.

---

## Likely Governance Questions & Model Answers

### Q1: "How do you build governance without slowing teams down?"

🟢 *"Start with Tier 1's 20%. Name them, line them, tag them, mask them. Publish a glossary and lineage so people self-serve. Automate: PII tags drive masking, quality tests run in CI, access requests go through a workflow with auto-expiry. A governance council meets monthly to resolve conflicts and approve policy, not to approve every request. I measure it: % Tier-1 with owner, test coverage, request turnaround, incident count."*

### Q2: "A user asks to be deleted under GDPR. How does it work in a data lake?"

🟢 *"Three steps: find, delete, prove. Find via subject identifier in a PII registry or lineage. Delete from operational stores immediately. In the lake: ACID row-level delete on Iceberg/Delta + compaction, OR rewrite partitions, OR crypto-shredding — pick by table format. Backups roll off on retention; documented. Derived data — features, aggregates, embeddings — need review; truly anonymised aggregates are out of scope, but user-keyed features are. Logs deletion of you, completion proof within legal's 1-month deadline."*

### Q3: "How do you protect PII for analytics while enabling analysis?"

🟢 *"Minimise, then pseudonymise, then restrict. Don't ingest what we don't need. Replace direct identifiers with a keyed hash/token so analysts can still join + count distinct. Role-based dynamic masking: emails show as `a***@domain.com` for most roles, clear only for the few with justification. Row-level policies for region. Sensitive free text (support tickets, test logs) gets PII redaction before lake and before any LLM. Everything audited."*

### Q4: "How do you measure and improve data quality?"

🟢 *"Define quality from the consumer's view: for each Tier-1 dataset write a short SLO — freshness by 7am, completeness >99.5%, no duplicates on key. Tests at ingestion, after transform, before publish. Failures block publishing + alert owner. Track incidents with time-to-detect + time-to-resolve. Blameless review per Tier-1 incident. Trend for the board: % days SLOs met. Detection should come from us, not from an executive spotting a wrong number."*

### Q5: "What is a data contract?"

🟢 *"A formal producer-consumer agreement: versioned schema, semantics, quality expectations, freshness — owned + enforced in CI. Moves quality upstream: the producer is accountable. Example: product team's `test_run` event has required fields, stable ID, documented meaning; breaking change is versioned + announced, not silent."*

### Q6: "Security of customer data when customers are Fortune 500"

🟢 *"Default to customer-confidential. Least-privilege access, encryption (KMS, per-domain keys), tenant-segregation, strict retention, no use for analytics or model training beyond contract/consent. Compliance evidence (SOC 2, ISO 27001 controls) is a sales asset — so access logs, lineage, retention are automatically auditable, not a scramble before audits."*

### Q7: "GDPR vs CCPA — what's the difference?"

🟢 *"GDPR is opt-in with a 1-month response deadline; CCPA is notice + opt-out with 45-day response. Both require minimisation, purpose limitation, security. Both give data-subject rights; the right to delete + correct is common. GDPR has DPIAs for high-risk; CCPA honours the Global Privacy Control signal. I treat both as: build the technical controls (classification, lineage, DSAR workflow) and verify interpretation with Legal."*

### Q8: "Hash vs anonymise — are they the same?"

🟢 *"No. Hashing an identifier is **pseudonymisation**, still personal data under GDPR. Anonymisation requires the key to be irreversibly severed so re-identification is no longer possible. Always check before claiming 'anonymised'. Same for k-anonymity, differential privacy — they're techniques, not automatic anonymisers."*

### Q9: "How do you govern screenshots that may contain credentials?"

🟢 *"Two controls. Preventive: redaction pipeline before the artifact hits the lake — detect credential patterns (API keys, JWTs, known PII formats) and mask. Detective: scan on read; flag artifacts containing high-risk patterns and quarantine. Plus access controls (tenant-scoped, time-bound signed URLs) and short lifecycle. Customer test artifacts are untrusted input — treat them like log files, not documents."*

### Q10: "How do you handle regional residency with global analytics need?"

🟢 *"Store + process in-region for regulated data; aggregate/anonymised flows cross regions with legal sign-off. Use regional warehouses (Snowflake regions, S3 cross-region replication with encryption), tenant routing at ingest, lineage that records where data lives. For global analytics: prefer pre-aggregated, anonymised rollups rather than raw data movement."*

### Q11: "A data scientist exports a sensitive training sample to a notebook. What controls?"

🟢 *"Preventive: notebook environments in a managed workspace; data access mediated by the platform, no direct table download; row-level + column-level policies enforced at query time. Detective: query audit + DLP on notebook egress. Responsive: kill session, audit the dataset, notify Security/Legal, document for compliance."*

### Q12: "What evidence do you provide during an audit?"

🟢 *"Three artefacts: (1) data inventory with classification + owners; (2) access logs for sensitive datasets in the audit period; (3) lineage + retention evidence for DSARs processed. Plus policy docs, DPIA records, breach log. If those artefacts are not auto-generated, the audit will be painful — so I build them in."*

---

## Common Traps (red-flag answers)

- ❌ "Hash PII and we're done" — that's pseudonymisation, not anonymisation
- ❌ "Governance is Legal's job" — Legal interprets, you engineer the controls
- ❌ "GDPR is opt-out like CCPA" — they're opposite on consent
- ❌ "Just delete the row" — backups, derived data, caches, embeddings still hold it
- ❌ "We'll add governance in v2" — controls from day 1 or you'll be re-platforming
- ❌ "Screenshots are public" — they may contain secrets, PII, customer logic
- ❌ Inventing deadlines ("72h for deletion") — verify with counsel

---

## Practice Log

| Date | Time | Mode | Self-score (1–4) | Notes |
|---|---|---|---|---|
| | | (cold / timed / peer) | | |
| | | | | |

---

## Linked Material

- **Main prep doc:** `Katalon_Head_of_Data_Interview_Prep.md` Section 8 (governance + GDPR flow), Section 13 (data quality + incident response)
- **Sister files:** `strategy-question-prep.md`, `platform-architecture-question-prep.md`
- **Stories bank:** Section 21 — find a `S7: Privacy / Security / Compliance event` story
- **Flashcards:** Section 23
- **Scoring rubric:** Section 20

---

## Checklist Before Walking In

- [ ] 60–90 second answer said aloud, no notes
- [ ] 6 pillars (C-O-Q-S-P-L) and 6 quality dims (C-V-U-T-C-A) named
- [ ] GDPR vs CCPA contrast in 30 seconds
- [ ] DSAR flow drawn from memory (find → delete → prove)
- [ ] 3 erasure options in a lake (ACID/VACUUM, rewrite partitions, crypto-shredding)
- [ ] Hash ≠ anonymise
- [ ] One Tier-1 SLO example ready
- [ ] One Katalon-specific story: customer test artifact treated as confidential
- [ ] No invented deadlines — say "I'd verify with Legal"

---

## Closing Sentence (if asked "anything else?")

> Governance is the platform feature that makes everything else safe to ship. I'd build it so the right data is **easy to find and safe to use** — and so audits aren't a scramble. **Compliance is engineered, not documented.**