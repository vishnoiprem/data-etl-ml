# Amazon Bedrock — hands-on course (text, image, embed, RAG, agents)

> **A complete working reference for Amazon Bedrock in
> Python and TypeScript.** The companion repo to a Udemy
> course on Bedrock. Every API surface (text, image,
> embedding, RAG, LangChain integration) is wired up and
> runnable, with both `boto3` and the AWS JS SDK.

The course covers the four things you actually do with
Bedrock: **generate text** (Claude / Titan / Llama),
**generate images** (Stable Diffusion / Titan Image
Generator), **embed text** (Titan Embeddings), and **RAG**
(retrieval-augmented generation over a PDF). The TypeScript
track mirrors the Python track so you can pick whichever
runtime matches your stack.

---

## What's in this directory

| Path | What it is |
|------|------------|
| `Amazon_Bedrock_Apple_Style.pptx` | The lecture deck (Apple-style slides, ~80 slides) |
| `artilce.md` | The course outline (11 sections, ~60 min total runtime) |
| `py/` | **Python reference code** — `src/services/{text,image,rag}`, `src/langchain/`, `src/embed/`, `src/intro/` |
| `ts/` | **TypeScript reference code** — same surface area as `py/`, written against the AWS JS SDK v3 |
| `imageApi/{py,ts}/` | Minimal image-generation clients (no framework) |
| `textApi/{py,ts}/` | Minimal text-generation clients (no framework) |
| `recap/{py-starter,ts-strarter}/` | The "recap" project the course ends on — a small starter that combines all four APIs |
| `py/requirements.txt` | Python deps: `boto3`, `langchain`, `langchain-aws`, `pypdf` |

The shape is **two parallel tracks** (Python + TypeScript)
covering the same four APIs. Pick the track that matches
your stack; the other is a reference.

---

## The course outline (11 sections, ~60 min)

| # | Section | Time | What you build |
|---|---------|------|----------------|
| 1 | How to take this course | 2 min | Orientation |
| 2 | Udemy tips | 4 min | How to use the Q&A + the lab workflow |
| 3 | Tools setup | 2 min | AWS account, IAM user, `aws configure` |
| 4 | Section intro | 1 min | What Bedrock is and what it isn't |
| 5 | What is Amazon Bedrock? | 4 min | Foundation models, model IDs, pricing |
| 6 | Hands on: Bedrock console overview | 9 min | Playground walkthrough |
| 7 | AWS configure — CLI access | 9 min | `aws configure` + IAM policy |
| 8 | Bedrock API — Boto3 (Python) | 8 min | `boto3.client("bedrock-runtime")` |
| 9 | Bedrock API — JS SDK (TypeScript) | 9 min | `@aws-sdk/client-bedrock-runtime` |
| 10 | Optional: VSCode debug | 7 min | `launch.json` for breakpoints |
| 11 | Course source code | 1 min | This repo |

The "Hands on" section (6) is the most useful — it
de-mystifies the Bedrock console, model access (you have
to *request access* to Claude / Stable Diffusion before
you can call them), and the playground's parameter
controls.

---

## The four APIs you'll write

### 1. Text generation (`py/src/services/text/`)

```python
import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
body = json.dumps({
    "prompt": "\n\nHuman: Write a haiku about Python.\n\nAssistant:",
    "max_tokens_to_sample": 100,
    "temperature": 0.7,
    "top_p": 0.9,
})
resp = client.invoke_model(
    body=body,
    modelId="anthropic.claude-v2",
    accept="application/json",
    contentType="application/json",
)
print(json.loads(resp["body"].read())["completion"])
```

The Anthropic models use the `\n\nHuman: ... \n\nAssistant:`
prompt format. The Claude 3 family uses the
`messages=[{"role": "user", "content": "..."}]` format
instead — both are in the repo, both are tested.

### 2. Image generation (`py/src/services/image/`)

Stable Diffusion XL and Titan Image Generator. The pattern
is the same: build a request body, call `invoke_model`,
decode the base64 PNG bytes, save to disk. The repo has
both.

### 3. Embeddings (`py/src/embed/`)

`amazon.titan-embed-text-v1` (1536-dim) and
`cohere.embed-english-v3` (1024-dim). Output goes to a
vector store (OpenSearch Serverless in the RAG example).

### 4. RAG over a PDF (`py/src/services/rag/` + `py/src/langchain/pdf_rag.py`)

The two halves of the course's RAG chapter:

- **`langchain/pdf_rag.py`** — the LangChain version
  (`AmazonKnowledgeBaseRetriever` + `ChatBedrock`).
  ~30 lines.
- **`services/rag/`** — the hand-rolled version
  (PyPDFLoader → chunk → embed → similarity search →
  context-augmented prompt). ~100 lines, no LangChain.

Both are tested against a sample PDF in `py/assets/`.

---

## How to run the Python track

```bash
cd py
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up auth (DO NOT hardcode keys)
aws configure
# or use an IAM role if running on EC2 / Lambda

# Text
python src/services/text/text_bedrock.py

# Image
python src/services/image/image_stable_diffusion.py
# -> writes output.png

# RAG (the showpiece)
python src/services/rag/rag_pdf.py \
    --pdf assets/sample.pdf \
    --query "What is the main argument of the paper?"
```

The TypeScript track uses the same AWS credentials; the
entry point is `ts/src/services/text/text_bedrock.ts`.

---

## What this is NOT

- **Not a Bedrock Agents tutorial.** Agents (action groups,
  knowledge bases, orchestration) are a separate API
  surface that this course doesn't cover. For agents, see
  [`../../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/).
- **Not a fine-tuning course.** Bedrock fine-tuning
  (continued pre-training, custom models) is out of scope.
- **Not a production deployment guide.** This is the
  *API surface* reference. For production-grade
  invocation (retries, cost controls, batch inference,
  provisioned throughput), see
  [`../../../ai-engineering/20-cog-style-inference-api/`](../../ai-engineering/20-cog-style-inference-api/).
- **Not a substitute for the AWS docs.** The course is
  the *first 60 minutes*. The
  [Bedrock docs](https://docs.aws.amazon.com/bedrock/)
  are the long-form reference and the source of truth for
  new model IDs and pricing.

---

## Related directories

- [`../4-AI-Agents-MCP/`](../4-AI-Agents-MCP/) — the
  course's sibling: agents + MCP (the protocol layer that
  sits on top of model calls).
- [`../8-swe-agent-devin-style/`](../8-swe-agent-devin-style/) —
  the Bedrock-Agents-style SWE agent build (action groups,
  tool use, planning).
- [`../../../ai-engineering/20-cog-style-inference-api/`](../../ai-engineering/20-cog-style-inference-api/) —
  the production inference API patterns (rate limiting,
  batching, streaming).
- [`../../../ai-engineering/01-enterprise-rag-platform/`](../../ai-engineering/01-enterprise-rag-platform/) —
  the RAG layer that the `pdf_rag.py` example is a
  stripped-down version of.
