# AI Engineering Portfolio — The Amazon Way

A production-minded portfolio of 8 GenAI/ML projects built around AWS best practices and the *Working Backwards* philosophy. Each project starts from a customer problem, defines measurable success criteria, and lands on a scalable, cost-aware architecture.

## Projects

| # | Project | Core Capability | Primary AWS Services |
|---|---------|-----------------|----------------------|
| 1 | [Enterprise RAG Platform](./01-enterprise-rag-platform) | RAG, vector DBs, hybrid retrieval, reranking | Bedrock, OpenSearch, S3, Lambda |
| 2 | [LLM Fine-Tuning Pipeline](./02-llm-fine-tuning) | LoRA/QLoRA, instruction tuning, RLHF | SageMaker Training, Bedrock |
| 3 | [Multi-Agent Platform](./03-multi-agent-platform) | Agentic workflows, tool use, memory | Bedrock AgentCore, Lambda, DynamoDB |
| 4 | [FM Evaluation Framework](./04-fm-evaluation) | Quality regression, drift detection | Bedrock Evaluations, SageMaker Pipelines |
| 5 | [Distributed Inference](./05-distributed-inference) | Cost-optimized serving, model routing | SageMaker Inference, Bedrock |
| 6 | [Regulated-Industry Architecture](./06-regulated-industry) | Private-network AI, audit, guardrails | VPC, KMS, Bedrock Guardrails |
| 7 | [Prompt Engineering Platform](./07-prompt-engineering) | Versioning, A/B testing, templates | Bedrock Prompt Management, DynamoDB |
| 8 | [LLMOps Platform](./08-llmops-platform) | End-to-end MLOps for GenAI | SageMaker Pipelines, EventBridge |

## Repository Philosophy

Following Amazon's tenets:

1. **Customer Obsession** — every project README starts with the customer problem and the press release / FAQ that would justify the work.
2. **Ownership** — each project is independently runnable; no hidden cross-dependencies.
3. **Dive Deep** — the code is real, not pseudocode. Sample data is included so you can run it locally.
4. **Frugality** — every project runs locally with open-source equivalents (FAISS, sentence-transformers, Llama via Ollama) before scaling to AWS managed services.
5. **Bias for Action** — `make demo` runs an end-to-end demo in every project.

## Quick Start

```bash
# One-time setup
make setup

# Run the flagship demo (Project 1)
cd 01-enterprise-rag-platform
make demo

# Or run any project's demo
cd 0X-project-name
make demo
```

## Local-First Architecture

Every project supports two modes:

- **`LOCAL` mode** — runs entirely on your laptop with open-source models. No AWS account needed. Good for development and demos.
- **`AWS` mode** — swaps in Bedrock / SageMaker / OpenSearch via thin adapter classes. Same business logic, different backends.

This is controlled by an environment variable:

```bash
export AI_ENGINEERING_MODE=LOCAL   # or AWS
```

## Prerequisites

- Python 3.11+
- Docker (optional, for running OpenSearch locally)
- AWS CLI configured (only for AWS mode)

## Layout Conventions

```
0X-project-name/
├── README.md                 # Theory, architecture, design decisions
├── ARCHITECTURE.md           # Diagrams and AWS service choices
├── requirements.txt
├── Makefile
├── .env.example
├── src/                      # All source code
├── tests/                    # Pytest tests
├── sample_data/              # Synthetic data to run demos
├── scripts/                  # CLI entry points
└── infrastructure/           # CDK/Terraform (where applicable)
```

## Working Backwards Templates

Each project includes a one-page **Working Backwards** doc (PR/FAQ style):
- The press release for the launched feature
- The customer FAQ (5–7 questions)
- Internal FAQ on architecture / cost / risk

This is the artifact you'd review with a Bar Raiser before any code is written.
