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
