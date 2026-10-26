# Microsoft — AI Engineer / Customer Engineer (Azure OpenAI / Copilot)

> Microsoft's AI Engineer / Customer Engineer role is the **Azure + M365 + Copilot + enterprise** variant. Unlike Anthropic / OpenAI / Sierra (pure model API), Microsoft's FDE ships **Azure OpenAI + Copilot Studio + M365 integration + the enterprise data plane (SharePoint, Outlook, Teams)** — they care about the **M365 tenant** as much as the model. The FDE signal: a candidate who can talk about **Azure OpenAI + Copilot Studio + M365 Graph API + the customer's tenant boundary** — is signaling they can own an enterprise AI deployment on Azure.

---

## TL;DR (1 page)

**Microsoft's AI Engineer / Customer Engineer (CE) role** sits between Sales Engineering and Applied AI. The work: ship **Azure OpenAI + Copilot Studio + M365 Graph API** into a Microsoft enterprise customer (banking, government, healthcare, retail). The interview loop tests 4 things: (1) can you design a Copilot that grounds on SharePoint / Outlook / Teams? (2) can you reason about the **M365 tenant** (data residency, compliance, audit)? (3) can you handle the **stakeholder map** (IT, security, compliance, business unit)? (4) can you own the handoff to the customer's M365 admin team? The candidate who names the **Azure OpenAI deployment + Copilot Studio + the Graph API + the M365 audit log** — is signaling they can own an enterprise AI deployment on Azure.

---

## Why Microsoft is the right target

The 4 reasons a Microsoft AI Engineer / CE interview is different from a generic FDE loop:

1. **The M365 tenant is the model.** Microsoft enterprise customers care about the **M365 tenant boundary** (data residency, audit, conditional access). The candidate who can talk about SharePoint sites, Outlook mailboxes, Teams channels, and the Graph API is signaling they understand enterprise data.
2. **Azure OpenAI is opinionated.** Azure OpenAI is a managed service with **deployments, content filters, fine-tuning, and PTU (Provisioned Throughput Units)**. The candidate who names the **PTU vs pay-as-you-go tradeoff + the content filter posture + the deployment region** is showing they know the Azure OpenAI stack.
3. **Copilot Studio is the agent framework.** Copilot Studio (formerly Power Virtual Agents) is the agent orchestration layer. The candidate who names **Copilot Studio's topic-based dialog + plugin actions + the Azure AI Search grounding** is showing they know the agent framework.
4. **The customer is M365-locked.** Most Microsoft enterprise customers are M365 customers (Exchange, SharePoint, Teams). They want AI to **respect the M365 permissions** (SharePoint site permissions, Outlook mailbox permissions, Teams channel permissions). The FDE has to land AI in that reality.

---

## The Microsoft AI Engineer / CE loop (5-6 rounds)

The typical Microsoft AI Engineer / Customer Engineer loop:

| Round | Format | Duration | Tests |
|---|---|---|---|
| 1. Recruiter | Phone (behavioral + resume) | 30 min | Communication, motivation, Microsoft fit |
| 2. Coding (technical screen) | Codility / HackerRank | 60 min | Algorithms + Python + C# / TypeScript |
| 3. **Copilot / Azure OpenAI Design** (signature) | Live system design | 60 min | Agent design + Azure OpenAI + M365 grounding |
| 4. **Customer Sim** | Live roleplay | 45 min | Stakeholder handling, scoping, M365 permissions |
| 5. **Azure Data Plane** | Live technical | 60 min | Azure OpenAI, Cosmos DB, Azure AI Search, Entra ID |
| 6. HM / Behavioral | Final loop | 60 min | Microsoft values + ownership + handoff story |

**Total time-spend:** 5-8 hours over 3-5 weeks. **Pass rate:** 4-6% (most candidates fail the Copilot Design round — the M365 tenant + grounding + Azure OpenAI cost is what Microsoft cares about).

---

## The 5 things Microsoft tests that other FDE loops don't

