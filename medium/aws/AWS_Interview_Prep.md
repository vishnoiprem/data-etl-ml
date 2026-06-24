# AWS Senior AI Architect SSA — Interview Prep
**Prem Vishnoi** | vishnoiprem@gmail.com | Prepared: June 2026

---

## Quick Reference — JD Match

| JD Requirement | Your Proof Point | Strength |
|---------------|------------------|----------|
| 7+ yrs distributed systems | Lazada (Alibaba) 5.5 yrs + Makro + SCB + DBS | ✅ Strong |
| 5+ yrs enterprise customer-facing | C-level advisory at Makro ($8B), Lazada (SEA's largest e-com) | ✅ Strong |
| 5+ yrs production AI systems | Makro RAG/ML, Lazada logistics ML, SCB AML | ✅ Strong |
| LLM fine-tuning LoRA/QLoRA/RLHF | Product content generation at Makro | ✅ |
| RAG + vector DBs + semantic search | Makro product search (OpenSearch), customer support | ✅ Strong |
| Agentic workflows | Multi-step agent architectures at Makro | ✅ |
| AWS Bedrock + SageMaker + AgentCore | Current daily stack at Makro | ✅ Strong |
| Secure private-network AI | VPC + PrivateLink + IAM at Makro; MAS compliance at SCB | ✅ Strong |
| Whitepapers / reference architectures | Medium author, internal reference archs at Makro/Lazada | ✅ |
| Regulated environments | SCB AML (15 countries, MAS), DBS Bank | ✅ Strong |
| Team leadership | 30-person org, 8→30 build-out | ✅ Strong |
| Cloud certification | AWS Solutions Architect Associate (Dec 2023) | ✅ |
| Master's degree | MS Data Science, Northwestern (in progress, 2025–2027) | ✅ |

---

## Round 1: HR Screen (15 Minutes)

### Tell Me About Yourself (2 min — always lead with this)

> "I'm Prem — a Senior AI Architect with 15 years building enterprise data and AI platforms. I currently lead AI strategy for Makro, an $8B omnichannel retail business in Southeast Asia, owning a 30-person engineering org and a $3M budget. My focus is taking GenAI, LLM, and Agentic AI from whiteboard to production — RAG pipelines, vector search, demand forecasting at scale, agentic automation.
>
> Before Makro I spent 5.5 years at Lazada, Alibaba's e-commerce platform, earning two promotions to VP of Data Engineering. And before that I built ML and data platforms for Standard Chartered Bank's AML compliance across 15 countries.
>
> What draws me to this AWS SSA role is that I've been doing exactly this work — converting AI ambition into delivered systems — but for one business at a time. At AWS I can do it across hundreds of customers and actually shape the product roadmap from the field."

---

### Why AWS? Why This Role? (2 min)

> "AWS is where serious enterprise AI gets built. Bedrock, SageMaker, AgentCore — these are the tools I architect with daily. The SSA role specifically appeals to me because it combines what I do best: deep technical architecture plus customer advisory and thought leadership. The JD talks about being a trusted advisor, capturing roadmap feedback, writing whitepapers, running workshops. I already do all of that — just internally. At AWS I can do it at scale and across industries."

---

### What Is Your Biggest Strength for This Role? (2 min)

> "Translating AI ambition into delivered, production systems. Most architects can design on a whiteboard. My track record is production — RAG at scale for product search and customer support, ML models serving 1,000+ vendors for demand forecasting, a data platform processing 10B+ rows daily. The AWS JD is explicitly looking for someone who converts AI vision into programs that can be delivered, operated, and scaled. That's my daily job."

---

### Salary / Availability

- Market rate for AWS SSA (SEA/Singapore): **SGD 200–280K OTE**
- Availability: Standard notice period, open to discuss
- Work authorisation: Vietnam TRC holder, 8+ years Singapore experience

---

### Questions to Ask HR

1. "What does the first 90 days look like — more internal ramp-up or early customer engagement?"
2. "How does the SSA team structure in SEA — which verticals or countries does this role cover?"

---

### Key Phrases to Use (JD Language)

| Say This | Why It Matters |
|----------|---------------|
| *"converting AI ambition into production"* | Exact JD language |
| *"trusted advisor"* | JD's framing for SSA relationship |
| *"voice of the customer"* | JD explicitly uses this |
| *"reference architectures"* | JD asks for content creation |
| *"$8B business, 30-person org, $3M budget"* | Establishes scale credibility instantly |

---

## Round 2: Technical Deep-Dive (60–90 Minutes)

### Architecture Design 1: Enterprise RAG System

**Likely prompt:** *"A large bank wants employees to query 10 years of policy documents using natural language. Design it on AWS."*

**Architecture:**

```
Documents (S3)
    → Textract (OCR/extraction)
    → Glue (chunking, metadata tagging)
    → Bedrock Titan Embeddings (embedding generation)
    → OpenSearch Serverless (k-NN vector index)
                  ↓
User Query → Bedrock Knowledge Bases (hybrid retrieval: BM25 + vector)
                  ↓
           Bedrock (Claude 3) → Response with citations
                  ↓
        Bedrock Guardrails (PII redaction, topic denial)
                  ↓
        CloudWatch + Bedrock Traces (audit, monitoring)

Auth: Cognito → API Gateway → Lambda → Bedrock (all within VPC via PrivateLink)
```

**Key decisions to justify:**

| Decision | Reasoning |
|----------|-----------|
| OpenSearch over Kendra | Hybrid BM25+vector search, lower cost at scale, native Bedrock KB integration |
| OpenSearch over Pinecone | No third-party dependency — critical for regulated environments |
| Bedrock Knowledge Bases over custom retrieval | Managed chunking, embedding refresh, built-in hybrid search |
| PrivateLink for all services | Data never traverses public internet — MAS/PDPA compliance |
| Bedrock Guardrails | PII redaction + hallucination mitigation + topic denial in one layer |

**Your story:** "I built this exact pattern at Makro for product search and customer support — vector search on OpenSearch, LLMs via Bedrock, private network via VPC endpoints."

---

### Architecture Design 2: Production MLOps Pipeline

**Likely prompt:** *"How would you set up a production ML pipeline for demand forecasting on AWS?"*

```
Raw Data: S3 (Parquet, Delta) + Glue Catalog
    ↓
Feature Engineering: SageMaker Processing Jobs → SageMaker Feature Store
    ↓
Training: SageMaker Pipelines (triggered by EventBridge on schedule or data drift)
         └── Spot Instances (70% cost saving for training)
    ↓
Tracking: MLflow on SageMaker / SageMaker Experiments → Model Registry
    ↓
Approval Gate: Manual/auto approval in Model Registry
    ↓
Deploy: SageMaker Real-Time Endpoint (p/m-series) with autoscaling
     OR SageMaker Batch Transform (for nightly batch scoring)
    ↓
Monitor: SageMaker Model Monitor (data drift, model quality)
         SageMaker Clarify (bias detection)
         CloudWatch (latency, error rate, invocations)
    ↓
CI/CD: CodePipeline → CodeBuild → SageMaker Pipelines SDK
```

**Your story:** "At Makro I deployed demand forecasting for 1,000+ vendors using this exact pattern. Before that at Lazada I built real-time ML inference for logistics ETA serving 100M+ daily events."

---

### Architecture Design 3: Agentic Customer Service System

**Likely prompt:** *"Design an AI agent that can look up orders, process refunds, and escalate to humans."*

```
User → API Gateway → Lambda (session mgmt)
              ↓
       Bedrock Agent (orchestrator)
              ↓
    ┌─────────┼──────────────┐
    ↓         ↓              ↓
Action:    Action:        Action:
Order      Refund         Ticket
Lookup     Processing     Creation
(DynamoDB) (Internal API) (Zendesk API)
              ↓
       Knowledge Base (Bedrock KB)
       └── Product FAQs, Return Policy, SLA docs
              ↓
       Bedrock Guardrails
       └── Block PII in responses
       └── Cap refund amounts
       └── Escalation triggers
              ↓
       Human-in-loop: SNS → SQS → Agent Handoff
              ↓
       Audit: Bedrock Agent Traces → CloudWatch → S3
```

**Key points:** Bedrock Agents handles multi-step reasoning and tool selection natively. Action Groups = Lambda functions. Knowledge Base for context grounding. Guardrails prevent runaway refunds or PII leaks.

---

### Architecture Design 4: Secure Private-Network AI (Regulated Industry)

**Likely prompt:** *"How do you architect AI for a bank — they have strict data sovereignty requirements?"*

**Four security layers:**

1. **Network isolation**
   - VPC with private subnets for all compute
   - VPC Endpoints (PrivateLink) for Bedrock, SageMaker, S3, KMS — no public internet
   - Security Groups + NACLs for least-privilege network access

2. **Identity & access**
   - IAM execution roles per workload (not shared)
   - SCPs at OU level to prevent service-level bypasses
   - Attribute-Based Access Control (ABAC) for data classification tags

3. **Data governance**
   - Amazon Macie for PII detection in training data
   - KMS CMK encryption for model artifacts, S3, SageMaker volumes
   - Lake Formation column-level security on feature data
   - S3 Object Lock for audit immutability

4. **Audit & compliance**
   - CloudTrail for all Bedrock/SageMaker API calls
   - SageMaker Model Cards for model documentation and governance
   - Config Rules for continuous compliance checking

**Your story:** "I implemented this architecture at Standard Chartered Bank for AML compliance pipelines across 15 countries, ensuring MAS regulatory compliance in Singapore."

---

## Deep Technical Questions

### LLM Fine-Tuning Decision Framework

**Q: When do you fine-tune vs. RAG vs. prompt engineering?**

| Approach | Use When | Cost |
|----------|----------|------|
| Prompt engineering | Model already knows your domain; need format/tone control | Near zero |
| RAG | Model needs access to private/current data; factual grounding | Low-medium |
| Fine-tuning (LoRA/QLoRA) | Need behavioral change; domain-specific reasoning; consistent output style | Medium-high |
| Full fine-tuning | Fundamental capability change; rare | Very high |

> "My default: start with prompting, add RAG, fine-tune only when the first two fail. LoRA/QLoRA gives 90% of fine-tuning benefit at 10% compute cost. On SageMaker I use ml.g5.12xlarge for QLoRA with PEFT + Hugging Face Trainer. At Makro I fine-tuned for product description generation — RAG wasn't enough because we needed consistent Thai/English bilingual output format."

---

### Vector Database Selection

**Q: OpenSearch vs. Pinecone vs. pgvector — when do you use what?**

| Option | Use When | Avoid When |
|--------|----------|------------|
| **OpenSearch Serverless** | AWS-native, Bedrock KB integration needed, hybrid BM25+vector | Very high query volume (cost scales) |
| **pgvector (Aurora/RDS)** | Team on RDS already, simple use case, low cardinality | High-scale production, complex filtering |
| **Pinecone** | Managed scale-out, metadata filtering at scale | Regulated environments (third-party data egress) |
| **FAISS (in-memory)** | Prototyping, offline batch similarity | Production serving |

> "In regulated environments I default to OpenSearch — no third-party dependency, data stays in my VPC, native Bedrock integration. At Makro that was the call for product search."

---

### Bedrock vs. SageMaker — When to Use Which

| Need | Use |
|------|-----|
| Call foundation models (Claude, Titan, Llama) | Bedrock |
| Build RAG with managed KB | Bedrock Knowledge Bases |
| Build agents with tool use | Bedrock Agents |
| Fine-tune your own model | SageMaker Training |
| Deploy custom model endpoint | SageMaker Endpoint |
| Run ML pipelines / MLOps | SageMaker Pipelines |
| Monitor production models | SageMaker Model Monitor |
| Both: use FM + custom model together | Bedrock for inference, SageMaker for custom training/serving |

---

### Distributed Inference for Large Models

**Q: How do you deploy a 70B parameter model in production?**

> "Three options on AWS: SageMaker with tensor parallelism across multiple GPUs (ml.p4d.24xlarge = 8x A100s), using LMI (Large Model Inference) container with DeepSpeed or vLLM. For lower latency at higher throughput I'd look at AWS Inferentia2 (Inf2) — purpose-built for inference, 4x better price/performance than GPU for serving. For very large models (175B+) I'd use FSDP or Megatron-LM for tensor+pipeline parallelism. Key metrics to tune: batch size, sequence length, KV-cache management."

---

### FM Evaluation

**Q: How do you evaluate an LLM in production?**

> "Two layers: offline evaluation before deployment and online monitoring after. Offline: RAGAS for RAG (faithfulness, answer relevancy, context recall), task-specific evals (BLEU/ROUGE for generation, accuracy for classification). Online: SageMaker Model Monitor for input/output distribution drift, custom CloudWatch metrics for hallucination rate (using an LLM-as-judge pattern), latency P50/P99, token usage cost. I set up automated eval pipelines in SageMaker Pipelines that gate promotion from staging to production."

---

## STAR Stories for Behavioral Questions

### "Tell me about influencing a senior decision-maker."
- **S:** Makro CTO wanted to purchase a $2M vendor AI platform
- **T:** I believed we could build equivalent capability in-house with better data control
- **A:** Built a working RAG prototype in 2 weeks on Bedrock + OpenSearch, benchmarked vs. vendor on latency, accuracy, and TCO. Presented to CTO with data
- **R:** CTO cancelled vendor contract. Saved $2M, retained data sovereignty, now own the platform roadmap

### "Tell me about a complex technical challenge."
- **S:** Lazada logistics: needed ML-powered ETA predictions, but legacy batch pipeline was 6 hours stale
- **T:** Build real-time ML inference for 100M daily logistics events with <200ms latency
- **A:** Re-architected on Kafka → Flink → ClickHouse for real-time feature serving. SageMaker real-time endpoint behind API Gateway with autoscaling. Rewrote feature pipeline from Hive to Flink
- **R:** 20M+ daily ML-driven insights, delivery SLA improved 30%, zero downtime migration

### "Tell me about building something that helped others (content / enablement)."
- **S:** Teams across Makro had no standard for GenAI architecture — everyone building differently
- **T:** Create reusable reference architectures to accelerate adoption
- **A:** Wrote internal whitepapers on RAG patterns, Agentic AI design, secure AI on AWS. Ran 5 deep-dive workshops for 30+ engineers. Published on Medium for external audience
- **R:** Consistent architecture patterns across 4 domain squads, faster onboarding, referenced by AWS partner team as a customer reference

### "Tell me about delivering in a highly regulated environment."
- **S:** Standard Chartered Bank: AML compliance pipelines had to process data across 15 countries, each with different regulatory requirements
- **T:** Build a unified platform that met MAS Singapore requirements and could be parameterised per-country
- **A:** Designed Hadoop-based pipeline with country-level data partitioning, built Lucid Search for high-risk entity screening using semantic matching, implemented full audit trail for regulators
- **R:** MAS compliant across all entities, compliance speed improved significantly, reused across 15 markets

---

## Questions to Ask the Technical Panel

1. "What's the biggest gap you see AWS customers struggle with when going from Bedrock prototype to production at scale?"
2. "How does the SSA team feed customer signal back into Bedrock and SageMaker roadmap — is there a formal loop with the product teams?"
3. "What does a strong 6-month mark look like for someone in this role — how is SSA success measured?"
4. "How is the SEA SSA team structured — vertical specialisation (FSI, retail) or geographic?"

---

## Things NOT to Say

| Avoid | Replace With |
|-------|-------------|
| "I've worked with OpenAI / ChatGPT" | Always anchor to AWS services |
| Going deep on Databricks | Mention as data foundation, pivot to AWS AI on top |
| "I'm still learning Bedrock" | "I use Bedrock in production at Makro daily" |
| Long explanations without business outcome | Always end with: cost saved / latency reduced / revenue impact |
| "I think..." on AWS service capabilities | Know the specifics — Bedrock regions, Inf2 specs, SageMaker quotas |

---

## AWS Service Cheat Sheet (Memorise These)

| Service | What It Does | Your Usage |
|---------|-------------|------------|
| **Bedrock** | Managed FM inference (Claude, Titan, Llama, Mistral) | Daily at Makro |
| **Bedrock Knowledge Bases** | Managed RAG with vector store | Product search, customer support |
| **Bedrock Agents** | Agentic orchestration with tool use | Multi-step automation at Makro |
| **Bedrock Guardrails** | Content filtering, PII redaction, hallucination mitigation | Production safety layer |
| **AgentCore** | Framework for building/deploying production agents | Newer — know the pitch |
| **SageMaker Pipelines** | ML workflow orchestration | Demand forecasting pipeline |
| **SageMaker Feature Store** | Centralised feature management (online + offline) | Cross-model feature sharing |
| **SageMaker Model Monitor** | Production drift/quality monitoring | Model governance at Makro |
| **SageMaker Clarify** | Bias detection + explainability | Regulatory compliance use cases |
| **OpenSearch Serverless** | Vector DB + BM25 hybrid search | Product search at Makro |
| **Inferentia2 (Inf2)** | Purpose-built inference chip (4x better price/perf vs GPU) | Know for cost discussions |
| **Trainium (Trn1)** | Purpose-built training chip | Know for fine-tuning cost discussions |
| **Amazon Q** | Enterprise AI assistant (Business + Developer editions) | Know the positioning |
| **Bedrock Studio** | Low-code GenAI app builder | Know for non-technical customers |

---

## Certification Status

| Cert | Status |
|------|--------|
| AWS Solutions Architect – Associate | ✅ Dec 2023 |
| AWS ML Specialty | 🎯 Target before final round |
| MS Data Science, Northwestern | 🔄 In progress (Sep 2025 – Jan 2027) |

---

*File location: `/Users/prem/PycharmProjects/data-etl-ml/medium/aws/AWS_Interview_Prep.md`*
*Last updated: June 2026*
