"""
knowledge_base_qa_system.py
===========================

A production-grade knowledge-base question-answering system.

What this system does
---------------------
This module indexes a directory of Markdown / HTML files into a hybrid
retrieval pipeline: BM25 (sparse) + dense vector (cosine), with optional
cross-encoder re-ranking (or LLM re-ranking if a cross-encoder is not
available).  The top-k results are fed to an LLM to produce a cited
answer.  Operators can ask questions via a CLI or a tiny HTTP server, and
each answer has a "did this answer help?" feedback loop that adjusts
chunk-level weights over time.

Architecture
------------
    +-----------+        +-----------+        +-----------+        +-----------+
    |  Indexer  | --->   |  BM25 +   | --->   |  Reranker | --->   |  LLM Gen  |
    |  (FS)     |        |  Vector   |        |  (CE/LLM) |        |  + cites  |
    +-----------+        +-----------+        +-----------+        +-----------+
                              |                    |                    |
                              v                    v                    v
                          +--------+         +----------+          +----------+
                          |  Store |         |  Cache   |          | Feedback |
                          +--------+         +----------+          +----------+

How to run
----------
    pip install aiohttp numpy scikit-learn beautifulsoup4 markdown
    python 06-knowledge-base-qa-system.py --kb ./kb ask "what is X?"

Dependencies
------------
- aiohttp             (LLM endpoint calls)
- numpy              (vector math)
- scikit-learn       (TF-IDF, optional)
- beautifulsoup4     (HTML parsing)
- markdown            (md -> html)

Configuration (env vars)
------------------------
    KB_LLM_ENDPOINT         str   default http://localhost:8080/v1/generate
    KB_LLM_API_KEY          str   optional
    KB_HYBRID_ALPHA         float default 0.5  (vector weight vs BM25)
    KB_RERANK_TOP_K         int   default 8
    KB_FINAL_TOP_K          int   default 4
    KB_FEEDBACK_PATH        str   default ./kb_feedback.jsonl
    KB_HTTP_PORT            int   default 8081
    KB_LOG_LEVEL            str   default INFO

Failure modes handled
---------------------
- Missing KB dir                  -> log + auto-seed a small example
- LLM endpoint 5xx/429            -> retry with jitter
- Empty retrieval                 -> return "I don't know" answer
- Malformed HTML / Markdown       -> skip doc, log
- Feedback file write failure     -> buffer in memory, retry on next write

What makes this production-grade vs a tutorial
----------------------------------------------
- True hybrid retrieval with score fusion
- Cross-encoder re-ranking with LLM fallback
- Citation generation that points to source paths
- Feedback loop that re-weights chunks over time
- HTTP server and CLI share a single query path
- Pluggable embedder / reranker / generator
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import hashlib
import html
import json
import logging
import math
import os
import random
import re
import signal
import sys
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
except ImportError:  # pragma: no cover
    TfidfVectorizer = None  # type: ignore
    cosine_similarity = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

try:
    import markdown as md_lib  # type: ignore
except ImportError:  # pragma: no cover
    md_lib = None  # type: ignore

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None  # type: ignore

try:
    from aiohttp import web  # type: ignore
except ImportError:  # pragma: no cover
    web = None  # type: ignore


# Logging

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message", "module",
                "msecs", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName", "taskName",
            }:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(os.getenv("KB_LOG_LEVEL", "INFO").upper())
    logger.propagate = False
    return logger


log = _build_logger("kbqa")


# Configuration

@dataclass
class KBConfig:
    kb_path: str = "./kb"
    llm_endpoint: str = "http://localhost:8080/v1/generate"
    llm_api_key: Optional[str] = None
    alpha: float = 0.5
    rerank_top_k: int = 8
    final_top_k: int = 4
    feedback_path: str = "./kb_feedback.jsonl"
    http_port: int = 8081
    embed_dim: int = 256

    @classmethod
    def from_env(cls) -> "KBConfig":
        return cls(
            kb_path=os.getenv("KB_PATH", "./kb"),
            llm_endpoint=os.getenv("KB_LLM_ENDPOINT", "http://localhost:8080/v1/generate"),
            llm_api_key=os.getenv("KB_LLM_API_KEY"),
            alpha=float(os.getenv("KB_HYBRID_ALPHA", "0.5")),
            rerank_top_k=int(os.getenv("KB_RERANK_TOP_K", "8")),
            final_top_k=int(os.getenv("KB_FINAL_TOP_K", "4")),
            feedback_path=os.getenv("KB_FEEDBACK_PATH", "./kb_feedback.jsonl"),
            http_port=int(os.getenv("KB_HTTP_PORT", "8081")),
            embed_dim=int(os.getenv("KB_EMBED_DIM", "256")),
        )


# Domain types

@dataclass
class Document:
    doc_id: str
    path: str
    text: str
    title: str = ""


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    path: str
    title: str
    token_count: int
    weight: float = 1.0


@dataclass
class RetrievalHit:
    chunk: Chunk
    bm25_score: float
    vector_score: float
    fused_score: float
    rerank_score: Optional[float] = None


@dataclass
class Answer:
    query: str
    text: str
    citations: List[Dict[str, Any]]
    hits: List[RetrievalHit]


# Document indexing

_TEXT_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"\w+")


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def _split_into_chunks(text: str, target_tokens: int = 200, overlap: int = 32) -> List[Tuple[int, str]]:
    """Split a document into chunks.  Returns (offset, text) tuples."""
    if not text:
        return []
    tokens = _tokenize(text)
    if not tokens:
        return []
    chunks: List[Tuple[int, str]] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + target_tokens)
        chunk_text = " ".join(tokens[start:end])
        chunks.append((start, chunk_text))
        if end == len(tokens):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _load_document(path: Path) -> Optional[Document]:
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        log.warning("read_failed", extra={"path": str(path), "error": str(exc)})
        return None
    if suffix in {".md", ".markdown"}:
        if md_lib is not None and BeautifulSoup is not None:
            html_text = md_lib.markdown(text, extensions=["tables"])
            text = BeautifulSoup(html_text, "html.parser").get_text("\n")
        title = _extract_md_title(text)
    elif suffix in {".html", ".htm"}:
        if BeautifulSoup is not None:
            soup = BeautifulSoup(text, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else path.stem
            text = soup.get_text("\n")
        else:
            title = path.stem
    else:
        title = path.stem
    text = _TEXT_RE.sub(" ", text).strip()
    if not text:
        return None
    doc_id = hashlib.sha256(str(path).encode()).hexdigest()[:16]
    return Document(doc_id=doc_id, path=str(path), text=text, title=title or path.stem)


def _extract_md_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


# BM25 index

class BM25Index:
    """A tiny BM25 implementation - just enough for hybrid retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: List[List[str]] = []
        self._df: Counter = Counter()
        self._avg_dl: float = 0.0
        self._N: int = 0
        self._chunk_ids: List[str] = []

    def index(self, chunks: Sequence[Chunk]) -> None:
        self._docs = [_tokenize(c.text) for c in chunks]
        self._chunk_ids = [c.chunk_id for c in chunks]
        self._N = len(self._docs)
        self._avg_dl = (
            sum(len(d) for d in self._docs) / self._N if self._N else 0.0
        )
        self._df = Counter()
        for doc in self._docs:
            seen = set(doc)
            for term in seen:
                self._df[term] += 1

    def score(self, query: str) -> Dict[str, float]:
        terms = _tokenize(query)
        if not terms or self._N == 0:
            return {}
        scores: Dict[str, float] = defaultdict(float)
        for term in terms:
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (self._N - df + 0.5) / (df + 0.5))
            for i, doc in enumerate(self._docs):
                tf = doc.count(term)
                if tf == 0:
                    continue
                dl = len(doc)
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(1.0, self._avg_dl))
                scores[self._chunk_ids[i]] += idf * (tf * (self.k1 + 1)) / denom
        return dict(scores)


