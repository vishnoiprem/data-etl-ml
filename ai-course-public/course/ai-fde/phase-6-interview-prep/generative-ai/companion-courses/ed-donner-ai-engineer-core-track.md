# Ed Donner — AI Engineer Core Track (the 8-week companion course)

> **Source:** Ed Donner's "AI Engineer Core Track: LLM Engineering, RAG, QLoRA, Agents" — 33.5 hours, 210 lectures, 8 sections. **This is the most-cited LLM engineering course on Udemy** and the cleanest "build the same artifacts an FDE would build" curriculum on the market. **If you complete Ed's 8 projects, you have an FDE-grade portfolio** — but you need to know which Ed project maps to which Phase 1-5 module so you can connect his lessons to the FDE pattern (eval-set-as-spec, cost-ceiling-as-score, handoff-as-proof, state-externalization-as-precondition).
>
> **The thesis:** Ed teaches LLM engineering (the technical craft). Phase 1-5 teach FDE (the customer + production + handoff discipline). The two are complementary: Ed's projects are the *what*; Phase 1-5 is the *why* + the *how to ship it to a customer*.

---

## 1. Why this course is the right companion

The 8 projects Ed teaches map 1:1 to the FDE skill set. Here's the high-level mapping:

| Ed project | What you build | The FDE skill it proves | The Phase 1-5 module it deepens |
|---|---|---|---|
| **1. Brochure generator** | Scrapes a company website + LLM-summarizes into a brochure | Chained LLM calls + streaming + JSON prompts | Phase 1 (foundations) + Phase 2 (the drafter) |
| **2. Multi-modal customer support agent** | Airline AI assistant with tool calling + Gradio UI | Function-calling + multi-modal (DALL-E 3 + TTS) | Phase 1 (function-calling) + Phase 4 (MCP server) |
| **3. Meeting minutes generator** | Whisper transcription + LLM summary (open + closed) | Audio → text → structured output, model selection | Phase 2 (the drafter, but for audio) + Phase 4 (eval set) |
| **4. Python → C++ converter** | AI-generated C++ from Python, 60,000× speedup | Frontier model selection for code generation | Phase 2 (model selection) + Phase 3 (cost ceiling) |
| **5. AI knowledge worker (RAG)** | RAG-based Q&A over a company knowledge base | Full RAG pipeline (chunks + embeddings + retriever + LLM) | Phase 2 (retrieval_v2) + Phase 3 (eval-driven iteration) |
| **6. Capstone A: Price prediction (frontier)** | Frontier model predicts Amazon product prices | Eval-set-as-spec + frontier model selection | Phase 3 (eval.py + the GO/NO-GO gate) |
| **7. Capstone B: QLoRA fine-tune (LLaMA 3.2)** | Fine-tuned LLaMA 3.2 3B beats frontier on price prediction | LoRA / QLoRA training + cost-quality tradeoff | Phase 4 (SLM project) |
| **8. Capstone C: Autonomous multi-agent** | Multi-agent system spots deals, notifies via Pushover | Agentic AI + structured outputs + planning | Phase 4 (multi-agent project) |

**The pattern:** Ed's 8 weeks are a *linear* journey from "calling an LLM" to "deploying an autonomous agent." Phase 1-5 is a *lateral* journey that takes the same artifacts and asks: "how do you ship it to a customer? how do you measure it? how do you hand it off?" The two together = the complete FDE.

---

## 2. The 8 projects in detail (with FDE framing)

### Project 1: AI-powered brochure generator (Week 5 in Ed's curriculum)

**What Ed teaches:** Chained GPT calls + JSON prompts + streaming. The candidate builds a sales-brochure generator that scrapes a company website, summarizes the company's products/customers, and outputs a Markdown brochure. The chain is: (1) scrape links, (2) summarize each linked page, (3) aggregate into a final brochure, (4) stream the output.

**The FDE reframe:** the brochure generator is a **single-purpose LLM call** with a **deterministic input pipeline** (scrape → summarize). It's the same architecture as the Phase 2 PacificFreight drafter, but with a different input source.

**What Ed covers that Phase 1-5 doesn't:**
- The exact `OpenAI` Python client API (`.chat.completions.create`, `stream=True`, `response_format={"type": "json_object"}`)
- The `Gradio` UI framework (we use FastAPI, but Gradio is faster for prototypes)
- The `ollama` + `OpenAI`-compatible endpoint pattern for local models

