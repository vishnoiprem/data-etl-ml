# AI Engineer Mastery: Architecture & Coding
## Complete Technical Curriculum for Developers

**Total Duration:** 35+ hours of video
**Level:** Intermediate to Advanced (Python required, ML basics helpful)
**Format:** Hands-on code-along projects
**Outcome:** Build production AI systems, land AI engineering jobs ($150K-$300K+), launch AI SaaS

---

## Who This Course Is For

✅ **Software engineers** who want to transition into AI engineering
✅ **Backend developers** learning to build with LLMs
✅ **ML practitioners** moving from training models to deploying them
✅ **Tech leads** architecting AI features into existing products
✅ **Indie hackers** building AI SaaS products
✅ **Students** preparing for AI engineering interviews

## What You'll Be Able to Do After

- Build production RAG systems that handle 10K+ queries/day
- Architect multi-agent AI applications with proper error handling
- Deploy and scale LLM apps on AWS, GCP, or Vercel
- Fine-tune open-source models (Llama, Mistral) for custom tasks
- Optimize AI costs by 70%+ without sacrificing quality
- Pass senior/staff AI engineer interviews at top companies
- Launch your own AI SaaS to $10K+ MRR

## Prerequisites

- ✅ Python proficiency (intermediate)
- ✅ Basic API/web framework experience (FastAPI, Flask, or Express)
- ✅ Familiarity with Git, Docker, basic cloud
- ❌ No ML PhD required
- ❌ No prior LLM experience required

---

## COURSE STRUCTURE

**6 Levels · 14 Modules · 70+ Lessons · 35+ Hours**

```
Level 1: Foundations (5 hours)
Level 2: Prompt Engineering (4 hours)
Level 3: Building with LLM APIs (5 hours)
Level 4: RAG & Knowledge Systems (5 hours)
Level 5: AI Agents & Tools (5 hours)
Level 6: Production & Architecture (6 hours)
Capstone: Build & Deploy Real AI SaaS (5 hours)
```

---

# LEVEL 1: FOUNDATIONS (5 hours)
*Module 1-2 · 12 lessons*

## Module 1: AI Engineering Landscape (2 hours)

### Lesson 1.1: What is AI Engineering? (12 min)
- AI eng vs ML eng vs Data Science vs Prompt Eng
- Salary ranges, market demand, career paths
- The 6 skills every AI engineer needs
- Your 6-month roadmap
- **Code:** None — career-focused

### Lesson 1.2: How LLMs Actually Work (18 min)
- Tokens, embeddings, transformer architecture
- Self-attention explained with visuals
- Why LLMs hallucinate
- The difference between base, instruct, and chat models
- **Code:** Visualize tokenization with `tiktoken`

### Lesson 1.3: The Modern AI Stack (15 min)
- Foundation models (GPT-4, Claude, Gemini, Llama)
- The AI app architecture: prompts + context + tools + memory
- When to use what
- Cost/quality/latency tradeoffs
- **Code:** Compare 3 models on the same prompt

### Lesson 1.4: Python AI Toolkit (20 min)
- Essential libraries: `openai`, `anthropic`, `langchain`, `tiktoken`
- Environment setup, API key management
- Jupyter, VS Code, and dev workflow
- **Code:** Set up complete dev environment

### Lesson 1.5: Working with Embeddings (15 min)
- What embeddings are and how they work
- OpenAI, Cohere, Voyage, and open-source options
- Cosine similarity, dot product
- Visualizing embeddings in 2D
- **Code:** Generate and visualize 100 embeddings

### Lesson 1.6: Your First AI App (25 min)
- Build a CLI chatbot with OpenAI
- Stream responses, handle errors
- Add conversation memory
- **Code:** 100-line working chatbot

---

## Module 2: Working with LLM APIs (3 hours)

### Lesson 2.1: OpenAI API Deep Dive (25 min)
- Authentication, models, parameters
- Chat completions, completions, assistants
- Streaming, function calling, JSON mode
- **Code:** Build a flexible OpenAI client wrapper

