# 06 — Regulated-Industry Reference Architecture

> **Customer problem:** Stand up a GenAI capability in a regulated environment (PII + PHI + cross-border data residency). Zero data egress, full auditability, regulator-ready evidence pack. Map every control to NIST AI RMF and ISO 42001.

This project is the **secure-by-default reference pattern** that any regulated GenAI workload should start from. It implements the four pillars: PII redaction, prompt-injection detection, tamper-evident audit logging, and IAM-scoped access control — all enforceable in code with a working demo.

---

## 1. Theory: The four pillars of regulated AI

| Pillar | What it protects against | Production tooling | Demo tooling |
|---|---|---|---|
| **PII / PHI redaction** | Sensitive data leaving the model boundary | Bedrock Guardrails, AWS Comprehend, Macie | Regex + entity rules in `pii.py` |
| **Prompt-injection defense** | User-controlled text exfiltrating data or hijacking tools | Bedrock Guardrails, Lakera, layered defenses | Heuristic detector in `injection.py` |
| **Tamper-evident audit log** | Repudiation, "what did the model see/say" | CloudTrail + QLDB or Glacier with Object Lock | Hash-chained log in `audit.py` |
| **Authorization** | Wrong tenant / role accessing data | IAM Identity Center + ABAC, Cedar | Policy engine in `authz.py` |

These are not optional in regulated industries. They are the **table stakes** before a single LLM call goes to production.

## 2. Defense-in-depth flow

```
                ┌──────────────────────────────────────────────┐
   user input  ▶│ 1. Authn / Authz   (who is calling? on what?)│
                └──────────────────┬───────────────────────────┘
                                   │ allow
                                   ▼
                ┌──────────────────────────────────────────────┐
                │ 2. Input PII redaction + injection detection │
                └──────────────────┬───────────────────────────┘
                                   │ sanitized
                                   ▼
                ┌──────────────────────────────────────────────┐
                │ 3. Retrieval with ACL filters (chunk-level)  │
                └──────────────────┬───────────────────────────┘
                                   │ allowed chunks only
                                   ▼
                ┌──────────────────────────────────────────────┐
                │ 4. Bedrock invoke (with Bedrock Guardrails)  │
                └──────────────────┬───────────────────────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────────────────┐
                │ 5. Output PII redaction + safety filters     │
                └──────────────────┬───────────────────────────┘
                                   │
                                   ▼
                ┌──────────────────────────────────────────────┐
                │ 6. Tamper-evident audit log (hash-chained)   │
                └──────────────────────────────────────────────┘
```

A failure at any layer is logged but does not assume layers above caught it. Defense is *layered*.

## 3. Compliance mapping

The demo's controls map to:

| Control family | NIST AI RMF | ISO 42001 | SOC 2 |
|---|---|---|---|
| PII handling | MAP 4.1, MEASURE 2.10 | A.7.4 | CC6.1, P5.1 |
| Prompt-injection | MEASURE 2.6 | A.6.2.5 | CC7.2 |
| Audit logging | GOVERN 4.1 | A.5.32 | CC4.1, CC7.3 |
| Access control | GOVERN 1.5 | A.5.15 | CC6.1, CC6.3 |

Every audit-log entry carries the control family it satisfies, so an auditor can pull "all evidence for SOC 2 CC6.1" with a single query.

## 4. Network architecture (production)

```
                       ┌────────────────────────────┐
                       │  Corporate IdP (Identity   │
                       │  Center) → SAML / OIDC     │
                       └───────────────┬────────────┘
                                       │ federation
   ┌───────────────────────────────────▼──────────────────────────────┐
   │                          PRIVATE VPC                              │
   │                                                                    │
   │  ┌────────────┐    ┌────────────┐    ┌──────────────────────┐    │
   │  │  API GW    │──▶ │  Lambda    │──▶ │  PrivateLink endpts  │    │
   │  │  (mTLS)    │    │  Auth+RAG  │    │  ┌──────────────┐    │    │
   │  └────────────┘    └─────┬──────┘    │  │  Bedrock     │    │    │
   │                           │          │  │  S3          │    │    │
   │                           ▼          │  │  OpenSearch  │    │    │
   │                     ┌──────────┐    │  │  KMS         │    │    │
   │                     │ Guard-   │    │  └──────────────┘    │    │
   │                     │ rails    │    └──────────────────────┘    │
   │                     └──────────┘                                  │
   │                                                                    │
   │  No internet egress. PrivateLink only. KMS CMKs per tenant.       │
   └────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                       ┌────────────────────────────┐
                       │ Audit account (separate):  │
                       │ S3 Object Lock + QLDB       │
                       └────────────────────────────┘
```

## 5. Quick Start

```bash
pip install -r requirements.txt
make demo
```

The demo:
1. Sends a mix of normal + adversarial requests through the full pipeline.
2. Shows authz decisions, PII redactions, injection detections, and final responses.
3. Validates the audit log hash chain (proves no entries were tampered with).

## 6. What "Done" Looks Like

| Metric | Target |
|---|---|
| PII leak rate (red-team set) | 0% |
| Prompt-injection success rate | < 2% |
| Audit-log gap detection | 100% |
| Control-mapping coverage | 100% of in-scope controls |
| Mean time to evidence pack (per audit) | < 1 day |