1. **The M365 tenant model.** The candidate who names **SharePoint sites + Outlook mailboxes + Teams channels + the Graph API + the M365 audit log** is signaling they understand enterprise data. The candidate who only knows "Azure OpenAI" is signaling they haven't shipped to enterprise.
2. **Azure OpenAI PTU vs pay-as-you-go.** PTU is **provisioned throughput** (predictable cost, guaranteed capacity). Pay-as-you-go is **per-token** (variable cost, no capacity guarantee). The candidate who names the **PTU for predictable workloads + pay-as-you-go for bursty workloads** is showing they understand Azure billing.
3. **Copilot Studio's topic-based dialog.** Copilot Studio is **declarative** (topics, trigger phrases, actions) — not code-first. The candidate who names **topics + trigger phrases + plugin actions + the Azure AI Search grounding** is showing they know the agent framework.
4. **The content filter + safety posture.** Azure OpenAI has **content filters** for hate, violence, sexual, self-harm. The candidate who names the **content filter configuration + the safety eval set + the "we don't ship models that we wouldn't ship to our own kids" stance** is signaling they understand the responsible-AI posture.
5. **The Microsoft values + the enterprise signal.** Microsoft loves **growth mindset + customer obsession + diversity + inclusion**. The candidate who can talk about delivering AI to a **global enterprise with 100K employees, 50+ languages, and 30+ regulatory jurisdictions** — is signaling they fit the enterprise culture.

---

## The signature question

> "Design a Microsoft Copilot for a global bank's M365 tenant. The Copilot helps relationship managers find customer info, summarize meetings, and draft emails. 10K RMs, 1M queries/day, sub-2-second P95 latency. The Copilot must respect M365 permissions (SharePoint site permissions, Outlook mailbox permissions) and meet the bank's regulatory requirements (data residency in EU, audit log for every query)."

**The FDE answer shape:**

1. **Clarify (5 min):** What's the workload? (10K RMs, 1M queries/day, M365-grounded). What's the latency budget? (2-second P95). What's the compliance boundary? (data residency in EU + audit log + M365 permissions). What's the eval set? (precision + recall on a held-out set of RM queries). What's the timeline? (PoC in 6 weeks; full deploy in 16 weeks).
2. **Decompose (10 min):** Entities (Query, Response, Citation, GraphResult, EvalResult). Services (CopilotStudio, AzureOpenAIClient, GraphAPIClient, AuditLogger). Flows (RM query → CopilotStudio routes → GraphAPIClient retrieves (with M365 permissions) → AzureOpenAI generates response with citations → AuditLogger logs every query).
3. **Design (15 min):** API (POST /copilot/query returns answer + citations + audit_id). Data model (queries + responses + citations + eval runs + audit log). Deployment (Copilot Studio + Azure OpenAI (PTU) + Graph API + Azure AI Search for semantic retrieval + Cosmos DB for the audit log). Monitoring (Azure Monitor + Application Insights + eval-set-as-spec regression check).
4. **Tradeoffs (10 min):** (a) **Copilot Studio vs Azure AI Foundry.** Copilot Studio is low-code and M365-aligned. Foundry is code-first and Azure-aligned. Pick Copilot Studio for M365 deployments. (b) **PTU vs pay-as-you-go.** PTU is predictable and guaranteed. Pick PTU for the bank's 1M queries/day. (c) **Graph API vs Azure AI Search.** Graph API is precise (M365 permissions). Azure AI Search is semantic. Pick Graph API for structured retrieval; pick Azure AI Search for unstructured grounding.
5. **Closing line:** "For 10K RMs at 1M queries/day with 2-second P95 and EU data residency, I'd use Copilot Studio + Azure OpenAI (PTU for predictable capacity) + Graph API (with M365 permissions) + Azure AI Search for semantic grounding + Cosmos DB for the audit log + Azure Monitor for observability. The cost is $X/month (PTU + Copilot Studio + Graph API + Cosmos DB), under the $X ceiling. The failure mode is hallucination; the mitigation is citations + the eval-set-as-spec regression check. The compliance boundary is the M365 tenant + the EU region + the audit log."

---

## The Microsoft prep plan (8 weeks)

**Weeks 1-2: Azure + M365 literacy**
- Set up an Azure free-tier account. Deploy an Azure OpenAI resource with GPT-4o. **Measure the PTU cost** vs pay-as-you-go for a 100K-token workload. The candidate who has measured PTU cost is signaling they understand Azure billing.
- Set up an M365 dev tenant. Use the Graph API to retrieve a SharePoint file, an Outlook email, a Teams message. The candidate who has used the Graph API is signaling they understand M365.
- Read the Azure OpenAI documentation (PTU, content filters, fine-tuning). Read the Copilot Studio documentation (topics, trigger phrases, actions).