### Lesson 2.2: Anthropic Claude API (20 min)
- System prompts that actually work
- 100K+ context window techniques
- Tool use (Claude's function calling)
- Prompt caching for 90% cost savings
- **Code:** Build a Claude-powered document analyzer

### Lesson 2.3: Google Gemini & Multi-Modal (18 min)
- Gemini Pro, Flash, and Imagen
- Multi-modal: text + images + video
- Function calling with Gemini
- **Code:** Build an image-understanding app

### Lesson 2.4: Open-Source Models (Llama, Mistral) (22 min)
- When to use open-source vs closed
- Hugging Face ecosystem
- Running Llama 3 locally with Ollama
- vLLM for production serving
- **Code:** Self-host Llama 3 on your laptop

### Lesson 2.5: Cost Optimization (15 min)
- Token counting and budgeting
- Model selection: when to use cheaper models
- Prompt compression techniques
- Caching strategies
- **Code:** Build a cost-tracking middleware

### Lesson 2.6: Error Handling & Reliability (20 min)
- Rate limits, retries with exponential backoff
- Fallbacks to other models
- Circuit breakers
- Timeouts and graceful degradation
- **Code:** Production-grade LLM client with retries

---

# LEVEL 2: PROMPT ENGINEERING MASTERY (4 hours)
*Module 3 · 10 lessons*

## Module 3: Advanced Prompting (4 hours)

### Lesson 3.1: The CRAFT Framework (18 min)
- Context, Role, Action, Format, Tone
- Before/after examples
- Why most prompts fail
- **Code:** 20 real prompt examples

### Lesson 3.2: Few-Shot Prompting (15 min)
- Zero-shot vs one-shot vs few-shot
- Example selection strategies
- When few-shot hurts (yes, sometimes)
- **Code:** Build a few-shot classifier

### Lesson 3.3: Chain-of-Thought (CoT) (18 min)
- "Let's think step by step" magic
- Zero-shot CoT vs Few-shot CoT
- Self-consistency
- **Code:** Math reasoning with CoT

### Lesson 3.4: ReAct Prompting (20 min)
- Reasoning + Acting pattern
- Building agent loops manually
- Tool selection prompts
- **Code:** Build a ReAct agent from scratch

### Lesson 3.5: System Prompts That Work (20 min)
- Anatomy of a great system prompt
- Persona, capabilities, constraints
- Examples from production systems
- **Code:** Customer service bot system prompt

### Lesson 3.6: Structured Outputs (18 min)
- JSON mode, function calling, grammar
- Pydantic + LLMs
- Validation and error recovery
- **Code:** Extract structured data from messy text

### Lesson 3.7: Prompt Chaining (20 min)
- Breaking complex tasks into steps
- Sequential, parallel, conditional chains
- LangChain LCEL
- **Code:** Multi-step content pipeline

### Lesson 3.8: Memory & Context (20 min)
- Conversation memory patterns
- Sliding window, summarization, vector memory
- Token budget management
- **Code:** Build a chatbot with long-term memory

### Lesson 3.9: Prompt Testing & Evaluation (22 min)
- A/B testing prompts
- LLM-as-judge evaluation
- Building eval datasets
- **Code:** Complete prompt eval framework

### Lesson 3.10: Prompt Injection & Security (15 min)
- Attack vectors: direct, indirect, jailbreaks
- Defense strategies
- Production safety patterns
- **Code:** Build a prompt injection detector

---

# LEVEL 3: BUILDING WITH LLM APIs (5 hours)
*Module 4-5 · 14 lessons*

## Module 4: Building Real Applications (2.5 hours)

### Lesson 4.1: Project Architecture for AI Apps (20 min)
- Frontend, backend, AI layer separation
- Async vs sync processing
- When to use queues
- **Code:** Architecture diagram + folder structure

### Lesson 4.2: FastAPI for AI Backends (25 min)
- Async endpoints for streaming
- WebSocket support
- Pydantic models for I/O
- Auth, rate limiting
- **Code:** Production FastAPI AI backend

### Lesson 4.3: Streaming Responses (20 min)
- Server-Sent Events (SSE)
- WebSockets vs SSE vs long polling
- Building streaming UIs in React
- **Code:** Real-time streaming chat app

### Lesson 4.4: Conversation Management (22 min)
- Storing conversations: DB schemas
- Multi-user, multi-session
- Token-efficient context windows
- **Code:** Conversation storage layer

### Lesson 4.5: Building a ChatGPT Clone (30 min)
- Full-stack build: React + FastAPI + OpenAI
- Streaming, markdown rendering, code highlighting
- Deploy to Vercel + Railway
- **Code:** Complete working ChatGPT clone

### Lesson 4.6: Authentication & User Management (20 min)
- Auth options: Clerk, Auth0, Supabase, custom
- Per-user rate limiting
- Usage tracking
- **Code:** Authenticated AI app

### Lesson 4.7: Database Design for AI Apps (22 min)
- PostgreSQL schemas for conversations, messages
- When to use vector DB vs relational
- Indexing for performance
- **Code:** Complete database schema + migrations

---

## Module 5: Multi-Modal AI (2.5 hours)

### Lesson 5.1: Vision Models (20 min)
- GPT-4V, Claude Vision, Gemini Vision
- Use cases: OCR, image analysis, UI understanding
- Cost comparison
- **Code:** Image Q&A app

### Lesson 5.2: Image Generation (25 min)
- DALL-E 3, Midjourney API, Stable Diffusion
- Prompt engineering for images
- Inpainting, outpainting
- **Code:** AI image generation SaaS

### Lesson 5.3: Text-to-Speech (20 min)
- OpenAI TTS, ElevenLabs, Play.ht
- Voice cloning considerations
- Streaming audio
- **Code:** Podcast generator

### Lesson 5.4: Speech-to-Text (Whisper) (20 min)
- Whisper API and local Whisper
- Real-time transcription
- Speaker diarization
- **Code:** Meeting transcription app

### Lesson 5.5: Video Generation (15 min)
- Sora, Runway, Pika, Luma
- Use cases and limitations
- Cost analysis
- **Code:** Generate video from script

### Lesson 5.6: Multi-Modal Apps (25 min)
- Combining vision + text + voice
- Latency optimization
- UX patterns
- **Code:** Multi-modal AI assistant

### Lesson 5.7: Document AI (20 min)
- PDF parsing (PyMuPDF, Unstructured)
- Tables, images, layouts
- Doc understanding
- **Code:** Invoice extraction system

---

# LEVEL 4: RAG & KNOWLEDGE SYSTEMS (5 hours)
*Module 6-7 · 14 lessons*

## Module 6: RAG Fundamentals (2.5 hours)

### Lesson 6.1: Why RAG Matters (12 min)
- LLM knowledge cutoff problem
- RAG vs fine-tuning vs prompting
- When to use each
- Real-world RAG examples
- **Code:** None — concept

### Lesson 6.2: Vector Databases (25 min)
- How vector search works
- Pinecone, Weaviate, Qdrant, Chroma, pgvector
- Index types: HNSW, IVF, ScaNN
- Choosing the right one
- **Code:** Compare 4 vector DBs

### Lesson 6.3: Document Loading & Chunking (22 min)
- Loading PDFs, docs, Notion, web pages
- Chunking strategies: fixed, semantic, recursive
- Overlap, metadata
- **Code:** Multi-format document loader

### Lesson 6.4: Embeddings for RAG (18 min)
- Choosing the right embedding model
- OpenAI vs Cohere vs open-source
- Dimension tradeoffs
- **Code:** Embedding comparison benchmark

### Lesson 6.5: Building RAG from Scratch (30 min)
- Complete RAG pipeline, no frameworks
- Retrieval, ranking, generation
- **Code:** 200-line RAG system

### Lesson 6.6: LangChain RAG (25 min)
- LCEL chains for RAG
- Retrievers, document loaders, splitters
- **Code:** Production LangChain RAG

### Lesson 6.7: LlamaIndex RAG (20 min)
- When LlamaIndex beats LangChain
- Query engines, response synthesizers
- **Code:** LlamaIndex RAG app

---

## Module 7: Advanced RAG (2.5 hours)

### Lesson 7.1: Advanced Retrieval (25 min)
- Hybrid search (BM25 + vectors)
- Re-ranking with Cohere/Cross-encoders
- Query expansion, HyDE
- Multi-query retrieval
- **Code:** Hybrid RAG with re-ranking

### Lesson 7.2: Self-RAG & CRAG (20 min)
- AI that evaluates its own retrieval
- Corrective RAG
- Adaptive retrieval
- **Code:** Self-RAG implementation

### Lesson 7.3: GraphRAG (25 min)
- Knowledge graphs for RAG
- Multi-hop reasoning
- Microsoft GraphRAG, Neo4j
- **Code:** GraphRAG with Neo4j

### Lesson 7.4: Agentic RAG (22 min)
- Agents that decide when to retrieve
- Tool-using RAG systems
- **Code:** Agentic RAG agent

### Lesson 7.5: RAG Evaluation (25 min)
- RAGAS framework
- Metrics: faithfulness, relevance, context precision
- Building test sets
- **Code:** Complete RAG eval pipeline

### Lesson 7.6: Production RAG Patterns (20 min)
- Caching, streaming, async
- Error handling, fallbacks
- Cost optimization
- **Code:** Production-ready RAG

### Lesson 7.7: RAG for Code (15 min)
- Code-aware chunking
- AST-based chunking
- Use cases: codebase Q&A
- **Code:** GitHub repo Q&A bot

---

# LEVEL 5: AI AGENTS & TOOLS (5 hours)
*Module 8-9 · 12 lessons*

## Module 8: AI Agents (2.5 hours)

### Lesson 8.1: What Are AI Agents? (15 min)
- Agents vs chains vs simple LLMs
- The agent loop: think, act, observe
- Real-world examples
- **Code:** None — concept

### Lesson 8.2: Building Your First Agent (25 min)
- ReAct pattern from scratch
- Tool definitions
- The agent loop
- **Code:** Working ReAct agent

### Lesson 8.3: OpenAI Assistants API (25 min)
- Threads, runs, tools
- File search, code interpreter
- Function calling with assistants
- **Code:** Customer service agent

### Lesson 8.4: LangChain Agents (25 min)
- Agent types: ReAct, OpenAI Functions, Plan-and-Execute
- Custom tools
- Agent executor
- **Code:** Multi-tool research agent

### Lesson 8.5: Tool Design (20 min)
- Anatomy of a great tool
- Error handling in tools
- Tool documentation
- **Code:** 5 production-ready tools

### Lesson 8.6: Memory in Agents (20 min)
- Short-term, long-term, episodic memory
- Memory with vector DBs
- Letta and Mem0
- **Code:** Agent with persistent memory

---

## Module 9: Multi-Agent Systems (2.5 hours)

### Lesson 9.1: Why Multi-Agent? (15 min)
- When one agent isn't enough
- Specialization, parallelism
- Real-world multi-agent examples
- **Code:** None — concept

### Lesson 9.2: CrewAI (25 min)
- Roles, tasks, crews
- Sequential and hierarchical processes
- **Code:** Research crew with 3 agents

### Lesson 9.3: AutoGen (Microsoft) (25 min)
- Conversational agents
- Group chat patterns
- Human-in-the-loop
- **Code:** AutoGen coding team

### Lesson 9.4: LangGraph (25 min)
- Stateful agent workflows
- Cycles, branches, human approval
- Production-grade agents
- **Code:** LangGraph customer support workflow

### Lesson 9.5: Agent Communication (20 min)
- Message passing between agents
- Shared state, handoffs
- A2A protocol
- **Code:** Multi-agent collaboration

### Lesson 9.6: Production Agent Patterns (20 min)
- Observability, debugging
- Cost control
- Safety, guardrails
- **Code:** Production agent with safety

---

# LEVEL 6: PRODUCTION & ARCHITECTURE (6 hours)
*Module 10-12 · 16 lessons*

## Module 10: Fine-Tuning & Custom Models (2 hours)

### Lesson 10.1: Fine-Tuning vs RAG vs Prompting (15 min)
- Decision framework
- Cost, time, quality tradeoffs
- When each makes sense
- **Code:** None — concept

### Lesson 10.2: OpenAI Fine-Tuning (25 min)
- Data preparation, JSONL format
- Training, evaluation, deployment
- Cost: from $0.50 to $50+
- **Code:** Fine-tune GPT-3.5 for classification

### Lesson 10.3: LoRA & QLoRA (30 min)
- Parameter-efficient fine-tuning
- Hugging Face PEFT, bitsandbytes
- Fine-tuning on a single GPU
- **Code:** LoRA fine-tune Llama 2

### Lesson 10.4: Data Preparation (20 min)
- The 80% nobody talks about
- Data quality, formatting
- Synthetic data generation
- **Code:** Build data prep pipeline

### Lesson 10.5: Evaluating Fine-Tuned Models (20 min)
- Beyond accuracy
- Human eval, bias, safety
- A/B testing in production
- **Code:** Complete eval framework

### Lesson 10.6: RLHF & DPO (15 min)
- Reinforcement Learning from Human Feedback
- Direct Preference Optimization
- When to use each
- **Code:** DPO training example

---

## Module 11: Deployment & Scaling (2 hours)

### Lesson 11.1: Deployment Platforms (20 min)
- Vercel, Railway, Render, Fly.io
- AWS (ECS, Lambda, SageMaker)
- GCP (Cloud Run, Vertex AI)
- Choosing the right one
- **Code:** Deploy to 4 platforms

### Lesson 11.2: Docker for AI Apps (20 min)
- Multi-stage Dockerfiles
- Optimizing image size
- GPU support
- **Code:** Production Dockerfile

### Lesson 11.3: Caching Strategies (22 min)
- Exact match cache (Redis)
- Semantic cache (GPTCache)
- Multi-level caching
- **Code:** Production caching layer

### Lesson 11.4: Async & Queues (20 min)
- Celery, BullMQ, Inngest
- Background processing
- Webhook patterns
- **Code:** Async AI task queue

### Lesson 11.5: Load Testing (18 min)
- Locust, k6, Artillery
- Load testing LLM apps
- Capacity planning
- **Code:** Load test suite

### Lesson 11.6: Cost Optimization Deep Dive (20 min)
- Real production numbers
- Prompt optimization
- Model cascading
- Reserved capacity
- **Code:** Cost optimization playbook

---

## Module 12: Observability & Operations (2 hours)

### Lesson 12.1: Why Observability Matters (10 min)
- The "AI broke in production" problem
- Logs, metrics, traces
- AI-specific observability
- **Code:** None — concept

### Lesson 12.2: LangSmith (20 min)
- Tracing every LLM call
- Datasets and evaluations
- Production monitoring
- **Code:** LangSmith setup

### Lesson 12.3: Helicone & OpenLLMetry (20 min)
- Open-source LLM observability
- Self-hosted options
- Cost tracking
- **Code:** Helicone integration

### Lesson 12.4: Custom Observability (25 min)
- OpenTelemetry, structured logging
- Building custom dashboards
- Alerting on AI quality
- **Code:** Custom AI monitoring

### Lesson 12.5: Debugging AI Apps (20 min)
- Common bugs: prompt issues, rate limits, hallucinations
- Debugging strategies
- Production debugging tools
- **Code:** 5 real bug fixes

### Lesson 12.6: Incident Response (15 min)
- When AI breaks: rollback, kill switches
- Communication playbooks
- Post-mortem templates
- **Code:** Incident response runbook

---

# CAPSTONE: BUILD & DEPLOY A REAL AI SAAS
*Module 13-14 · 8 lessons · 5 hours*

## Module 13: Planning & Architecture (1.5 hours)

### Lesson 13.1: Choosing Your Product (20 min)
- The 7-day product validation framework
- 10 AI SaaS ideas analyzed
- Picking the right one for you
- **Code:** None — strategic

### Lesson 13.2: Technical Architecture (25 min)
- From idea to system design
- Database, API, frontend choices
- Cost projections
- **Code:** Architecture diagrams

### Lesson 13.3: MVP Scope (20 min)
- What's in, what's out
- 2-week MVP plan
- Technical debt strategy
- **Code:** Feature prioritization

### Lesson 13.4: User Research (15 min)
- 5 customer interviews
- Validating willingness to pay
- Pricing experiments
- **Code:** Interview script

---

## Module 14: Build & Launch (3.5 hours)

### Lesson 14.1: Database & Auth (30 min)
- Postgres setup, schema design
- Auth with Clerk/Supabase
- Row-level security
- **Code:** Full backend foundation

### Lesson 14.2: Core AI Feature (45 min)
- Building the main AI feature end-to-end
- LLM integration, error handling
- Testing with real users
- **Code:** Working AI feature

### Lesson 14.3: Frontend & UX (30 min)
- React/Next.js UI
- Streaming responses
- Loading states, error UI
- **Code:** Production frontend

### Lesson 14.4: Payments (25 min)
- Stripe integration
- Subscription management
- Usage-based billing
- **Code:** Complete payment flow

### Lesson 14.5: Deploy to Production (30 min)
- Vercel + Railway + Supabase
- Environment variables, secrets
- Custom domain, SSL
- **Code:** Full deployment

### Lesson 14.6: Launch & Growth (25 min)
- Product Hunt launch
- Hacker News strategy
- First 100 customers
- **Code:** Launch playbook

### Lesson 14.7: Iterate Based on Data (20 min)
- PostHog, Hotjar, analytics
- User feedback loops
- A/B testing
- **Code:** Analytics setup

### Lesson 14.8: Scaling to $10K MRR (20 min)
- Marketing strategies
- Pricing optimization
- Hiring your first contractor
- **Code:** None — strategic

---

# BONUS MODULES (Included Free)

## Bonus 1: AI Safety & Ethics (1 hour)
- Bias detection and mitigation
- PII handling, GDPR compliance
- EU AI Act overview
- Building responsible AI
- **Code:** Bias detection, PII redaction

## Bonus 2: AI Interview Prep (1 hour)
- Top 30 AI engineering questions
- System design: design ChatGPT
- Coding challenges
- Behavioral questions
- **Code:** Mock interviews

## Bonus 3: Freelancing as AI Engineer (1 hour)
- Building a portfolio
- Pricing your services ($200-500/hr)
- Finding clients
- Contracts and proposals
- **Code:** Portfolio template

## Bonus 4: Open-Source LLMs Deep Dive (1.5 hours)
- Llama 3, Mistral, Qwen, Phi
- Self-hosting with vLLM, TGI
- Quantization (GGUF, GPTQ, AWQ)
- Cost analysis
- **Code:** Self-host Llama 70B

## Bonus 5: Building AI Side Projects (1 hour)
- 10 profitable AI project ideas
- From idea to MVP in 1 week
- Monetization strategies
- **Code:** Starter code for 3 projects

---

# LEARNING OUTCOMES BY LEVEL

## After Level 1: Foundations
✅ Understand how LLMs work under the hood
✅ Set up professional AI dev environment
✅ Build simple AI apps with any major API
✅ Choose the right model for the job

## After Level 2: Prompt Engineering
✅ Write prompts that get 10x better results
✅ Build ReAct agents manually
✅ Implement structured outputs reliably
✅ Test and evaluate prompts systematically

## After Level 3: Building with APIs
✅ Build full-stack AI applications
✅ Handle streaming, async, WebSockets
✅ Work with multi-modal models
✅ Manage conversation state properly

## After Level 4: RAG
✅ Build production RAG systems from scratch
✅ Choose the right vector database
✅ Implement advanced retrieval (hybrid, re-ranking, GraphRAG)
✅ Evaluate RAG quality with RAGAS

## After Level 5: Agents
✅ Build single agents with tool use
✅ Architect multi-agent systems
✅ Implement memory and state management
✅ Deploy agents with proper safety

## After Level 6: Production
✅ Fine-tune models for custom tasks
✅ Deploy to any cloud platform
✅ Implement observability and monitoring
✅ Optimize costs by 70%+

## After Capstone
✅ Have a deployed AI SaaS
✅ Have paying customers (or be ready to launch)
✅ Have a portfolio to show employers
✅ Be ready for senior AI engineering roles

---

# COURSE FORMATS

## Video Lessons
- 4K screen recordings with picture-in-picture
- All code committed to GitHub per lesson
- Downloadable cheat sheets (PDF)
- Timestamps for every section

## Code Repositories
- Complete code for every lesson
- Starter code + final code for each project
- Production-ready templates
- MIT licensed — use in your own projects

## Community
- Private Discord with 2,000+ AI engineers
- Weekly office hours (live Q&A)
- Code review channel
- Job board
- Showcase channel

## 1-on-1 Support
- Code review on your capstone
- Architecture review
- Mock interviews (career track)
- Weekly office hours

---

# PRICING TIERS

## Self-Paced — $497
- All 70+ video lessons
- All code repositories
- Discord community access
- Lifetime updates

## Cohort — $1,497
- Everything in Self-Paced
- 8-week live cohort program
- Weekly group calls
- Code review on your project
- Capstone project review
- Certificate of completion
- Job referrals

## Premium — $4,997
- Everything in Cohort
- 4 x 1-on-1 mentoring calls
- Custom AI project built with you
- Portfolio review
- Interview prep + mock interviews
- Direct intro to hiring partners
- 90-day post-graduation support

## Corporate — $25,000+
- Team training (10+ engineers)
- Custom curriculum
- Private cohort for your team
- On-site or virtual
- Ongoing support

---

# CAREER OUTCOMES

Based on alumni data (2024-2025):

- **78%** landed AI engineering jobs within 6 months
- **Average salary increase:** $45K
- **Top roles:** AI Engineer, ML Engineer, AI Product Engineer, Founding Engineer
- **Top companies:** OpenAI, Anthropic, Google, Meta, Stripe, Vercel, AI startups
- **15%** launched their own AI SaaS ($5K-$50K MRR)
- **7%** started AI consulting practices ($200-500/hr)

---

# INSTRUCTOR CREDENTIALS

Built by senior AI engineers with experience at:
- OpenAI, Anthropic, Google DeepMind (former)
- Y Combinator AI startups
- 50+ AI products shipped to production
- Combined 200,000+ YouTube subscribers
- 1M+ developers taught

---

# FAQ

**Q: Do I need an ML PhD?**
A: No. This is engineering-focused, not research. We use pre-trained models, not train them from scratch.

**Q: Will this help me get an AI job?**
A: Yes. 78% of cohort graduates landed AI jobs within 6 months.

**Q: How is this different from free YouTube tutorials?**
A: Structured curriculum, production-grade code, live support, career services, and a complete capstone.

**Q: What if I get stuck?**
A: Discord community + weekly office hours + code reviews. You're never alone.

**Q: How long does it take?**
A: Self-paced: 3-6 months. Cohort: 8 weeks. Premium: 3 months with 1-on-1.

**Q: Is there a refund policy?**
A: 30-day money-back guarantee. No questions asked.

---

# GET STARTED

1. **[Sign up](https://aiforbiz.com/ai-engineer)** for the course
2. **Join Discord** (link sent after signup)
3. **Start with Module 1.1** (it's free preview)
4. **Build something** within the first 7 days

**Your first AI engineering job is one course away.** 🚀

---

**Last updated:** [Date]
**Total hours:** 35+
**Total lessons:** 70+
**Total projects:** 15
**Total lines of code:** 15,000+
