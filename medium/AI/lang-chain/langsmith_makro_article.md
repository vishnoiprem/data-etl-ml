# LangSmith: How I Added Full Observability to CPAxtra's LLM Platform in One Day

*Debugging, evaluating, and monitoring every LLM call across Makro and Lotus's — from a single dashboard*

---

Running LLMs in production without observability is like running Databricks jobs without logs.

When our Axtra360 LLM Gateway started serving store managers, suppliers, and analysts across Thailand, Cambodia, and Myanmar, something happened that always happens at scale:

> **A store manager in Chiang Mai complained: "The chatbot gave me wrong sales figures."**

Without tracing, I had no idea which call failed, which prompt was used, how many tokens it consumed, or what the LLM actually returned. I was debugging blind.

LangSmith solved this in one day. Here is exactly how.

---

## What is LangSmith?

LangSmith is the **observability layer** of the LangChain ecosystem. It sits above everything else:

```
LangSmith   ← observability: trace, debug, evaluate, monitor  ← THIS ARTICLE
LangServe   ← deployment: chains as REST APIs
LangChain   ← chain and agent building
LCEL        ← LangChain Expression Language
```

It gives you four capabilities:

**1. Tracing** — every LLM call logged with full input, output, latency, tokens, cost. Click into any call and see the exact prompt that was sent.

**2. Debugging** — when something fails, you see the complete execution tree. Which step failed, what the input was, what error came back.

**3. Evaluation** — run your chain against a dataset of test questions and score outputs on correctness, conciseness, helpfulness, semantic similarity.

**4. Monitoring** — production dashboards showing latency (P50/P99), tokens per second, cost per day, error rate, user feedback over time.

---

## Why This Matters for E-Commerce at Scale

At CPAxtra we run five LLM-powered services across Axtra360. Without LangSmith, when something goes wrong, you ask:

- Which of the 5 services failed?
- Which user's session was it?
- Was the prompt the problem or the retrieval step?
- Is latency degrading after a model update?
- Is GPT-4o actually better than GPT-4 for Thai queries?

With LangSmith, every one of these questions has a 30-second answer. You click through to the trace, see every step, compare experiments side by side.

For any e-commerce operation running LLMs — product search, recommendation, supplier chatbots, fraud explanation, campaign generation — observability is not optional. It is the difference between a reliable product and a liability.

---

## Setup — Four Environment Variables

This is all it takes to turn on tracing for any existing LangChain code:

```python
import os

# LangSmith — get your key at smith.langchain.com
os.environ["LANGCHAIN_TRACING_V2"]  = "true"
os.environ["LANGCHAIN_ENDPOINT"]    = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]     = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"]     = "makro-axtra360-production"

# Your existing Azure OpenAI keys
os.environ["AZURE_OPENAI_ENDPOINT"]    = "https://your-resource.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"]     = "your-azure-openai-key"
os.environ["AZURE_OPENAI_DEPLOYMENT"]  = "gpt-4o"
```

That is it. Every `.invoke()`, `.stream()`, `.batch()` call now appears in your LangSmith dashboard automatically. No code changes to the chain itself.

---

## Part 1 — Tracing: See Every Call

### Basic chain with tracing enabled

```python
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = AzureChatOpenAI(
    azure_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"],
    azure_endpoint   = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key          = os.environ["AZURE_OPENAI_API_KEY"],
    api_version      = "2024-02-01",
    temperature      = 0.3,
)

# Makro sales analysis chain
sales_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a retail analytics assistant for CPAxtra (Makro/Lotus's).
You analyze sales data and provide actionable insights.
Always respond in the same language the user uses — Thai or English.
Be concise and data-focused."""),
    ("human", "{question}"),
])

sales_chain = sales_prompt | llm | StrOutputParser()

# This call is now automatically traced in LangSmith
response = sales_chain.invoke({
    "question": "Fresh Food category ยอดขายลดลง 12% สัปดาห์ที่แล้ว สาเหตุที่เป็นไปได้คืออะไร?"
})
print(response)
```

In your LangSmith dashboard you now see:

