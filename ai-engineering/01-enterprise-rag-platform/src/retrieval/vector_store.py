"""Vector store adapters.

LOCAL: FAISS flat index (exact search, fine up to ~1M chunks). For larger,
swap in IVF/HNSW.

AWS: Amazon OpenSearch Serverless k-NN. The exact same query supports
hybrid (BM25 + dense) scoring; we use the `hybrid` query type at retrieval
time (see hybrid.py).

The two backends expose the same interface so calling code is mode-agnostic.
"""
from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import numpy as np
from loguru import logger

from src.config import settings
from src.ingestion.chunker import Chunk


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> None: ...
    @abstractmethod
    def search(self, query_vec: np.ndarray, k: int = 10, filters: dict | None = None) -> list[tuple[Chunk, float]]: ...
    @abstractmethod
    def all_chunks(self) -> list[Chunk]: ...


class FaissVectorStore(VectorStore):
    """In-process FAISS index with chunks persisted alongside.

    Index file: {INDEX_DIR}/faiss.index
    Chunks file: {INDEX_DIR}/chunks.pkl  (parallel list keyed by FAISS row id)
    """

    INDEX_FILE = "faiss.index"
    CHUNKS_FILE = "chunks.pkl"

    def __init__(self, dim: int, index_dir: Path | None = None):
        import faiss
        self.dim = dim
        self.index_dir = Path(index_dir or settings.INDEX_DIR)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        # IndexFlatIP = inner product. Combined with normalized embeddings,
        # this is equivalent to cosine similarity.
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: list[Chunk] = []
        self._load()

    def _load(self):
        import faiss
        idx_path = self.index_dir / self.INDEX_FILE
        chunks_path = self.index_dir / self.CHUNKS_FILE
        if idx_path.exists() and chunks_path.exists():
            self.index = faiss.read_index(str(idx_path))
            self.chunks = pickle.loads(chunks_path.read_bytes())
            logger.info(f"Loaded FAISS index with {len(self.chunks)} chunks")

    def _persist(self):
        import faiss
        faiss.write_index(self.index, str(self.index_dir / self.INDEX_FILE))
        (self.index_dir / self.CHUNKS_FILE).write_bytes(pickle.dumps(self.chunks))

    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> None:
        if len(chunks) != vectors.shape[0]:
            raise ValueError("chunks and vectors length mismatch")
        if vectors.shape[1] != self.dim:
            raise ValueError(f"vector dim {vectors.shape[1]} != index dim {self.dim}")
        # FAISS Flat is append-only; for true upsert we'd dedupe by chunk_id.
        # In a real system, deletes go through a tombstone + periodic rebuild.
        existing_ids = {c.chunk_id for c in self.chunks}
        new_chunks: list[Chunk] = []
        new_vecs: list[np.ndarray] = []
        for c, v in zip(chunks, vectors):
            if c.chunk_id not in existing_ids:
                new_chunks.append(c)
                new_vecs.append(v)
        if new_chunks:
            self.index.add(np.vstack(new_vecs))
            self.chunks.extend(new_chunks)
        self._persist()
        logger.info(f"FAISS upsert: +{len(new_chunks)} chunks (total {len(self.chunks)})")

    def search(self, query_vec: np.ndarray, k: int = 10, filters: dict | None = None) -> list[tuple[Chunk, float]]:
        if self.index.ntotal == 0:
            return []
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        # Over-fetch when filters are present (filter-then-trim) — naive but works for demo
        fetch_k = k * 5 if filters else k
        scores, ids = self.index.search(query_vec, min(fetch_k, self.index.ntotal))
        out: list[tuple[Chunk, float]] = []
        for s, i in zip(scores[0], ids[0]):
            if i < 0 or i >= len(self.chunks):
                continue
            chunk = self.chunks[i]
            if filters and not self._matches(chunk, filters):
                continue
            out.append((chunk, float(s)))
            if len(out) >= k:
                break
        return out

    @staticmethod
    def _matches(chunk: Chunk, filters: dict) -> bool:
        for key, expected in filters.items():
            actual = getattr(chunk, key, None) or chunk.metadata.get(key)
            if isinstance(expected, (list, tuple, set)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def all_chunks(self) -> list[Chunk]:
        return list(self.chunks)


class OpenSearchVectorStore(VectorStore):
    """Amazon OpenSearch Serverless backend.

    NOTE: This is a working sketch — to keep the demo dependency-light it isn't
    instantiated in LOCAL mode. To use it: pip install opensearch-py and set
    OPENSEARCH_ENDPOINT.
    """

    def __init__(self, dim: int):
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3

        self.dim = dim
        creds = boto3.Session().get_credentials()
        auth = AWS4Auth(
            creds.access_key, creds.secret_key, settings.AWS_REGION, "aoss",
            session_token=creds.token,
        )
        host = settings.OPENSEARCH_ENDPOINT.replace("https://", "")
        self.client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
        self.index_name = settings.OPENSEARCH_INDEX
        self._ensure_index()

    def _ensure_index(self):
        if self.client.indices.exists(self.index_name):
            return
        self.client.indices.create(self.index_name, body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "doc_id": {"type": "keyword"},
                    "text": {"type": "text"},
                    "source": {"type": "keyword"},
                    "title": {"type": "text"},
                    "acl_groups": {"type": "keyword"},
                    "vector": {
                        "type": "knn_vector",
                        "dimension": self.dim,
                        "method": {"engine": "faiss", "name": "hnsw", "space_type": "cosinesimil"},
                    },
                }
            }
        })

    def upsert(self, chunks: Sequence[Chunk], vectors: np.ndarray) -> None:
        from opensearchpy.helpers import bulk
        actions = []
        for c, v in zip(chunks, vectors):
            doc = asdict(c) | {"vector": v.tolist()}
            actions.append({"_index": self.index_name, "_id": c.chunk_id, "_source": doc})
        bulk(self.client, actions)

    def search(self, query_vec: np.ndarray, k: int = 10, filters: dict | None = None):
        body = {
            "size": k,
            "query": {"knn": {"vector": {"vector": query_vec.tolist(), "k": k}}}
        }
        if filters:
            body["post_filter"] = {"terms": {k: v if isinstance(v, list) else [v] for k, v in filters.items()}}
        resp = self.client.search(index=self.index_name, body=body)
        out = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            chunk = Chunk(
                chunk_id=src["chunk_id"], doc_id=src["doc_id"], text=src["text"],
                chunk_index=src.get("chunk_index", 0), total_chunks=src.get("total_chunks", 1),
                source=src.get("source", ""), title=src.get("title", ""),
                metadata=src.get("metadata", {}),
            )
            out.append((chunk, hit["_score"]))
        return out

    def all_chunks(self) -> list[Chunk]:
        # Implementing scroll for completeness skipped in this sketch.
        raise NotImplementedError("Use OpenSearch scroll API in production")


def get_vector_store(dim: int) -> VectorStore:
    if settings.is_aws:
        return OpenSearchVectorStore(dim=dim)
    return FaissVectorStore(dim=dim)
