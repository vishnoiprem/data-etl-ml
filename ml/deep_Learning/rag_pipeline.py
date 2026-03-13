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

    print(f"\n Question: {question}")
    print(f"\n Retrieved Context ({len(context_chunks)} chunks):")
    for i, chunk in enumerate(context_chunks, 1):
        print(f"  [{i}] {chunk[:80]}...")
    print(f"\n Answer: {response.choices[0].message.content}")

# ── Run ──
ask_rag("What causes ERR-503 errors and how do I fix them?")