```
Project: makro-axtra360-production
│
└── RunnableSequence  ✓  1.83s  196 tokens  $0.004
    ├── ChatPromptTemplate  0.00s
    ├── AzureChatOpenAI  1.81s  196 tokens
    └── StrOutputParser  0.00s

Input:  "Fresh Food category ยอดขายลดลง 12%..."
Output: "สาเหตุที่เป็นไปได้: 1) ฤดูกาล..."
```

Every step, every token, every millisecond. Click any step to see the exact prompt sent.

---

### Adding metadata for Makro-specific filtering

```python
from langchain_core.callbacks import CallbackManager
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer

# Tag traces with business metadata — filter by store, country, chain in dashboard
tracer = LangChainTracer(project_name="makro-axtra360-production")

response = sales_chain.invoke(
    {"question": "What drove the spike in Household category last Tuesday?"},
    config={
        "callbacks": [tracer],
        "tags": ["sales-analysis", "country-TH", "store-bangna"],
        "metadata": {
            "user_id":    "store_mgr_bkk_bangna_001",
            "store_code": "TH-0042",
            "country":    "TH",
            "service":    "chat-with-data"
        }
    }
)
```

Now in LangSmith you can filter traces by `country-TH`, `store-bangna`, or any metadata tag. When a store manager complains, you filter by their `user_id` and see every single call they made.

---

## Part 2 — Debugging: Finding What Went Wrong

### RAG chain with full trace visibility

This is where LangSmith pays off most. A RAG chain has multiple steps — retrieval, document ranking, generation. When the answer is wrong, you need to know: was the retrieval bad, or the generation?

```python
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough

# Makro supplier contract RAG — the DOC-LM service in Axtra360
embeddings = AzureOpenAIEmbeddings(
    azure_deployment = "text-embedding-3-large",
    azure_endpoint   = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key          = os.environ["AZURE_OPENAI_API_KEY"],
)

vector_store = AzureSearch(
    azure_search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"],
    azure_search_key      = os.environ["AZURE_SEARCH_KEY"],
    index_name            = "makro-supplier-contracts",
    embedding_function    = embeddings.embed_query,
)

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a contract analysis assistant for CPAxtra procurement team.
Answer questions based only on the provided supplier contract documents.
If the answer is not in the documents, say 'ไม่พบข้อมูลในสัญญา' (not found in contract).
Always cite the document section you reference."""),
    ("human", """Context documents:
{context}

Question: {question}"""),
])

def format_docs(docs):
    return "\n\n".join([
        f"[Section {i+1} | {doc.metadata.get('supplier','Unknown')} | {doc.metadata.get('page','?')}]\n{doc.page_content}"
        for i, doc in enumerate(docs)
    ])

# Full RAG chain — every step traced
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# LangSmith traces this as:
# RunnableParallel
#   ├── Retriever (shows which 5 docs were returned + similarity scores)
#   ├── RunnablePassthrough
#   ├── ChatPromptTemplate
#   ├── AzureChatOpenAI
#   └── StrOutputParser

result = rag_chain.invoke(
    "What is the penalty clause for late delivery in the Nestle contract?",
    config={
        "tags": ["doc-lm", "procurement"],
        "metadata": {"supplier": "nestle", "contract_year": "2024"}
    }
)
print(result)
```

When the answer is wrong, you open the trace in LangSmith and immediately see: did the retriever return the right documents? Was the penalty clause actually in the top 5 results? If not — retrieval problem, not a generation problem.

---

## Part 3 — Evaluation: Is Your Chain Actually Good?

### Build a Makro evaluation dataset

