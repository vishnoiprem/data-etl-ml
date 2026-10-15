"""
================================================================
M6 L6  --  Chunking and Context Preservation
================================================================

Run:    python3 lessons/m06-chunking/L6-chunking.py
Keys:   none

Builds three chunkers and a small ablation harness:
  * FixedWindow: split by character count with overlap
  * Recursive:   split on a hierarchy of separators (paragraphs, then sentences)
  * Structure:   keep headings as section anchors; chunk by heading + N sentences

The lesson's point: chunking is the highest-leverage knob in RAG
retrieval quality.  A 200-token chunk vs an 800-token chunk can
mean 30 points of recall.  Always ablate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M6.L6"
DEFAULT_CHUNK_SIZE = 400      # characters
DEFAULT_OVERLAP = 50
DEFAULT_SENTENCES_PER_CHUNK = 5


# =================================================================
# SECTION 1  --  Chunk record
# =================================================================

@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    start: int
    end: int
    chunker: str


# =================================================================
# SECTION 2  --  Fixed-window chunker
# =================================================================

def chunk_fixed_window(
    doc_id: str,
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Sliding window of `chunk_size` chars with `overlap` overlap.

    Simple, predictable, and the right baseline.  Worst case for retrieval
    quality because it splits mid-sentence.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")
    chunks: list[Chunk] = []
    n = len(text)
    step = chunk_size - overlap
    for i, start in enumerate(range(0, n, step)):
        end = min(start + chunk_size, n)
        if end - start < 1:
            break
        chunks.append(Chunk(
            chunk_id=f"{doc_id}-fw{i:03d}",
            doc_id=doc_id,
            text=text[start:end],
            start=start,
            end=end,
            chunker="fixed_window",
        ))
        if end == n:
            break
    return chunks


# =================================================================
# SECTION 3  --  Recursive chunker (paragraph -> sentence -> word)
# =================================================================

def _split_paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def _split_sentences(text: str) -> list[str]:
    # crude sentence splitter
    sents = re.split(r"(?<=[.!?])\s+", text)
    return [s for s in sents if s.strip()]


def chunk_recursive(
    doc_id: str,
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split on paragraphs first; if a paragraph is too big, split on
    sentences; if a sentence is too big, split on words.  Greedy pack.
    """
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    pos = 0
    i = 0

    def flush() -> None:
        nonlocal buf, buf_len, i
        if not buf:
            return
        joined = " ".join(buf).strip()
        if joined:
            chunks.append(Chunk(
                chunk_id=f"{doc_id}-rc{i:03d}",
                doc_id=doc_id, text=joined,
                start=pos, end=pos + len(joined),
                chunker="recursive",
            ))
            i += 1
        buf = []
        buf_len = 0

    for para in _split_paragraphs(text):
        if len(para) <= chunk_size:
            if buf_len + len(para) > chunk_size:
                flush()
            buf.append(para)
            buf_len += len(para)
        else:
            for sent in _split_sentences(para):
                if len(sent) > chunk_size:
                    # word-level fallback
                    words = sent.split()
                    for w in words:
                        if buf_len + len(w) + 1 > chunk_size:
                            flush()
                        buf.append(w)
                        buf_len += len(w) + 1
                else:
                    if buf_len + len(sent) + 1 > chunk_size:
                        flush()
                    buf.append(sent)
                    buf_len += len(sent) + 1
    flush()
    return chunks


# =================================================================
# SECTION 4  --  Structure-aware chunker (headings + sentences)
# =================================================================

def chunk_structure(
    doc_id: str,
    text: str,
    sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
) -> list[Chunk]:
    """Each chunk = a heading + N sentences.  Keeps the topic anchor with the body.

    Headings are detected as lines starting with '#'.  Body is everything
    else, sentence-split.
    """
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []  # (heading, body_sentences)
    cur_heading = "(no heading)"
    cur_body: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            if cur_body or cur_heading != "(no heading)":
                sections.append((cur_heading, cur_body))
            cur_heading = s.lstrip("#").strip()
            cur_body = []
        else:
            cur_body.extend(_split_sentences(s))
    sections.append((cur_heading, cur_body))

    chunks: list[Chunk] = []
    for sec_i, (heading, sents) in enumerate(sections):
        for k in range(0, len(sents), sentences_per_chunk):
            group = sents[k : k + sentences_per_chunk]
            text_block = (heading + ". " if heading != "(no heading)" else "") + " ".join(group)
            chunks.append(Chunk(
                chunk_id=f"{doc_id}-st{sec_i:02d}-{k:03d}",
                doc_id=doc_id, text=text_block,
                start=-1, end=-1,
                chunker="structure",
            ))
    return chunks


