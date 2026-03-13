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
    "automobile repair guide",       # → should match car maintenance
    "AI and deep neural networks",   # → should match ML docs
    "coding tutorial for beginners", # → should match Python docs
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
