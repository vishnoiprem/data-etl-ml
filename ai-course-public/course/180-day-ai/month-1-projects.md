# Month 1: AI + PostgreSQL — 30 Days of Hands-On Projects
### Theme: "Teach AI to talk to your database"

**Data system:** PostgreSQL (via Neon, Supabase, or local Docker)
**Tools:** Python 3.10+, OpenAI/Anthropic API, psycopg2/asyncpg, Streamlit (for UI)
**Setup time:** 30 min (one time)
**Time per project:** 30-90 min
**Total time:** ~25 hours over 30 days

---

## Setup (do this once, before Day 1)

```bash
mkdir ai-daily && cd ai-daily
python -m venv venv && source venv/bin/activate
pip install openai psycopg2-binary streamlit pandas python-dotenv
echo "DATABASE_URL=postgresql://..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

Use a Neon/Supabase free Postgres DB. See README for full schema and helper files.

---

## Day 1: Text-to-SQL Generator (30 min)

**Project:** Build a function that takes a question in English and returns a valid SQL query.

```python
# day01_text_to_sql.py
from openai import OpenAI
from db import query

client = OpenAI()

def get_schema() -> str:
    return """
    users (id, email, name, created_at, country, plan)
    orders (id, user_id, amount, product, status, created_at)
    products (id, name, category, price, inventory)
    """

def text_to_sql(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""You are a SQL expert.
Schema: {get_schema()}
Generate a valid PostgreSQL query. Return ONLY the SQL."""},
            {"role": "user", "content": question}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# Test
for q in ["How many users signed up this month?",
          "Total revenue from US users?",
          "Top 5 products by sales"]:
    sql = text_to_sql(q)
    print(f"Q: {q}\nSQL: {sql}\n")
```

**Stretch:** Add Streamlit UI, add safety (block DROP/DELETE), add EXPLAIN validation.

---

## Day 2: Schema Explainer (30 min)

```python
# day02_schema_explainer.py
from openai import OpenAI
from db import query

client = OpenAI()

def get_full_schema() -> str:
    rows = query("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    tables = {}
    for row in rows:
        t = row['table_name']
        tables.setdefault(t, []).append(
            f"  {row['column_name']} ({row['data_type']})"
        )
    return "\n".join(f"TABLE {t}:\n" + "\n".join(cols)
                     for t, cols in tables.items())

def explain_schema(audience: str = "executive") -> str:
    schema = get_full_schema()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Explain this database to a {audience}.
Use plain language, no jargon. Schema: {schema}"""}
        ]
    )
    return response.choices[0].message.content

print(explain_schema("executive"))
```

---

## Day 3: Query Optimizer (45 min)

```python
# day03_query_optimizer.py
from openai import OpenAI
from db import query

client = OpenAI()

def analyze_query(sql: str) -> dict:
    explain = query(f"EXPLAIN ANALYZE {sql}")
    indexes = query("""
        SELECT tablename, indexname, indexdef
        FROM pg_indexes WHERE schemaname = 'public'
    """)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""You are a PostgreSQL performance expert.

EXPLAIN: {explain}
Indexes: {indexes}

Suggest:
1. Missing indexes (CREATE INDEX statements)
2. Query rewrites
3. Statistics updates
4. Estimated improvement

Be specific."""},
            {"role": "user", "content": sql}
        ]
    )
    return response.choices[0].message.content

slow = """SELECT u.email, COUNT(o.id), SUM(o.amount)
FROM users u LEFT JOIN orders o ON u.id = o.user_id
WHERE u.country = 'US' GROUP BY u.email ORDER BY SUM(o.amount) DESC LIMIT 100"""

print(analyze_query(slow))
```

---

## Day 4: Data Quality Checker (45 min)

```python
# day04_data_quality.py
from openai import OpenAI
from db import query
import json

client = OpenAI()

def check_data_quality(table: str) -> list[dict]:
    rows = query(f"SELECT * FROM {table} ORDER BY RANDOM() LIMIT 100")
    schema = query("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_name = %s
    """, (table,))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""You are a data quality expert.