# =================================================================
# SECTION 5  --  Ablation harness (mocked)
# =================================================================

@dataclass
class AblationRow:
    chunker: str
    n_chunks: int
    mean_chunk_chars: float
    max_chunk_chars: int
    recall_at_3: float           # mocked; in production compute from golden set


def ablation(doc_id: str, text: str, recall_table: dict[str, float] | None = None) -> list[AblationRow]:
    """Run all 3 chunkers and report stats.  `recall_table` is optional;
    if not provided, recall_at_3 is mocked from the chunker name length.
    """
    rt = recall_table or {}
    out: list[AblationRow] = []
    for name, chunks in (
        ("fixed_window", chunk_fixed_window(doc_id, text)),
        ("recursive",    chunk_recursive(doc_id, text)),
        ("structure",    chunk_structure(doc_id, text)),
    ):
        sizes = [len(c.text) for c in chunks]
        if sizes:
            out.append(AblationRow(
                chunker=name,
                n_chunks=len(chunks),
                mean_chunk_chars=float(sum(sizes)) / len(sizes),
                max_chunk_chars=max(sizes),
                recall_at_3=rt.get(name, 0.5 + len(name) * 0.05),
            ))
    return out


# =================================================================
# SECTION 6  --  Sample text  (a long policy document)
# =================================================================

SAMPLE_TEXT = """# Vacation Policy
All full-time employees accrue 20 days of vacation per year, accrued monthly at 1.67 days per month. Unused vacation carries over up to a maximum of 5 days. Requests must be submitted at least 2 weeks in advance for blocks longer than 3 days. Manager approval is required.

# 401k Match
The company matches 100% of the first 3% of salary and 50% of the next 2%. Vesting is immediate. Enrollment is open quarterly. The match is calculated on the first $300,000 of salary.

# Sick Leave
Sick leave is provided at 10 days per year, accrued monthly. A doctor's note is required for absences longer than 3 consecutive days. Sick leave does not carry over; it is reset on January 1.

# Expense Policy
Expenses must be submitted within 30 days of the expense date. Receipts are required for any expense over $25. Manager approval is required for any expense over $500. Reimbursement is processed within 14 days of approval.

# Code Review
All code must be reviewed by at least one engineer other than the author. PRs should be under 400 lines. Reviews should be completed within 1 business day. Use the team's PR template; include a test plan.

# Incident Response
P1 incidents must be acknowledged within 15 minutes and resolved within 4 hours. P2 within 1 hour and resolved within 1 business day. P3 within 1 business day and resolved within 1 week. The on-call rotation is published in the team wiki.

# Data Retention
Customer PII is retained for 7 years. Financial records are retained for 10 years. Logs are retained for 90 days. Backups are kept for 1 year. All data deletion must be logged and auditable.

# On-Call
The on-call rotation has primary and secondary engineers. Compensation is $200 per shift. The shift is 1 week long, Monday to Monday. Handoff is at 10am on Monday with a written status update.

# Vendor Onboarding
All vendors must complete a security review, a contract review, and a billing setup. The security review takes 5 business days. The contract review takes 10 business days. Total onboarding is 15-20 business days.

# Hiring
The interview process has four stages: phone screen, take-home, system design, behavioral. The take-home is 4 hours max. The system design is 1 hour. The behavioral is 1 hour. Decisions are made within 2 business days of the final interview."""


# =================================================================
# SECTION 7  --  Demo
# =================================================================

