# CLP AI/Data Engineer Interview
## Complete Technical Portfolio with Q&A

---

# INTERVIEW STRUCTURE

**Date:** Monday, 9th March 2026, 5:00 PM  
**Duration:** 30 min - 1 hour  
**Format:** Online Video Conference  

**Panel:**
| Interviewer | Role | Likely Questions |
|-------------|------|------------------|
| **Sudhir Bisht** | Principal, Data/AI/GenAI | RAG, LLMs, GenAI architecture |
| **Patrik Forsstroem** | AD, Data & Analytics | Data pipelines, BI, delivery |
| **Panda Soonam** | SM, Technical Delivery | Project execution, scalability |
| **Eric Sze** | Senior PM/Scrum | Agile, stakeholder management |

---

# PROJECT PORTFOLIO OVERVIEW

| Project | Technology | Business Value | Complexity |
|---------|------------|----------------|------------|
| **1. Supplier Document LLM** | RAG, LangChain, Vector DB | Search 1000s of contracts instantly | High |
| **2. Energy Demand Forecasting** | Prophet, XGBoost, LSTM, MLflow | Optimize grid operations, reduce costs | High |
| **3. Conversational Analytics** | Text-to-SQL, LLM | Self-service BI for business users | Medium |

---

# PROJECT 1: SUPPLIER DOCUMENT LLM (RAG)

## Business Problem

> "CLP manages contracts with hundreds of suppliers for turbines, transformers, and maintenance services. Finding specific warranty terms or compliance requirements across thousands of documents takes hours. We need instant, accurate answers."

## Architecture Explanation

**When asked "Walk me through your RAG architecture":**

> "The system has four main components:
>
> **1. Document Ingestion Pipeline:**
> - Load PDFs, Word docs, and markdown from SharePoint/network drives
> - Use LangChain document loaders for consistent parsing
> - Handle OCR for scanned documents via Azure Document Intelligence
>
> **2. Chunking Strategy:**
> - Semantic chunking with 500-token chunks, 50-token overlap
> - Preserve document structure (headers, sections)
> - Store metadata: source file, page number, contract ID
>
> **3. Vector Store:**
> - Embed chunks using OpenAI `text-embedding-3-small` (1536 dimensions)
> - Store in ChromaDB for development, Pinecone for production
> - Index by supplier name, document type for filtered retrieval
>
> **4. Retrieval & Generation:**
> - User query → embed → top-5 similar chunks
> - Rerank for relevance using cross-encoder (optional)
> - Send to GPT-4 with strict citation requirements
> - Return answer with source documents"

## Code Walkthrough

**When asked "Show me the key code":**

```python
# 1. Document Loading & Chunking
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

loader = DirectoryLoader('./contracts', glob="**/*.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " "]
)
chunks = splitter.split_documents(documents)

# 2. Embedding & Vector Store
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 3. RAG Chain
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# 4. Query
result = qa_chain({"query": "What are Siemens turbine warranty terms?"})
print(result["result"])
```

## Interview Q&A

### Q1: "How do you handle hallucinations in RAG systems?"

**Answer:**
> "I implement multiple safeguards:
>
> 1. **Strict System Prompt:** Tell the LLM to only answer from provided context, and say 'I don't have that information' if not found
>
> 2. **Mandatory Citations:** Require the model to cite specific document sections
>
> 3. **Retrieval Validation:** Check similarity scores - if all retrieved chunks have low scores (<0.7), warn the user
>
> 4. **Human Feedback Loop:** Track when users report incorrect answers, use for fine-tuning retrieval
>
> 5. **Confidence Scoring:** Have the model rate its confidence; flag low-confidence answers for human review"

### Q2: "How do you choose chunk size?"

**Answer:**
> "It's a trade-off:
>
> - **Too small (100-200 tokens):** Loses context, fragments meaning
> - **Too large (1000+ tokens):** Dilutes relevance, hits context limits
>
> For technical documents like contracts, I use 400-600 tokens. I test by:
> 1. Creating a test set of 50 question-answer pairs
> 2. Measuring retrieval precision at different chunk sizes
> 3. Measuring end-to-end answer accuracy
>
> At Makro, 500 tokens with 50 overlap gave best results for supplier contracts."

