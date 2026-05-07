# QUICKSTART

After extracting the zip into `/Users/pvishnoi/PycharmProjects/data-etl-ml/ai-engineering`:

```bash
cd /Users/pvishnoi/PycharmProjects/data-etl-ml/ai-engineering

# 1. Create a virtualenv (recommended)
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install shared deps once
pip install -r shared/requirements.txt
```

## Run any project's demo

Every project follows the same shape:

```bash
cd 01-enterprise-rag-platform
pip install -r requirements.txt
make demo
```

Replace `01-enterprise-rag-platform` with any of the eight directories.

## Run all tests

```bash
# from the workspace root
for p in 0[1-8]-*/; do
  echo "=== $p ==="
  (cd "$p" && python -m pytest tests/ -q)
done
```

## What each project demonstrates

| # | Project | What `make demo` does |
|---|---|---|
| 1 | enterprise-rag-platform | Ingest 8 docs → hybrid retrieve → rerank → answer with citations → eval |
| 2 | llm-fine-tuning | Build instruction JSONL → LoRA adapter math → DPO preference math → pre/post acc |
| 3 | multi-agent-platform | Run 5 loan applications through KYC → Credit → Policy specialists |
| 4 | fm-evaluation | Score baseline vs candidate model on golden + adversarial sets, gate the promotion |
| 5 | distributed-inference | Simulate 400 requests with router + semantic cache, show 90%+ cost savings |
| 6 | regulated-industry | 6 sample requests through authz → injection → PII → audit chain |
| 7 | prompt-engineering | Register 2 prompt versions, run Bayesian A/B, demonstrate rollback + context budget |
| 8 | llmops-platform | Three pipeline scenarios (ship / block / rollback) + drift detection on prod stream |

## LOCAL vs AWS mode

Every project has two modes controlled by an env var:

```bash
export AI_ENGINEERING_MODE=LOCAL   # default — runs offline
export AI_ENGINEERING_MODE=AWS     # uses Bedrock + OpenSearch + SageMaker
```

LOCAL mode is the default and requires no AWS account. AWS mode swaps in
Bedrock / OpenSearch / SageMaker via thin adapter classes — same business
logic, different backends.

## Project 1 — note on first-run dependencies

The flagship project (Enterprise RAG) tries to load `sentence-transformers` for
embeddings. If your machine has internet access to HuggingFace, it will download
the model (~80MB) and use proper transformer embeddings. If not, it transparently
falls back to a hashing-trick embedder that runs fully offline. Either way the
demo works end-to-end.

## Layout reminder

```
ai-engineering/
├── README.md
├── QUICKSTART.md
├── Makefile
├── shared/
│   ├── __init__.py
│   ├── utils.py
│   └── requirements.txt
├── 01-enterprise-rag-platform/
├── 02-llm-fine-tuning/
├── 03-multi-agent-platform/
├── 04-fm-evaluation/
├── 05-distributed-inference/
├── 06-regulated-industry/
├── 07-prompt-engineering/
└── 08-llmops-platform/
```
