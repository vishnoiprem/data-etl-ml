# AI Engineering Course — Complete Notes

> Source: [Outcome School — AI Engineering Course](https://outcomeschool.com/ai-engineering-course)
> Author: Amit Shekhar | 18 modules · 146+ lessons
> Audience: Engineers moving into AI Engineering · ML engineers going deep on LLMs · Interview prep

---

## Course Promise

> "Understand how AI models work from the inside — Transformer math, attention, fine-tuning, RAG, agents, inference, evaluation, safety, system design — and how to build real production systems on top of them."

This is the **comprehensive AI Engineering curriculum**, structured to take you from ML foundations to architecting a complete AI system end to end.

---

## Module Map

| # | Module | Lessons | Theme |
|---|--------|--------:|-------|
| 0 | [Must Know](./00-must-know/) | 1 | The six words: LLM, RAG, MCP, Agent, Fine-tuning, Quantization |
| 1 | [ML Foundations](./01-ml-foundations/) | 9 | Supervised/unsupervised, regression, precision/recall, regularization, RL, contrastive |
| 2 | [Deep Learning](./02-deep-learning/) | 10 | Gradient descent, backprop, cross-entropy, dropout, normalization, RNN, PyTorch |
| 3 | [Transformer Architecture](./03-transformer-architecture/) | 15 | BPE, embeddings, self-attention, Q/K/V, RoPE, FFN |
| 4 | [How LLMs Generate Text](./04-how-llms-generate-text/) | 4 | Temperature, top-k/p, streaming, lost in the middle |
| 5 | [Modern LLM Architecture](./05-modern-llm-architecture/) | 7 | MoE, GQA, sliding window, attention sinks, Flash Attention, DeepSeek-V4 |
| 6 | [Types of Language Models](./06-types-of-language-models/) | 5 | SLMs, LRMs, RLMs, DLMs, System One |
| 7 | [Training, Fine-Tuning & Alignment](./07-training-finetuning-alignment/) | 11 | LoRA, prefix tuning, distillation, continual learning, RLHF, PPO, DPO, GRPO |
| 8 | [Prompt & Context Engineering](./08-prompt-and-context-engineering/) | 5 | CoT, chaining, caching, context engineering, compaction |
| 9 | [Vector Search & RAG](./09-vector-search-and-rag/) | 13 | ANN, semantic/hybrid search, rerankers, ColBERT, chunking, HyDE, Agentic/Graph/Vectorless RAG |
| 10 | [AI Agents & Agentic Systems](./10-ai-agents-and-agentic-systems/) | 16 | Function calling, agent loop, ReAct, Plan-and-Execute, Reflection, MCP, SubAgents, orchestration |
| 11 | [Agentic Engineering](./11-agentic-engineering/) | 8 | Harness/Loop/Graph engineering, LangChain, LangGraph, Claude Code, Cursor |
| 12 | [LLM Inference Engineering](./12-llm-inference-engineering/) | 17 | KV cache, paged attention, continuous batching, speculative decoding, Medusa, EAGLE, GGUF, vLLM, SGLang, TensorRT-LLM |
| 13 | [Evaluation & Observability](./13-evaluation-and-observability/) | 4 | LLM eval, LLM-as-judge, agent eval, agent observability |
| 14 | [AI Safety & Security](./14-ai-safety-and-security/) | 3 | Guardrails, prompt injection, watermarking |
| 15 | [Multimodal AI](./15-multimodal-ai/) | 6 | ViT, image embeddings, diffusion, GANs, VAEs |
| 16 | [AI Infrastructure & System Design](./16-ai-infrastructure-deployment/) | 10 | GPU/TPU/LPU, cloud vs on-device, LLM routing, real-time voice AI agent, system design |
| 17 | [Frontier Ideas](./17-frontier-ideas/) | 3 | JEPA, world models, recursive self-improvement |
| 18 | [AI Engineering Interviews](./18-ai-engineering-interviews/) | 1 | Question bank + answers |

**Total: 146+ lessons · 18 modules · End-to-end AI engineering curriculum**

---

## How to Use These Notes

Each module folder follows the convention used across the other tracks:

```
NN-module-name/
├── README.md                  # Module overview + lesson index
├── 01-lead-lesson.md          # Article-style notes (lead lesson includes a worked example)
├── 02-...
└── ...
```

Each lead lesson ends with a **Worked Example** section — a code-first build that demonstrates the concepts at production scale. Examples include the math, the eval harness, the failure modes, and the cost numbers, not just the happy path.

---

## The Learning Path (in order)

```
   MODULES 0-2: Foundations
   ─────────────────────────────────────
   Must Know → ML Foundations → Deep Learning
   "What is a model? How does it learn? How does a network actually train?"

   MODULES 3-6: Inside the LLM
   ─────────────────────────────────────
   Transformer → Generation → Modern Architecture → Types of Models
   "How does a Transformer work? What is attention? What is MoE? What kinds of LMs exist?"

   MODULES 7-8: Adapting LLMs
   ─────────────────────────────────────
   Fine-tuning & Alignment → Prompt & Context Engineering
   "How do we adapt a pre-trained model to our task? How do we talk to it well?"

   MODULES 9-11: Building with LLMs
   ─────────────────────────────────────
   RAG → Agents → Agentic Engineering
   "How do we give the LLM knowledge? Tools? A loop? A graph?"

   MODULES 12-13: Running LLMs
   ─────────────────────────────────────
   Inference Engineering → Evaluation & Observability
   "How do we make it fast and cheap? How do we know it's working?"

   MODULES 14-17: Production & Frontier
   ─────────────────────────────────────
   Safety → Multimodal → Infrastructure → Frontier
   "How do we keep it safe? How does it see? How do we deploy it? What's next?"

   MODULE 18: Interview Prep
   ─────────────────────────────────────
   Question bank + structured answers
```

---

## Cross-Cutting Themes

These show up in every module:

1. **Math first, intuition second.** Each concept is built from the math up with worked numeric examples.
2. **Production-grade depth.** Every lead lesson's worked example is principal-engineer-level: real code, real eval, real cost.
3. **Eval is the moat.** Evaluation appears in every module where it applies.
4. **Cost is a feature.** Cost numbers appear in every architectural lesson.
5. **The failure modes are the spec.** Each worked example names the failure modes it defends against.

---

## Prerequisites

- Basic programming (Python preferred)
- High-school math (linear algebra, calculus, probability explained inside lessons)
- Curiosity

---

## After This Course

The natural next steps:

- **Production deployment** (`01-enterprise-rag-platform/`, `08-llmops-platform/`)
- **Fine-tuning deep dive** (`02-llm-fine-tuning/`)
- **Multi-agent orchestration** (`03-multi-agent-platform/`)
- **Inference at scale** (`05-distributed-inference/`)
- **Regulated AI** (`06-regulated-industry/`)

This course is the **theoretical + applied foundation**. The other tracks are the **production build-out**.