```python
from langsmith import Client

client = Client()

# Create evaluation dataset — Makro e-commerce Q&A pairs
# These are questions where you know the correct answer
makro_eval_dataset = [
    {
        "question": "What is Makro's primary B2B customer segment?",
        "answer":   "Hotels, restaurants, caterers (HoReCa), and small business owners (SMEs)"
    },
    {
        "question": "Fresh Food ยอดขายหลักมาจากกลุ่มลูกค้าไหน?",
        "answer":   "ร้านอาหาร โรงแรม และผู้ประกอบการ HoReCa"
    },
    {
        "question": "What does O2O mean at Makro?",
        "answer":   "Online-to-Offline: customers order online and receive delivery or pick up at store"
    },
    {
        "question": "CPAxtra ดำเนินธุรกิจในประเทศใดบ้าง?",
        "answer":   "ไทย กัมพูชา เมียนมา และมาเลเซีย"
    },
    {
        "question": "What is slab_discount in Makro transactions?",
        "answer":   "A tiered promotional discount applied based on quantity purchased"
    },
    {
        "question": "What payment channels does Makro O2O support?",
        "answer":   "Credit card, debit card, bank transfer, QR payment, and cash on delivery"
    },
    {
        "question": "Axtra360 คืออะไร?",
        "answer":   "แพลตฟอร์ม AI ของ CPAxtra ที่รวม Chat with Data, DOC-LM, SSBI, Martech และ Forecasting"
    },
    {
        "question": "How does Makro's comp_discount differ from slab_discount?",
        "answer":   "comp_discount is a compound promotional discount applied on top of slab_discount for specific campaign combinations"
    },
]

# Upload to LangSmith
dataset = client.create_dataset(
    dataset_name = "makro-llm-eval-v1",
    description  = "CPAxtra/Makro Q&A evaluation dataset for LLM chain quality testing"
)

for item in makro_eval_dataset:
    client.create_example(
        inputs   = {"question": item["question"]},
        outputs  = {"answer":   item["answer"]},
        dataset_id = dataset.id,
    )

print(f"Dataset created: {dataset.id}")
print(f"Examples: {len(makro_eval_dataset)}")
```

### Run evaluation with multiple evaluators

```python
from langchain.evaluation import load_evaluator
from langsmith.evaluation import evaluate, LangChainStringEvaluator

# Define evaluators — each scores the output on a different dimension
correct_evaluator = LangChainStringEvaluator(
    "labeled_criteria",
    config={"criteria": "correctness"},
    prepare_data=lambda run, example: {
        "prediction": run.outputs["output"],
        "reference":  example.outputs["answer"],
        "input":      example.inputs["question"],
    }
)

concise_evaluator = LangChainStringEvaluator(
    "labeled_criteria",
    config={"criteria": "conciseness"}
)

helpful_evaluator = LangChainStringEvaluator(
    "labeled_criteria",
    config={"criteria": "helpfulness"}
)

semantic_evaluator = LangChainStringEvaluator("embedding_distance")

# Run evaluation
def run_chain(inputs):
    return {"output": sales_chain.invoke({"question": inputs["question"]})}

results = evaluate(
    run_chain,
    data            = "makro-llm-eval-v1",
    evaluators      = [correct_evaluator, concise_evaluator,
                       helpful_evaluator, semantic_evaluator],
    experiment_prefix = "gpt4o-makro-v1",
    metadata        = {"model": "gpt-4o", "temperature": 0.3, "version": "1.0"}
)

print(f"\nEvaluation results:")
print(f"  Correctness  : {results.to_pandas()['feedback.correctness'].mean():.2f}")
print(f"  Conciseness  : {results.to_pandas()['feedback.conciseness'].mean():.2f}")
print(f"  Helpfulness  : {results.to_pandas()['feedback.helpfulness'].mean():.2f}")
```

### Compare two models side by side

```python
# Run the same evaluation with a different model
# This is how you decide: is GPT-4o worth the cost over GPT-4?

llm_gpt4 = AzureChatOpenAI(
    azure_deployment = "gpt-4",          # cheaper model
    azure_endpoint   = os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key          = os.environ["AZURE_OPENAI_API_KEY"],
    api_version      = "2024-02-01",
    temperature      = 0.3,
)

sales_chain_gpt4 = sales_prompt | llm_gpt4 | StrOutputParser()

def run_gpt4_chain(inputs):
    return {"output": sales_chain_gpt4.invoke({"question": inputs["question"]})}

results_gpt4 = evaluate(
    run_gpt4_chain,
    data            = "makro-llm-eval-v1",
    evaluators      = [correct_evaluator, concise_evaluator, helpful_evaluator],
    experiment_prefix = "gpt4-makro-v1",
    metadata        = {"model": "gpt-4", "temperature": 0.3, "version": "1.0"}
)

# LangSmith shows both experiments side by side in the UI:
# Experiment          Correctness  Conciseness  Helpfulness  Cost/call
# gpt4o-makro-v1      0.92         0.88         0.94         $0.0041
# gpt4-makro-v1       0.85         0.82         0.88         $0.0018
# Decision: GPT-4o is 8% more correct but 2.3x more expensive — Thai queries
```

