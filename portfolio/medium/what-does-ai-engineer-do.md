# What Does an AI Engineer Actually Do?

*Not what LinkedIn tells you. Not what bootcamps sell you. What the job actually looks like when you sit down at your desk on Monday morning.*

---

I've been an AI Engineer for four years. Before that I was a backend developer who got pulled into "the AI stuff" because I was the only one on the team who'd used the OpenAI API.

That's how most of us ended up here. Not through a PhD. Not through Kaggle. Through being a decent software engineer who happened to be curious about ML — and then discovering there's a massive gap between a model that works in a notebook and a model that works in a product.

That gap is the job.

---

## The one-line job description

You take AI models and make them work inside real products.

That's it. You don't train models from scratch (usually). You don't run experiments on datasets all day. You don't write research papers. You build the systems that connect models to users — the APIs, the data pipelines, the evaluation frameworks, the monitoring, the deployment infrastructure. All the boring-sounding stuff that determines whether a product actually works or just demos well.

---

## What I actually did last week

Monday: Spent three hours figuring out why our chatbot was hallucinating on financial questions. Turned out the retrieval was pulling wrong document chunks. Fixed the chunking strategy from 1000 tokens to 400 with overlap. Accuracy went from 71% to 89%.

Tuesday: Wrote a new API endpoint for our internal tool. FastAPI, 200 lines, nothing fancy. The interesting part was adding a circuit breaker so the app doesn't crash when OpenAI's API goes down (which happens more than you'd think).

Wednesday: Production alert at 9am. Inference latency spiked to 4 seconds. Root cause: our vector database ran out of memory because someone indexed 2M documents without telling me. Scaled the instance, added an alert, wrote a runbook.

Thursday: Sprint planning. PM wants to add image understanding to the product. I spent the afternoon prototyping with GPT-4o's vision API. Got a working demo in 3 hours. Told the PM it would take 6 weeks to productionize. He didn't love that answer.

Friday: Code reviews. Updated our evaluation suite to catch a new class of failure we'd seen in production. Deployed a new model version using blue-green deployment.

No Jupyter notebooks were harmed in the making of this week.

---

## How this differs from every other ML title

I get asked this constantly, so here's the honest version:

**Data Scientist** — Explores data, finds patterns, builds prototype models, presents findings. Heavy on statistics, pandas, SQL, visualization. Their output is usually a model or an insight, not a running system.

**ML Engineer** — Trains models, optimizes them, builds training pipelines. Deep in PyTorch, GPU clusters, hyperparameter tuning, experiment tracking. Closer to research than to production.

**AI Engineer** — Takes models (often from an API — OpenAI, Anthropic, open-source) and integrates them into applications. Builds the RAG pipelines, the agent logic, the serving infrastructure, the evaluation systems. Closer to software engineering than to research.

**Data Engineer** — Builds the pipelines that move and transform data. Spark, Airflow, Kafka, dbt. They make sure data exists in the right place, in the right format, at the right time.

The overlap is real. At a startup you might do all four. At a large company the boundaries are sharper. But the trend is clear: AI Engineer has become the role that owns "model in production" end-to-end.

| | Data Scientist | ML Engineer | AI Engineer |
|---|---|---|---|
| **Main output** | Models, insights | Trained models, pipelines | Production APIs, shipped features |
| **Primary tools** | Jupyter, pandas, scikit-learn | PyTorch, W&B, GPUs | LangChain, FastAPI, Docker, vector DBs |
| **Cares most about** | Accuracy, statistical validity | Model performance, training speed | Latency, reliability, user experience |
| **On-call?** | Rarely | Sometimes | Yes |
| **Writes tests?** | Sometimes | For model validation | Extensively |

---

## The actual tech stack

What's installed on my machine right now:

**Daily:** Python, FastAPI, LangChain, Docker, PostgreSQL, Redis, Git

**AI-specific:** OpenAI API, Anthropic API, sentence-transformers, vLLM, Hugging Face

**Vector DBs:** Pinecone (work), Qdrant (side projects), pgvector (when I don't want another service)

**Monitoring:** Prometheus, Grafana, LangSmith, custom eval dashboards

**Infra:** AWS (ECS, Lambda, S3), Terraform, GitHub Actions

I don't use TensorFlow. I haven't opened a Jupyter notebook in months. I write Python in VS Code, test with pytest, and deploy with Docker. It's software engineering with AI components, not the other way around.

---

## Code: what AI engineers actually write

Short, real patterns. Not tutorials — stuff I use every week.

### RAG query with source tracking

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
import time

vectorstore = Qdrant.from_existing_collection(
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="product-docs",
    url="http://localhost:6333",
)

chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.1),
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
)

start = time.time()
result = chain.invoke({"query": "How do I reset my password?"})

print(f"Answer: {result['result']}")
print(f"Sources: {[d.metadata['source'] for d in result['source_documents']]}")
print(f"Latency: {(time.time() - start) * 1000:.0f}ms")
```

That's 18 lines. Complete RAG pipeline. In production you add error handling, caching, and metrics — but the core logic is exactly this.

### Model serving API

```python
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import time

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")
started_at = time.time()

class EmbedRequest(BaseModel):
    texts: list[str]

@app.post("/v1/embed")
async def embed(req: EmbedRequest):
    start = time.time()
    vectors = model.encode(req.texts, normalize_embeddings=True)
    return {
        "embeddings": vectors.tolist(),
        "latency_ms": round((time.time() - start) * 1000, 2),
    }

@app.get("/health")
async def health():
    return {"status": "ok", "uptime_s": round(time.time() - started_at)}
