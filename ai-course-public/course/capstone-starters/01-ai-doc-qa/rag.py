"""
RAG Pipeline for AI Document Q&A
================================
A production-grade RAG system:
  - chunking (1000 tokens, 200 overlap)
  - embedding (text-embedding-3-small)
  - retrieval (top-5 from Pinecone, per-user)
  - generation (GPT-4o-mini with citations)
  - cost tracking
  - error handling with retry
"""

import time
import logging
from typing import Optional
import tiktoken
from openai import OpenAI, RateLimitError, APIError
from pinecone import Pinecone

logger = logging.getLogger("doc-qa.rag")

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"
EMBED_DIM = 1536
CHUNK_SIZE = 1000      # tokens
CHUNK_OVERLAP = 200    # tokens
TOP_K = 5

INDEX_NAME = "doc-qa"

# Pricing per 1M tokens (2026)
PRICING = {
    "text-embedding-3-small": {"input": 0.02},
    "gpt-4o-mini":            {"input": 0.15, "output": 0.60},
}


def count_tokens(text: str) -> int:
    """Count tokens using the same tokenizer as GPT-4o-mini."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks based on token count."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        if end == len(tokens):
            break
        start += chunk_size - overlap
    return chunks


class RAGPipeline:
    """Production-grade RAG: chunk, embed, store, retrieve, generate."""

    def __init__(self, openai_api_key: str, pinecone_api_key: str):
        self.openai = OpenAI(api_key=openai_api_key)
        self.pc = Pinecone(api_key=pinecone_api_key)

        # Ensure index exists
        if INDEX_NAME not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=INDEX_NAME,
                dimension=EMBED_DIM,
                metric="cosine",
            )
        self.index = self.pc.Index(INDEX_NAME)

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------

    def index_document(self, user_id: str, document_id: str, title: str, pages: list[str]) -> tuple[str, int]:
        """Chunk + embed + upsert a document. Returns (document_id, num_chunks)."""
        chunks = []
        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            page_chunks = chunk_text(page_text)
            for chunk_idx, chunk in enumerate(page_chunks):
                chunk_id = f"{document_id}__p{page_num}__c{chunk_idx}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "page": page_num,
                })

        if not chunks:
            return document_id, 0

        # Embed in batches of 100 (OpenAI limit)
        BATCH = 100
        vectors = []
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            response = self.openai.embeddings.create(
                model=EMBEDDING_MODEL,
                input=[c["text"] for c in batch],
            )
            for j, emb_data in enumerate(response.data):
                vectors.append({
                    "id": batch[j]["id"],
                    "values": emb_data.embedding,
                    "metadata": {
                        "user_id": user_id,
                        "document_id": document_id,
                        "title": title,
                        "page": batch[j]["page"],
                        "text": batch[j]["text"],
                    },
                })

        # Upsert in batches
        UPSERT_BATCH = 100
        for i in range(0, len(vectors), UPSERT_BATCH):
            self.index.upsert(vectors=vectors[i : i + UPSERT_BATCH])

        return document_id, len(chunks)

    # ------------------------------------------------------------------
    # QUERY
    # ------------------------------------------------------------------

    def query(self, user_id: str, question: str, document_id: Optional[str] = None) -> dict:
        """Embed question, retrieve top-k, generate answer with citations."""
        start = time.time()

        # Embed the question
        q_emb = self._embed_with_retry(question)

        # Build filter (always filter by user_id for isolation)
        filter_dict = {"user_id": user_id}
        if document_id:
            filter_dict["document_id"] = document_id

        # Retrieve
        results = self.index.query(
            vector=q_emb,
            top_k=TOP_K,
            include_metadata=True,
            filter=filter_dict,
        )

        matches = results.get("matches", [])
        if not matches:
            return {
                "answer": "I couldn't find relevant information in your documents. Try rephrasing or uploading more documents.",
                "citations": [],
                "cost_usd": 0.0,
            }

        # Build context from matches
        context_parts = []
        citations = []
        for i, match in enumerate(matches, 1):
            text = match["metadata"]["text"]
            page = match["metadata"]["page"]
            title = match["metadata"]["title"]
            doc_id = match["metadata"]["document_id"]
            context_parts.append(f"[{i}] (Page {page} of {title})\n{text}")
            citations.append({
                "chunk_id": match["id"],
                "document_title": title,
                "document_id": doc_id,
                "page": page,
                "score": match["score"],
                "text": text,
            })

        context_str = "\n\n".join(context_parts)

        # Generate answer
        system_prompt = (
            "You are a helpful AI assistant that answers questions about user-uploaded documents. "
            "Use ONLY the context below to answer. Cite sources as [1], [2], etc. "
            "If the answer is not in the context, say 'I don't know based on the provided documents.'\n\n"
            f"Context:\n{context_str}"
        )

        completion = self._generate_with_retry(
            system_prompt=system_prompt,
            user_message=question,
        )
        answer = completion.choices[0].message.content
        usage = completion.usage

        # Estimate cost
        cost = (
            (usage.prompt_tokens / 1_000_000) * PRICING[LLM_MODEL]["input"]
            + (usage.completion_tokens / 1_000_000) * PRICING[LLM_MODEL]["output"]
        )

        elapsed = time.time() - start
        logger.info(
            f"query user={user_id} chunks={len(matches)} "
            f"in_tok={usage.prompt_tokens} out_tok={usage.completion_tokens} "
            f"cost=${cost:.4f} elapsed={elapsed:.2f}s"
        )

        return {
            "answer": answer,
            "citations": citations,
            "cost_usd": cost,
        }

    # ------------------------------------------------------------------
    # RETRY HELPERS
    # ------------------------------------------------------------------

    def _embed_with_retry(self, text: str, max_retries: int = 3) -> list[float]:
        for attempt in range(max_retries):
            try:
                return self.openai.embeddings.create(
                    model=EMBEDDING_MODEL, input=text
                ).data[0].embedding
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning(f"Rate limited on embed, waiting {wait}s")
                time.sleep(wait)
            except APIError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

    def _generate_with_retry(self, system_prompt: str, user_message: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return self.openai.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0,
                )
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning(f"Rate limited on generate, waiting {wait}s")
                time.sleep(wait)
            except APIError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
