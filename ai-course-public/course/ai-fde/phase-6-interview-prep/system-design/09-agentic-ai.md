# System Design Sub-Lesson 9 — Agentic AI Systems (the canonical Pattern 9 walkthrough)

> **Agentic AI systems are the ninth most common system design pattern.** 10-15% of system design questions at AI companies involve agents (Claude Code, Cursor, LangChain agents, MCP servers, multi-agent dispatchers). The FDE signal: a candidate who names the hybrid retriever AND the cost ceiling AND the citation strategy — is showing they can own an AI system. **This sub-lesson walks through the canonical agentic AI design.**

---

## Why agentic AI is the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Agentic = LLM + tools + memory + planning. The requirement drives the design (single-agent vs multi-agent, RAG vs fine-tune, hosted vs self-hosted).
2. **Can you pick the right retriever?** BM25 for keyword search; dense for semantic search; hybrid (BM25 + dense + RRF) for both. The candidate who names the hybrid retriever is showing they understand the retrieval problem.
3. **Can you handle the cost ceiling?** LLM calls are $0.01-$0.10 per call. The candidate who names the cost ceiling + circuit breaker is showing they understand the operational boundary.
4. **Can you handle hallucination?** LLMs hallucinate. The candidate who names the citation strategy + thumbs-up/down feedback loop is showing they understand the quality problem.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is AI-focused.

---

## The canonical agentic AI design (worked example)

### The prompt

> "Design an agentic AI system: a customer support agent for a SaaS company. The agent answers customer questions about billing, account management, and product usage. 10K tickets/day, 80% handled by AI, 20% escalated to human. The agent must cite its sources and respect the customer's role (admin vs user vs guest)."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Customers (external) asking questions; CS team (internal) handling escalations.
2. **What's the scale?** 10K tickets/day = ~0.1 tickets/sec average (peak: 5 tickets/sec); 80% AI-handled.
3. **What's the constraint?** < 2-second P95 latency; cost < $500/month; citation in every response; role-based access (admin/user/guest).
4. **What's the failure mode?** LLM hallucinates; tool call fails; rate limit exceeded; cost ceiling breached.
5. **What's the timeline?** MVP in 4 weeks; full scale in 8 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Ticket (id, customer_id, subject, body, status, created_at)
- Response (id, ticket_id, content, citations, thumbs_up, created_at)
- Citation (id, response_id, doc_id, chunk_id, score)
- ToolCall (id, ticket_id, tool_name, input, output, status)
- Escalation (id, ticket_id, reason, priority, created_at)

**Services:**
- TicketAPI (CRUD for tickets)
- Retriever (hybrid: BM25 + dense + RRF)
- LLMClient (with circuit breaker + cost ceiling)
- ToolRegistry (MCP server with policy file)
- EscalationService (routes complex tickets to humans)

**Flows:**
- Customer submits ticket → TicketAPI validates → Retriever retrieves top-5 chunks → LLMClient generates response with citations → ToolRegistry checks for tool calls → returns response
- If LLM hallucinates (no citations): user clicks thumbs-down → thumbs-down feedback loop triggers a regression check
- If cost ceiling breached: circuit breaker fails closed, returns a fallback response
- If ticket is complex (refund > $100, account deletion): EscalationService routes to human

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /tickets
  Body: {"customer_id": "CUST-12345", "subject": "...", "body": "..."}
  → 201 Created
  → {"ticket_id": "TKT-12345", "status": "processing"}

GET /tickets/{id}
  → 200 OK
  → {"ticket_id": "TKT-12345", "status": "answered", "response": "...", "citations": [...]}

POST /tickets/{id}/feedback
  Body: {"thumbs": "up" | "down"}
  → 200 OK

POST /admin/tickets/{id}/escalate
  Body: {"reason": "...", "priority": "low" | "medium" | "high"}
  → 200 OK
```

**The data model (3-5 tables):**

```
tickets (
  id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  subject VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'processing',  -- processing, answered, escalated, failed
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
)

responses (
  id BIGSERIAL PRIMARY KEY,
  ticket_id BIGINT REFERENCES tickets(id),
  content TEXT NOT NULL,
  thumbs_up BOOLEAN,
  thumbs_down BOOLEAN,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
)

citations (
  id BIGSERIAL PRIMARY KEY,
  response_id BIGINT REFERENCES responses(id),
  doc_id BIGINT,
  chunk_id BIGINT,
  score DECIMAL(3, 2) NOT NULL
)

