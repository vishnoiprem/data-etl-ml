# From TF-IDF to Embeddings: The Complete Guide to Information Retrieval, Semantic Search & Hybrid Search

*Boolean models, vector spaces, tokenization, word embeddings, and the hybrid architectures powering modern search — explained with working Python code you can run today.*

**Published Mar 10, 2026 · 26 min read**

---

Every time you type a query into Google, filter products on Amazon, or ask ChatGPT a question, you're triggering an **information retrieval** pipeline. What happens between your keystrokes and the ranked results is one of the most fascinating problems in computer science — and it's evolved dramatically over the past 50 years.

In this article, we'll walk the entire journey: from classical Boolean retrieval through TF-IDF and the Vector Space Model, into modern embedding-based semantic search, and finally to the hybrid architectures that power production systems today. Every concept comes with working Python code and architecture diagrams.

Let's start at the beginning.

---

## Part I: Traditional Information Retrieval

Traditional IR systems answer one fundamental question: *given a query, which documents in my collection are relevant?* The two foundational models that shaped decades of search technology are the **Boolean Model** and the **Vector Space Model (VSM)**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE IR LANDSCAPE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    🔍  User Query                               │
│          "machine learning python tutorial"                     │
│                         │                                       │
│          ┌──────────────┼──────────────────┐                   │
│          │              │                  │                    │
│    ┌─────▼─────┐  ┌─────▼─────┐  ┌────────▼────────┐          │
│    │  Boolean   │  │  TF-IDF   │  │    Semantic     │          │
│    │  Model     │  │   / VSM   │  │    Search       │          │
│    │ AND/OR/NOT │  │  Cosine   │  │  Embeddings     │          │
│    │ Binary     │  │  Ranking  │  │  Neural kNN     │          │
│    └─────┬─────┘  └─────┬─────┘  └────────┬────────┘          │
│          │              │                  │                    │
│          └──────────────┼──────────────────┘                   │
│                         │                                       │
│                    ⚡ Hybrid Search                             │
│               (Reciprocal Rank Fusion)                          │
│                         │                                       │
│                    📄 Ranked Results                            │
└─────────────────────────────────────────────────────────────────┘
```

### The Boolean Model

The Boolean Model is the simplest and oldest retrieval model. Documents are either *relevant* or *not relevant* — there's no ranking. Queries use logical operators: `AND`, `OR`, and `NOT`.

If you search `python AND machine learning NOT java`, the system returns every document that contains both "python" and "machine learning" but not "java." No scoring. No ordering. Just a set.

**boolean_model.py**

```python
# ── Boolean Retrieval Model from Scratch ──

# Sample document corpus
documents = {
    1: "Python is great for machine learning and data science",
    2: "Java is widely used in enterprise applications",
    3: "Machine learning with Python and TensorFlow",
    4: "Data science requires statistics and programming",
    5: "Java and Python are both popular programming languages",
}

# ── Step 1: Build the inverted index ──
from collections import defaultdict

def build_inverted_index(docs):
    """Map each term to the set of document IDs containing it."""
    index = defaultdict(set)
    for doc_id, text in docs.items():
        tokens = text.lower().split()
        for token in tokens:
            index[token].add(doc_id)
    return index

inv_index = build_inverted_index(documents)

# ── Step 2: Boolean query engine ──
def boolean_search(query, index, all_docs):
    """
    Supports: AND, OR, NOT
    Example: 'python AND machine NOT java'
    """
    tokens = query.lower().split()
    result = None
    operation = "or"    # default combiner
    negate = False

    for token in tokens:
        if token == "and":
            operation = "and"; continue
        elif token == "or":
            operation = "or"; continue
        elif token == "not":
            negate = True; continue

        term_docs = index.get(token, set())
        if negate:
            term_docs = all_docs - term_docs
            negate = False

        if result is None:
            result = term_docs
        elif operation == "and":
            result = result & term_docs
        else:
            result = result | term_docs

    return result or set()

# ── Test queries ──
all_doc_ids = set(documents.keys())

q1 = "python AND machine"
q2 = "python AND machine NOT java"
q3 = "java OR data"

