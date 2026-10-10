# Intro to AI Agents and Agentic AI — The 2-hour foundations primer

> **Source:** "Intro to AI Agents and Agentic AI" — 9 sections, 54 lectures, 2h 11m total. **This is the shortest, most-focused companion course in Phase 6:** a 2-hour primer that covers the agent fundamentals (ReAct, ReWoo, multi-agent, n8n workflow) in a way that pairs naturally with Ed Donner's 8-week deep-dive. **Best for candidates who want a fast ramp-up to the agent terminology before tackling Ed's Week 8 capstone or the Phase 4 multi-agent project.**

---

## Why this course is the right primer

Ed Donner's "AI Engineer Core Track" is 33.5 hours and assumes you have time to build 8 projects. This course is **2 hours and assumes you have 2 hours.** The two are complementary:

- **Ed Donner's Week 8 capstone** = the deep-dive. Build a multi-agent system with Modal + Pydantic + LangGraph. 8-12 hours.
- **This course** = the primer. Learn what an agent is, what ReAct and ReWoo mean, why multi-agent matters, and how to wire one up in n8n. 2 hours.

**The pattern:** Ed teaches the build. This course teaches the vocabulary. The Phase 1-5 modules teach the FDE layer (eval-set-as-spec, cost ceiling, circuit breaker, handoff, customer simulation). The three together = the complete FDE agent skillset.

---

## Section-by-section cross-reference to Phase 1-5

The course has 9 sections, 54 lectures, 2h 11m. Here's what each section teaches + which Phase 1-5 module deepens it + which company-experience report tests it.

### Section 1: What is an AI agent? (1:31 + 3:06 + 4:18 + quiz = ~10 min)

**What this course teaches:**

- **Definition:** an AI agent is a system that perceives its environment (via sensors), makes decisions (via a model), and takes actions (via actuators) to achieve a goal.
- **Why agents matter:** LLMs are reactive (you ask, they answer); agents are proactive (they plan, act, observe, iterate).
- **The "next big thing" framing:** agents are the next abstraction layer above LLMs — they're how you turn an LLM into a system that does work, not just answers questions.

**What Phase 1-5 adds:**