**Weeks 3-4: The M365 grounding + Copilot Studio**
- Build a grounding pipeline: a user's question → Graph API (with M365 permissions) → Azure OpenAI → answer. Validate on a 100-row eval set.
- Build a Copilot Studio agent that uses a topic, a trigger phrase, and a plugin action. Deploy the agent to a test M365 tenant. The candidate who has deployed a Copilot Studio agent is signaling they can ship.
- **The canonical artifact:** a `copilot_guide.md` that walks a customer through the Copilot Studio + Azure OpenAI + Graph API + the eval set as the regression check.

**Weeks 5-6: The customer sim + decomposition drills**
- Practice 5 customer sims: (a) bank wants EU data residency + audit log + Entra ID conditional access; (b) government wants FedRAMP + IL5 + air-gapped deployment; (c) healthcare wants HIPAA + the Copilot to never log PHI; (d) retailer wants the Copilot to ground on SharePoint + Outlook + Teams with M365 permissions; (e) manufacturer wants the Copilot to ground on Azure AI Search (unstructured docs) + Cosmos DB (structured data).
- Practice 3 decomposition questions: ship a Copilot grounded on M365, debug a hallucination, scale the Copilot to 10M queries/day.
- **The closing line:** "For X workload at Y scale with Z constraint, I'd use Copilot Studio + Azure OpenAI + Graph API (with M365 permissions) + Azure AI Search for semantic grounding + Cosmos DB for the audit log + the eval set as the regression check. The compliance boundary is the M365 tenant + the EU region + the audit log. The handoff is the copilot_guide.md + the runbook + the on-call rotation."

**Weeks 7-8: Mock loop + STAR rehearsal**
- Mock the 5-round loop with an AI assistant. Time yourself at 60 min per round.
- Rehearse 5 STAR stories: (1) shipped a Copilot grounded on M365 for a global bank; (2) handled a FedRAMP conversation with a government customer; (3) debugged a hallucination caused by stale SharePoint data; (4) wrote a copilot guide for a customer; (5) handed off a Copilot to a customer's M365 admin team.

---

## The 5 anti-patterns for Microsoft

1. **Treating Azure OpenAI as "just an OpenAI endpoint."** Azure OpenAI is **managed, region-pinned, content-filtered, PTU-priced**. The candidate who doesn't mention PTU is signaling they haven't shipped to enterprise.
2. **Skipping the M365 tenant model.** The candidate who doesn't mention **SharePoint sites + Outlook mailboxes + Teams channels + the Graph API** is signaling they don't understand enterprise data.
3. **Skipping the M365 permissions story.** The candidate who doesn't mention **SharePoint site permissions + Outlook mailbox permissions + Teams channel permissions** is signaling they don't understand M365.
4. **Skipping the data residency + audit log story.** The candidate who doesn't mention **EU data residency + FedRAMP + the audit log + Entra ID conditional access** is signaling they don't understand enterprise compliance.
5. **Skipping the handoff story.** The candidate who doesn't mention the **handoff artifact (copilot_guide.md + runbook + the M365 admin handoff)** is signaling they don't own the delivery.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle M365 permissions for a Copilot?" | "The Graph API respects M365 permissions. The Copilot uses the RM's M365 token, not a service account, so the RM only sees what they're allowed to see. The audit log records every query with the RM's identity." |
| 2. "What if Azure OpenAI is too slow under load?" | "Scale PTU. Move from 100 PTU to 500 PTU. The cost goes up but the latency goes down. The bank signs off on the PTU capacity before deploy." |
| 3. "How do you handle data drift in SharePoint?" | "SharePoint site-level monitoring + freshness alerts. Eval-set-as-spec regression check on a weekly cadence. If the eval metrics drop > 5%, alert the customer's M365 admin team." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The M365 grounding + retrieval-augmented generation pattern |
| `../system-design/04-distributed-storage.md` | The Cosmos DB + Azure AI Search data plane |
| `../decomposition/README.md` | The 4-step framework applied to a Copilot deployment |

---

## The thesis

**Microsoft's AI Engineer / Customer Engineer role is the M365 + Azure OpenAI + Copilot Studio + enterprise variant.** The candidate who names **Copilot Studio + Azure OpenAI (PTU) + Graph API + the M365 audit log + the data residency boundary** — is signaling they can own an enterprise AI deployment on Azure.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The signature question — "design a Copilot for a global bank's M365 tenant with 1M queries/day, EU residency, and audit log" — is the worked example. Practice it out loud, time yourself at 60 minutes, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Microsoft prep gets you past the centerpiece round at Microsoft Customer Engineering, Azure AI, and Copilot / M365 enterprise deployments.**