Table: {table}, Schema: {schema}
Sample: {rows[:20]}

Identify quality issues. For each: column, issue, severity, examples, fix.
Return JSON."""},
            {"role": "user", "content": "Analyze."}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

print(check_data_quality("users"))
```

---

## Day 5: Auto ER Diagrams (45 min)

```python
# day05_er_diagram.py
from openai import OpenAI
from db import query

client = OpenAI()

def get_schema_with_relationships() -> str:
    tables = query("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    fks = query("""
        SELECT tc.table_name, kcu.column_name,
               ccu.table_name AS foreign_table_name,
               ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
    """)

    schema = "TABLES:\n"
    current = None
    for row in tables:
        if row['table_name'] != current:
            current = row['table_name']
            schema += f"\n{current}:\n"
        schema += f"  {row['column_name']} ({row['data_type']})\n"
    schema += "\nFK:\n"
    for fk in fks:
        schema += f"  {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}\n"
    return schema

def generate_er_diagram() -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Generate Mermaid ER diagram.
{get_schema_with_relationships()}
Return only valid Mermaid syntax starting with 'erDiagram'."""}
        ]
    ).choices[0].message.content

print(generate_er_diagram())
```

---

## Day 6: SQL Error Explainer (30 min)

```python
# day06_error_explainer.py
from openai import OpenAI
from db import query

client = OpenAI()

def explain_error(sql: str, error: Exception) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """Explain SQL error in plain English.
Format: What went wrong | Why | How to fix (with SQL) | Prevention tip"""},
            {"role": "user", "content": f"SQL: {sql}\nError: {error}"}
        ]
    )
    return response.choices[0].message.content

def safe_query(sql: str):
    try:
        return {"success": True, "data": query(sql)}
    except Exception as e:
        return {"success": False, "explanation": explain_error(sql, e)}

print(safe_query("SELECT * FORM users"))  # typo
```

---

## Day 7: WEEKEND — NL SQL SaaS v0.1 (3 hours)

Combine Days 1-6 into a Streamlit app with NL input, SQL display, results, error explanation, schema viewer. Deploy to Railway. Share publicly.

---

## Day 8: Migration Generator (45 min)

```python
# day08_migration_generator.py
from openai import OpenAI
from db import query

client = OpenAI()

def get_schema_snapshot() -> str:
    tables = query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    parts = []
    for t in tables:
        cols = query("""
            SELECT column_name || ' ' || data_type AS col
            FROM information_schema.columns WHERE table_name = %s
        """, (t['table_name'],))
        if cols:
            parts.append(f"CREATE TABLE {t['table_name']} ({', '.join(c['col'] for c in cols)})")
    return ";\n\n".join(parts)

def generate_migration(old: str, new: str) -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Generate Postgres migration.
Old: {old}
New: {new}
Use IF EXISTS, transactions, data migrations if needed."""}
        ]
    ).choices[0].message.content

print(generate_migration(
    "CREATE TABLE users (id SERIAL, email VARCHAR(255))",
    "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, name VARCHAR(255), created_at TIMESTAMP DEFAULT NOW())"
))
```

---

## Day 9: Row-Level Explanations (30 min)

```python
# day09_row_explainer.py
from openai import OpenAI
from db import query

client = OpenAI()

def explain_row(table: str, row: dict) -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Explain this row in 1-2 sentences.
Row: {row}
Be specific. Mention important fields. Highlight anomalies."""}
        ]
    ).choices[0].message.content

for user in query("SELECT * FROM users LIMIT 5"):
    print(f"User #{user['id']}: {explain_row('users', user)}")
```

---

## Day 10: SQL Anomaly Detector (60 min)

```python
# day10_anomaly_detector.py
from openai import OpenAI
from db import query
import json

client = OpenAI()