---

## Part 4 — Monitoring: Production Health Dashboard

### Add feedback collection to LangServe

```python
# In your server_api.py — add feedback endpoint
# LangServe's enable_feedback_endpoint=True does this automatically

from langsmith import Client

client = Client()

def collect_user_feedback(run_id: str, score: int, comment: str = ""):
    """
    Call this when a user gives thumbs up/down on a response.
    score: 1 = thumbs up, 0 = thumbs down
    """
    client.create_feedback(
        run_id   = run_id,
        key      = "user_rating",
        score    = score,
        comment  = comment,
        feedback_source_type = "app"
    )
```

### Custom monitoring metrics for Makro

```python
from langsmith.run_helpers import traceable
import time

@traceable(
    name    = "makro-fraud-explanation",
    tags    = ["fraud", "compliance"],
    metadata= {"service": "fraud-detection", "country": "TH"}
)
def explain_fraud_flag(transaction_id: str, fraud_score: float, features: dict) -> str:
    """
    Generates a human-readable explanation of why a transaction was flagged.
    Used by the fraud ops team to review flagged transactions.
    Automatically traced with transaction metadata.
    """
    explanation_prompt = f"""
    Transaction {transaction_id} was flagged with fraud score {fraud_score:.2f}.

    Key signals detected:
    - Margin rate: {features.get('margin_rate', 'N/A')}
    - Discount rate: {features.get('discount_rate', 'N/A')}
    - Transaction velocity (7d): {features.get('txn_count_7d', 'N/A')} transactions
    - Spend vs 30d average: {features.get('spend_vs_avg_30d', 'N/A')}x

    Explain in 2-3 sentences why this looks suspicious, in Thai.
    """
    return sales_chain.invoke({"question": explanation_prompt})


@traceable(
    name    = "makro-product-recommendation",
    tags    = ["recommendation", "personalization"],
)
def generate_product_recommendation(customer_id: str, purchase_history: list,
                                     category: str) -> str:
    """
    Generates personalised product recommendations for B2B customers.
    Used in the Martech service for campaign personalisation.
    """
    history_text = ", ".join(purchase_history[-10:])  # last 10 purchases
    prompt = f"""
    B2B customer {customer_id} frequently buys: {history_text}
    They are browsing the {category} category.
    Suggest 3 complementary products they might need for their restaurant/hotel business.
    Keep it concise and business-focused.
    """
    return sales_chain.invoke({"question": prompt})


# Both functions are now fully traced — every call logged with
# input, output, latency, tokens, cost, tags, metadata
result = explain_fraud_flag(
    transaction_id = "TXN-2024-889234",
    fraud_score    = 0.87,
    features       = {
        "margin_rate":       -0.12,
        "discount_rate":     0.65,
        "txn_count_7d":      47,
        "spend_vs_avg_30d":  8.3
    }
)
print(result)
```

---

## Part 5 — E-Commerce Use Cases with Full Code

### Use Case 1: Product search quality monitoring

```python
@traceable(name="makro-product-search", tags=["search", "e-commerce"])
def semantic_product_search(query: str, top_k: int = 5) -> list:
    """
    Semantic product search for Makro O2O platform.
    Translates Thai/English queries to structured product matches.
    LangSmith traces which queries fail — lets you improve the search prompt.
    """
    search_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a product search assistant for Makro Thailand.
Given a customer search query, return the top matching product categories
and search keywords in JSON format.
Handle Thai/English mixed queries correctly.

Return JSON only:
{
  "categories": ["category1", "category2"],
  "keywords": ["keyword1", "keyword2"],
  "customer_intent": "HoReCa|Retail|SME",
  "query_language": "TH|EN|Mixed"
}"""),
        ("human", "Query: {query}"),
    ])

    from langchain_core.output_parsers import JsonOutputParser
    search_chain = search_prompt | llm | JsonOutputParser()

    return search_chain.invoke({"query": query})


# Test across query types — all traced in LangSmith
test_queries = [
    "น้ำมันพืชราคาส่ง 20 ลิตร",           # Thai: bulk cooking oil
    "coffee machine commercial grade",      # English
    "ผงซักฟอก bulk สำหรับโรงแรม",          # Thai: hotel laundry bulk
    "disposable gloves food grade 100pcs",  # English
    "เนื้อแช่แข็ง halal certified",         # Thai: halal frozen meat
]

for query in test_queries:
    result = semantic_product_search(query)
    print(f"Query: {query}")
    print(f"Result: {result}\n")
```