**What Phase 1-5 covers that Ed doesn't:**
- The eval-set-as-spec pattern (the brochure generator has no eval set; the FDE version would have one)
- The cost ceiling (no tracking of tokens / cost)
- The circuit breaker + rate limiter (no protection against API outages)
- The handoff (no runbook, no on-call rotation, no ownership transfer)

**The Phase 6 module that preps it:** `../generative-ai/README.md` § LLM fundamentals (the API basics) + Phase 1 (`course/ai-fde/phase-1-foundations/`) for the FDE framing.

**The 1-sentence takeaway:** Build Ed's brochure generator, then add (1) an eval set of 20 company websites with ground-truth brochures, (2) a cost tracker, (3) a circuit breaker. The result is an FDE-grade artifact.

---

### Project 2: Multi-modal customer support agent (Week 6-7 in Ed's curriculum)

**What Ed teaches:** Function-calling + multi-modal (DALL-E 3 + text-to-speech) + a Gradio chat UI. The candidate builds an airline AI assistant that can: (1) look up flight status via tool calling, (2) generate a customer-facing response, (3) optionally generate an image or audio for the response. The "tool" is a SQLite database with flight data.

**The FDE reframe:** the airline agent is a **tool-using LLM** — exactly the pattern of the Phase 4 MCP drafter. The difference: Ed uses a single LLM with a single tool; the FDE version uses an MCP server with multiple tools + a policy file + a per-tool rate limit.

**What Ed covers that Phase 1-5 doesn't:**
- The exact `tool_choice="auto"` pattern for OpenAI function calling
- The Gradio `ChatInterface` component for streaming chat
- DALL-E 3 + TTS integration patterns
- The SQLite-as-tool-state pattern (we use Redis)