def detect_anomalies(table: str) -> dict:
    daily = query(f"""
        SELECT DATE(created_at) as day, COUNT(*) as count
        FROM {table} WHERE created_at >= NOW() - INTERVAL '90 days'
        GROUP BY DATE(created_at) ORDER BY day
    """)

    return json.loads(client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""You are a data analyst.
Daily counts: {daily}
Identify anomalies (spikes, dips, gaps, trend changes).
For each: date, type, severity, possible cause, action.
Return JSON."""}
        ],
        response_format={"type": "json_object"}
    ).choices[0].message.content)

print(json.dumps(detect_anomalies("orders"), indent=2))
```

---

## Day 11: NL Dashboard (60 min)

```python
# day11_dashboard.py
import streamlit as st
import plotly.express as px
import pandas as pd
from openai import OpenAI
from db import query

client = OpenAI()
st.title("📊 AI Dashboard")

q = st.text_input("Ask:", "Revenue by country, last 30 days")

if q:
    sql = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """Generate PostgreSQL.
Schema: users(id,country,plan,created_at), orders(id,user_id,amount,status,created_at)
Return only SQL."""},
            {"role": "user", "content": q}
        ]
    ).choices[0].message.content.strip()

    try:
        df = pd.DataFrame(query(sql))
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(df, use_container_width=True)
            with col2:
                if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                    st.plotly_chart(px.bar(df, x=df.columns[0], y=df.columns[1]),
                                    use_container_width=True)
            with st.expander("SQL"):
                st.code(sql, language="sql")
    except Exception as e:
        st.error(str(e))
```

---

## Day 12: SQL to Pandas (30 min)

```python
# day12_sql_to_pandas.py
from openai import OpenAI

client = OpenAI()

def sql_to_pandas(sql: str) -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """Convert SQL to pandas.
DataFrames: users_df, orders_df, products_df. Return only code."""},
            {"role": "user", "content": sql}
        ]
    ).choices[0].message.content

print(sql_to_pandas("""
SELECT country, COUNT(*) FROM users u JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed' GROUP BY country
"""))
```

---

## Day 13: Test Data Generator (45 min)

```python
# day13_test_data.py
from openai import OpenAI
from db import query
import json

client = OpenAI()

def generate_test_data(table: str, n: int = 100) -> str:
    schema = query("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns WHERE table_name = %s
    """, (table,))

    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Generate {n} INSERTs for {table}.
Schema: {json.dumps(schema, default=str)}
Realistic data, no 'test123'. Multi-row INSERT. Return only SQL."""}
        ]
    ).choices[0].message.content

print(generate_test_data("users", 1000)[:300])
```

---

## Day 14: WEEKEND — Add Auth + Deploy (3 hours)

Add Supabase Auth to Day 7's NL SQL app, save query history per user, custom domain.

---

## Day 15: Embeddings from Text (45 min)

```sql
-- Setup
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE products ADD COLUMN embedding vector(1536);
CREATE INDEX products_emb_idx ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

```python
# day15_embeddings.py
from openai import OpenAI
from db import query, get_db

client = OpenAI()

def get_embedding(text: str) -> list[float]:
    return client.embeddings.create(
        model="text-embedding-3-small", input=text
    ).data[0].embedding

def embed_products():
    products = query("SELECT id, name, category FROM products WHERE embedding IS NULL")
    with get_db() as conn:
        with conn.cursor() as cur:
            for p in products:
                emb = get_embedding(f"{p['name']} in {p['category']}")
                cur.execute("UPDATE products SET embedding = %s WHERE id = %s", (emb, p['id']))
    print(f"Embedded {len(products)} products")

embed_products()
```

---

## Day 16: Semantic Search (45 min)

```python
# day16_semantic_search.py
from openai import OpenAI
from db import query

client = OpenAI()

def get_embedding(text: str) -> list[float]:
    return client.embeddings.create(
        model="text-embedding-3-small", input=text
    ).data[0].embedding

def search(query_text: str, limit: int = 5):
    emb = get_embedding(query_text)
    return query("""
        SELECT id, name, category, price,
               1 - (embedding <=> %s::vector) as similarity
        FROM products
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (emb, emb, limit))

for r in search("warm winter clothing"):
    print(f"{r['similarity']:.3f}  {r['name']} (${r['price']})")
