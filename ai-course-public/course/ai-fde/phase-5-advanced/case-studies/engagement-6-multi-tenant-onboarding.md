# Case Study 6 — Onboarding the 2nd Tenant (multi-tenant without breaking the 1st)

> **TL;DR.** A second customer (an e-commerce platform with 50-person CS team) signed up for the PacificFreight drafter 6 weeks after Phase 4. Onboarding them took 4 hours. **The drafter didn't change. The eval set didn't change. The 25/25 tests still pass.** What changed: a new YAML file (`tenants/ecom.yaml`), a new tenant_id in OAuth, a new bucket in Redis. **The pattern: every new tenant is a config change, not a code change.** This case study walks through the 4 hours, the 3 design decisions, and the 1 incident that almost happened.

---

## 1. The ask

ECommercePlatform (a pseudonym) had been watching PacificFreight's drafter for 6 weeks. Their CS team processes ~3,000 customer emails/day. They wanted:

- A 2nd-tenant deployment of the drafter (different policy, different rate limit, different cost ceiling).
- The same SLA (P95 < 2s, 99.5% uptime).
- Their own data, isolated from PacificFreight's.

The ECommercePlatform's CS lead (call her Sara) was the stakeholder. The PacificFreight CS lead (Mei) was the secondary stakeholder (to make sure the new tenant didn't break her own).

## 2. The 4 hours, minute by minute

| Minute | What | Why |
|---|---|---|
| 0-15 | Read the Phase 4 portfolio + the runbook | The lift must NOT break PacificFreight's eval set or 5-question test |
| 15-30 | Create `tenants/ecom.yaml` with their config | Code-reviewable, version-controlled, diffable |
| 30-60 | Issue the OAuth keys for Sara's team (RS256 keypair) | The private key lives on the auth server; the public key is in the drafter |
| 60-90 | Update the budget alert (Prometheus at 80% of $50/mo) | Their budget is $50/mo (10× PacificFreight's $5/mo) |
| 90-150 | Run the eval set against the new tenant's data | Confirms the drafter works on their CSVs + their policy corpus |
| 150-180 | Run the 25/25 tests with the new tenant's OAuth token | Confirms no regression in the existing test suite |
| 180-210 | 2 SEV-3 incidents during the eval: rate limiter too tight (rejected 3 legitimate requests) | Adjusted the per-user rate limit from 60/min → 200/min in their YAML |
| 210-240 | Onboarding Sara's team: 1-hour walkthrough, 5-question test (Sara's answers) | Same playbook as PacificFreight |

**The 4 hours were: 30% setup, 30% testing, 20% config tuning, 20% handoff.**

## 3. The 3 design decisions that mattered

### 3.1 Tenant config in YAML, not in a database

Same reason as Phase 4 MCP: code-reviewable, version-controlled, diffable. A database-backed policy would lose all three. **A new tenant is a 1-file change, not a deploy.**

### 3.2 OAuth tenant claim in the JWT, not in the URL

If `tenant_id` were in the URL (`/draft?tenant_id=ecom`), it would leak via logs, browser history, and Prometheus labels. Putting it in the signed JWT means a tenant can't be spoofed — the signature is verified on every request.

### 3.3 Rate limit at the application layer, not at the load balancer

The Phase 4 `TokenBucketRateLimiter` was per-worker, in-process. The Phase 5 `RedisTokenBucket` is per-tenant, per-user, atomic. The load balancer (Caddy) doesn't see the rate limit; the application does. **A tenant can have 200/min while another has 60/min, and the load balancer doesn't care.**

## 4. The 1 incident that almost happened

At minute 165, the eval set ran against ECommercePlatform's data and the **faithfulness metric dropped from 0.94 to 0.81**. The cause: their CS team writes emails in Bahasa Melayu (Malay) in addition to English, and the Phase 3 hybrid retriever wasn't tuned for the language.

**The fix:** I added a 5th metric to the eval set (`multilingual_faithfulness`) and a 3rd language to the policy corpus. Total time: 90 minutes. **The PacificFreight eval set is unchanged; ECommercePlatform's eval set is a superset.**

The 90-minute fix was the proof that the multi-tenant pattern works: one tenant's needs don't break another tenant's setup.

## 5. The 5-question test for the 2nd tenant (engagement 6)

| # | Question | Sara's answer (ECommercePlatform) | Mei's answer (PacificFreight, regression check) |
|---|---|---|---|
| 1 | What does the drafter do? | "Drafts replies to e-commerce customer emails." | unchanged ✅ |
| 2 | How do you know it's working? | "My thumbs-up rate. If it drops below 70%, something's wrong." | unchanged ✅ |
| 3 | What breaks first when it goes wrong? | "Same as PacificFreight — wrong shipment status, customer escalates." | unchanged ✅ |
| 4 | How do you fix it? | "Tell the FDE (or my new IT owner)." | unchanged ✅ |
| 5 | What's the cost ceiling, and how do you know when you've hit it? | "$50/month. Prometheus alert at $40/wk." | unchanged ✅ (different number; same pattern) |

**All 5 answered correctly by both tenants. The 2nd tenant's onboarding didn't regress the 1st tenant's handoff.**

## 6. The pattern (generalized)

Multi-tenancy is **per-tenant isolation + per-tenant config + per-tenant data**. The implementation:

| Layer | Per-tenant | Pattern |
|---|---|---|
| Auth | JWT `tenant_id` claim | OAuth + RS256 |
| Config | `tenants/{tenant_id}.yaml` | Same pattern as Phase 4 MCP |
| Data | Redis namespacing (`sess:{tenant_id}:...`) | Same pattern as Phase 5 P1 |
| Rate limit | `RedisTokenBucket` keyed on `(tenant_id, user_id)` | Same pattern as Phase 5 P1 |
| Cost ceiling | Prometheus alert per tenant | Standard Prometheus |
| Eval set | Per-tenant JSONL files | Eval set is a contract per tenant |
| Tests | Same 25/25 tests run with each tenant's OAuth token | The contract is the test |

**A new tenant is a config change + a 1-hour onboarding. Not a deploy.**

## 7. References

- The OAuth + multi-tenant code: `phase-5-advanced/projects/02-oauth-multi-tenant/`
- The Phase 4 multi-tenant roadmap: `phase-4-capstone/case-studies/PORTFOLIO-NARRATIVE.md` §4.5
- The 2nd-tenant YAML: `tenants/ecom.yaml` (the example; production is a real customer)
- The 5-question test for both tenants: `phase-4-capstone/case-studies/engagement-5-handoff.md`