### Q3: "What vector database would you recommend for CLP?"

**Answer:**
> "For CLP's Azure environment:
>
> **Primary Recommendation: Azure Cognitive Search**
> - Native Azure integration
> - Hybrid search (vector + keyword)
> - Enterprise security (managed identity)
> - Scales to millions of documents
>
> **Alternative: Databricks Vector Search**
> - If CLP uses Databricks extensively
> - Integrates with Unity Catalog governance
> - Good for ML teams
>
> **Avoid for production:** ChromaDB (great for POC, not enterprise scale)"

### Q4: "How would you handle document updates?"

**Answer:**
> "I implement an incremental update pipeline:
>
> 1. **Change Detection:** Monitor SharePoint/file system for new/modified documents
> 2. **Document Hashing:** Hash each document; only re-process if hash changes
> 3. **Chunk-Level Updates:** Delete old chunks by document_id, insert new ones
> 4. **Version Tracking:** Keep document version history in metadata
>
> ```python
> # Pseudo-code
> for doc in changed_documents:
>     doc_hash = hash_document(doc)
>     if doc_hash != stored_hash[doc.id]:
>         vectorstore.delete(filter={'document_id': doc.id})
>         new_chunks = process_document(doc)
>         vectorstore.add(new_chunks)
>         update_hash(doc.id, doc_hash)
> ```"

---

# PROJECT 2: ENERGY DEMAND FORECASTING

## Business Problem

> "CLP needs to forecast electricity demand to optimize power generation scheduling, plan maintenance windows, and manage peak load. Inaccurate forecasts cost millions in fuel or cause reliability issues."

## Architecture Explanation

**When asked "Explain your forecasting approach":**

> "I use an ensemble of three models, each capturing different patterns:
>
> **1. Prophet (30% weight):**
> - Captures yearly, weekly, and daily seasonality
> - Handles holidays automatically
> - Good for trend changes
>
> **2. XGBoost (40% weight):**
> - Feature-based: temperature, humidity, hour, day type
> - Captures complex non-linear relationships
> - Handles sudden changes well
>
> **3. LSTM (30% weight):**
> - Sequence-to-sequence learning
> - Captures temporal dependencies
> - Good for short-term patterns
>
> The ensemble weights are optimized on a validation set using grid search."

## Key Code

```python
# Feature Engineering
def create_features(df):
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
    
    # Cyclical encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Lag features
    for lag in [1, 24, 168]:  # 1h, 1d, 1w
        df[f'consumption_lag_{lag}'] = df['consumption'].shift(lag)
    
    # Rolling statistics
    df['consumption_rolling_24h'] = df['consumption'].rolling(24).mean()
    
    # Temperature effect (cooling degree hours)
    df['cooling_degree'] = np.maximum(df['temperature'] - 25, 0)
    
    return df

# Prophet Model
from prophet import Prophet

prophet_df = df.reset_index()[['timestamp', 'consumption']].copy()
prophet_df.columns = ['ds', 'y']

model = Prophet(
    seasonality_mode='multiplicative',
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=True
)
model.add_regressor('temperature')
model.fit(prophet_df)

# XGBoost Model
import xgboost as xgb

features = ['hour', 'day_of_week', 'month', 'temperature', 
            'consumption_lag_24', 'cooling_degree']
X = df[features]
y = df['consumption']

model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1
)
model.fit(X_train, y_train)

# Ensemble
ensemble_pred = (
    0.3 * prophet_pred +
    0.4 * xgb_pred +
    0.3 * lstm_pred
)
```

## Interview Q&A

### Q1: "How do you handle the temperature-demand relationship?"

**Answer:**
> "In Hong Kong, temperature is the primary driver of demand due to AC usage:
>
> **Non-linear Relationship:**
> - Below 25°C: Minimal impact
> - 25-30°C: Linear increase (~3% per degree)
> - Above 30°C: Accelerating increase (~5% per degree)
>
> **Implementation:**
> ```python
> # Cooling Degree Hours (CDH)
> df['cdh'] = np.maximum(df['temperature'] - 25, 0)
> 
> # Quadratic term for extreme heat
> df['cdh_squared'] = df['cdh'] ** 2
> ```
>
> I also add humidity interaction since Hong Kong has high humidity, which increases perceived temperature and AC usage."

