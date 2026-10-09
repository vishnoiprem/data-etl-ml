"""
Lesson 4.5: Building RAG from Scratch
======================================
A 100-line RAG system. No frameworks -- just openai and numpy.

Run:  export OPENAI_API_KEY=sk-...
       python lesson-4-5-rag-from-scratch.py

Requires: pip install openai numpy
"""

import os
import time
import numpy as np
from openai import OpenAI


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"   # 1536 dimensions, $0.02/1M tokens
LLM_MODEL = "gpt-4o-mini"                     # cheap + smart
TOP_K = 3                                      # how many chunks to retrieve
EMBED_DIM = 1536                               # text-embedding-3-small dim


# =============================================================================
# SAMPLE DOCUMENTS -- In production, load from a database
# =============================================================================

DOCUMENTS = [
    "Our company offers a 30-day money-back guarantee on all products.",
    "Shipping is free for orders over $50. Standard shipping takes 3-5 business days.",
    "To cancel a subscription, go to Account Settings > Subscriptions and click Cancel.",
    "Refund requests are processed within 5-7 business days after we receive the item.",
    "We accept Visa, Mastercard, American Express, and PayPal.",
    "Customer support is available 24/7 via email and live chat.",
    "Bulk orders of $500+ receive a 10% discount automatically at checkout.",
    "Returns must be in original packaging with all tags attached.",
    "Account deletion is permanent and removes all associated data within 30 days.",
    "Two-factor authentication is available and recommended for all accounts.",
    "Premium members get early access to sales and exclusive product launches.",
    "International shipping rates are calculated at checkout based on destination.",
]


# =============================================================================
# STARTER (TODOs) -- Implement these functions
# =============================================================================

def get_embedding(client: OpenAI, text: str) -> list[float]:
    """TODO: Call OpenAI embeddings API and return the vector.
    Hint: client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    """
    pass


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """TODO: Compute cosine similarity between two vectors.
    Hint: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    """
    pass


def retrieve(client: OpenAI, query: str, doc_embeddings: list, top_k: int = TOP_K) -> list:
    """TODO: Embed the query, compute similarity to all docs, return top_k.
    Each result should be: (document_text, similarity_score)
    """
    pass


def generate_answer(client: OpenAI, question: str, context_docs: list) -> str:
    """TODO: Call gpt-4o-mini with the question + context docs as a system prompt.
    Hint: Pass context_docs as bullet points in the system message.
    """
    pass


# =============================================================================
# SOLUTION -- Complete, runnable version
# =============================================================================

def get_embedding_solution(client: OpenAI, text: str) -> list[float]:
    """Embed text using OpenAI's embedding model."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def cosine_similarity_solution(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_np, b_np = np.array(a), np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


def retrieve_solution(client: OpenAI, query: str, doc_embeddings: list, top_k: int = TOP_K) -> list:
    """Retrieve top-k most similar documents to the query."""
    query_emb = get_embedding_solution(client, query)
    scored = [
        (doc_text, cosine_similarity_solution(query_emb, doc_emb))
        for doc_text, doc_emb in doc_embeddings
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def generate_answer_solution(client: OpenAI, question: str, context_docs: list) -> str:
    """Generate an answer using the LLM with retrieved context."""
    context_str = "\n".join(f"- {doc}" for doc, _ in context_docs)
    system_prompt = (
        "You are a helpful customer support assistant. "
        "Answer the user's question using ONLY the context below. "
        "If the answer is not in the context, say 'I don't know based on our docs.'\n\n"
        f"Context:\n{context_str}"
    )
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


# =============================================================================
# RAG PIPELINE -- The orchestrator
# =============================================================================

class SimpleRAG:
    """A complete RAG system in <100 lines of code."""

    def __init__(self, documents: list[str]):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.documents = documents
        # Pre-compute embeddings for all documents (one-time cost)
        print(f"  Embedding {len(documents)} documents...")
        self.doc_embeddings = [
            (doc, get_embedding_solution(self.client, doc))
            for doc in documents
        ]
        print(f"  Done. {len(self.doc_embeddings)} documents indexed.\n")

    def query(self, question: str) -> dict:
        """Run the full RAG pipeline: retrieve, then generate."""
        start_time = time.time()

        # Step 1: Retrieve top-k similar documents
        retrieved = retrieve_solution(self.client, question, self.doc_embeddings, top_k=TOP_K)

        # Step 2: Generate answer using retrieved context
        answer = generate_answer_solution(self.client, question, retrieved)

        elapsed = time.time() - start_time

        return {
            "question": question,
            "answer": answer,
            "retrieved": retrieved,
            "elapsed_seconds": round(elapsed, 2),
        }


# =============================================================================
# DEMO
# =============================================================================

def main():
    print("=" * 70)
    print("  LESSON 4.5: Building RAG from Scratch")
    print("=" * 70)

    if not os.getenv("OPENAI_API_KEY"):
        print("\n  ERROR: Set OPENAI_API_KEY environment variable.")
        print("  export OPENAI_API_KEY=sk-...")
        return

    # Build the RAG system
    rag = SimpleRAG(DOCUMENTS)

    # Test questions
    questions = [
        "How do I cancel my subscription?",
        "What is your refund policy?",
        "Do you ship internationally?",        # not explicitly in docs
        "What payment methods do you accept?",
    ]

    for q in questions:
        print(f"\n  Q: {q}")
        result = rag.query(q)

        print(f"  A: {result['answer']}")

        print(f"  Retrieved ({len(result['retrieved'])} chunks):")
        for i, (doc, score) in enumerate(result['retrieved'], 1):
            print(f"    {i}. [{score:.3f}] {doc[:80]}{'...' if len(doc) > 80 else ''}")

        print(f"  Latency: {result['elapsed_seconds']}s")
        print(f"  {'-' * 60}")

    print("\n  Total documents indexed:", len(DOCUMENTS))
    print("  Top-k:", TOP_K)
    print("  Embedding model:", EMBEDDING_MODEL)
    print("  LLM:", LLM_MODEL)
    print("=" * 70)


if __name__ == "__main__":
    main()
