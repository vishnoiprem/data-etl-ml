# 99. Palantir (ML / AIP)

- **Role:** Forward Deployed Engineer (FDE) / ML Engineer (AIP — AI Platform)
- **Tech stack:** Java, TypeScript, Python, Scala, Spark, Flink, Foundry, Ontology, AWS/Azure/GovCloud, PostgreSQL, Kubernetes
- **Comp band:** $130K-$300K base + significant equity; senior $250K-$500K; staff $400K-$1M+ (Levels.fyi 2026, including equity)
- **Cumulative pass rate:** ~1.5-2.5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, role fit, willingness to deploy | 30 min | ~50% advance |
| 2. **Coding screen** | 1-2 LeetCode medium-hard problems | 60 min | ~35% advance |
| 3. **Onsite (5-6 rounds)** | 2 coding, 1 system design, 1 deployment/architecture, 1 behavioral, 1 hiring manager | 2-3 days | ~25% advance |
| 4. **Hiring committee** | Site lead + cross-functional | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp + level + team | 1 week | — |

Palantir's loop is unique: Forward Deployed Engineers are the primary hire, and they deploy to customer sites (defense, gov, commercial) to build Foundry/AIP solutions. The ML surface (AIP, launched 2023) is for building AI agents on top of Palantir's ontology — the integrated data model of the customer's operations. Bar is high on coding and customer-deployment readiness. Some roles require US security clearance.

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** "I built [X] for [Y]. Most recently I [deployed / shipped / solved] [Z]."
**Tip:** Palantir FDEs deploy. Mention customer-facing work, ability to travel, US citizenship or clearance if you have it.

### Q1.2: "Why Palantir?"
**Answer:** "Three reasons. First, AIP is a real product for the most demanding customers — defense, intel, healthcare, manufacturing. The ML is mission-critical. Second, the ontology approach is genuinely different — instead of building ML on raw data, you build it on an integrated data model. Third, I want to work on AI for problems that actually matter — not ads, not engagement, but supply chains, military logistics, public health."
**Tip:** Reference AIP, Foundry, and the 2026 customer stories. Be specific about which missions excite you.

### Q1.3: "Deployment willingness + clearance"
**Answer:** Palantir FDEs travel (often 50%+). Be clear on willingness. Some roles require TS/SCI clearance.

## Stage 2: Coding screen (60 min)

### Q2.1: Coding — "Word break" or "LRU cache" or "Merge intervals"
**Answer:** Standard.
**Tip:** Medium-hard LeetCode. Palantir's bar is high on coding.

### Q2.2: System design chat — "Design a system to integrate 10 enterprise data sources"
**Answer:** "Source-specific connectors (JDBC, S3, API, SFTP) → schema discovery → ontology mapping (entity resolution, type inference) → write to Foundry's object store with lineage → expose via query layer (SQL, Pipeline Builder) → audit logging. Handle schema drift. Reference Palantir's data integration capabilities."
**Tip:** Ontology is Palantir's core. Show you understand entity resolution and data integration at scale.

### Q2.3: ML — "How would you build an AI agent on Palantir's ontology?"
**Answer:** "Three parts. (1) Tool definitions: AIP exposes the ontology as a set of tools — query, transform, write — that the LLM can call. (2) Planning: LLM agent with multi-step planning, error recovery, human-in-the-loop checkpoints. (3) Eval: golden task suite, success rate, steps-to-completion, human feedback. (4) Deployment: customer-specific ontology, customer-specific tools, sandbox before live write."
**Tip:** AIP is the canonical "AI on enterprise data" product. Be specific.

## Stage 3: Onsite (5-6 rounds, 2-3 days)

### Round 3.1: Coding (2 rounds)
**Q3.1.1:** "Median of two sorted arrays" or "Longest palindromic substring."
**Q3.1.2:** "Design a real-time event processor" — sliding window, dedup, state.
**Q3.1.3:** "Parse a log file and produce a report" — string processing, hash maps.

### Round 3.2: System design
**Q3.2.1:** "Design a Foundry deployment for a 1000-user enterprise." Discuss deployment architecture, multi-tenancy, security, integration with customer's identity, observability.
**Q3.2.2:** "Design an AIP agent for supply chain disruption response." Discuss tools, planning, integration with customer's data, human oversight, audit.

### Round 3.3: Architecture / Deployment
**Q3.3.1:** "How would you deploy AIP to a customer with no internet access (air-gapped)?" Discuss on-prem deployment, model size, GPU, offline update.
**Q3.3.2:** "How would you handle customer PII in AIP?" Discuss data minimization, on-prem inference, audit, opt-in.

### Round 3.4: Behavioral
**Q3.4.1:** "Time you had to ship under customer pressure." STAR.
**Q3.4.2:** "Time you disagreed with a customer." STAR.
**Q3.4.3:** "Why deployment over pure engineering?" — Palantir values customer-facing work.

### Round 3.5: Hiring manager
**Q3.5.1:** "Walk me through your favorite customer-facing project." Be specific about technical work and customer impact.

## Stage 4: Hiring committee
Palantir's committee includes the site lead and a senior FDE. The bar is "can this person deploy to a government customer next quarter?" — practical, not theoretical. Senior requires independent deployment leadership. Staff requires cross-customer platform influence. Loop is long (2-3 days) and rigorous.

## Stage 5: Offer
Palantir comp is high but with a lower base than FAANG and more equity weight. RSU is 4-year vest. They negotiate on equity. Relocation is funded. Team match is usually pre-onsite for some roles. Post-offer, expect to deploy to a customer within 30-90 days.

## Tips for the Palantir loop
1. **Deployment readiness is a first-class signal** — show you can talk to customers.
2. **Ontology thinking is the differentiator** — entities, links, actions.
3. **Defense / gov awareness matters** — some roles need clearance, all roles need awareness.
4. **AIP is the LLM platform** — know the architecture (tools, planning, ontology-backed).
5. **Coding is medium-hard LeetCode** — clean, fast code.
6. **Reference Palantir's customer stories** — defense, healthcare, manufacturing, finance.
7. **Be ready to defend the mission** — Palantir is controversial; have a thoughtful answer.

## Real candidate report
> "I interviewed for FDE. 5 rounds over 2 days. The deployment round asked me to design a Foundry deployment for a government customer with no internet — they wanted air-gapped architecture, on-prem ML inference, and audit. The behavioral round was on customer pushback. Got an offer at $250K base + $600K RSU/4yr, Denver. They moved equity by $100K on negotiation. The interview prep was the most rigorous I've done — Palantir doesn't apologize for long loops." — Blind, 2025

## Sources
- [Palantir Engineering Blog](https://blog.palantir.com/)
- [Palantir AIP Documentation](https://palantir.com/docs/foundry/aip/overview/)
- [Levels.fyi Palantir](https://www.levels.fyi/companies/palantir)
- [Glassdoor Palantir interviews](https://www.glassdoor.com/Interview/Palantir-Interview-Questions-E236428.htm)
- [LeetCode Palantir tagged](https://leetcode.com/company/palantir/)