### Q2: "How do you evaluate forecast accuracy?"

**Answer:**
> "I use multiple metrics at different time horizons:
>
> | Metric | Formula | Use Case |
> |--------|---------|----------|
> | **MAPE** | Mean Absolute % Error | Overall accuracy |
> | **MAE** | Mean Absolute Error | Operational planning |
> | **RMSE** | Root Mean Square Error | Penalizes large errors |
> | **Weighted MAPE** | MAPE weighted by load | Focus on high-demand periods |
>
> **By time horizon:**
> - Hour-ahead: < 2% MAPE target
> - Day-ahead: < 3% MAPE target
> - Week-ahead: < 5% MAPE target
>
> At Makro, our demand forecasting achieved 2.3% MAPE for day-ahead."

### Q3: "How do you handle holidays and special events?"

**Answer:**
> "Hong Kong has unique patterns:
>
> **1. Chinese New Year:** 
> - Commercial load drops 60%
> - Residential load spikes (reunions)
> - Model separately using historical CNY data
>
> **2. Typhoons:**
> - Signal 8+ suspends work
> - Commercial drops, residential increases
> - Use weather API for typhoon tracking
>
> **Implementation:**
> ```python
> # Holiday calendar
> hk_holidays = ['01-01', '02-10', '02-11', '04-05', 
>                '05-01', '07-01', '10-01', '12-25']
> df['is_holiday'] = df.index.strftime('%m-%d').isin(hk_holidays)
> 
> # Prophet holiday effects
> holidays = pd.DataFrame({
>     'holiday': 'cny',
>     'ds': pd.to_datetime(['2024-02-10', '2024-02-11']),
>     'lower_window': -1,
>     'upper_window': 3
> })
> model.add_country_holidays(country_name='HK')
> ```"

### Q4: "How would you deploy this model to production?"

**Answer:**
> "Using MLflow on Databricks:
>
> **1. Model Registry:**
> - Version all models in MLflow
> - Track experiments (hyperparameters, metrics)
> - Promote to staging → production
>
> **2. Serving:**
> - Databricks Model Serving for real-time inference
> - Batch predictions via scheduled Databricks job
>
> **3. Monitoring:**
> - Track prediction vs actual hourly
> - Alert if MAPE exceeds threshold
> - Automatic retraining if drift detected
>
> **4. Feature Store:**
> - Centralized feature computation
> - Point-in-time correctness for training
> - Serve features in real-time
>
> ```python
> import mlflow
> 
> with mlflow.start_run():
>     mlflow.log_params(params)
>     mlflow.log_metrics({'mape': mape, 'rmse': rmse})
>     mlflow.sklearn.log_model(model, 'model')
>     mlflow.register_model(uri, 'energy_forecaster')
> ```"

---

# PROJECT 3: CONVERSATIONAL DATA ANALYTICS

## Business Problem

> "Business users want to query consumption data without knowing SQL. Instead of waiting for analysts, they should be able to ask 'What was last month's consumption by district?' and get instant answers."

## Architecture Explanation

**When asked "How does Text-to-SQL work?":**

> "The system has four components:
>
> **1. Schema Context:**
> - Store table definitions (CREATE TABLE statements)
> - Column descriptions in business terms
> - Sample values for categorical columns
> - Table relationships
>
> **2. SQL Generation:**
> - Send user question + schema to GPT-4
> - Few-shot examples guide correct patterns
> - Temperature=0 for deterministic output
>
> **3. Validation Layer:**
> - Parse generated SQL for syntax errors
> - Block dangerous operations (DROP, DELETE)
> - Check table/column names exist
>
> **4. Execution & Formatting:**
> - Execute against read-only replica
> - Format results as table/chart
> - Natural language summary of findings"

## Key Code