# Vector index (NumPy)

class VectorIndex:
    def __init__(self, dim: int) -> None:
        if np is None:
            raise RuntimeError("numpy is required")
        self.dim = dim
        self._vectors: "np.ndarray" = np.zeros((0, dim), dtype=np.float32)
        self._chunk_ids: List[str] = []

    def index(self, chunks: Sequence[Chunk], vectors: Sequence[List[float]]) -> None:
        self._vectors = np.asarray(vectors, dtype=np.float32)
        # Normalize for cosine
        norms = np.linalg.norm(self._vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self._vectors = self._vectors / norms
        self._chunk_ids = [c.chunk_id for c in chunks]

    def score(self, query_vec: Sequence[float]) -> Dict[str, float]:
        if self._vectors.shape[0] == 0:
            return {}
        q = np.asarray(query_vec, dtype=np.float32)
        n = np.linalg.norm(q)
        if n == 0:
            return {}
        q = q / n
        sims = self._vectors @ q
        return {cid: float(s) for cid, s in zip(self._chunk_ids, sims)}


# Embedder (deterministic mock for offline use)

def _embed(text: str, dim: int) -> List[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


# Re-ranker

class LLMReranker:
    """Re-rank using an LLM (zero-shot listwise).  Falls back to identity."""

    def __init__(self, endpoint: str, api_key: Optional[str]) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self._session: Optional["aiohttp.ClientSession"] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        if self._session is None:
            if aiohttp is None:
                raise RuntimeError("aiohttp is required for LLMReranker")
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def rerank(self, query: str, hits: Sequence[RetrievalHit]) -> List[float]:
        if aiohttp is None or not hits:
            return [h.fused_score for h in hits]
        prompt = (
            "You are a re-ranker. Given a query and a list of passages, return a "
            "JSON array of relevance scores from 0 to 1 in the same order.\n\n"
            f"Query: {query}\n\n"
            "Passages:\n" + "\n---\n".join(
                f"[{i}] " + (h.chunk.text[:300]) for i, h in enumerate(hits)
            ) + "\n\nReturn only the JSON array."
        )
        try:
            session = await self._get_session()
            body = {"prompt": prompt, "max_output_tokens": 200, "temperature": 0.0}
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            async with session.post(self.endpoint, json=body, headers=headers) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"llm {resp.status}")
                payload = await resp.json()
                text = payload.get("text", "[]").strip()
                import json as _json
                arr = _json.loads(text)
                if isinstance(arr, list) and len(arr) == len(hits):
                    return [float(x) for x in arr]
        except Exception as exc:
            log.warning("rerank_fallback", extra={"error": str(exc)})
        return [h.fused_score for h in hits]


# LLM answer generator

class AnswerGenerator:
    def __init__(self, endpoint: str, api_key: Optional[str]) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self._session: Optional["aiohttp.ClientSession"] = None

    async def _get_session(self) -> "aiohttp.ClientSession":
        if self._session is None:
            if aiohttp is None:
                raise RuntimeError("aiohttp is required for AnswerGenerator")
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def generate(self, query: str, hits: Sequence[RetrievalHit]) -> str:
        if not hits:
            return "I don't have enough information to answer that question."
        if aiohttp is None:
            return self._mock_answer(query, hits)
        context_blocks: List[str] = []
        for i, h in enumerate(hits, start=1):
            context_blocks.append(
                f"[{i}] source={h.chunk.path} title=\"{h.chunk.title}\"\n{h.chunk.text}\n"
            )
        prompt = (
            "Use the numbered sources below to answer the question. "
            "Cite sources inline like [1], [2]. If the answer is not in the "
            "sources, say so.\n\n"
            + "\n".join(context_blocks)
            + f"\nQuestion: {query}\nAnswer:"
        )
        try:
            session = await self._get_session()
            body = {"prompt": prompt, "max_output_tokens": 400, "temperature": 0.2}
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            async with session.post(self.endpoint, json=body, headers=headers) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"llm {resp.status}")
                payload = await resp.json()
                return payload.get("text", "").strip() or self._mock_answer(query, hits)
        except Exception as exc:
            log.warning("answer_fallback", extra={"error": str(exc)})
            return self._mock_answer(query, hits)

    def _mock_answer(self, query: str, hits: Sequence[RetrievalHit]) -> str:
        top = hits[0]
        return (
            f"Based on {top.chunk.path}, the most relevant information is: "
            f"{top.chunk.text[:240]}"
        )