for q in [q1, q2, q3]:
    results = boolean_search(q, inv_index, all_doc_ids)
    print(f"Query: '{q}'")
    print(f"  Docs: {sorted(results)}")
    for doc_id in sorted(results):
        print(f"    [{doc_id}] {documents[doc_id]}")
    print()

# Output:
# Query: 'python AND machine'
#   Docs: [1, 3]
#     [1] Python is great for machine learning and data science
#     [3] Machine learning with Python and TensorFlow
```

> 💡 **Limitation:** The Boolean Model has no concept of ranking. A document with "machine learning" mentioned 50 times is treated exactly the same as one that mentions it once. That's where TF-IDF and the Vector Space Model come in.

---

### The Vector Space Model & TF-IDF

The Vector Space Model (VSM) transforms both documents and queries into vectors in a high-dimensional space, where each dimension represents a unique term. The weight of each dimension is computed using **TF-IDF**.

```
┌───────────────────────────────────────────────┐
│              TF-IDF FORMULA                    │
│                                                │
│   TF-IDF(t, d) = TF(t, d) × IDF(t)          │
│                                                │
│   TF(t, d)  = count(t in d) / total terms in d│
│   IDF(t)    = log( N / df(t) )                │
│                                                │
│   N   = total number of documents              │
│   df  = number of documents containing term t  │
└───────────────────────────────────────────────┘
```

**Term Frequency (TF)** measures how often a term appears in a specific document — more frequent means more important to that document. **Inverse Document Frequency (IDF)** penalizes terms that appear in many documents — common words like "the" get low scores, while rare words like "TensorFlow" get high scores.

**tfidf_vsm.py**

```python
import math
from collections import Counter

# ── Same corpus ──
documents = {
    1: "Python is great for machine learning and data science",
    2: "Java is widely used in enterprise applications",
    3: "Machine learning with Python and TensorFlow",
    4: "Data science requires statistics and programming",
    5: "Java and Python are both popular programming languages",
}

# ── Tokenize ──
def tokenize(text):
    return text.lower().split()

corpus = {doc_id: tokenize(text) for doc_id, text in documents.items()}
N = len(corpus)

# ── Build vocabulary ──
vocab = sorted(set(word for tokens in corpus.values() for word in tokens))
print(f"Vocabulary size: {len(vocab)} terms\n")

# ── Compute TF ──
def compute_tf(tokens):
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}

# ── Compute IDF ──
def compute_idf(corpus, vocab):
    idf = {}
    for term in vocab:
        df = sum(1 for tokens in corpus.values() if term in tokens)
        idf[term] = math.log(N / df) if df > 0 else 0
    return idf

idf = compute_idf(corpus, vocab)

# ── Compute TF-IDF vectors ──
def tfidf_vector(tokens, idf, vocab):
    tf = compute_tf(tokens)
    return [tf.get(term, 0) * idf.get(term, 0) for term in vocab]

doc_vectors = {doc_id: tfidf_vector(tokens, idf, vocab)
               for doc_id, tokens in corpus.items()}

# ── Cosine similarity ──
def cosine_sim(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a**2 for a in v1))
    mag2 = math.sqrt(sum(b**2 for b in v2))
    return dot / (mag1 * mag2) if mag1 and mag2 else 0

# ── Search with ranking ──
def search_vsm(query, doc_vectors, idf, vocab):
    query_tokens = tokenize(query)
    query_vec = tfidf_vector(query_tokens, idf, vocab)

    scores = {}
    for doc_id, doc_vec in doc_vectors.items():
        scores[doc_id] = cosine_sim(query_vec, doc_vec)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# ── Test ──
query = "machine learning python"
results = search_vsm(query, doc_vectors, idf, vocab)

print(f"Query: '{query}'\n")
print("Ranked Results:")
for doc_id, score in results:
    if score > 0:
        print(f"  [{doc_id}] score: {score:.4f} → {documents[doc_id]}")