### Use Case 2: Automated supplier feedback classification

```python
@traceable(
    name     = "makro-supplier-feedback-classifier",
    tags     = ["supplier", "quality-control"],
    metadata = {"version": "2.0", "model": "gpt-4o"}
)
def classify_supplier_feedback(feedback_text: str, supplier_id: str) -> dict:
    """
    Classifies incoming supplier feedback into actionable categories.
    Used by procurement team to auto-route complaints.
    LangSmith tracks classification accuracy over time.
    """
    classify_prompt = ChatPromptTemplate.from_messages([
        ("system", """Classify supplier feedback for Makro procurement team.

Return JSON only:
{
  "category": "QUALITY|DELIVERY|PRICING|DOCUMENTATION|COMPLIANCE|OTHER",
  "severity": "HIGH|MEDIUM|LOW",
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "action_required": true|false,
  "route_to": "quality-team|logistics|commercial|compliance|general",
  "summary": "one sentence summary in English"
}"""),
        ("human", "Supplier: {supplier_id}\nFeedback: {feedback}"),
    ])

    from langchain_core.output_parsers import JsonOutputParser
    classify_chain = classify_prompt | llm | JsonOutputParser()

    return classify_chain.invoke({
        "supplier_id": supplier_id,
        "feedback":    feedback_text
    })


# Sample feedback from Makro suppliers
feedbacks = [
    ("SUP-NESTLE-001",
     "สินค้าที่ส่งมาหมดอายุอีก 3 วัน ไม่ตรงตามสัญญาที่กำหนดอย่างน้อย 30 วัน"),
    ("SUP-UNILEVER-002",
     "We cannot meet the 48-hour delivery SLA for the Chiang Mai distribution center due to truck shortage"),
    ("SUP-CP-003",
     "ราคาที่ตกลงในสัญญา Q1 ต้องการปรับขึ้น 8% เนื่องจากต้นทุนวัตถุดิบ"),
    ("SUP-BETAGRO-004",
     "Halal certification renewal for pork-free processing line completed successfully"),
]

for supplier_id, feedback in feedbacks:
    result = classify_supplier_feedback(feedback, supplier_id)
    print(f"Supplier: {supplier_id}")
    print(f"Category: {result['category']} | Severity: {result['severity']}")
    print(f"Route to: {result['route_to']}")
    print(f"Summary: {result['summary']}\n")
```

### Use Case 3: Campaign copy generation with quality evaluation

```python
from langsmith import Client
from langsmith.run_helpers import traceable

client = Client()

@traceable(
    name     = "makro-campaign-copy-generator",
    tags     = ["marketing", "martech", "campaign"],
    metadata = {"service": "axtra360-martech"}
)
def generate_campaign_copy(
    product_category: str,
    target_segment:   str,
    discount_percent: int,
    channel:          str   # LINE|Facebook|Email|SMS
) -> dict:
    """
    Generates localised campaign copy for Makro marketing.
    Thai and English versions generated in one call.
    LangSmith tracks which campaigns get positive user feedback.
    """
    copy_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a marketing copywriter for Makro Thailand.
Write campaign copy for the {channel} channel.
Target audience: {target_segment} (HoReCa operators, SME owners, restaurants).
Be direct, mention the discount clearly, use a strong call to action.

Return JSON only:
{{
  "thai_copy": "Thai version (max 80 chars for SMS, 200 for others)",
  "english_copy": "English version",
  "hashtags": ["#tag1", "#tag2"],
  "cta": "call to action text",
  "emoji": "2-3 relevant emojis"
}}"""),
        ("human", """Product: {product}
Discount: {discount}%
Channel: {channel}"""),
    ])

    from langchain_core.output_parsers import JsonOutputParser
    copy_chain = copy_prompt | llm | JsonOutputParser()

    return copy_chain.invoke({
        "product":  product_category,
        "discount": discount_percent,
        "channel":  channel,
    })


# Generate campaigns — all traced, compare quality across runs
campaigns = [
    ("Fresh Food", "HoReCa",   15, "LINE"),
    ("Household",  "SME",      20, "Facebook"),
    ("Beverages",  "Retail",   10, "SMS"),
    ("Frozen Food","HoReCa",   25, "Email"),
]

for category, segment, discount, channel in campaigns:
    copy = generate_campaign_copy(category, segment, discount, channel)
    print(f"\n{category} → {channel}")
    print(f"TH: {copy['thai_copy']}")
    print(f"EN: {copy['english_copy']}")
    print(f"CTA: {copy['cta']} {copy['emoji']}")
```