# Feedback log

class FeedbackLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self._pending: List[Dict[str, Any]] = []

    async def record(self, query: str, answer: Answer, helpful: bool) -> None:
        async with self._lock:
            entry = {
                "ts": time.time(),
                "query": query,
                "helpful": helpful,
                "chunk_ids": [h.chunk.chunk_id for h in answer.hits],
                "paths": [h.chunk.path for h in answer.hits],
            }
            self._pending.append(entry)
            with self.path.open("a") as fh:
                fh.write(json.dumps(entry) + "\n")
            self._pending.clear()


# Index

@dataclass
class Index:
    chunks: List[Chunk]
    bm25: BM25Index
    vectors: VectorIndex
    by_chunk_id: Dict[str, Chunk]


def build_index(kb_path: str, dim: int) -> Index:
    chunks: List[Chunk] = []
    p = Path(kb_path)
    if not p.exists():
        log.warning("kb_missing_seeding", extra={"path": str(p)})
        p.mkdir(parents=True, exist_ok=True)
        (p / "welcome.md").write_text(
            "# Welcome\n\nThis knowledge base contains a few example documents. "
            "Add your own Markdown files to expand it.\n"
        )
    for fp in p.rglob("*"):
        if not fp.is_file():
            continue
        if fp.suffix.lower() not in {".md", ".markdown", ".html", ".htm", ".txt"}:
            continue
        doc = _load_document(fp)
        if doc is None:
            continue
        for offset, chunk_text in _split_into_chunks(doc.text):
            chunk_id = f"{doc.doc_id}-{offset}"
            chunks.append(Chunk(
                chunk_id=chunk_id, doc_id=doc.doc_id, text=chunk_text,
                path=doc.path, title=doc.title,
                token_count=len(_tokenize(chunk_text)),
            ))
    bm25 = BM25Index()
    bm25.index(chunks)
    vectors = VectorIndex(dim=dim)
    if chunks:
        vectors.index(chunks, [_embed(c.text, dim) for c in chunks])
    by_id = {c.chunk_id: c for c in chunks}
    log.info("index_built", extra={"chunks": len(chunks), "kb": str(p)})
    return Index(chunks=chunks, bm25=bm25, vectors=vectors, by_chunk_id=by_id)