# Output:
# Query: 'machine learning python'
# Ranked Results:
#   [3] score: 0.8914 → Machine learning with Python and TensorFlow
#   [1] score: 0.7632 → Python is great for machine learning and data science
#   [5] score: 0.1847 → Java and Python are both popular programming languages
```

> 📐 **Key insight:** Unlike the Boolean Model, the VSM *ranks* documents by similarity. Document 3 scores higher than Document 1 because "machine," "learning," and "Python" are more concentrated relative to its length.

---

### Regex Search & Fuzzy Search

**Regex Search** uses pattern matching for complex text patterns. **Fuzzy Search** handles typos using edit distance (Levenshtein distance).

**regex_fuzzy_search.py**

```python
import re

# ── Regex Search ──
texts = [
    "Contact us at support@company.com for help",
    "Meeting scheduled for 2026-03-15 at 10am",
    "Error code: ERR-404-TIMEOUT in module alpha",
    "Send feedback to feedback@company.com",
]

# Find all email addresses
email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
print("📧 Emails found:")
for i, text in enumerate(texts):
    matches = email_pattern.findall(text)
    if matches:
        print(f"  Doc {i}: {matches}")

# Find dates in YYYY-MM-DD format
date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
print("\n📅 Dates found:")
for i, text in enumerate(texts):
    matches = date_pattern.findall(text)
    if matches:
        print(f"  Doc {i}: {matches}")