def demo() -> None:
    """End-to-end: chunk SAMPLE_TEXT three ways + ablation table."""
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Chunking and Context Preservation")
    print("=" * 70)

    # 1. Fixed window
    print("\n  Section 1: Fixed-window chunker (chunk_size=400, overlap=50)")
    print("  " + "-" * 66)
    fw = chunk_fixed_window("doc-1", SAMPLE_TEXT, chunk_size=400, overlap=50)
    print(f"    n_chunks: {len(fw)}")
    for c in fw[:2]:
        print(f"    {c.chunk_id}  chars={len(c.text)}  text={c.text[:60]!r}...")

    # 2. Recursive
    print("\n  Section 2: Recursive chunker (paragraph -> sentence)")
    print("  " + "-" * 66)
    rc = chunk_recursive("doc-1", SAMPLE_TEXT, chunk_size=400, overlap=50)
    print(f"    n_chunks: {len(rc)}")
    for c in rc[:2]:
        print(f"    {c.chunk_id}  chars={len(c.text)}  text={c.text[:60]!r}...")

    # 3. Structure
    print("\n  Section 3: Structure-aware chunker (heading + 5 sentences)")
    print("  " + "-" * 66)
    st = chunk_structure("doc-1", SAMPLE_TEXT, sentences_per_chunk=5)
    print(f"    n_chunks: {len(st)}")
    for c in st[:2]:
        print(f"    {c.chunk_id}  chars={len(c.text)}  text={c.text[:60]!r}...")

    # 4. Compare chunk counts
    print("\n  Section 4: Chunk count comparison")
    print("  " + "-" * 66)
    print(f"    fixed_window: {len(fw)}")
    print(f"    recursive:    {len(rc)}")
    print(f"    structure:    {len(st)}")

    # 5. Chunk size distribution
    print("\n  Section 5: Mean chunk size (chars)")
    print("  " + "-" * 66)
    for name, chunks in (("fixed_window", fw), ("recursive", rc), ("structure", st)):
        sizes = [len(c.text) for c in chunks]
        mean = sum(sizes) / len(sizes)
        print(f"    {name:<14}  mean={mean:>6.1f}  max={max(sizes):>4}  min={min(sizes):>4}")

    # 6. Ablation
    print("\n  Section 6: Chunking ablation (mocked recall)")
    print("  " + "-" * 66)
    rt = {"fixed_window": 0.62, "recursive": 0.78, "structure": 0.85}
    rows = ablation("doc-1", SAMPLE_TEXT, recall_table=rt)
    print(f"    {'chunker':<14} {'n_chunks':>9} {'mean':>8} {'max':>5} {'recall@3':>10}")
    for r in rows:
        print(f"    {r.chunker:<14} {r.n_chunks:>9} {r.mean_chunk_chars:>8.1f} {r.max_chunk_chars:>5} {r.recall_at_3:>10.2f}")

    # 7. Heuristic
    print("\n  Section 7: Heuristic  --  bigger isn't always better")
    print("  " + "-" * 66)
    print("""
    Rule of thumb:
      * 200-400 chars  ->  best for factoid Q&A (high precision)
      * 600-1000 chars ->  best for "explain X" questions (more context)
      * 1500+ chars    ->  usually worse (dilutes the signal)
      * structure-aware + 200-400 chars  ->  best default for policy docs

    Always ablate on YOUR golden set, not the textbook.
    """)

    print("=" * 70)
    print("  See L6-chunking.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 8  --  Tests
# =================================================================

def test_fixed_window_covers_text() -> None:
    """The union of fixed-window chunks covers the input text (with overlap)."""
    text = "x" * 1000
    chunks = chunk_fixed_window("d", text, chunk_size=200, overlap=20)
    assert len(chunks) > 0
    # first chunk starts at 0
    assert chunks[0].start == 0
    # last chunk ends at the end of the text
    assert chunks[-1].end == 1000


def test_fixed_window_invalid_overlap() -> None:
    try:
        chunk_fixed_window("d", "abc", chunk_size=10, overlap=10)
    except ValueError:
        return
    assert False


def test_recursive_splits_paragraphs() -> None:
    text = "Para 1.\n\nPara 2.\n\nPara 3."
    chunks = chunk_recursive("d", text, chunk_size=10, overlap=0)
    assert len(chunks) >= 2


def test_recursive_handles_long_sentence() -> None:
    """A single very long sentence is split word-by-word."""
    text = "word " * 200
    chunks = chunk_recursive("d", text, chunk_size=100, overlap=0)
    assert len(chunks) > 1


def test_structure_preserves_headings() -> None:
    text = "# A\nfirst sentence. second sentence. third sentence.\n# B\nfourth sentence."
    chunks = chunk_structure("d", text, sentences_per_chunk=2)
    # first chunk should include "A"
    assert any("A" in c.text for c in chunks)


def test_structure_chunks_under_5_sentences() -> None:
    text = "# X\n" + ". ".join([f"sent{i}" for i in range(12)])
    chunks = chunk_structure("d", text, sentences_per_chunk=5)
    # expect 3 chunks (5 + 5 + 2)
    assert len(chunks) == 3


def test_chunk_id_unique() -> None:
    """Within one doc, chunk_ids are unique."""
    chunks = chunk_recursive("d", "a. b. c. d. e. f. g. h.", chunk_size=5, overlap=0)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_ablation_returns_three_rows() -> None:
    rows = ablation("d", "Some text. " * 50)
    assert len(rows) == 3
    names = {r.chunker for r in rows}
    assert names == {"fixed_window", "recursive", "structure"}


def test_ablation_recall_in_range() -> None:
    rows = ablation("d", "text", recall_table={"fixed_window": 0.5, "recursive": 0.7, "structure": 0.9})
    for r in rows:
        assert 0.0 <= r.recall_at_3 <= 1.0


def test_chunker_label_matches_method() -> None:
    """Each chunk's chunker field is the name of the method that made it."""
    fw = chunk_fixed_window("d", "a" * 200)
    rc = chunk_recursive("d", "a. " * 50)
    st = chunk_structure("d", "# H\nbody sentence.")
    assert all(c.chunker == "fixed_window" for c in fw)
    assert all(c.chunker == "recursive" for c in rc)
    assert all(c.chunker == "structure" for c in st)


def test_fixed_window_handles_empty_text() -> None:
    """Empty input → zero chunks (not a crash)."""
    assert chunk_fixed_window("d", "", chunk_size=100, overlap=10) == []


def test_recursive_handles_single_word() -> None:
    """A single short token produces a single chunk."""
    out = chunk_recursive("d", "hello", chunk_size=100, overlap=0)
    assert len(out) == 1
    assert out[0].text == "hello"


def test_ablation_picks_winner() -> None:
    """ablation lets us pick the chunker with the highest recall_at_3."""
    rows = ablation("d", "Some text. " * 50)
    max_recall = max(r.recall_at_3 for r in rows)
    winner = max(rows, key=lambda r: r.recall_at_3)
    assert winner.recall_at_3 == max_recall
    assert winner.n_chunks > 0


def test_structure_strips_headings_from_body() -> None:
    """The body of structure chunks does not contain the markdown heading chars."""
    chunks = chunk_structure("d", "# Title\nA sentence. Another sentence. Third sentence.")
    bodies = [c.text for c in chunks]
    assert all("# " not in b for b in bodies)


def test_chunks_have_doc_id() -> None:
    """All chunkers stamp the doc_id on every chunk."""
    fw = chunk_fixed_window("doc-A", "a" * 300)
    rc = chunk_recursive("doc-B", "a. " * 50)
    st = chunk_structure("doc-C", "# H\nbody. body. body.")
    assert all(c.doc_id == "doc-A" for c in fw)
    assert all(c.doc_id == "doc-B" for c in rc)
    assert all(c.doc_id == "doc-C" for c in st)


def test_chunk_start_increases() -> None:
    """Within a fixed-window chunker, start is monotonic and step = chunk_size - overlap."""
    text = "abcdefghij" * 50  # 500 chars
    chunks = chunk_fixed_window("d", text, chunk_size=100, overlap=20)
    starts = [c.start for c in chunks]
    assert starts == sorted(starts)
    if len(chunks) > 1:
        # step is chunk_size - overlap = 80
        assert starts[1] - starts[0] == 80


def test_chunker_count_consistent() -> None:
    """Ablation reports 3 rows, one per chunker (fixed/recursive/structure)."""
    rows = ablation("d", "Some text. " * 50)
    labels = sorted(r.chunker for r in rows)
    assert labels == ["fixed_window", "recursive", "structure"]


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