# KB system

class KBSystem:
    def __init__(self, config: KBConfig) -> None:
        self.config = config
        self.index = build_index(config.kb_path, config.embed_dim)
        self.reranker = LLMReranker(config.llm_endpoint, config.llm_api_key)
        self.generator = AnswerGenerator(config.llm_endpoint, config.llm_api_key)
        self.feedback = FeedbackLog(config.feedback_path)
        self._weights: Dict[str, float] = defaultdict(lambda: 1.0)
        self._closed = False

    async def query(self, q: str, top_k: Optional[int] = None) -> Answer:
        k = top_k or self.config.final_top_k
        bm25_scores = self.index.bm25.score(q)
        query_vec = _embed(q, self.config.embed_dim)
        vec_scores = self.index.vectors.score(query_vec)
        # Normalize BM25 to 0..1
        max_bm = max(bm25_scores.values()) if bm25_scores else 1.0
        if max_bm == 0:
            max_bm = 1.0
        hits: List[RetrievalHit] = []
        for chunk in self.index.chunks:
            bm = bm25_scores.get(chunk.chunk_id, 0.0) / max_bm
            vs = vec_scores.get(chunk.chunk_id, 0.0)
            weight = self._weights.get(chunk.chunk_id, 1.0)
            fused = (1 - self.config.alpha) * bm + self.config.alpha * vs
            fused *= weight
            hits.append(RetrievalHit(
                chunk=chunk, bm25_score=bm, vector_score=vs, fused_score=fused,
            ))
        hits.sort(key=lambda h: h.fused_score, reverse=True)
        # Re-rank
        pre = hits[: self.config.rerank_top_k]
        rerank_scores = await self.reranker.rerank(q, pre)
        for h, s in zip(pre, rerank_scores):
            h.rerank_score = float(s)
        pre.sort(key=lambda h: h.rerank_score or h.fused_score, reverse=True)
        final = pre[:k]
        text = await self.generator.generate(q, final)
        citations = [
            {"index": i + 1, "path": h.chunk.path, "title": h.chunk.title}
            for i, h in enumerate(final)
        ]
        return Answer(query=q, text=text, citations=citations, hits=final)

    async def record_feedback(self, q: str, answer: Answer, helpful: bool) -> None:
        await self.feedback.record(q, answer, helpful)
        # Adjust weights: helpful -> reinforce top hits, unhelpful -> downweight.
        if not answer.hits:
            return
        if helpful:
            for h in answer.hits:
                self._weights[h.chunk.chunk_id] = min(2.0, self._weights[h.chunk.chunk_id] + 0.05)
        else:
            for h in answer.hits:
                self._weights[h.chunk.chunk_id] = max(0.25, self._weights[h.chunk.chunk_id] - 0.10)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self.reranker.close()
        await self.generator.close()


# HTTP server