```

Deployable AI microservice. Health check for Kubernetes. Latency tracking built in. Under 25 lines. Run it with `uvicorn api:app --port 8000`.

### Evaluation — the part nobody talks about

This matters more than model choice. If you can't measure quality, you can't improve it.

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

eval_data = Dataset.from_dict({
    "question": ["How do I reset my password?", "What's the refund policy?"],
    "answer": [answer_1, answer_2],
    "contexts": [contexts_1, contexts_2],
    "ground_truth": [expected_1, expected_2],
})

results = evaluate(eval_data, metrics=[faithfulness, answer_relevancy, context_precision])
print(results)
# {'faithfulness': 0.92, 'answer_relevancy': 0.87, 'context_precision': 0.85}
```

If faithfulness drops below 0.85, we don't deploy. That's the rule. No exceptions.

---

## System architecture

What a typical AI feature looks like in production:

```
Users → API Gateway → App Server → AI Service → Vector DB
                                       ↓              ↓
                                    LLM API      Embedding Model
                                       ↓
                                  Monitoring (Prometheus + LangSmith)
```

The AI Engineer owns the AI Service box and everything it talks to. Frontend owns the UI. Backend owns the app server. Data team owns the pipelines that populate the vector DB.

In practice the boundaries blur. I've written frontend code when I needed to test something. I've fixed data pipeline bugs when the data team was on holiday. But the core responsibility is clear: make the AI part work reliably at scale.

---

## What separates mid from senior

After interviewing 30+ candidates:

**Mid-level** can build a RAG pipeline, deploy a model, write decent APIs. They follow patterns they've seen before. When things break they can usually fix them with guidance.

**Senior** designs the system before writing code. They know when to use RAG vs fine-tuning vs prompt engineering — and more importantly, when to not use AI at all. They build evaluation frameworks. They make infrastructure decisions. When things break at 2am they know exactly where to look.

The biggest gap isn't technical. It's judgment. Knowing that switching from GPT-4o to GPT-4o-mini saves $8K/month but drops accuracy by 3% — and making that call with confidence because you have the evaluation data to back it up.

---

## Salary in 2026

Real numbers:

| Level | US (total comp) | Remote / Global |
|---|---|---|
| Junior (0–2 yrs) | $100K–$135K | $55K–$100K |
| Mid (2–5 yrs) | $140K–$180K | $80K–$140K |
| Senior (5+ yrs) | $175K–$225K | $120K–$180K |
| Staff+ (7+ yrs) | $200K–$315K | $150K–$250K |

Finance and big tech pay the most. Healthcare and government pay less but the work is often more interesting. The demand is real — AI job postings grew even while overall tech hiring declined. But the bar is rising. "I completed a LangChain tutorial" doesn't cut it anymore.

---

## 10 interview questions I actually ask

**1. "Your RAG system returns wrong answers. Walk me through debugging it."**
I want systematic: check retrieval first, then the prompt, then the model. Not "try a bigger model."

**2. "When would you fine-tune vs use RAG vs prompt-engineer?"**
RAG: model needs external knowledge. Prompt engineering: model needs different behavior. Fine-tuning: model needs a new style prompts can't capture. Most of the time you start with RAG.

**3. "How do you measure if your AI feature is working?"**
If they only say "accuracy" I pass. I want user metrics (task completion), system metrics (latency, cost), and AI metrics (faithfulness, hallucination rate).

**4. "Tell me about a time your AI system broke in production."**
Everyone's has. I want: what broke, how they found it, how they fixed it, what they changed. If they say "nothing's ever broken" they haven't shipped anything.

**5. "Our LLM costs are $40K/month. Reduce that."**
Caching. Routing easy queries to smaller models. Reducing prompt tokens. Batching. Moving non-critical features to open-source. Each has trade-offs.

**6. "Design a system for asking questions about 10,000 PDFs."**
Parse → chunk → embed → index → retrieve → generate with citations. The interesting parts: chunk size, handling tables/images in PDFs, evaluation.

**7. "Keyword search vs semantic search."**
Keyword matches words. Semantic matches meaning. Best systems use both (hybrid). "Automobile repair" matches "car maintenance" in semantic but not keyword.

**8. "How do you handle hallucinations?"**
RAG with source attribution. Output validation. Confidence scoring. Human-in-the-loop for high-stakes. Defense in depth — no single solution.

**9. "Build or buy?"**
If AI is your product, build. If AI is a feature, buy (APIs). If you need full control, self-host open-source. Most companies use APIs and that's fine.

**10. "Explain your last project to me like I'm a PM."**
Filters out half the candidates. If you can't explain what you built, why it matters, and what the results were without jargon, you're not ready for a senior role.

---

## How to get here

**If you're a software engineer:** You're 70% there. Learn LLM APIs (a weekend). Build a RAG chatbot (a week). Deploy it with monitoring (another week). Done. More useful experience than most bootcamps.

**If you're a data scientist:** Level up the engineering. Learn FastAPI. Learn Docker. Write tests. The modeling skills transfer. The engineering is the bottleneck.

**If you're starting from zero:** Learn Python. Build web APIs. Understand databases. Then add AI. Don't start with AI — start with engineering.

**What you don't need:** A PhD. Kaggle medals. Ability to derive backpropagation by hand.

**What you do need:** Ability to ship reliable software. Comfort with ambiguity. Patience to build evaluation before declaring something "works."

---

## The role now vs three years ago

2023: Train models, fine-tune, notebooks, scikit-learn.

2026: Integrate LLM APIs, build RAG, deploy with Docker, evaluate with automated suites, monitor in production, manage costs.

The shift is from model-building to system-building. Models got good enough that the hard problem moved from "make the model work" to "make the product work."

That's the job. Less glamorous than "I train neural networks." More useful.

---

Go build something. That's how you learn this. Not by reading another article — including this one.

---

*Tags: AI Engineer · Software Engineering · Career · LLMs · RAG · Python · System Design*