```python
# Schema Context
SCHEMA_CONTEXT = """
Table: fact_consumption
- customer_id: Unique customer identifier
- consumption_kwh: Energy consumed in kilowatt-hours
- date_key: Date reference (YYYYMMDD)
- hour: Hour of day (0-23)

Table: dim_customer
- customer_id: Unique customer identifier
- customer_type: 'residential', 'commercial', 'industrial'
- district: Hong Kong district name

Table: dim_location
- district: Hong Kong district
- region: 'hong_kong_island', 'kowloon', 'new_territories'
"""

# Few-shot Examples
EXAMPLES = [
    {
        "question": "Total consumption by district",
        "sql": """SELECT l.district, SUM(c.consumption_kwh) as total
                  FROM fact_consumption c
                  JOIN dim_location l ON c.location_id = l.location_id
                  GROUP BY l.district
                  ORDER BY total DESC"""
    },
    # ... more examples
]

# SQL Generation with OpenAI
def generate_sql(question: str) -> str:
    prompt = f"""You are a SQL expert. Generate SQLite query for:

Schema:
{SCHEMA_CONTEXT}

Examples:
{format_examples(EXAMPLES)}

Question: {question}

SQL:"""
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    sql = response.choices[0].message.content
    return clean_sql(sql)

# Validation
def validate_sql(sql: str) -> bool:
    # Block dangerous operations
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE']
    for keyword in dangerous:
        if keyword in sql.upper():
            return False
    return True

# Execute
def execute_query(sql: str, conn):
    if not validate_sql(sql):
        raise ValueError("Query contains unsafe operations")
    return pd.read_sql_query(sql, conn)
```

## Interview Q&A

### Q1: "How do you prevent SQL injection in Text-to-SQL?"

**Answer:**
> "Multiple layers of protection:
>
> **1. Whitelist Approach:**
> - Only allow SELECT statements
> - Block DDL (CREATE, DROP, ALTER) and DML (INSERT, UPDATE, DELETE)
>
> **2. Read-Only Connection:**
> - Connect to read-only replica
> - Database user has only SELECT permissions
>
> **3. Query Parsing:**
> - Parse SQL with sqlparse library
> - Validate table/column names against known schema
>
> **4. Parameterization:**
> - If user provides filter values, parameterize them
>
> ```python
> import sqlparse
> 
> def is_safe_sql(sql: str) -> bool:
>     parsed = sqlparse.parse(sql)[0]
>     
>     # Only allow SELECT
>     if parsed.get_type() != 'SELECT':
>         return False
>     
>     # No multiple statements
>     if len(sqlparse.parse(sql)) > 1:
>         return False
>     
>     return True
> ```"

### Q2: "How do you handle ambiguous questions?"

**Answer:**
> "I implement clarification workflows:
>
> **1. Detect Ambiguity:**
> - 'Show me sales' → Which metric? Which period?
> - 'Top customers' → By what measure? How many?
>
> **2. Ask Clarifying Questions:**
> - Before generating SQL, check for required parameters
> - Return options: 'Did you mean consumption or revenue?'
>
> **3. Default Assumptions:**
> - For time, default to 'last month'
> - For aggregation, default to 'sum'
> - State assumptions in response
>
> **4. Schema-Driven:**
> - Use column descriptions to resolve synonyms
> - 'usage' → consumption_kwh, 'bills' → fact_billing"

### Q3: "How accurate is the SQL generation?"

**Answer:**
> "At Makro, we achieved 85-90% accuracy on first attempt:
>
> **Factors Affecting Accuracy:**
> | Factor | Impact |
> |--------|--------|
> | Schema clarity | High - descriptive column names help |
> | Few-shot examples | High - quality examples critical |
> | Query complexity | Lower for JOINs > 3 tables |
>
> **Improvement Strategies:**
> 1. **Example Selection:** Retrieve similar examples using embedding similarity
> 2. **Multi-Step:** For complex queries, break into subqueries
> 3. **Validation Loop:** If SQL fails, send error back to LLM for correction
> 4. **Human Feedback:** Track corrections, use for fine-tuning
>
> **Evaluation Dataset:**
> - Create 100+ test question-SQL pairs
> - Measure exact match and execution match
> - Weekly regression testing"

### Q4: "How would you handle joins across multiple tables?"