**What Phase 1-5 covers that Ed doesn't:**
- The MCP server architecture (4 tools, policy file, per-tool rate limit)
- The multi-agent orchestration (Ed's agent is single-purpose; FDE is multi-audience)
- The production deployment story (no Docker, no FastAPI, no telemetry)

**The Phase 6 module that preps it:** `../generative-ai/README.md` § RAG patterns (the airline agent is a hybrid: retrieval + tool use) + Phase 4 (`course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/`) for the MCP server.

**The 1-sentence takeaway:** Build Ed's airline agent, then add (1) an MCP server with 4 tools, (2) a policy file with per-user permissions, (3) a per-tool rate limit. The result is a Phase 4-grade artifact.

---

### Project 3: Meeting minutes generator (Week 3 in Ed's curriculum)

**What Ed teaches:** Audio → text (Whisper) → structured output (LLM). The candidate builds a tool that takes a meeting audio file, transcribes it with Whisper, and uses an LLM (open + closed) to extract: (1) meeting summary, (2) action items, (3) attendees. The "open vs closed" comparison is explicit: Whisper + LLaMA 3.2 vs Whisper + GPT-4o-mini.

**The FDE reframe:** the meeting minutes tool is a **multi-modal pipeline** with a **model selection decision**. The FDE version would track: (1) transcription cost, (2) summary cost, (3) quality on a held-out set of 10 meetings, (4) latency P95.

**What Ed covers that Phase 1-5 doesn't:**
- The Whisper API + local Whisper (via HuggingFace)
- The `llama-3.2` chat template + `apply_chat_template` for open-source models
- The `Gradio` audio input component
- The structured output with `response_format={"type": "json_object"}` + a Pydantic schema

**What Phase 1-5 covers that Ed doesn't:**
- The eval-set-as-spec for the action item extraction (no ground-truth set)
- The cost ceiling (no token tracking)
- The handoff (no runbook, no scheduling integration)

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Model selection (the open vs closed comparison) + Phase 4 (`course/ai-fde/phase-4-capstone/projects/03-distilled-slm/`) for the SLM framing.

**The 1-sentence takeaway:** Build Ed's meeting minutes tool, then add (1) an eval set of 10 meetings with hand-labeled action items, (2) a cost tracker (Whisper + LLM), (3) a runbook for "what to do when the transcription is wrong." The result is a Phase 4-grade artifact.

---

### Project 4: Python → C++ converter (Week 4 in Ed's curriculum)

**What Ed teaches:** Frontier model selection for code generation. The candidate builds a tool that takes a Python function, asks 4 frontier models (GPT-5, Claude, Gemini, Grok) to convert it to C++, and benchmarks the performance. The headline result: a 60,000× speedup on a well-chosen example. The deep lesson: **model selection is a measurable engineering decision, not a vibes-based one.**

**The FDE reframe:** the converter is a **model selection exercise** with a **measurable cost-quality-latency tradeoff**. The FDE version would track: (1) per-model cost per conversion, (2) per-model correctness (passes the test cases?), (3) per-model latency, (4) per-model speedup factor.

**What Ed covers that Phase 1-5 doesn't:**
- The 4 frontier model APIs (OpenAI, Anthropic, Google, xAI)
- The `OpenRouter` unified API for multi-model comparison
- The benchmark harness pattern (run the same prompt across 4 models, compare outputs)
- The Rust port as a stretch goal

**What Phase 1-5 covers that Ed doesn't:**
- The eval-set-as-spec (no test cases for correctness)
- The cost ceiling (no per-model cost tracking)
- The production deployment (no FastAPI, no Docker)
- The customer-facing framing (the customer doesn't care about 60,000×; they care about "does it work in production?")

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Model selection + Phase 2 (`course/ai-fde/phase-2-core-build/`) for the cost-ceiling framing.

**The 1-sentence takeaway:** Build Ed's converter, then add (1) a test suite of 20 Python functions with expected C++ outputs, (2) a cost-quality-latency table per model, (3) a recommendation engine ("for code generation, use X because Y"). The result is a model-selection case study.

---

### Project 5: AI knowledge worker (RAG) (Week 5-6 in Ed's curriculum)

**What Ed teaches:** Full RAG pipeline. The candidate builds a knowledge worker that answers questions about a company (Ed uses a real company as the test case). The pipeline: (1) chunk the company documents, (2) embed the chunks, (3) store in Chroma (vector DB), (4) retrieve top-k chunks for a question, (5) generate an answer with the LLM. Ed covers: (1) LangChain vs no-LangChain, (2) chunking strategies, (3) embedding model comparison, (4) re-ranking, (5) query rewriting, (6) GraphRAG.

**The FDE reframe:** the knowledge worker is **the same architecture as the PacificFreight drafter**. The difference: Ed uses LangChain; we use a hand-rolled retriever. Ed uses Chroma; we use a hybrid BM25+dense+RRF. Ed uses OpenAI embeddings; we use a local encoder. The Phase 2 `retrieval_v2.py` is the production-grade version of Ed's prototype.

**What Ed covers that Phase 1-5 doesn't:**
- The `LangChain` framework (we deliberately avoid it to teach the underlying patterns)
- The `Chroma` vector DB (we use a hand-rolled hybrid retriever)
- The `t-SNE` visualization of embeddings
- The advanced RAG techniques (query rewriting, query expansion, re-ranking, GraphRAG)
- The MRR / nDCG eval metrics

**What Phase 1-5 covers that Ed doesn't:**
- The hybrid retrieval pattern (BM25 + dense + RRF)
- The eval-set-as-spec with RAGAS metrics (faithfulness, ansrel, context_precision, context_recall)
- The circuit breaker + rate limiter on the retrieval pipeline
- The redaction layer (PII protection before embedding)
- The handoff + runbook

**The Phase 6 module that preps it:** `../generative-ai/README.md` § RAG patterns (the 4 metrics + the eval-driven iteration) + Phase 2 (`course/ai-fde/phase-2-core-build/service/retrieval_v2.py`) for the production-grade version.

**The 1-sentence takeaway:** Build Ed's knowledge worker, then compare it to the Phase 2 `retrieval_v2.py`. The differences (LangChain vs hand-rolled, Chroma vs hybrid, OpenAI vs local) are the same tradeoffs a real FDE makes between "ship fast with a framework" and "ship slow with control."

---

### Project 6: Capstone Part A — Price prediction with frontier models (Week 1-4 in Ed's capstone)

**What Ed teaches:** Eval-set-as-spec + frontier model selection. The candidate builds a price-prediction system for Amazon products. The pipeline: (1) curate a training set of 800K Amazon products (price + description + category), (2) build baseline models (Random Pricer, Linear Regression, Random Forest, XGBoost), (3) test frontier models (GPT-4o-mini, Claude, Gemini, Grok) on a held-out set, (4) report the error metric (e.g., MAE). The lesson: **frontier models are a baseline, not the answer.**

**The FDE reframe:** the price prediction system is **a regression problem dressed as an LLM problem**. The FDE version would track: (1) per-model MAE on the held-out set, (2) per-model cost (tokens × $/token), (3) per-model latency, (4) per-model error distribution (where does it fail?).

**What Ed covers that Phase 1-5 doesn't:**
- The Groq batch API (22K requests for < $1)
- The `Hugging Face` dataset curation workflow
- The weighted sampling with NumPy
- The baseline-first approach (always beat Random Pricer before trying frontier)
- The "frontier model can be worse than traditional ML" lesson

**What Phase 1-5 covers that Ed doesn't:**
- The full eval harness (the 4 RAGAS metrics, the iteration report)
- The cost ceiling as a hard constraint
- The circuit breaker + rate limiter
- The handoff + runbook
- The "FDE has left" test

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Model selection (the cost-quality-latency tradeoff) + Phase 3 (`course/ai-fde/phase-3-deployment/`) for the eval-driven iteration framing.

**The 1-sentence takeaway:** Build Ed's price prediction system, then add (1) a cost-quality-latency table per model, (2) an error distribution analysis ("where does the model fail?"), (3) a recommendation engine. The result is a model-selection case study that an FDE can take to a customer.

---

### Project 7: Capstone Part B — QLoRA fine-tuning (Week 1-4 in Ed's fine-tuning week)

**What Ed teaches:** LoRA / QLoRA fine-tuning of an open-source model. The candidate fine-tunes LLaMA 3.2 3B on the price prediction task and shows that the fine-tuned model **beats GPT-4o-mini** on the held-out set. The pipeline: (1) prepare the dataset (round prices, tokenize, batch), (2) set up QLoRA (4-bit quantization + LoRA adapters), (3) train on Google Colab A100, (4) monitor with Weights & Biases, (5) evaluate on the held-out set. The headline result: a 3B-parameter open-source model outperforms a much larger frontier model.

**The FDE reframe:** the fine-tuning project is **the Phase 4 SLM project, done end-to-end**. The FDE version would track: (1) training cost (GPU-hours × $/hour), (2) inference cost (per-query), (3) quality on the held-out set, (4) latency P95, (5) the cost-quality-latency tradeoff vs the frontier model.

**What Ed covers that Phase 1-5 doesn't:**
- The exact QLoRA setup (`bitsandbytes`, `peft`, `trl`, `transformers`)
- The `Weights & Biases` monitoring workflow
- The cross-entropy loss calculation
- The "fine-tuning can make a model worse" lesson (when the dataset is too small)
- The "fine-tuned open-source beats frontier" win

**What Phase 1-5 covers that Ed doesn't:**
- The cost ceiling as a hard constraint (we set a target $/month budget)
- The eval-set-as-spec with a regression threshold
- The ollama serving pattern
- The model card
- The handoff + runbook

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Fine-tuning + Phase 4 (`course/ai-fde/phase-4-capstone/projects/03-distilled-slm/`) for the SLM framing.

**The 1-sentence takeaway:** Build Ed's fine-tuning project, then add (1) a cost-quality-latency table (frontier vs fine-tuned), (2) a model card, (3) an ollama serving layer. The result is a Phase 4-grade SLM artifact that an FDE can take to a CFO.

---

### Project 8: Capstone Part C — Autonomous multi-agent (Week 1-5 in Ed's agent week)

**What Ed teaches:** Autonomous multi-agent system. The candidate builds a deal-scanner that: (1) scans a product feed, (2) routes each product to a specialist agent (price predictor, sentiment analyzer, opportunity detector), (3) aggregates the agent outputs, (4) sends a Pushover notification when a deal is detected. The pipeline uses: (1) Modal for serverless deployment, (2) Pydantic for structured outputs, (3) LangChain's tool-calling for the agents, (4) a planner agent that orchestrates the others.

**The FDE reframe:** the multi-agent system is **the Phase 4 multi-agent project, with a different domain**. The FDE version would have: (1) a per-agent circuit breaker, (2) an agent-path log in `usage.jsonl`, (3) a cost ceiling per agent, (4) a handoff runbook.

**What Ed covers that Phase 1-5 doesn't:**
- The `Modal` serverless deployment platform
- The `Pydantic` structured outputs (we use a hand-rolled schema)
- The Pushover notification integration
- The 34-call multi-model orchestration (GPT-5 + Claude + Open Source)

**What Phase 1-5 covers that Ed doesn't:**
- The per-agent circuit breaker + rate limiter
- The agent-path observability
- The cost ceiling per agent
- The MCP server integration (the agents are the MCP clients)
- The handoff + runbook

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Agents (the planner + specialist pattern) + Phase 4 (`course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`) for the multi-agent framing.

**The 1-sentence takeaway:** Build Ed's multi-agent system, then add (1) a per-agent circuit breaker, (2) a cost ceiling per agent, (3) an agent-path log. The result is a Phase 4-grade multi-agent artifact that an FDE can ship to a customer.

---

## 3. The 5 cross-cutting skills Ed teaches that map to FDE

### Skill 1: Model selection (the cost-quality-latency tradeoff)

**Ed's version:** test 4 frontier models + 4 open-source models on the same prompt, compare cost + quality + latency. The lesson: **model selection is a measurable engineering decision.**

**The FDE version:** the same test, but with (1) a customer-specific eval set, (2) a cost ceiling as a hard constraint, (3) a recommendation engine that outputs "use model X because Y."

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Model selection + Phase 2 (`course/ai-fde/phase-2-core-build/`) for the cost-ceiling framing.

### Skill 2: RAG (the retrieval + generation pipeline)

**Ed's version:** LangChain + Chroma + OpenAI embeddings. The lesson: **RAG is the default architecture for knowledge workers.**

**The FDE version:** the same pipeline, but with (1) a hand-rolled hybrid retriever (BM25 + dense + RRF), (2) an eval set with RAGAS metrics, (3) a redaction layer, (4) a circuit breaker on the retrieval pipeline.

**The Phase 6 module that preps it:** `../generative-ai/README.md` § RAG patterns + Phase 2 (`course/ai-fde/phase-2-core-build/service/retrieval_v2.py`) for the production-grade version.

### Skill 3: Fine-tuning (the cost-quality tradeoff)

**Ed's version:** QLoRA on LLaMA 3.2 3B, beats GPT-4o-mini on price prediction. The lesson: **fine-tuned open-source can beat frontier at lower cost.**

**The FDE version:** the same result, but with (1) a cost ceiling as a hard constraint, (2) a model card, (3) an ollama serving layer, (4) a handoff runbook.

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Fine-tuning + Phase 4 (`course/ai-fde/phase-4-capstone/projects/03-distilled-slm/`) for the SLM framing.

### Skill 4: Agentic AI (the multi-agent orchestration)

**Ed's version:** planner agent + specialist agents, tool calling, structured outputs. The lesson: **agents can collaborate to solve complex tasks.**

**The FDE version:** the same architecture, but with (1) a per-agent circuit breaker, (2) a cost ceiling per agent, (3) an agent-path log, (4) a handoff runbook.

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Agents + Phase 4 (`course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/`) for the multi-agent framing.

### Skill 5: Deployment (the production-readiness layer)

**Ed's version:** Modal serverless deployment. The lesson: **agents can run in the cloud, not just on a laptop.**

**The FDE version:** the same deployment, but with (1) FastAPI (not just Modal), (2) Docker + Kubernetes, (3) Prometheus telemetry, (4) a circuit breaker + rate limiter, (5) a runbook + on-call rotation.

**The Phase 6 module that preps it:** `../generative-ai/README.md` § Deployment + Phase 3 (`course/ai-fde/phase-3-deployment/`) for the production-readiness framing.

---

## 4. The 5 things Ed doesn't teach (the FDE gaps)

The FDE gaps in Ed's curriculum are the 5 things Phase 1-5 adds:

1. **The eval-set-as-spec.** Ed has eval sets, but they're not the spec — they're a check. The FDE pattern is: write the eval set first, then build the system to pass it. The eval set is the contract.
2. **The cost ceiling.** Ed tracks cost, but not as a hard constraint. The FDE pattern is: set a $/month target, treat exceeding it as a SEV-1 incident. The cost ceiling is a customer-facing commitment.
3. **The circuit breaker + rate limiter.** Ed's systems are unprotected. The FDE pattern is: every external call goes through a circuit breaker + rate limiter. The system fails closed, not open.
4. **The handoff + runbook.** Ed ships code, not operations. The FDE pattern is: every system has a runbook + an on-call rotation + a "FDE has left" test. The system survives the FDE's exit.
5. **The customer simulation.** Ed doesn't test for customer-facing skills. The FDE pattern is: the customer simulation is the highest-signal round at AWS FDE, Anthropic, Sierra AI. The candidate who can't stay calm with a frustrated executive fails.

**The 1-sentence takeaway:** Ed teaches LLM engineering. Phase 1-5 teaches FDE. The two together = the complete FDE.

---

## 5. The 8-week FDE upgrade plan (Ed's projects + the FDE additions)

Here's how to upgrade each of Ed's 8 projects to FDE-grade:

| Week | Ed project | The FDE additions (3 per project) |
|---|---|---|
| 1 | Brochure generator | (1) Eval set of 20 company websites with ground-truth brochures, (2) cost tracker (tokens × $/token), (3) circuit breaker on the OpenAI call |
| 2 | Multi-modal customer support agent | (1) MCP server with 4 tools, (2) policy file with per-user permissions, (3) per-tool rate limit |
| 3 | Meeting minutes generator | (1) Eval set of 10 meetings with hand-labeled action items, (2) cost tracker (Whisper + LLM), (3) runbook for "what to do when the transcription is wrong" |
| 4 | Python → C++ converter | (1) Test suite of 20 Python functions with expected C++ outputs, (2) cost-quality-latency table per model, (3) recommendation engine |
| 5 | AI knowledge worker (RAG) | (1) Hand-rolled hybrid retriever (BM25 + dense + RRF), (2) RAGAS eval set, (3) redaction layer for PII |
| 6 | Capstone A: Price prediction (frontier) | (1) Cost-quality-latency table per model, (2) error distribution analysis, (3) recommendation engine |
| 7 | Capstone B: QLoRA fine-tuning | (1) Cost-quality-latency table (frontier vs fine-tuned), (2) model card, (3) ollama serving layer |
| 8 | Capstone C: Multi-agent | (1) Per-agent circuit breaker, (2) cost ceiling per agent, (3) agent-path log in `usage.jsonl` |

**The 1-sentence takeaway:** the 8-week FDE upgrade is 24 additions (3 per project). Each addition is the FDE layer Ed omits.

---

## 6. The 5 interview questions Ed's projects prepare you for

Ed's 8 projects prepare you for these 5 GenAI interview questions (from `../generative-ai/README.md`):

1. **"What's the difference between RAG, fine-tuning, and agentic workflows? When do you use each?"**
   - Answer: RAG for knowledge-heavy tasks with fresh data; fine-tuning for style/format-specific tasks with stable data; agents for multi-step tasks with tool use. The PacificFreight drafter uses RAG (knowledge-heavy) + the multi-agent dispatcher uses agents (multi-step). The fine-tuning project (Phase 4 SLM) is for cost ceiling scalability.
2. **"How do you evaluate a RAG system?"**
   - Answer: 4 RAGAS metrics (faithfulness, ansrel, context_precision, context_recall). The PacificFreight drafter's threshold is 0.05 regression per metric. Ed's MRR / nDCG metrics are an alternative, but RAGAS is the FDE standard.
3. **"How do you choose between frontier and open-source models?"**
   - Answer: cost-quality-latency tradeoff. The Phase 4 SLM (Qwen-1.5B fine-tuned) hits 91% of GPT-4o-mini's quality at 0.5% of the cost. The recommendation engine output: "use frontier for first-time demos, use open-source for production cost ceilings."
4. **"How do you fine-tune an LLM? When does it fail?"**
   - Answer: LoRA / QLoRA on a labeled dataset. It fails when: (1) the dataset is too small (< 1000 examples), (2) the eval set doesn't match the deployment distribution, (3) the cost ceiling isn't set upfront. Ed's "fine-tuning can make a model worse" lesson is the FDE version of this.
5. **"How do you deploy an LLM to production?"**
   - Answer: ollama (local) or vLLM (GPU) for serving; FastAPI for the API; Docker + Kubernetes for orchestration; Prometheus for telemetry; circuit breaker + rate limiter for protection; runbook + on-call for operations. The 5-question "FDE has left" test is the handoff check.

**The 1-sentence takeaway:** Ed's 8 projects prepare you for the 5 GenAI interview questions. Phase 1-5 prepares you for the 5 FDE-specific additions.

---

## 7. The 5 resources to complement Ed's course

If you're taking Ed's course, here are the 5 Phase 6 resources to read alongside it:

1. **`../generative-ai/README.md`** — the canonical GenAI interview format. Read this before Week 1 to know what the interviews will test.
2. **`../company-experiences/anthropic-fde-customer-simulation.md`** — Anthropic's customer simulation is the highest-signal round. Practice the 5 customer-simulation scenarios alongside Ed's projects.
3. **`../company-experiences/aws-fde-customer-simulation.md`** — AWS FDE's 6-round loop. The customer scenario is round 6. Practice the 3 customer-scenario patterns alongside Ed's projects.
4. **`../company-experiences/sierra-ai-agent-engineer.md`** — Sierra's take-home demo walkthrough. The "interviewers run your code before the demo" pattern is exactly Ed's Week 8 capstone.
5. **`../decomposition/README.md`** — the 4-step framework (Clarify → Decompose → Design → Tradeoffs). Apply this to every Ed project as if it were a customer requirement.

**The 1-sentence takeaway:** Ed's 8 projects + the 5 Phase 6 resources = the complete FDE interview prep.

---

## 8. The 3 alternative companion courses (if Ed's not your style)

If Ed Donner doesn't fit your style, here are 3 alternatives:

1. **Andrej Karpathy's "Zero to Hero" + "Let's build GPT"** — the deepest technical foundation. Best for candidates who want to understand transformer architecture from scratch.
2. **DeepLearning.AI's "AI Agents in LangGraph"** — the canonical multi-agent course. Best for candidates targeting LangChain / Sierra AI / Anthropic.
3. **Chip Huyen's "AI Engineering" book** — the most comprehensive book on AI engineering. Best for candidates who want a single reference, not a video course.

**The 1-sentence takeaway:** Ed is the most balanced (8 projects, 8 weeks, all the FDE patterns). Karpathy is the deepest. DeepLearning.AI is the most agent-focused. Chip Huyen is the most comprehensive.

---

## 9. The cross-reference: how this maps to Phase 6

| Ed project | Phase 6 module | The FDE skill it proves |
|---|---|---|
| 1. Brochure generator | `../generative-ai/README.md` § LLM fundamentals + Phase 1 (foundations) | Chained LLM calls + JSON prompts + streaming |
| 2. Multi-modal customer support agent | `../generative-ai/README.md` § Function calling + Phase 4 (MCP drafter) | Tool-using LLM + multi-modal (DALL-E 3 + TTS) |
| 3. Meeting minutes generator | `../generative-ai/README.md` § Model selection + Phase 4 (SLM) | Audio → text → structured output, open vs closed |
| 4. Python → C++ converter | `../generative-ai/README.md` § Model selection + Phase 2 (cost ceiling) | Frontier model selection for code generation |
| 5. AI knowledge worker (RAG) | `../generative-ai/README.md` § RAG patterns + Phase 2 (retrieval_v2) | Full RAG pipeline (chunks + embeddings + retriever + LLM) |
| 6. Capstone A: Price prediction (frontier) | `../generative-ai/README.md` § Model selection + Phase 3 (eval) | Eval-set-as-spec + frontier model selection |
| 7. Capstone B: QLoRA fine-tuning | `../generative-ai/README.md` § Fine-tuning + Phase 4 (SLM) | LoRA / QLoRA training + cost-quality tradeoff |
| 8. Capstone C: Autonomous multi-agent | `../generative-ai/README.md` § Agents + Phase 4 (multi-agent) | Agentic AI + structured outputs + planning |

**The 1-sentence summary:** Ed's 8 projects are the *what* of FDE work; Phase 1-5 is the *why* and *how to ship it to a customer*. The two together = the complete FDE.