```

---

## Day 17: RAG over Schema (60 min)

```python
# day17_rag_docs.py
from openai import OpenAI
from db import query, get_db

client = OpenAI()

def create_docs_table():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS table_docs (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) UNIQUE,
                    content TEXT,
                    embedding vector(1536)
                )
            """)

def index_documentation():
    create_docs_table()
    tables = query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    with get_db() as conn:
        with conn.cursor() as cur:
            for t in tables:
                cols = query("""
                    SELECT column_name, data_type FROM information_schema.columns
                    WHERE table_name = %s
                """, (t['table_name'],))
                content = f"Table: {t['table_name']}\n" + "\n".join(
                    f"  - {c['column_name']} ({c['data_type']})" for c in cols
                )
                emb = client.embeddings.create(
                    model="text-embedding-3-small", input=content
                ).data[0].embedding
                cur.execute("""
                    INSERT INTO table_docs (table_name, content, embedding)
                    VALUES (%s, %s, %s) ON CONFLICT (table_name) DO UPDATE SET
                    content = EXCLUDED.content, embedding = EXCLUDED.embedding
                """, (t['table_name'], content, emb))

def ask(question: str) -> str:
    emb = client.embeddings.create(
        model="text-embedding-3-small", input=question
    ).data[0].embedding
    docs = query("""
        SELECT content FROM table_docs
        ORDER BY embedding <=> %s::vector LIMIT 3
    """, (emb,))
    context = "\n\n".join(d['content'] for d in docs)
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer based on schema docs:\n{context}\nIf not there, say so."},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content

index_documentation()
print(ask("Which table stores subscription plans?"))
```

---

## Day 18: Hybrid Search (60 min)

```python
# day18_hybrid_search.py
from openai import OpenAI
from db import query, get_db

client = OpenAI()

def setup():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE products
                ADD COLUMN IF NOT EXISTS search_vector tsvector
                GENERATED ALWAYS AS (
                    to_tsvector('english', coalesce(name,'') || ' ' || coalesce(category,''))
                ) STORED
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS products_search_idx ON products USING GIN(search_vector)")

def hybrid_search(q: str, limit: int = 10):
    emb = client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    return query("""
        WITH sem AS (
            SELECT id, name, category, price,
                   1-(embedding <=> %s::vector) as score
            FROM products
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector LIMIT 20
        ),
        kw AS (
            SELECT id, name, category, price,
                   ts_rank(search_vector, plainto_tsquery('english', %s)) as score
            FROM products
            WHERE search_vector @@ plainto_tsquery('english', %s)
            ORDER BY score DESC LIMIT 20
        )
        SELECT id, name, category, price, MAX(score) as best_score
        FROM (SELECT * FROM sem UNION ALL SELECT * FROM kw) t
        GROUP BY id, name, category, price
        ORDER BY best_score DESC LIMIT %s
    """, (emb, emb, q, q, limit))

setup()
for r in hybrid_search("warm jacket"):
    print(f"{r['best_score']:.3f}  {r['name']}")
```

---

## Day 19: Auto-Embed on Insert (45 min)

```python
# day19_auto_embed.py
from openai import OpenAI
from db import query, get_db

client = OpenAI()

def setup():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS embed_queue (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255),
                    row_id INTEGER,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)

def queue(table: str, row_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO embed_queue (table_name, row_id) VALUES (%s, %s)", (table, row_id))

def process_queue():
    pending = query("SELECT id, table_name, row_id FROM embed_queue WHERE NOT processed LIMIT 100")
    for item in pending:
        rows = query(f"SELECT name, category FROM {item['table_name']} WHERE id = %s", (item['row_id'],))
        if not rows:
            continue
        text = f"{rows[0]['name']} in {rows[0]['category']}"
        emb = client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE {item['table_name']} SET embedding = %s WHERE id = %s", (emb, item['row_id']))
                cur.execute("UPDATE embed_queue SET processed = TRUE WHERE id = %s", (item['id'],))

setup()
process_queue()
```

---

## Day 20: Vector Search UI (60 min)

```python
# day20_search_ui.py
import streamlit as st
from openai import OpenAI
from db import query

client = OpenAI()
st.title("🔍 Semantic Product Search")

q = st.text_input("Looking for:", "comfortable office chair")

if q:
    emb = client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    results = query("""
        SELECT name, category, price, inventory,
               1 - (embedding <=> %s::vector) as similarity
        FROM products WHERE embedding IS NOT NULL AND inventory > 0
        ORDER BY embedding <=> %s::vector LIMIT 12
    """, (emb, emb))

    cols = st.columns(3)
    for i, r in enumerate(results):
        with cols[i % 3]:
            st.markdown(f"### {r['name']}")
            st.write(f"${r['price']} · {r['category']}")
            st.progress(float(r['similarity']))
```

---

## Day 21: WEEKEND — Polish + Share (3 hours)

Add filters to Day 20's app. Deploy. Blog post. Twitter/HN post.

---

## Day 22: Multi-Table RAG (60 min)

```python
# day22_multi_table_rag.py
from openai import OpenAI
from db import query
import json

client = OpenAI()

def answer(question: str) -> dict:
    plan = json.loads(client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """Identify tables needed.