tool_calls (
  id BIGSERIAL PRIMARY KEY,
  ticket_id BIGINT REFERENCES tickets(id),
  tool_name VARCHAR(50) NOT NULL,
  input JSONB,
  output JSONB,
  status VARCHAR(20) NOT NULL
)
```

**The cost ceiling model:**
- Cost per ticket: $0.0017 (LLM $0.001 + retriever $0.0005 + tool calls $0.0002)
- Tickets per day: 10K
- Cost per day: $17
- Cost per month: $510 (~$500/month)
- Cost ceiling: $500/month (the customer wants this)
- Circuit breaker: fail closed when cost ceiling is hit

**The scale model:**

- **Tickets:** 10K/day; ~0.1 tickets/sec average; 5 tickets/sec peak
- **Latency:** < 2-second P95
- **Cost:** ~$500/month (LLM $300 + retriever $150 + tool calls $50 + Postgres + Redis + observability)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Hosted LLM (GPT-4o-mini) vs self-hosted SLM (Qwen-1.5B).** Hosted is simpler; self-hosted is cheaper at scale. Pick hosted for MVP; pick self-hosted at 100K tickets/day.
2. **Single agent vs multi-agent.** Single is simpler; multi-agent is more capable. Pick single for 80% of tickets; pick multi-agent for complex tickets (refund + account change).
3. **Citation in every response vs on-demand citation.** Citation in every response builds trust; on-demand is faster. Pick citation in every response for high-stakes (billing); pick on-demand for low-stakes (general questions).

**The closing line:** "For 10K tickets/day with < 2-second P95 latency, 80% AI-handled, and < $500/month cost, I'd use a hybrid retriever (BM25 + dense + RRF), a hosted LLM (GPT-4o-mini) with a circuit breaker, an MCP server with policy enforcement (role-based access), and citation in every response + a thumbs-up/down feedback loop. The cost is $500/month, under the $500/month ceiling. The failure mode is hallucination; the mitigation is citation + thumbs-up/down + the eval-set-as-spec regression check."

---

## The 5 most common agentic AI questions

The 5 questions that cover 90% of agentic AI system design:

1. **"Design a customer support agent"** — covered by the canonical example above.
2. **"Design a code generation agent (Claude Code / Cursor)"** — same pattern, with file system tools + diff-based output.
3. **"Design a knowledge worker agent (RAG over company docs)"** — same pattern, with hybrid retriever + eval set.
4. **"Design a multi-agent dispatcher"** — same pattern, with orchestrator + per-agent state + escalation.
5. **"Design an AI data analyst (code generation + execution)"** — same pattern, with sandbox + security blocklist.

**The pattern:** agentic AI = hybrid retriever + LLM (with circuit breaker + cost ceiling) + tool registry (with policy file) + citation + feedback loop. The variations are the agent count (1 vs N), the tools (read vs write), and the safety model (RBAC vs sandbox).

---

## The 5 anti-patterns for agentic AI

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the cost ceiling.** The candidate who doesn't mention the cost ceiling + circuit breaker is signaling they don't operate AI systems.
3. **Skipping the citation strategy.** The candidate who doesn't mention citation + thumbs-up/down is signaling they don't think about hallucination.
4. **Skipping the policy file.** The candidate who doesn't mention role-based access (admin/user/guest) is signaling they don't think about security.
5. **Skipping the eval set.** The candidate who doesn't mention the eval set as the regression check is signaling they don't ship AI systems.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you prevent hallucination?" | "Citation in every response. Thumbs-up/down feedback loop. Eval set as the regression check (RAGAS 4 metrics: faithfulness, ansrel, context_precision, context_recall). The eval set is the contract." |
| 2. "How do you handle a tool call failure?" | "Circuit breaker on the tool. Retry with exponential backoff. After 3 failures, escalate to human. Log the failure to the audit log." |
| 3. "How do you scale to 100K tickets/day?" | "Self-hosted SLM (Qwen-1.5B) for 90% of traffic. Hosted LLM (GPT-4o-mini) for the long-tail 10%. Cost: $500/month (10x reduction)." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../generative-ai/companion-courses/ed-donner-ai-engineer-core-track.md` | The 8-project cross-reference |
| `../generative-ai/companion-courses/intro-to-ai-agents.md` | The agent vocabulary primer |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 9: agentic AI) |

---

## The thesis

**Agentic AI is the ninth and fastest-growing system design pattern.** The candidate who names the hybrid retriever AND the cost ceiling AND the citation strategy — is showing they can own an AI system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (customer support, code generation, knowledge worker, multi-agent, data analyst) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Agentic AI system design prep gets you past the centerpiece round at Anthropic, OpenAI, LangChain, Sierra AI, Databricks, and Scale AI.**