# ── Fuzzy Search (Levenshtein Distance) ──
def levenshtein(s1, s2):
    """Compute minimum edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]

# Fuzzy search with threshold
def fuzzy_search(query, vocab, max_distance=2):
    matches = []
    for term in vocab:
        dist = levenshtein(query.lower(), term.lower())
        if dist <= max_distance:
            matches.append((term, dist))
    return sorted(matches, key=lambda x: x[1])

vocabulary = ["machine", "learning", "python", "programming",
              "tensorflow", "statistics", "science"]

print("\n🔍 Fuzzy search for 'machin lerning':")
for term in ["machin", "lerning"]:
    results = fuzzy_search(term, vocabulary)
    print(f"  '{term}' → {results}")

# Output:
# 🔍 Fuzzy search for 'machin lerning':
#   'machin' → [('machine', 1)]
#   'lerning' → [('learning', 1)]
```

---

## Part II: Semantic Search With Embeddings

Traditional IR has a fundamental blind spot: it matches **words**, not **meaning**. Search "automobile repair guide" and a TF-IDF system won't find a document titled "car maintenance manual" — even though they mean the same thing.

Semantic search solves this by representing both queries and documents as **dense vector embeddings** — numerical arrays that capture meaning.

```
┌─────────────────────────────────────────────────────────────────┐
│         VECTOR REPRESENTATIONS: TF-IDF vs EMBEDDINGS           │
├────────────────────────────┬────────────────────────────────────┤
│  📐 TF-IDF Vector (Sparse) │  🧠 Embedding Vector (Dense)      │
│                            │                                    │
│  "machine learning python" │  "machine learning python"         │
│                            │                                    │
│  [0, 0, 0, 0.32, 0, 0.41, │  [0.234, -0.891, 0.456, -0.123,  │
│   0, 0, 0, 0, 0, 0.38, 0, │   0.789, -0.345, 0.567, -0.234,  │
│   0, 0.29, 0, 0, 0, 0, 0, │   0.891, -0.678, 0.112, ...]     │
│   0, 0, 0, 0, 0, 0 ... ]  │                                    │
│                            │  Dimensions: 384–1536              │
│  Dimensions: 10,000+       │  Every value non-zero (dense)      │
│  Mostly zeros (sparse)     │  Captures meaning & context        │
│  No semantic understanding │  "car" ≈ "automobile"              │
└────────────────────────────┴────────────────────────────────────┘
```

### The Embedding Pipeline

```
Raw Text → Tokenizer (WordPiece/BPE) → Transformer (BERT/MiniLM) → Embedding [0.23, -0.89, ...]
```

**semantic_search.py**

```python
# pip install sentence-transformers numpy
from sentence_transformers import SentenceTransformer
import numpy as np

# ── Load a pre-trained embedding model ──
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim embeddings, very fast

# ── Document corpus ──
documents = [
    "Python is great for machine learning and data science",
    "Java is widely used in enterprise applications",
    "Machine learning with Python and TensorFlow",
    "How to fix and maintain your automobile",
    "Car maintenance tips and repair manual",
    "Deep learning neural networks explained",
    "Introduction to artificial intelligence concepts",
]

# ── Encode all documents into embeddings ──
doc_embeddings = model.encode(documents, show_progress_bar=True)
print(f"Embedding shape: {doc_embeddings.shape}")
# → (7, 384) — 7 documents, 384 dimensions each

# ── Semantic search function ──
def semantic_search(query, doc_embeddings, documents, top_k=5):
    """Encode query → compute cosine similarity → rank."""
    query_embedding = model.encode([query])

    # Cosine similarity = dot product of normalized vectors
    similarities = np.dot(doc_embeddings, query_embedding.T).flatten()

    # Rank by descending similarity
    ranked_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in ranked_indices:
        results.append({
            "document": documents[idx],
            "score":    float(similarities[idx]),
        })
    return results

# ── Test: semantic understanding! ──
queries = [
    "automobile repair guide",        # → should match car maintenance
    "AI and deep neural networks",    # → should match ML docs
    "coding tutorial for beginners",  # → should match Python docs
]

for q in queries:
    print(f"\n🔍 Query: '{q}'")
    for r in semantic_search(q, doc_embeddings, documents, top_k=3):
        print(f"  score: {r['score']:.4f} → {r['document']}")

# Output:
# 🔍 Query: 'automobile repair guide'
#   score: 0.7832 → Car maintenance tips and repair manual
#   score: 0.7156 → How to fix and maintain your automobile
#   score: 0.0921 → Java is widely used in enterprise applications
```

> 🧠 **This is the magic moment.** The query "automobile repair guide" matched "Car maintenance tips and repair manual" with a score of 0.78 — even though they share *zero words in common*. TF-IDF would score this as 0.00.

---

## Vocabulary & Tokenization

Before any retrieval model can process text, raw strings must be broken into tokens. Here's how the major strategies compare:

| Method | How It Works | Example: "unhappiness" | Used By |
|---|---|---|---|
| **Whitespace** | Split on spaces | ["unhappiness"] | Simple IR systems |
| **Word-level** | Split on spaces + punctuation | ["unhappiness"] | NLTK, SpaCy |
| **Stemming** | Reduce to word root (heuristic) | ["unhappi"] | Elasticsearch, Solr |
| **Lemmatization** | Reduce to dictionary form | ["unhappy"] | SpaCy, NLP pipelines |
| **BPE (Byte-Pair)** | Merge frequent character pairs | ["un", "happiness"] | GPT-4, LLaMA |
| **WordPiece** | Subword units maximizing likelihood | ["un", "##happi", "##ness"] | BERT, Sentence-Transformers |
| **SentencePiece** | Language-agnostic subword tokenizer | ["▁un", "happi", "ness"] | T5, mBART |

**tokenization_demo.py**

```python
# pip install transformers nltk
from transformers import AutoTokenizer
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer

nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

text = "The unhappiness of running machines learning algorithms"

# ── 1. Whitespace tokenization ──
ws_tokens = text.split()
print(f"Whitespace : {ws_tokens}")

# ── 2. NLTK word tokenization ──
word_tokens = nltk.word_tokenize(text)
print(f"NLTK       : {word_tokens}")

# ── 3. Stemming (Porter) ──
stemmer = PorterStemmer()
stems = [stemmer.stem(t) for t in word_tokens]
print(f"Stemmed    : {stems}")

# ── 4. Lemmatization ──
lemmatizer = WordNetLemmatizer()
lemmas = [lemmatizer.lemmatize(t) for t in word_tokens]
print(f"Lemmatized : {lemmas}")

# ── 5. BERT WordPiece tokenization ──
bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
bert_tokens = bert_tokenizer.tokenize(text)
print(f"BERT       : {bert_tokens}")

# ── 6. GPT-2 BPE tokenization ──
gpt_tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
gpt_tokens = gpt_tokenizer.tokenize(text)
print(f"GPT-2 BPE  : {gpt_tokens}")

# Output:
# Whitespace : ['The', 'unhappiness', 'of', 'running', 'machines', 'learning', 'algorithms']
# NLTK       : ['The', 'unhappiness', 'of', 'running', 'machines', 'learning', 'algorithms']
# Stemmed    : ['the', 'unhappi', 'of', 'run', 'machin', 'learn', 'algorithm']
# Lemmatized : ['The', 'unhappiness', 'of', 'running', 'machine', 'learning', 'algorithm']
# BERT       : ['the', 'un', '##happi', '##ness', 'of', 'running', 'machines', 'learning', 'algorithms']
# GPT-2 BPE  : ['The', 'Ġun', 'happiness', 'Ġof', 'Ġrunning', 'Ġmachines', 'Ġlearning', 'Ġalgorithms']
```

---

## Part III: Hybrid Search — Best of Both Worlds

Here's the uncomfortable truth: **neither keyword search nor semantic search is sufficient alone.**

Keyword search (TF-IDF/BM25) excels at exact matching — product SKUs, error codes, proper nouns. But it fails on synonyms. Semantic search excels at understanding meaning but can miss exact matches and struggles with rare technical terms.

Hybrid search combines both, typically using **Reciprocal Rank Fusion (RRF)**.

```
┌──────────────────────────────────────────────────────────────┐
│               HYBRID SEARCH ARCHITECTURE                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│               🔍 User Query                                   │
│  "ERR-503 timeout in authentication service"                  │
│                    │                                          │
│         ┌──────────┴──────────┐                              │
│         │                     │                               │
│  ┌──────▼───────┐     ┌──────▼───────┐                      │
│  │  BM25/TF-IDF │     │   Semantic   │                      │
│  │   Pipeline   │     │   Pipeline   │                      │
│  │              │     │              │                      │
│  │ Exact match  │     │ "timeout" ≈  │                      │
│  │ on "ERR-503" │     │ "latency"    │                      │
│  └──────┬───────┘     └──────┬───────┘                      │
│         │                     │                               │
│  Rank: [42,17,8]       Rank: [17,5,42]                      │
│         │                     │                               │
│         └──────────┬──────────┘                              │
│                    │                                          │
│         ┌──────────▼──────────┐                              │
│         │  Reciprocal Rank   │                               │
│         │  Fusion (RRF)      │                               │
│         │                    │                               │
│         │  score(d) = Σ 1/(k + rank_i(d))                   │
│         └──────────┬──────────┘                              │
│                    │                                          │
│              ⚡ Merged Results                                │
│         [doc_17, doc_42, doc_5, doc_8]                       │
└──────────────────────────────────────────────────────────────┘
```

**hybrid_search.py**

```python
# pip install sentence-transformers numpy rank-bm25
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

# ── Document corpus ──
documents = [
    "ERR-503 gateway timeout error in production server",
    "Authentication service experiencing high latency",
    "How to debug timeout issues in microservices",
    "Python tutorial for machine learning beginners",
    "ERR-503 connection refused by upstream service",
    "Network latency troubleshooting best practices",
    "Introduction to REST API design patterns",
]

# ── Pipeline 1: BM25 Keyword Search ──
tokenized_docs = [doc.lower().split() for doc in documents]
bm25 = BM25Okapi(tokenized_docs)

def bm25_search(query, top_k=5):
    scores = bm25.get_scores(query.lower().split())
    ranked = np.argsort(scores)[::-1][:top_k]
    return [(idx, scores[idx]) for idx in ranked if scores[idx] > 0]

# ── Pipeline 2: Semantic Search ──
model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = model.encode(documents)

def semantic_search_pipeline(query, top_k=5):
    q_emb = model.encode([query])
    sims = np.dot(doc_embeddings, q_emb.T).flatten()
    ranked = np.argsort(sims)[::-1][:top_k]
    return [(idx, sims[idx]) for idx in ranked]

# ── Reciprocal Rank Fusion ──
def reciprocal_rank_fusion(rankings_list, k=60):
    """
    Merge multiple ranked lists using RRF.
    RRF_score(d) = Σ  1 / (k + rank_i(d))
    """
    rrf_scores = {}
    for rankings in rankings_list:
        for rank, (doc_idx, _) in enumerate(rankings):
            if doc_idx not in rrf_scores:
                rrf_scores[doc_idx] = 0.0
            rrf_scores[doc_idx] += 1.0 / (k + rank + 1)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

# ── Hybrid Search ──
def hybrid_search(query, top_k=5):
    print(f"\n{'='*60}")
    print(f"🔍 Hybrid Search: '{query}'")
    print(f"{'='*60}")

    # Run both pipelines
    bm25_results = bm25_search(query, top_k)
    sem_results = semantic_search_pipeline(query, top_k)

    print(f"\n📋 BM25 Results:")
    for idx, score in bm25_results:
        print(f"  [{score:.3f}] {documents[idx]}")

    print(f"\n🧠 Semantic Results:")
    for idx, score in sem_results[:top_k]:
        print(f"  [{score:.3f}] {documents[idx]}")

    # Fuse with RRF
    fused = reciprocal_rank_fusion([bm25_results, sem_results])

    print(f"\n⚡ Hybrid (RRF) Results:")
    for doc_idx, rrf_score in fused[:top_k]:
        print(f"  [RRF: {rrf_score:.4f}] {documents[doc_idx]}")

# ── Run it ──
hybrid_search("ERR-503 timeout in authentication service")
hybrid_search("how to fix slow API response times")
```

> ⚡ **Why RRF works:** Reciprocal Rank Fusion doesn't care about raw scores — it only uses rank positions. A document ranked #1 in both pipelines gets the highest RRF score. This is robust across different scoring scales without needing normalization.

---

### Real-World Hybrid Search Applications

| Application | Keyword Component | Semantic Component | Why Hybrid |
|---|---|---|---|
| **E-Commerce** | SKU, brand name, exact ID | "comfortable shoes" → intent | Users search by SKU *and* description |
| **Legal Discovery** | Case numbers, statute citations | "breach of duty" → precedents | Exact citations + conceptual relevance |
| **Medical Records** | ICD codes, drug names | "chest pain" → related diagnoses | Coded data + clinical narrative |
| **Log Analytics** | Error codes, timestamps | "connection failing" → timeouts | Structured + unstructured logs |
| **RAG Chatbots** | Keyword extraction | Dense retrieval of context | Precision on entities + recall on concepts |

---

## Part IV: How LLMs Redefine Search

Large Language Models have changed search in three fundamental ways:

**1. Retrieval-Augmented Generation (RAG).** Instead of returning document links, the system retrieves passages, feeds them to an LLM, and generates a direct answer.

**2. Better Embeddings.** LLM-derived models produce dramatically better semantic representations that understand nuance, negation, and domain-specific terminology.

**3. Query Understanding.** LLMs can rewrite vague queries into precise retrieval queries before they hit the index.

```
┌──────────────────────────────────────────────────────────────┐
│         RAG (Retrieval-Augmented Generation) Pipeline        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│    User: "What causes ERR-503 in our auth service?"          │  
│                        │                                     │
│              ┌─────────▼─────────┐                           │
│              │  STEP 1: RETRIEVE │                           │
│              │  Hybrid Search    │                           │
│              │  ES (BM25) +      │                           │
│              │  Milvus (kNN)     │                           │
│              └─────────┬─────────┘                           │
│                        │                                     │
│              ┌─────────▼─────────┐                           │
│              │  STEP 2: AUGMENT  │                           │
│              │  Top 5 passages   │                           │
│              │  injected into    │                           │
│              │  LLM prompt       │                           │
│              └─────────┬─────────┘                           │
│                        │                                     │
│              ┌─────────▼─────────┐                           │
│              │  STEP 3: GENERATE │                           │
│              │  GPT-4 / Claude   │                           │
│              │  Grounded answer  │                           │
│              └─────────┬─────────┘                           │
│                        │                                     │
│       "ERR-503 occurs when the auth service upstream         │
│       connection pool is exhausted. Common fixes..."         │
└──────────────────────────────────────────────────────────────┘
```

**rag_pipeline.py**

```python
# pip install openai sentence-transformers numpy rank-bm25
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

# ── Knowledge base (your documents) ──
knowledge_base = [
    "ERR-503 occurs when the upstream service is unreachable. Common causes include connection pool exhaustion and DNS resolution failures.",
    "The authentication service uses OAuth 2.0 with JWT tokens. Timeout errors typically indicate the token validation endpoint is overloaded.",
    "To scale the auth service, increase the connection pool size in config.yaml and add read replicas to the user database.",
    "Gateway timeout errors (503) can be mitigated by implementing circuit breakers using libraries like resilience4j or Polly.",
    "Monitoring auth service health: set up alerts on p99 latency > 500ms and error rate > 1% using Prometheus and Grafana.",
]

# ── Build retrieval pipelines ──
# BM25
tokenized_kb = [doc.lower().split() for doc in knowledge_base]
bm25 = BM25Okapi(tokenized_kb)

# Semantic
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
kb_embeddings = embed_model.encode(knowledge_base)

def retrieve_context(query, top_k=3):
    """Hybrid retrieval using RRF."""
    # BM25 ranking
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_ranked = [(i, bm25_scores[i]) for i in np.argsort(bm25_scores)[::-1]]

    # Semantic ranking
    q_emb = embed_model.encode([query])
    sims = np.dot(kb_embeddings, q_emb.T).flatten()
    sem_ranked = [(i, sims[i]) for i in np.argsort(sims)[::-1]]

    # RRF fusion
    rrf = {}
    for rankings in [bm25_ranked, sem_ranked]:
        for rank, (idx, _) in enumerate(rankings):
            rrf[idx] = rrf.get(idx, 0) + 1 / (60 + rank + 1)

    top_indices = [idx for idx, _ in sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]]
    return [knowledge_base[i] for i in top_indices]

# ── RAG: Retrieve + Generate ──
def ask_rag(question):
    # Step 1: Retrieve relevant context
    context_chunks = retrieve_context(question)
    context = "\n\n".join(context_chunks)

    # Step 2: Generate answer with LLM
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""You are a helpful assistant. Answer ONLY based on the provided context. If the context doesn't contain the answer, say so.

Context:
{context}"""},
            {"role": "user", "content": question}
        ],
        temperature=0.1,
    )

    print(f"\n💬 Question: {question}")
    print(f"\n📄 Retrieved Context ({len(context_chunks)} chunks):")
    for i, chunk in enumerate(context_chunks, 1):
        print(f"  [{i}] {chunk[:80]}...")
    print(f"\n🤖 Answer: {response.choices[0].message.content}")