Tables: users(id,email,name,country,plan,created_at), orders(id,user_id,amount,product,status,created_at), products(id,name,category,price,inventory)
Return JSON: {"tables": [...], "reasoning": "..."}"""},
            {"role": "user", "content": question}
        ],
        response_format={"type": "json_object"}
    ).choices[0].message.content)

    sql = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Generate SQL using tables: {plan['tables']}. Return only SQL."},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content.strip()

    data = query(sql)
    answer = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer in plain English based on data."},
            {"role": "user", "content": f"Q: {question}\nData: {data}"}
        ]
    ).choices[0].message.content

    return {"answer": answer, "sql": sql, "data": data, "tables": plan['tables']}

print(answer("Which country has highest avg order value?")['answer'])
```

---

## Day 23: Result Summarizer (30 min)

```python
# day23_summarizer.py
from openai import OpenAI
from db import query

client = OpenAI()

def summarize(sql: str) -> str:
    data = query(sql)
    if not data:
        return "No results."
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Summarize in 2-3 sentences.
Key insights, outliers, patterns. Use specific numbers.
Data: {data[:50]} (Total: {len(data)} rows)"""}
        ]
    ).choices[0].message.content

print(summarize("SELECT country, COUNT(*) as n, AVG(amount) as avg FROM users u JOIN orders o ON u.id = o.user_id GROUP BY country"))
```

---

## Day 24: CSV to SQL (45 min)

```python
# day24_csv_to_sql.py
import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI()
st.title("📄 CSV to SQL")

f = st.file_uploader("CSV", type="csv")
table = st.text_input("Table name", "my_data")

if f and table:
    df = pd.read_csv(f)
    st.dataframe(df.head())
    schema = {c: ('INTEGER' if 'int' in str(df[c].dtype) else
                  'DECIMAL' if 'float' in str(df[c].dtype) else 'TEXT')
              for c in df.columns}
    st.write("Schema:", schema)

    if st.button("Generate SQL"):
        sql = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""Generate SQL:
1. CREATE TABLE {table} ({schema})
2. INSERT all {len(df)} rows from: {df.head(5).to_dict()}
Use parameterized inserts. Return only SQL."""}
            ]
        ).choices[0].message.content
        st.code(sql, language="sql")
```

---

## Day 25: Index Tuner (60 min)

```python
# day25_index_tuner.py
from openai import OpenAI
from db import query, get_db
import time

client = OpenAI()

def benchmark(idx_type: str, params: dict) -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS products_embedding_idx")
            if idx_type == 'ivfflat':
                cur.execute(f"CREATE INDEX products_embedding_idx ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = {params['lists']})")
            else:
                cur.execute(f"CREATE INDEX products_embedding_idx ON products USING hnsw (embedding vector_cosine_ops) WITH (m = {params['m']}, ef_construction = {params['ef_construction']})")
    emb = client.embeddings.create(model="text-embedding-3-small", input="test").data[0].embedding
    start = time.time()
    for _ in range(100):
        query("SELECT id FROM products ORDER BY embedding <=> %s::vector LIMIT 10", (emb,))
    return {"type": idx_type, "params": params, "ms": (time.time()-start)/100*1000}

for cfg in [('ivfflat', {'lists': 10}), ('ivfflat', {'lists': 100}),
            ('hnsw', {'m': 16, 'ef_construction': 64}),
            ('hnsw', {'m': 32, 'ef_construction': 128})]:
    r = benchmark(*cfg)
    print(f"{r['type']} {r['params']}: {r['ms']:.2f}ms")
```

---

## Day 26: Embedding Drift Detector (60 min)

```python
# day26_drift_detector.py
from db import query
import numpy as np
from scipy import stats

def centroid(table: str) -> np.ndarray:
    rows = query(f"SELECT embedding::text as e FROM {table} WHERE embedding IS NOT NULL LIMIT 1000")
    return np.array([[float(x) for x in r['e'].strip('[]').split(',')] for r in rows]).mean(axis=0)

# Setup: np.save("baseline.npy", centroid("products"))
baseline = np.load("baseline.npy")
current = centroid("products")
distance = np.linalg.norm(current - baseline)
ks, p = stats.ks_2samp(current, baseline)
print(f"Drift distance: {distance:.4f}, p-value: {p:.4f}")
if p < 0.05:
    print("⚠️ Drift detected! Re-embed everything.")
```

---

## Day 27: RAG with Citations (60 min)

```python
# day27_rag_citations.py
from openai import OpenAI
from db import query

client = OpenAI()

def answer(question: str) -> dict:
    emb = client.embeddings.create(model="text-embedding-3-small", input=question).data[0].embedding
    products = query("""
        SELECT id, name, category, price, 1-(embedding <=> %s::vector) as score
        FROM products WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector LIMIT 5
    """, (emb, emb))
    sources = [{"content": f"{p['name']} ({p['category']}, ${p['price']})", "score": p['score']} for p in products]
    context = "\n".join(f"[{i+1}] {s['content']}" for i, s in enumerate(sources))
    answer = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer using sources. Cite [number] inline.\n\n{context}"},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content
    return {"answer": answer, "sources": sources}

r = answer("Most expensive item?")
print(r['answer'])
for s in r['sources']:
    print(f"  {s['content']} ({s['score']:.2f})")
```

---

## Day 28: WEEKEND — RAG Evaluation (3 hours)

Build a RAGAS-style eval harness with a test set of 20+ Q&A pairs, auto-scoring, tracking over time.

---

## Day 29: Multi-Language SQL (45 min)

```python
# day29_multilang.py
from openai import OpenAI

LANGS = {"es": "Spanish", "fr": "French", "de": "German", "ja": "Japanese", "zh": "Chinese"}

def multilingual_sql(question: str, lang: str) -> str:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""User asks in {LANGS.get(lang, lang)}.
Translate to English, generate SQL. Schema: users, orders, products. Return only SQL."""},
            {"role": "user", "content": question}
        ]
    ).choices[0].message.content

for q in ["¿Cuántos usuarios este mes?", "Combien d'utilisateurs?", "今月のユーザー数？"]:
    print(multilingual_sql(q, "es" if "¿" in q else "fr" if "Combien" in q else "ja"))
```

---

## Day 30: MONTH PROJECT — NL SQL Assistant v1 (6 hours)

Build the full product:
- Streamlit frontend
- FastAPI backend
- Supabase auth
- Multi-table RAG
- Visualization
- Query history
- Deploy to Railway

Share publicly. Apply to YC (optional).

---

## Month 1 Summary

**Built:** 30 projects · 1 deployed SaaS · 1 portfolio piece
**Time:** ~25 hours over 30 days
**Cost:** ~$5 in API fees

**Next:** Month 2 — AI + REST APIs. 30 more projects, harder concepts, real webhooks and OAuth.
