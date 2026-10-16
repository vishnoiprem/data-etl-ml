# Lesson 23: Security and privacy

> **Week 5 · Day 23 · 90 min**
> **Deliverable:** The 5 security controls + the breach response playbook.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Security and privacy are the CDO's license to operate. A breach kills the AI mandate, the customer trust, and sometimes the company. The CDO must own this, not delegate it to "the CISO will handle it."

The 5 security controls for a data platform:

| Control | What it does | Implementation |
|---|---|---|
| **1. IAM (identity & access)** | Who can access what, under what conditions | RBAC + ABAC; least privilege; JIT access; MFA |
| **2. Encryption** | Protect data at rest and in transit | AES-256 at rest; TLS 1.3 in transit; customer-managed keys |
| **3. Lineage + audit** | Trace every read/write to a user, time, purpose | Column-level lineage; immutable audit log |
| **4. Key management** | Who holds the keys; rotation; break-glass | KMS; rotation policy; dual control for master keys |
| **5. Network isolation** | Where the data physically and logically lives | VPC; private endpoints; no public S3; egress controls |

The single biggest mistake is to **treat security as a checkpoint at deploy**. Security is a property of the architecture. If the architecture has public S3 buckets and shared service accounts, no amount of "review" will save you.

The second biggest mistake is to **not have an incident response plan**. The plan is not "call the CISO." The plan is: who declares the incident, who leads the war-room, who communicates to the board, who communicates to the regulator, who communicates to the press. The plan is rehearsed quarterly.

The third biggest mistake is to **not rehearse the breach**. A plan that has never been tested is a hope. Tabletop exercises, red-team / blue-team, and phishing simulations are the only way to know the plan works.

## 🛠️ Build It

**Spec:** Design the 5 controls + the breach response for the retailer. Assume PCI-DSS, GDPR, CCPA, and (in 24 months) AI Act.

**Acceptance:**
- 5 controls, each with implementation
- Breach response: detection, war-room, comms, regulator notification, post-mortem
- Notification timelines: GDPR (72h), CCPA (varies), AI Act (varies)
- 1 paragraph on the trade-off (zero-trust vs. perimeter)

**Starter:** Use the architecture from Week 4. Layer the security controls on top.

**Solution (5 controls, abridged):**

| Control | Implementation |
|---|---|
| IAM | RBAC (role) + ABAC (attribute: project, BU, purpose). Least privilege. JIT access. MFA mandatory. |
| Encryption | AES-256 at rest (S3, warehouse). TLS 1.3 in transit. Customer-managed keys (KMS). |
| Lineage + audit | DataHub column-level. Immutable audit log (S3 Object Lock). Every query logged. |
| Key management | KMS, 90-day rotation, dual control for master keys, break-glass procedure documented. |
| Network isolation | VPC, private endpoints, no public S3, egress controls, flow logs. |

**Breach response (abridged):**

| Phase | Action | Owner | Timeline |
|---|---|---|---|
| Detection | Alert (SIEM, observability) | Security on-call | <15 min |
| Triage | Declare incident; convene war-room | CISO + CDO | <30 min |
| Containment | Isolate affected systems | Security + platform | <2 h |
| Eradication | Remove threat; patch | Security | <24 h |
| Recovery | Restore from clean backup | Platform | <72 h |
| Notification | GDPR: 72h to regulator; CCPA: per state; customers: ASAP | Legal + comms | <72 h |
| Post-mortem | Blameless review; action items with owners | CISO + CDO | <14 days |

## 🏛️ Architect Notes

- **Trade-off:** Zero-trust vs. perimeter. Default: zero-trust. Every request authenticated, authorized, logged. Perimeter is a fallback for legacy.
- **Capacity / cost:** A security org (CISO + 8-12) for a 1,200-store retailer. The data org is a stakeholder, not the owner. CISO owns the controls; CDO owns the data.
- **When NOT to use:** Don't run a breach response for the first time during an actual breach. Rehearse quarterly.
- **Production checklist:**
  - [ ] 5 controls named
  - [ ] Implementation per control
  - [ ] Breach response phases
  - [ ] Notification timelines (GDPR, CCPA, AI Act)
  - [ ] Post-mortem process
  - [ ] Tabletop exercise cadence

## 🌙 Reflect

- Which control is the most-likely breach vector for the role you're interviewing for? Pre-write the answer.
- Who would you call first if you discovered a breach at 2am?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 24 — Responsible AI.