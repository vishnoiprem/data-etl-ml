# Lesson 1 — The Six Words of AI Engineering

> **Type:** Article + Worked Example · Module 0
> LLM, RAG, MCP, Agent, Fine-tuning, Quantization — with a system that uses all six together.

---

## Why these six words

Every AI Engineering conversation eventually uses these terms. If you don't have crisp definitions for each, every later module is harder than it needs to be.

```
   LLM            The base model (what we're building on)
   RAG            How we give the model knowledge it didn't train on
   MCP            The standard way the model talks to tools and data
   Agent          The model + a loop + tools + memory (a system, not a chatbot)
   Fine-tuning    How we adapt the model to our specific task
   Quantization   How we make the model small enough to run cheaply
```

---

## The 1-paragraph definition of each

| Term | 1-paragraph definition |
|---|---|
| **LLM** | A Large Language Model is a neural network (usually a Transformer) trained on a huge corpus of text to predict the next token. It "knows" things only because they appeared in its training data. Out of the box, it cannot read your company's wiki, call your API, or remember yesterday's conversation. |
| **RAG** | Retrieval-Augmented Generation is the pattern of (1) finding relevant chunks from your data at query time and (2) stuffing them into the prompt before the model generates an answer. RAG is what makes an LLM useful on your private, fresh, or proprietary data. |
| **MCP** | Model Context Protocol is an open standard that defines how an AI application exposes its tools and data to a model. Think USB-C for AI tools — one protocol, many integrations. |
| **Agent** | An AI Agent is an LLM plus (1) a goal, (2) tools it can call, (3) memory of what it has done, and (4) a loop that runs until the goal is reached. The loop is the difference between "AI that answers" and "AI that does work." |
| **Fine-tuning** | Fine-tuning is the process of taking a pre-trained model and training it a little more on your own data so it becomes good at your specific task. LoRA is the popular cheap version. |
| **Quantization** | Quantization is the process of storing a model's weights at lower precision (e.g., INT4 instead of FP16) so it takes less memory and runs faster. The trade-off is a small quality loss. |

---

## How they fit together

```
   ┌────────────────────────────────────────────────────────────────┐
   │                      AI APPLICATION                             │
   │                                                                │
   │   USER QUERY                                                   │
   │       │                                                        │
   │       ▼                                                        │
   │   ┌─────────┐         ┌─────────────┐                          │
   │   │  AGENT  │ ──MCP──►│  TOOLS      │  (calendar, db, web, ...)│
   │   │  (loop) │         └─────────────┘                          │
   │   └────┬────┘                                                 │
   │        │                                                      │
   │        │ context = system prompt + memory + retrieved docs     │
   │        ▼                                                      │
   │   ┌─────────┐   retrieves via                                 │
   │   │   LLM   │ ◄──────────── RAG                               │
   │   │ (quant) │                                                  │
   │   └─────────┘                                                  │
   │        ▲                                                      │
   │        │ if base model isn't good enough                       │
   │   ┌────┴────┐                                                  │
   │   │ FINE-   │  LoRA on your data                               │
   │   │ TUNING  │                                                  │
   │   └─────────┘                                                  │
   │                                                                │
   └────────────────────────────────────────────────────────────────┘
```

A real application uses **all six**. The LLM is the brain. RAG gives it knowledge. MCP exposes tools. The agent loop decides when to use them. Fine-tuning specializes the brain. Quantization makes it cheap to run.

---

## The "do I actually need this?" decision tree

```
   Q: Is the model's general knowledge enough?
   └─► No  → you need RAG (give it your data)
   └─► Yes → next question

   Q: Does the task need specific phrasing, format, or behavior?
   └─► Yes → you need prompt engineering, maybe fine-tuning
   └─► No  → next question

   Q: Does the task need to call APIs, query DBs, or take actions?
   └─► Yes → you need an agent with tools (MCP for the protocol)
   └─► No  → next question

   Q: Is the model too slow or too expensive to run?
   └─► Yes → you need quantization, batching, or a smaller model
   └─► No  → ship it
```

---

## Worked Example — a system that uses all six

> **Goal:** Build a minimal system that touches all six concepts. Local quantized LLM, RAG over a small doc set, MCP-style tool, wrapped in an agent loop, with an optional fine-tuning step to specialize.