---

## Part 6 — Connect LangSmith to Your Existing LangServe API

Add two flags to your existing `server_api.py` from the LangServe article:

```python
# server_api.py — add LangSmith to existing LangServe deployment

import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"]    = "makro-axtra360-production"
os.environ["LANGCHAIN_API_KEY"]    = os.environ["LANGSMITH_API_KEY"]

# Everything else stays the same
add_routes(
    app,
    llm_chain,
    path                     = "/llm-chain",
    enable_feedback_endpoint = True,    # ← thumbs up/down in UI logged to LangSmith
    enable_public_trace_link = True,    # ← shareable trace URLs for debugging
)
```

Now every call through LangServe — from store managers, supplier portals, Databricks notebooks — is automatically logged. You open LangSmith, filter by project, and see everything.

---

## What You See in the LangSmith Dashboard

After running the code above, your LangSmith project shows:

**Traces tab:**
```
Run Name                          Status  Latency  Tokens  Cost
makro-fraud-explanation           ✓       2.1s     312     $0.006
makro-product-search              ✓       1.4s     198     $0.004
makro-supplier-feedback-class     ✓       1.8s     245     $0.005
makro-campaign-copy-generator     ✗       timeout  —       —       ← this needs fixing
```

**Monitor tab (production metrics):**
```
Trace Latency P50: 1.6s  P99: 4.2s
Tokens/second: 847
Cost today: $24.30
Error rate: 0.3%
User feedback positive: 89%
```

**Experiments tab:**
```
gpt4o-makro-v1   Correctness: 0.92  Conciseness: 0.88  Cost: $0.004/call
gpt4-makro-v1    Correctness: 0.85  Conciseness: 0.82  Cost: $0.002/call
```

That last table is how you make a data-driven decision about which model to use. Not a gut feel — an experiment with your actual questions and your actual evaluation criteria.

---

## Key Takeaways

**1. Four environment variables turn on full tracing.** No code changes to your chains. Everything existing starts logging immediately.

**2. `@traceable` decorator is how you trace custom functions.** Any Python function that calls an LLM — wrap it with `@traceable` and it appears in your dashboard with full input/output/latency.

**3. Build an evaluation dataset from your real questions.** The Makro Q&A pairs above are better evaluators than generic benchmarks because they test what your system actually needs to know.

**4. LangSmith makes model comparison rigorous.** Running two experiments against the same dataset with the same evaluators is how you decide GPT-4o vs GPT-4 — not by feel.

**5. Production monitoring closes the loop.** Trace latency, cost, error rate, and user feedback in one dashboard means you know immediately when something degrades after a prompt change or model update.

---

## This Series So Far

This is Part 3 of the CPAxtra LLM platform series:

- **Part 1** — BERT Complete Architecture Guide: From Embeddings to Fine-Tuning
- **Part 2** — LangServe: Deploy Your LLM Chain as a Production REST API
- **Part 3** — LangSmith: Full Observability for Production LLM Apps ← this article
- **Part 4** — Coming next: LangGraph Agentic AI for Makro's Lead Generation Automation

---

*Prem Vishnoi is Head of Data & AI at CPAxtra (Makro/Lotus's), leading a 25-person team across Thailand, Cambodia, Myanmar, and Malaysia. He writes about building production AI systems on Azure Databricks, LangChain, and the broader LangChain ecosystem.*

*Tags: LangSmith, LangChain, LLM Observability, Production AI, Azure OpenAI, E-Commerce AI, Python, MLOps*