# ── Run ──
ask_rag("What causes ERR-503 errors and how do I fix them?")
```

---

## The Complete Comparison

| Dimension                | Boolean       | TF-IDF / BM25   | Semantic       | Hybrid             |
|--------------------------|---------------|-----------------|----------------|--------------------|
| **Vector Type**          | Binary (0/1)  | Sparse, high-dim | Dense, low-dim | Both               |
| **Understands Synonyms** | No            | No              | Yes            | Yes                |
| **Exact Match**          | Perfect       | Good            | ️ Weak         | Good               |
| **Ranking**              | None          | TF-IDF score    | Cosine sim     | RRF fusion         |
| **Speed**                | Very fast     |  Fast           | Slower (kNN)   |  Balanced          |
| **Storage**              | Low           | Medium          | High (vectors) | High               |
| **Best For**             | Exact filters | Keyword search  | Concept search | Production systems |

---

## Final Thoughts

Information retrieval has evolved from simple set operations (Boolean) through statistical term weighting (TF-IDF) into neural semantic understanding (embeddings) — and the cutting edge combines all of these in hybrid architectures powered by LLMs.

The key takeaway: **there's no single "best" approach.** Every production search system uses multiple retrieval strategies working together. BM25 handles the precision. Embeddings handle the recall. RRF merges the signals. And increasingly, an LLM sits on top to synthesize the answer.

The code in this article runs on your laptop. Clone it. Break it. Rebuild it. That's how you learn search.

---

*Tags: Information Retrieval · NLP · TF-IDF · Embeddings · Semantic Search · Hybrid Search · RAG · Elasticsearch · Vector Database · Python · LLMs*

---

*If this helped you, follow for more deep dives on search, NLP, and data engineering. I publish weekly.*