**Answer:**
> "I provide explicit relationship context:
>
> ```python
> RELATIONSHIPS = '''
> Relationships:
> - fact_consumption.customer_id → dim_customer.customer_id
> - fact_consumption.location_id → dim_location.location_id
> - fact_consumption.date_key → dim_time.date_key
> - dim_customer.district = dim_location.district
> '''
> ```
>
> **For complex joins:**
> 1. Include relationship diagram in prompt
> 2. Add examples with similar join patterns
> 3. Use chain-of-thought: 'First identify needed tables...'
>
> **Production tip:** For queries spanning >3 tables, validate the join path before execution to catch Cartesian products."

---

# GENERAL AI/DATA ENGINEERING Q&A

## GenAI Strategy Questions

### Q: "How would you approach GenAI adoption at CLP?"

**Answer:**
> "I'd follow a phased approach:
>
> **Phase 1: Foundation (Months 1-3)**
> - Establish AI governance framework
> - Set up Azure OpenAI with proper security
> - Identify 3-5 high-value use cases
> - Build internal RAG capability
>
> **Phase 2: Quick Wins (Months 4-6)**
> - Deploy document Q&A for contracts/procedures
> - Implement code assistant (Copilot) for engineers
> - Create operational knowledge base
>
> **Phase 3: Scale (Months 7-12)**
> - Customer-facing applications (with human oversight)
> - Predictive maintenance with AI explanations
> - Expand to multi-modal (images of equipment)
>
> **Key Principles:**
> - Human-in-the-loop for critical decisions
> - No sensitive data in external APIs
> - Clear ownership and accountability"

### Q: "What are the risks of GenAI in energy operations?"

**Answer:**
> "Energy is safety-critical, so we must be careful:
>
> **Risks:**
> | Risk | Mitigation |
> |------|------------|
> | Hallucination in safety procedures | Human approval for all safety content |
> | Data leakage to external APIs | Use Azure OpenAI (CLP data stays in Azure) |
> | Over-reliance on AI | Position as assistant, not decision-maker |
> | Outdated information | RAG with live document index |
>
> **Governance Requirements:**
> - Hong Kong's Ethical AI Framework compliance
> - Audit trail for all AI-generated recommendations
> - Clear escalation for AI uncertainty
> - Regular bias testing on customer-facing features"

---

# DEMO SCRIPT

**If asked to demo a project, here's a script:**

## Supplier RAG Demo (5 minutes)

```
"Let me show you the Supplier Document RAG system.

[Show architecture diagram]

First, I load supplier contracts - we have Siemens, ABB, and Vestas.
The system chunks these into 500-token segments and embeds them.

[Run query]
Question: 'What are the warranty terms for Siemens turbines?'

[Show retrieval]
The system retrieves the top 5 most relevant chunks.
You can see the similarity scores here.

[Show answer]
The answer includes:
- 24-month warranty from commissioning
- 10-year spare parts availability
- Source citation: CLP-SUP-2024-001

Key features:
- No hallucination - only answers from documents
- Cites sources for audit trail
- Handles follow-up questions with context

For CLP, this could search thousands of supplier contracts instantly."
```

---

# FILES INCLUDED IN THIS PACKAGE

```
clp_projects/
├── README.md                           # This overview
├── supplier_llm/
│   ├── data/
│   │   └── supplier_documents.md       # Sample supplier contracts
│   └── src/
│       └── supplier_rag.py             # Complete RAG implementation
├── forecasting/
│   ├── data/
│   │   └── (generated at runtime)
│   └── src/
│       ├── generate_data.py            # Energy data generator
│       └── energy_forecast.py          # Ensemble forecasting
└── data_qa/
    └── src/
        └── text_to_sql.py              # Text-to-SQL system
```

---

# CLOSING STATEMENT

**When they ask "Any final thoughts?":**

> "These three projects demonstrate my hands-on AI capabilities:
>
> 1. **RAG for Supplier Documents** - Ready for CLP's contract management
> 2. **Ensemble Forecasting** - Directly applicable to demand prediction
> 3. **Conversational Analytics** - Self-service BI for business users
>
> I've implemented similar systems at Makro, processing billions of records daily. I understand that energy is safety-critical, so I emphasize governance, human oversight, and clear auditability in all AI solutions.
>
> I'm excited about CLP's digital transformation journey and ready to contribute from day one."

---

**Good luck with your interview!** 🚀
