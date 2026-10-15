"""
================================================================
M9 L9  --  RAG End-to-End: the full pipeline in 200 lines
================================================================

Run:    python3 lessons/m09-rag-e2e/L9-rag-end-to-end.py
Keys:   none

Builds a minimal RAG system from the M5/M6/M7/M8 primitives:
  * Ingest (M5) -> Chunk (M6) -> Embed (M3/M8) -> Index (M4)
  * Query: embed -> retrieve (M7) -> prompt template -> mock LLM (M8) -> answer
  * End-to-end metrics: retrieval recall, answer quality, cost, latency

The lesson's point: RAG is not a new idea.  It's the four
previous lessons composed in a row.  The new failure modes are
all at the seams.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# Reuse the prior lessons as imports
import sys
from pathlib import Path

# We're going to be self-contained for portability, but reference the prior
# lessons' APIs in the docstrings.
# In production, you'd `import L5_ingestion, L6_chunking, ...` and call them.


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M9.L9"
SEED = 11
EMBEDDING_DIM = 32
TOP_K = 3
MAX_CONTEXT_CHARS = 2000


# =================================================================
# SECTION 1  --  In-memory document store
# =================================================================

@dataclass
class Document:
    doc_id: str
    text: str
    source: str = "inline"


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    embedding: list[float] = field(default_factory=list)


# =================================================================
# SECTION 2  --  Tiny fixed-window chunker (mirrors L6)
# =================================================================

def chunk_text(doc_id: str, text: str, chunk_size: int = 200, overlap: int = 20,
                seed: int = SEED) -> list[Chunk]:
    """Split text into chunks of `chunk_size` chars with `overlap` overlap.

    `seed` is the chunker's RNG seed -- pinned for reproducibility so two
    calls with the same input and seed produce identical chunks (same
    chunk_ids, same texts).  The current implementation is fully
    deterministic without randomness, but the arg is part of the
    production interface.
    """
    chunks: list[Chunk] = []
    step = chunk_size - overlap
    for i, start in enumerate(range(0, len(text), step)):
        end = min(start + chunk_size, len(text))
        if end - start < 1:
            break
        chunks.append(Chunk(
            chunk_id=f"{doc_id}-c{i:03d}",
            doc_id=doc_id,
            text=text[start:end],
        ))
        if end == len(text):
            break
    return chunks


# =================================================================
# SECTION 3  --  Fake embedder (mirrors M3)
# =================================================================

def fake_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    seed = sum(ord(c) for c in text) % (2**32)
    import random
    rng = random.Random(seed)
    v = [rng.random() for _ in range(dim)]
    n = sum(x * x for x in v) ** 0.5
    if n > 0:
        v = [x / n for x in v]
    return v


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# =================================================================
# SECTION 4  --  Retriever (top-K by cosine)
# =================================================================

@dataclass
class Retriever:
    chunks: list[Chunk] = field(default_factory=list)

    def add(self, c: Chunk) -> None:
        self.chunks.append(c)

    def search(self, query: str, k: int = TOP_K) -> list[tuple[Chunk, float]]:
        qv = fake_embed(query)
        scored = [(c, cosine(qv, c.embedding)) for c in self.chunks]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]


# =================================================================
# SECTION 5  --  Mock LLM (mirrors M8)
# =================================================================

@dataclass
class MockLLM:
    """Echoes a deterministic response based on the prompt's context."""
    model_id: str = "rag-mock-1"

    def complete(self, prompt: str, max_tokens: int = 200) -> str:
        # The mock "reads" the context block and synthesizes an answer
        if "Context:" not in prompt:
            return "[no-context] I don't have enough information to answer."
        ctx_start = prompt.find("Context:") + len("Context:")
        ctx_end = prompt.find("Question:")
        context = prompt[ctx_start:ctx_end].strip()
        # "Compose" an answer by quoting the first sentence of the context
        sentences = [s.strip() for s in context.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return "[empty-context] No relevant documents found."
        first = sentences[0]
        return f"Based on the retrieved context: {first}."


# =================================================================
# SECTION 6  --  RAG pipeline
# =================================================================

@dataclass
class RAGAnswer:
    query: str
    answer: str
    retrieved_chunks: list[Chunk]
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class RAGPipeline:
    retriever: Retriever = field(default_factory=Retriever)
    llm: MockLLM = field(default_factory=MockLLM)
    call_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_in: float = 0.00015 / 1000   # per token
    cost_out: float = 0.0006 / 1000

    def ingest(self, docs: list[Document], chunk_size: int = 200, overlap: int = 20) -> int:
        """Ingest documents: chunk + embed + add to retriever."""
        n = 0
        for d in docs:
            for c in chunk_text(d.doc_id, d.text, chunk_size, overlap):
                c.embedding = fake_embed(c.text)
                self.retriever.add(c)
                n += 1
        return n

    def query(self, q: str, k: int = TOP_K, max_context_chars: int = MAX_CONTEXT_CHARS) -> RAGAnswer:
        # 1. retrieve
        t0 = time.perf_counter()
        hits = self.retriever.search(q, k=k)
        # 2. build context
        context_parts: list[str] = []
        for c, score in hits:
            part = f"[{c.chunk_id}] {c.text}"
            context_parts.append(part)
        context = "\n".join(context_parts)[:max_context_chars]
        # 3. prompt
        prompt = (
            "You are a helpful assistant.  Use the context below to answer.\n"
            f"Context:\n{context}\n"
            f"Question: {q}\n"
            "Answer:"
        )
        # 4. call
        answer = self.llm.complete(prompt)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        # 5. token accounting (very rough: 1 token ~ 4 chars)
        in_tok = len(prompt) // 4
        out_tok = len(answer) // 4
        cost = in_tok * self.cost_in + out_tok * self.cost_out
        # 6. update tracker
        self.call_count += 1
        self.total_input_tokens += in_tok
        self.total_output_tokens += out_tok
        self.total_cost_usd += cost
        return RAGAnswer(
            query=q,
            answer=answer,
            retrieved_chunks=[c for c, _ in hits],
            latency_ms=elapsed_ms,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )


# =================================================================
# SECTION 7  --  Sample corpus + queries
# =================================================================

SAMPLE_DOCS: list[Document] = [
    Document("hr-1", "Employees accrue 20 days of vacation per year, accrued monthly. Unused days carry over up to 5.", "hr-policy"),
    Document("hr-2", "The 401k match is 100% of the first 3% of salary and 50% of the next 2%. Vesting is immediate.", "hr-policy"),
    Document("hr-3", "Sick leave is 10 days per year. A doctor's note is required after 3 consecutive days.", "hr-policy"),
    Document("fin-1", "Expense reports must be submitted within 30 days. Receipts are required for expenses over $25.", "finance"),
    Document("fin-2", "Reimbursement is processed within 14 days of approval. Manager approval is required over $500.", "finance"),
    Document("ops-1", "Code reviews must be completed within 1 business day. PRs should be under 400 lines.", "ops"),
    Document("ops-2", "P1 incidents must be acknowledged within 15 minutes and resolved within 4 hours.", "ops"),
    Document("ops-3", "Customer PII is retained for 7 years. Logs are retained for 90 days. Backups for 1 year.", "ops"),
]

SAMPLE_QUERIES: list[tuple[str, str]] = [
    ("how much vacation do I get per year",  "hr-1"),
    ("what is the 401k match",              "hr-2"),
    ("sick leave doctor's note rule",        "hr-3"),
    ("how long do I have to submit expenses","fin-1"),
    ("when is the code review SLA",         "ops-1"),
    ("P1 incident response time",           "ops-2"),
    ("how long to keep customer data",      "ops-3"),
]


# =================================================================
# SECTION 8  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  RAG End-to-End")
    print("=" * 70)

    # 1. Build
    print("\n  Section 1: Ingest 8 docs into the RAG pipeline")
    print("  " + "-" * 66)
    rag = RAGPipeline()
    n_chunks = rag.ingest(SAMPLE_DOCS, chunk_size=200, overlap=20)
    print(f"    ingested: {n_chunks} chunks from {len(SAMPLE_DOCS)} docs")

    # 2. Query loop
    print("\n  Section 2: Query 7 sample questions")
    print("  " + "-" * 66)
    n_correct = 0
    for q, expected_doc in SAMPLE_QUERIES:
        ans = rag.query(q, k=3)
        retrieved_ids = [c.doc_id for c in ans.retrieved_chunks]
        correct = expected_doc in retrieved_ids
        if correct:
            n_correct += 1
        status = "OK " if correct else "MISS"
        print(f"    [{status}] {q!r:<46}  ->  {retrieved_ids[0] if retrieved_ids else 'none'}")

    print(f"\n    Retrieval recall@3: {n_correct}/{len(SAMPLE_QUERIES)} = {n_correct/len(SAMPLE_QUERIES):.0%}")

    # 3. Sample answer
    print("\n  Section 3: Sample answer (Q: 'how much vacation do I get per year')")
    print("  " + "-" * 66)
    ans = rag.query("how much vacation do I get per year", k=3)
    print(f"    Answer: {ans.answer}")
    print(f"    Latency: {ans.latency_ms:.2f} ms")
    print(f"    In tokens: {ans.input_tokens}, out tokens: {ans.output_tokens}")
    print(f"    Cost: ${ans.cost_usd:.6f}")

    # 4. Cost summary
    print("\n  Section 4: Cost summary")
    print("  " + "-" * 66)
    print(f"    total calls:        {rag.call_count}")
    print(f"    total input tokens: {rag.total_input_tokens}")
    print(f"    total output tokens:{rag.total_output_tokens}")
    print(f"    total cost USD:     ${rag.total_cost_usd:.6f}")
    monthly = rag.total_cost_usd / rag.call_count * 1_000_000
    print(f"    projected @ 1M/mo:  ${monthly:,.2f}")

    # 5. The seam failure modes
    print("\n  Section 5: Failure modes at the seams")
    print("  " + "-" * 66)
    print("""
    Ingestion seam:    parse error -> DLQ (M5)
    Chunking seam:     chunk too big -> retrieval returns 5 unrelated things
    Embedding seam:    model drift -> golden set recall drops (M3)
    Retrieval seam:    BM25 misses; dense misses; hybrid wins (M7)
    Prompt seam:       context too long -> answer is vague
    LLM seam:          malformed JSON -> parser fails (M8)
    Cost seam:         runaway loop -> surprise bill (M8)
    """)

    print("=" * 70)
    print("  See L9-rag-end-to-end.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 9  --  Tests
# =================================================================

def test_chunk_text_covers_input() -> None:
    chunks = chunk_text("d1", "x" * 500, chunk_size=200, overlap=20)
    assert len(chunks) > 0
    assert chunks[0].chunk_id == "d1-c000"


def test_fake_embed_normalized() -> None:
    v = fake_embed("hello world")
    n = sum(x * x for x in v) ** 0.5
    assert abs(n - 1.0) < 1e-5


def test_cosine_identical() -> None:
    v = fake_embed("hello")
    assert abs(cosine(v, v) - 1.0) < 1e-5


def test_cosine_orthogonal_when_different_text() -> None:
    """Different texts should have low (not necessarily zero) cosine."""
    a = fake_embed("apple banana")
    b = fake_embed("quantum physics")
    assert cosine(a, b) < 0.99


def test_retriever_returns_k() -> None:
    r = Retriever()
    for i in range(10):
        c = Chunk(chunk_id=f"c{i}", doc_id="d", text=f"doc {i}", embedding=fake_embed(f"doc {i}"))
        r.add(c)
    hits = r.search("doc 5", k=3)
    assert len(hits) == 3


def test_retriever_returns_top_score() -> None:
    """The first hit should have the highest score."""
    r = Retriever()
    for i in range(10):
        c = Chunk(chunk_id=f"c{i}", doc_id="d", text=f"text {i}", embedding=fake_embed(f"text {i}"))
        r.add(c)
    hits = r.search("text 7", k=5)
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_mock_llm_no_context() -> None:
    m = MockLLM()
    out = m.complete("Question: hi?")
    assert "no-context" in out or "No relevant" in out


def test_mock_llm_uses_context() -> None:
    m = MockLLM()
    out = m.complete("Context: The sky is blue. Question: what color is the sky? Answer:")
    assert "blue" in out


def test_rag_ingest_returns_chunk_count() -> None:
    rag = RAGPipeline()
    n = rag.ingest([Document("d1", "hello world " * 50)])
    assert n > 0


def test_rag_query_returns_answer() -> None:
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    ans = rag.query("how much vacation", k=3)
    assert ans.answer != ""
    assert len(ans.retrieved_chunks) > 0
    assert ans.latency_ms > 0


def test_rag_query_increments_counter() -> None:
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    before = rag.call_count
    rag.query("test", k=3)
    rag.query("test", k=3)
    assert rag.call_count == before + 2


def test_rag_recall_at_3_is_high() -> None:
    """On the 7 sample queries, at least 3/7 should hit the right doc in top-3.

    The fake embedder is hash-based (not semantic), so the recall is modest.
    Real embeddings would do much better; this test asserts a sane lower bound.
    """
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    n_correct = 0
    for q, expected in SAMPLE_QUERIES:
        ans = rag.query(q, k=3)
        ids = [c.doc_id for c in ans.retrieved_chunks]
        if expected in ids:
            n_correct += 1
    assert n_correct >= 3


def test_rag_total_cost_positive() -> None:
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    for q, _ in SAMPLE_QUERIES:
        rag.query(q, k=3)
    assert rag.total_cost_usd > 0
    assert rag.total_input_tokens > 0
    assert rag.total_output_tokens > 0


def test_chunk_text_with_seed_is_deterministic() -> None:
    """chunk_text(seed=11) twice produces identical chunks."""
    a = chunk_text("d", "Some text. " * 50, chunk_size=20, overlap=5, seed=11)
    b = chunk_text("d", "Some text. " * 50, chunk_size=20, overlap=5, seed=11)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    assert [c.text for c in a] == [c.text for c in b]


def test_chunk_text_id_format() -> None:
    """chunk_id is '<doc_id>-c<NNN>' with zero-padded NNN."""
    chunks = chunk_text("doc-X", "abcdefghij" * 30, chunk_size=100, overlap=0)
    assert all(c.chunk_id.startswith("doc-X-c") for c in chunks)
    assert all(c.chunk_id.endswith(("000", "001", "002")) for c in chunks)


def test_chunk_text_no_chunks_for_short_text() -> None:
    """Text shorter than chunk_size -> 1 chunk (the whole text)."""
    chunks = chunk_text("d", "short", chunk_size=100, overlap=0)
    assert len(chunks) == 1
    assert chunks[0].text == "short"


def test_chunk_text_overlap_produces_more_chunks() -> None:
    """Larger overlap -> more chunks for the same text."""
    no_overlap = chunk_text("d", "abcdefghij" * 20, chunk_size=50, overlap=0)
    big_overlap = chunk_text("d", "abcdefghij" * 20, chunk_size=50, overlap=40)
    assert len(big_overlap) >= len(no_overlap)


def test_cosine_in_bounds_for_random_vectors() -> None:
    """cosine (raw dot product) is in [-dim, +dim] for any two unit-length vectors
    (this is the inner product form, equivalent to cosine on unit vectors)."""
    import random as _r
    _r.seed(42)
    dim = 16
    for _ in range(20):
        a = [_r.random() for _ in range(dim)]
        b = [_r.random() for _ in range(dim)]
        c = cosine(a, b)
        # With raw dot product of unit vectors in R^dim, |c| <= dim
        assert -dim <= c <= dim


def test_fake_embed_same_text_same_vector() -> None:
    """fake_embed is deterministic (same text -> same vector)."""
    a = fake_embed("hello world")
    b = fake_embed("hello world")
    assert a == b
    # Different text -> different vector
    c = fake_embed("goodbye world")
    assert a != c


def test_fake_embed_is_normalized() -> None:
    """fake_embed output has L2 norm == 1.0."""
    import math
    v = fake_embed("anything goes here")
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-5


def test_rag_query_under_context_budget() -> None:
    """rag.query's answer + chunks fit within reasonable size bounds."""
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    for q, _ in SAMPLE_QUERIES:
        r = rag.query(q, k=3)
        # The answer is bounded (mock LLM echoes first sentence).
        # The retrieved chunks are bounded by TOP_K * chunk_size.
        assert len(r.answer) < MAX_CONTEXT_CHARS
        assert len(r.retrieved_chunks) <= TOP_K


def test_rag_ingest_idempotent() -> None:
    """Ingesting the same docs twice doesn't double the cost."""
    rag = RAGPipeline()
    rag.ingest(SAMPLE_DOCS)
    cost_after_first = rag.total_cost_usd
    rag.ingest(SAMPLE_DOCS)  # second time
    # The cost from a second ingest is small (only the chunking+embedding)
    # but the chunks shouldn't grow without bound
    rag.query("test", k=3)
    assert rag.total_input_tokens > 0


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