### The system in one block

```python
# main.py — the full system, end to end
from llama_cpp import Llama                      # 6. Quantized local LLM
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Load quantized model (INT4, 4GB → fits on a laptop)
llm = Llama(model_path="models/llama-3-8b-instruct.Q4_K_M.gguf",
            n_ctx=4096, n_threads=8, n_gpu_layers=20)

# 2. RAG: embed a tiny doc set
embedder = SentenceTransformer("all-MiniLM-L6-v2")
docs = ["Refund policy: 30 days, no questions asked.",
        "Hours: Mon-Fri 9am-5pm PT.",
        "Shipping: 3-5 business days, free over $50."]
doc_embs = np.array(embedder.encode(docs))

def rag_retrieve(query: str, k: int = 2) -> list[str]:
    q_emb = embedder.encode([query])[0]
    sims = doc_embs @ q_emb / (np.linalg.norm(doc_embs, axis=1) * np.linalg.norm(q_emb))
    return [docs[i] for i in np.argsort(-sims)[:k]]

# 3. MCP-style tool: callable by the agent, validated
TOOLS = {
    "lookup_order": lambda order_id: {"id": order_id, "status": "shipped", "eta": "2026-09-30"},
    "create_ticket": lambda title, body: {"ticket_id": "T-1042", "title": title},
}

# 4. Agent loop: LLM + RAG + tool, decides what to do
def run_agent(user_query: str) -> str:
    # RAG: retrieve relevant docs
    context = "\n".join(rag_retrieve(user_query))

    # Tool calling: let the model pick a tool (simplified)
    tool_prompt = f"""Available tools:
- lookup_order(order_id): get order status
- create_ticket(title, body): open a support ticket

If you need a tool, reply: TOOL: <tool_name>(<args>)
Otherwise, answer using the context.

Context: {context}
User: {user_query}
"""
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": tool_prompt}],
        max_tokens=256,
    )["choices"][0]["message"]["content"]

    if response.startswith("TOOL:"):
        # Parse and execute
        tool_name = response.split("(")[0].replace("TOOL:", "").strip()
        args_str = response.split("(", 1)[1].rstrip(")")
        # Naive arg parsing for the demo
        if tool_name == "lookup_order":
            order_id = args_str.strip().strip("'\"")
            result = TOOLS["lookup_order"](order_id)
            return f"Your order {order_id} is {result['status']}, ETA {result['eta']}."
        elif tool_name == "create_ticket":
            return "I've opened a ticket for you."

    return response

# 5. Fine-tuning step (separate): LoRA on your own Q&A
# from peft import LoraConfig, get_peft_model
# lora_config = LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"])
# model = get_peft_model(base_model, lora_config)
# ... train on your Q&A dataset ...

# Run it
print(run_agent("Where is my order #1234?"))
# -> Your order #1234 is shipped, ETA 2026-09-30.
```

Each numbered block in the code maps to one of the six words.

### What each component buys you

| Component | What it gives you | Cost |
|---|---|---|
| Quantized local LLM | No API fees, no data leaving your machine | 1–3% quality loss |
| RAG | Knowledge of your docs, freshness | Embedding compute, retrieval infra |
| MCP-style tools | The model can act, not just chat | Tool maintenance, security review |
| Agent loop | Multi-step reasoning, self-correction | Latency, loop-budget risk |
| Fine-tuning (LoRA) | Domain expertise, format control | Training compute, eval set |
| Quantization | Cheaper, faster inference | Slight quality loss |

### What this example demonstrates

1. **All six words compose.** A real system uses them together, not in isolation.
2. **The architecture is small.** ~50 lines shows the whole stack.
3. **The decisions are sequential.** Start with the LLM + RAG + agent. Add fine-tuning only if those aren't enough. Quantize last.
4. **Each word is replaceable.** Swap the local LLM for an API. Swap the in-process retriever for a vector DB. The shape stays the same.

This is the mental model for every later module. Read it once and you have the vocabulary. Read it twice and you have the architecture.

---

## What Comes Next

> Module 1 — **Machine Learning Foundations** — what a model is, how it learns, the math behind it.