- The **circuit breaker** + **rate limiter** (so the agent fails closed, not open)
- The **cost ceiling** (so the agent doesn't blow the customer's budget)
- The **handoff runbook** (so the agent survives the FDE's exit)
- The **eval-set-as-spec** (so the agent's quality is measurable)

**The Phase 1-5 module that preps it:** Phase 1 (foundations) + Phase 4 (`course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`).

**The company-experience report that tests it:** all 12 company reports. Every FDE customer simulation tests "did you build an agent?" or "did you use an agent?" at some point.

---

### Section 2: The agent loop (Environment → Sensors → Model → Decision → Actions → Updated environment)

**What this course teaches:**

- **Environment:** the external world the agent perceives and interacts with
- **Sensors:** how the agent collects data about the environment (APIs, scraping, file reads)
- **Model:** the agent's reasoning (the LLM)
- **Decision-making logic:** rules and objectives that guide the agent's actions
- **Actions:** how the agent shapes the environment (API calls, file writes, message sends)
- **Updated environment:** the loop continues — the agent observes the new state

**What Phase 1-5 adds:**

- **State externalization** (Phase 1-3): the agent's state is in Redis or a DB, not in the LLM context
- **Idempotency keys** (Phase 4 MCP): every action has an idempotency key so retries are safe
- **Audit log** (Phase 4 MCP): every action is logged with user_id, timestamp, cost, result

**The Phase 1-5 module that preps it:** Phase 1 (the agent loop) + Phase 4 (the MCP server which implements this loop with policy code in the middle).

**The company-experience report that tests it:** Anthropic FDE § 3 (the take-home is "build an agent with this loop") + Sierra AI § 2-3 (the take-home is "build + demo an agent").

---

### Section 3: Types of AI agents (5 types + LLM-based)

**What this course teaches:**

- **Simple reflex agent:** if-then rules, no memory
- **Model-based reflex agent:** has an internal model of the world, no goals
- **Goal-based agent:** has goals, plans actions to achieve them
- **Utility-based agent:** has a utility function, optimizes for it
- **Learning agent:** improves over time based on feedback
- **Modern LLM-based agent:** typically goal-based with memory, planning, and tool use

**What Phase 1-5 adds:**

- The **PacificFreight drafter** is a model-based reflex agent (no goals, just pattern matching)
- The **multi-agent dispatcher** is a goal-based agent with planning (the orchestrator plans, the sub-agents act)
- The **SLM project** is a learning agent (the fine-tuning improves over the baseline)
- The **MCP server** wraps any of these with policy code in the middle

**The Phase 1-5 module that preps it:** Phase 4 (`course/ai-fde/phase-4-capstone/`) — the 4 projects cover all 5 agent types.

**The company-experience report that tests it:** LangChain FDE § 3 (the build-an-agent take-home is a goal-based agent with memory) + Anthropic FDE § 4 (the Constitutional AI round tests whether the agent handles failure modes).

---

### Section 4: How agents learn (from humans + from external systems)

**What this course teaches:**

- **Learning from humans:** RLHF, human-in-the-loop, expert demonstrations
- **Learning from external systems:** RL from environment feedback, A/B testing, eval sets

**What Phase 1-5 adds:**

- **The eval-set-as-spec** (Phase 3): the agent learns from the eval set, not from RLHF
- **The thumbs-up/thumbs-down feedback loop** (Phase 2): every Mei edit becomes a training signal
- **The 3-loop iteration cadence** (Phase 3): every Monday, run the eval set, ship improvements

**The Phase 1-5 module that preps it:** Phase 3 (`course/ai-fde/phase-3-deployment/`) — the eval-driven iteration pattern.

**The company-experience report that tests it:** all 12 company reports. The "manufacture labels" answer in customer-simulation Q9 is exactly this: build an eval set as the first step.

---

### Section 5: LLM workflows vs agents (ReAct + ReWoo + single + multi-agent)

**What this course teaches:**

- **Distinguishing LLMs vs AI workflows vs agents:** LLMs are reactive; workflows are deterministic pipelines; agents are autonomous loops.
- **ReAct (Reason + Act):** the agent reasons about what to do, takes an action, observes the result, repeats. This is the canonical agent loop.
- **ReWoo (Reasoning Without Observation):** the agent plans all actions upfront, then executes them. Faster but less adaptive.
- **Single agent:** one LLM with a tool list. The LangChain / Sierra take-home pattern.
- **Multi-agent:** multiple LLMs coordinating. The LangGraph + Phase 4 multi-agent dispatcher pattern.

**What Phase 1-5 adds:**

- The **state object** in `agents_state.py` (Phase 4): the shared memory between agents
- The **per-agent circuit breaker**: each agent fails independently
- The **agent_path log** (Phase 4): every agent's path is logged to `usage.jsonl` for observability

**The Phase 1-5 module that preps it:** Phase 4 (`course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`) — `service/agents.py` is a ReAct-style orchestrator.

**The company-experience report that tests it:** LangChain FDE § 3 (the take-home is single-agent or multi-agent) + Anthropic FDE § 3 (the take-home can be either) + Sierra AI § 2-3 (the take-home is single-agent, the demo is single-agent).

---

### Section 6: How to implement AI agents in business (model selection + tools + prompting + guardrails + human-in-the-loop)

**What this course teaches:**

- **Select a model:** GPT-4o / Claude / Gemini / open-source — the cost-quality-latency tradeoff
- **External tools:** the agent has a tool list (API calls, file reads, message sends)
- **Configuring instructions + prompt engineering:** the system prompt defines the agent's role, constraints, and output format
- **Few-shot prompting:** show the agent 2-5 examples in the prompt
- **Chain of Thought reasoning:** ask the agent to reason step-by-step before answering
- **Guardrails:** hard constraints that the agent cannot violate (per-tool rate limits, content filters, action allowlists)
- **Human intervention:** the agent escalates to a human when it can't handle the query

**What Phase 1-5 adds:**

- The **cost ceiling** (Phase 3): the model selection decision is bounded by the cost ceiling
- The **circuit breaker + rate limiter** (Phase 2): guardrails in code, not just in prompts
- The **policy file** (Phase 4 MCP): `mcp_policies.yaml` is the guardrail manifest
- The **customer-sim escalation** (Anthropic FDE): the human-in-the-loop pattern is the highest-signal round

**The Phase 1-5 module that preps it:** Phase 1 (the agent design) + Phase 4 (the MCP server, which implements the tool list + policy file).

**The company-experience report that tests it:** Anthropic FDE § 4 (the Constitutional AI round tests whether the candidate understands guardrails) + AWS FDE § 6 (the customer scenario tests whether the candidate can scope the guardrails).

---

### Section 7: How to evaluate AI agents (the eval framework)

**What this course teaches:**

- **Functional evals:** does the agent do what it's supposed to do? Tool selection accuracy, response accuracy.
- **Safety evals:** does the agent avoid doing what it's not supposed to do? Refusal rate on bad inputs, prompt injection resistance.
- **Operational evals:** does the agent meet the SLAs? Latency P95, cost per query, uptime.

**What Phase 1-5 adds:**

- The **RAGAS 4 metrics** (Phase 2 `eval.py`): faithfulness, ansrel, context_precision, context_recall
- The **eval-set-as-spec** (Phase 3): the eval set is the contract; the agent must pass before shipping
- The **regression threshold** (Phase 3): 0.05 regression per metric is the SEV-2 bar

**The Phase 1-5 module that preps it:** Phase 2 (`course/ai-fde/phase-2-core-build/service/eval.py`) + Phase 3 (the GO/NO-GO gate).

**The company-experience report that tests it:** Anthropic FDE § 4 (the Constitutional AI round tests eval literacy) + customer-simulation Q9 ("no labelled data, no eval culture" is the exact 3-step eval setup).

---

### Section 8: Build an agent with n8n (the practical primer)

**What this course teaches:**

- **n8n introduction:** the open-source workflow automation tool (similar to Zapier, but self-hostable)
- **Node types in n8n:** trigger nodes, action nodes, logic nodes, AI nodes
- **The project we will build:** a customer-support agent that reads Gmail + writes to Google Sheets
- **Defining the agent's personality:** the system prompt (role + constraints + output format)
- **Adding the brain:** wiring the LLM as a node in the workflow
- **Implementing memory in n8n:** simple state store + lookup
- **Integrating tools:** Google Sheets + Gmail as agent actions
- **Producing the final output:** the agent's response is delivered to the user

**What Phase 1-5 adds:**

- The **PacificFreight drafter** is an n8n-equivalent workflow, but with a Python + FastAPI backend and a domain-specific tool set
- The **MCP server** is the policy-enforcing equivalent of n8n's guardrails
- The **handoff runbook** is the operational equivalent of n8n's error-handling nodes

**The Phase 1-5 module that preps it:** Phase 1 (the agent workflow) + Phase 4 (the MCP server, which is the production-grade version of the n8n demo).

**The company-experience report that tests it:** Sierra AI § 2-3 (the take-home is exactly this: build + demo an agent that integrates with Gmail + Sheets, with a policy file and a handoff runbook).

---

### Section 9: Agent implementation landscape (APIs + cloud services + data + frameworks + deployment)

**What this course teaches:**

- **APIs:** the agent calls external APIs (OpenAI, Anthropic, internal services)
- **Cloud services:** the agent runs on cloud infrastructure (AWS Lambda, GCP Cloud Functions, Modal)
- **Data and knowledge integration:** the agent pulls data from databases, warehouses, vector stores
- **Development frameworks:** LangChain, LangGraph, LlamaIndex, Semantic Kernel, AutoGen
- **Deployment:** the agent is deployed to production, not run on a laptop

**What Phase 1-5 adds:**

- The **PacificFreight service** is the deployment target (FastAPI + uvicorn + Redis + S3)
- The **4 Phase 4 projects** are the deployment artifacts (MCP server, multi-agent dispatcher, SLM server, data analyst sandbox)
- The **handoff runbook** is the deployment deliverable

**The Phase 1-5 module that preps it:** Phase 2 (the service architecture) + Phase 3 (the deployment + runbook) + Phase 4 (the 4 project deployments).

**The company-experience report that tests it:** all 12 company reports. Every FDE company tests deployment readiness as a phase-2 signal.

---

## The 5 things this course teaches that Phase 1-5 doesn't

1. **The agent vocabulary.** ReAct, ReWoo, single-agent, multi-agent, guardrails, human-in-the-loop — the terms every FDE interview will use.
2. **The n8n primer.** The 2-hour project shows a working agent end-to-end without writing Python.
3. **The 5 agent types.** Simple reflex, model-based, goal-based, utility-based, learning — a vocabulary map for every FDE design conversation.
4. **The ReAct vs ReWoo tradeoff.** When to use reactive (ReAct) vs planning-upfront (ReWoo) — the design decision every multi-agent project makes.
5. **The eval framework breakdown.** Functional + Safety + Operational — the three categories of evals every FDE eval set has.

## The 5 things Phase 1-5 adds (the FDE layer)

1. **The cost ceiling.** Every agent decision is bounded by the customer's $/month budget. The course doesn't mention cost.
2. **The circuit breaker + rate limiter.** Every external call goes through a breaker + rate limiter. The course doesn't mention protection.
3. **The eval-set-as-spec.** The eval set is the contract; the agent must pass before shipping. The course covers evals, not the contract framing.
4. **The handoff runbook.** Every agent has a runbook + an on-call rotation + a "FDE has left" test. The course doesn't mention operations.
5. **The customer simulation.** The agent's behavior under a frustrated executive is the highest-signal test. The course doesn't mention customers.

---

## The 8-week upgrade plan (this course + Ed Donner's + the FDE additions)

If you take both courses, here's the combined plan:

| Week | This course (2 hr) | Ed Donner (8 weeks) | The FDE additions |
|---|---|---|---|
| 1 | Sections 1-2: what is an agent + the agent loop | Week 1-2: brochure generator + multi-modal agent | (1) eval set, (2) cost tracker, (3) circuit breaker |
| 2 | Section 3: the 5 agent types | Week 3: meeting minutes | (1) Whisper cost model, (2) action item eval set, (3) rollback runbook |
| 3 | Section 4: how agents learn | Week 4: Python → C++ converter | (1) cost-quality-latency table, (2) recommendation engine |
| 4 | Section 5: ReAct vs ReWoo | Week 5: AI knowledge worker (RAG) | (1) hybrid retriever, (2) RAGAS eval set, (3) redaction layer |
| 5 | Section 6: how to implement | Week 6: Capstone A (frontier price prediction) | (1) eval-set-as-spec, (2) cost ceiling |
| 6 | Section 7: how to evaluate | Week 7: Capstone B (QLoRA fine-tuning) | (1) model card, (2) cost-quality-latency table |
| 7 | Section 8: build with n8n | Week 8: Capstone C (multi-agent) | (1) per-agent circuit breaker, (2) agent-path log |
| 8 | Section 9: deployment landscape | Project polish + handoff | (1) runbook, (2) on-call rotation, (3) "FDE has left" test |

**The 1-sentence takeaway:** the 2-hour primer + the 8-week deep-dive + the FDE additions = the complete FDE agent skillset.

---

## The 5 interview questions this course prepares you for (from `../README.md` + customer-simulation README)

This course + the customer-simulation module prepares you for these 5 interview questions:

1. **"What is an agent vs a workflow vs an LLM call?"** → Answer: LLMs are reactive; workflows are deterministic pipelines; agents are autonomous loops that perceive, reason, and act.
2. **"ReAct vs ReWoo — when do you use each?"** → Answer: ReAct for unknown environments (the agent observes and adapts); ReWoo for known environments (the agent plans upfront and executes). The PacificFreight multi-agent dispatcher uses ReAct because the shipments are unknown.
3. **"How do you add guardrails to an agent?"** → Answer: deterministic policy code (not prompts). The MCP server's `mcp_policies.yaml` is the guardrail manifest: which user can call which tool, with what rate limit.
4. **"How do you evaluate an agent?"** → Answer: functional (does it do what it's supposed to?), safety (does it avoid what it's not supposed to?), operational (does it meet the SLAs?). The PacificFreight eval set has all three categories.
5. **"How do you handle the customer-simulation round?"** → Answer: stay calm, scope live, push back without damaging the relationship, know when to say no. The 5 customer-simulation scenarios in `../customer-simulation/README.md` are the practice arena.

---

## The 5-question "what would the candidate do differently" recap

1. **Pair this course with Ed Donner.** This course is the 2-hour primer; Ed's course is the 8-week deep-dive. Don't take just one.
2. **Build something with n8n first.** The 2-hour project is the fastest way to internalize the agent loop. Then graduate to LangGraph.
3. **Apply the FDE layer to your agent.** Cost ceiling + circuit breaker + eval set + runbook + customer simulation. The 5 FDE additions.
4. **Practice ReAct + ReWoo out loud.** When someone asks "ReAct vs ReWoo," you should be able to answer in 60 seconds with a concrete example.
5. **Read the Phase 4 `service/agents.py`.** It's the production-grade version of the n8n demo. The hand-rolled state machine + per-agent circuit breaker + agent-path log are the FDE additions to the agent loop.

---

## The cross-reference: how this maps to Phase 6

| Section | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. What is an agent | `../generative-ai/README.md` + Phase 1 | Agent vocabulary + the "why agents matter" framing |
| 2. The agent loop | Phase 1 + Phase 4 (the MCP server) | State externalization + idempotency keys + audit log |
| 3. The 5 agent types | Phase 4 (the 4 projects cover all 5 types) | Mapping agent types to project patterns |
| 4. How agents learn | Phase 3 (eval-driven iteration) | Eval-set-as-spec + the 3-loop cadence |
| 5. ReAct vs ReWoo | Phase 4 (multi-agent dispatcher) | Orchestrator pattern + per-agent state |
| 6. How to implement | Phase 4 (MCP server + policy file) | Tool list + guardrails + human-in-the-loop |
| 7. How to evaluate | Phase 2 (eval.py) + Phase 3 (GO/NO-GO gate) | RAGAS 4 metrics + regression threshold |
| 8. Build with n8n | Phase 1 (the PacificFreight drafter) | End-to-end agent in 2 hours vs 8 weeks |
| 9. Deployment landscape | Phase 2 (service architecture) + Phase 3 (runbook) | Production deployment + handoff |

**The 1-sentence summary:** this course teaches the agent vocabulary in 2 hours. Ed Donner teaches the agent build in 8 weeks. Phase 1-5 teaches the FDE agent pattern (eval-set-as-spec, cost-ceiling-as-score, handoff-as-proof, customer-simulation-as-test). The three together = the complete FDE agent skillset.