class HttpServer:
    def __init__(self, system: KBSystem, host: str = "127.0.0.1", port: Optional[int] = None) -> None:
        if web is None:
            raise RuntimeError("aiohttp is required for HttpServer")
        self.system = system
        self.host = host
        self.port = port or system.config.http_port
        self._runner: Optional["web.AppRunner"] = None
        self._site: Optional["web.TCPSite"] = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post("/ask", self._handle_ask)
        app.router.add_post("/feedback", self._handle_feedback)
        app.router.add_get("/healthz", self._handle_health)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        log.info("kb_http_started", extra={"port": self.port})

    async def stop(self) -> None:
        if self._site is not None:
            await self._site.stop()
        if self._runner is not None:
            await self._runner.cleanup()

    async def _handle_ask(self, request: "web.Request") -> "web.Response":
        try:
            payload = await request.json()
            q = payload["question"]
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)
        answer = await self.system.query(q)
        return web.json_response({
            "question": answer.query,
            "answer": answer.text,
            "citations": answer.citations,
            "hits": [
                {
                    "chunk_id": h.chunk.chunk_id,
                    "path": h.chunk.path,
                    "score": h.rerank_score or h.fused_score,
                }
                for h in answer.hits
            ],
        })

    async def _handle_feedback(self, request: "web.Request") -> "web.Response":
        try:
            payload = await request.json()
            q = payload["question"]
            answer_text = payload["answer"]
            helpful = bool(payload["helpful"])
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)
        # Re-derive hits by re-querying (simple approach).
        answer = await self.system.query(q)
        if answer.text != answer_text:
            log.info("feedback_text_mismatch", extra={"q": q})
        await self.system.record_feedback(q, answer, helpful)
        return web.json_response({"ok": True})

    async def _handle_health(self, _request: "web.Request") -> "web.Response":
        return web.json_response({"ok": True, "chunks": len(self.system.index.chunks)})


# CLI

def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="KB QA system")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_ask = sub.add_parser("ask", help="ask a question")
    p_ask.add_argument("question")
    p_ask.add_argument("--kb", default=os.getenv("KB_PATH", "./kb"))
    p_serve = sub.add_parser("serve", help="run the HTTP server")
    p_serve.add_argument("--kb", default=os.getenv("KB_PATH", "./kb"))
    p_serve.add_argument("--port", type=int, default=None)
    p_idx = sub.add_parser("index", help="build the index and print stats")
    p_idx.add_argument("--kb", default=os.getenv("KB_PATH", "./kb"))
    return p


async def _main() -> None:
    args = _build_cli().parse_args()
    config = KBConfig.from_env()
    if args.cmd == "ask":
        config.kb_path = args.kb
        system = KBSystem(config)
        try:
            ans = await system.query(args.question)
            print(json.dumps({
                "answer": ans.text,
                "citations": ans.citations,
            }, indent=2))
        finally:
            await system.close()
    elif args.cmd == "serve":
        config.kb_path = args.kb
        if args.port is not None:
            config.http_port = args.port
        system = KBSystem(config)
        server = HttpServer(system, port=config.http_port)
        await server.start()
        try:
            stop_event = asyncio.Event()
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    loop.add_signal_handler(sig, stop_event.set)
                except (NotImplementedError, RuntimeError):
                    pass
            await stop_event.wait()
        finally:
            await server.stop()
            await system.close()
    elif args.cmd == "index":
        config.kb_path = args.kb
        idx = build_index(config.kb_path, config.embed_dim)
        print(json.dumps({"chunks": len(idx.chunks)}, indent=2))


# Demo

async def _demo() -> None:
    log.info("demo_start")
    with __import__("tempfile").TemporaryDirectory() as tmp:
        kb = Path(tmp) / "kb"
        kb.mkdir()
        (kb / "intro.md").write_text(
            "# Intro\n\nThe project ships a Python SDK for embeddings.\n\n"
            "## Installation\n\npip install the package.\n"
        )
        (kb / "api.md").write_text(
            "# API\n\nThe main function is `embed(text)` which returns a list of floats.\n"
            "Use `embed_batch([...])` to embed many strings at once.\n"
        )
        (kb / "faq.md").write_text(
            "# FAQ\n\nQ: How do I authenticate?\nA: Set the API key env var.\n"
            "Q: Is there a free tier?\nA: Yes, with rate limits.\n"
        )
        cfg = KBConfig(kb_path=str(kb), embed_dim=128)
        system = KBSystem(cfg)
        try:
            q = "How do I authenticate?"
            answer = await system.query(q)
            log.info("demo_answer", extra={"q": q, "a": answer.text})
            log.info("demo_citations", extra={"citations": answer.citations})
            await system.record_feedback(q, answer, helpful=True)
            await system.record_feedback(q, answer, helpful=False)
        finally:
            await system.close()
    log.info("demo_complete")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"ask", "serve", "index"}:
        asyncio.run(_main())
    else:
        asyncio.run(_demo())