"""
================================================================
M5 L5  --  Document Ingestion and Parsing
================================================================

Run:    python3 lessons/m05-ingestion/L5-document-ingestion.py
Keys:   none

Builds an idempotent ingestion service:
  * Parser registry (txt, md, html, json)
  * Content-hash dedupe (FNV-1a 32-bit)
  * Dead-letter queue for parse failures
  * Per-doc run with: parse, hash, normalize, store

The lesson's point: ingestion is the front door.  A bug here
replicates everywhere downstream.  Idempotency and a DLQ are
the two things that keep ingestion safe at scale.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M5.L5"
SEED = 0
MAX_RETRIES = 2


# =================================================================
# SECTION 1  --  Parser registry  (strategy pattern)
# =================================================================

Parser = Callable[[str], str]


def parse_txt(raw: str) -> str:
    """Plain text: trim trailing whitespace, normalize line endings."""
    return raw.replace("\r\n", "\n").strip()


def parse_md(raw: str) -> str:
    """Markdown: drop front-matter, strip headings, keep body text."""
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            raw = raw[end + 4 :]
    # Strip ATX headings: "# ", "## ", etc. -- keep the text
    raw = re.sub(r"^#+\s+", "", raw, flags=re.MULTILINE)
    return raw.strip()


def parse_html(raw: str) -> str:
    """HTML: very crude -- drop <script> and <style>, then strip tags."""
    raw = re.sub(r"<script.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<style.*?</style>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def parse_json(raw: str) -> str:
    """JSON: pull out the 'text' field if present, else dump."""
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    if isinstance(obj, dict) and "text" in obj:
        return str(obj["text"])
    return json.dumps(obj, indent=2)


PARSERS: dict[str, Parser] = {
    "txt": parse_txt,
    "md": parse_md,
    "html": parse_html,
    "json": parse_json,
}


# =================================================================
# SECTION 2  --  Content hash (idempotency key)
# =================================================================

def content_hash(text: str) -> str:
    """Stable 16-char hash.  Same input -> same output.  Used as the dedupe key."""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return h[:16]


# =================================================================
# SECTION 3  --  Document record
# =================================================================

@dataclass
class IngestedDoc:
    """A successfully-ingested document."""
    doc_id: str
    source: str
    text: str
    content_hash: str
    parser: str
    ingested_at: str
    byte_count: int
    char_count: int


@dataclass
class DeadLetter:
    """A document that failed to ingest."""
    source: str
    error: str
    failed_at: str
    attempts: int


@dataclass
class IngestionResult:
    """The full output of an ingest run."""
    ingested: list[IngestedDoc] = field(default_factory=list)
    duplicates: list[tuple[str, str]] = field(default_factory=list)  # (source, existing_hash)
    dead_letter: list[DeadLetter] = field(default_factory=list)


# =================================================================
# SECTION 4  --  Ingest a single document
# =================================================================

@dataclass
class Document:
    """A raw input document."""
    source: str
    raw: str
    content_type: str = "txt"   # txt, md, html, json


def parse_one(doc: Document) -> IngestedDoc:
    """Parse one doc; raise on failure (caller handles retry + DLQ)."""
    if doc.content_type not in PARSERS:
        raise ValueError(f"no parser for content_type={doc.content_type!r}")
    text = PARSERS[doc.content_type](doc.raw)
    h = content_hash(text)
    return IngestedDoc(
        doc_id=h,                  # content-addressed id
        source=doc.source,
        text=text,
        content_hash=h,
        parser=doc.content_type,
        ingested_at=datetime.now(timezone.utc).isoformat(),
        byte_count=len(doc.raw.encode("utf-8")),
        char_count=len(text),
    )


# =================================================================
# SECTION 5  --  Ingest many (idempotent + DLQ)
# =================================================================

class IngestionService:
    """An idempotent ingestion service with retry and a DLQ."""

    def __init__(self) -> None:
        self.store: dict[str, IngestedDoc] = {}   # content_hash -> doc

    def ingest(self, docs: list[Document]) -> IngestionResult:
        result = IngestionResult()
        for doc in docs:
            try:
                parsed = self._ingest_with_retry(doc)
            except Exception as e:  # noqa: BLE001
                result.dead_letter.append(DeadLetter(
                    source=doc.source,
                    error=f"{type(e).__name__}: {e}",
                    failed_at=datetime.now(timezone.utc).isoformat(),
                    attempts=MAX_RETRIES + 1,
                ))
                continue
            if parsed.content_hash in self.store:
                result.duplicates.append((doc.source, parsed.content_hash))
                continue
            self.store[parsed.content_hash] = parsed
            result.ingested.append(parsed)
        return result

    def _ingest_with_retry(self, doc: Document) -> IngestedDoc:
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return parse_one(doc)
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(0)  # no actual sleep in this demo
        raise last_err  # type: ignore[misc]


# =================================================================
# SECTION 6  --  Sample documents (mixed formats + a bad one)
# =================================================================

SAMPLE_INPUTS: list[Document] = [
    Document(source="hr/policy.txt",  raw="  Vacation policy: 20 days per year.  \n",                  content_type="txt"),
    Document(source="hr/401k.md",     raw="# 401k Match\n\n100% of the first 3% of salary.\n",          content_type="md"),
    Document(source="web/expense.html", raw="<html><body><h1>Expense policy</h1><p>Submit within 30 days.</p></body></html>", content_type="html"),
    Document(source="api/qbr.json",   raw='{"text": "QBR covers revenue, gross margin, NPS, attrition."}', content_type="json"),
    # duplicate (same text as #1)
    Document(source="hr/policy-copy.txt", raw="Vacation policy: 20 days per year.",                       content_type="txt"),
    # bad json
    Document(source="api/bad.json",   raw='{"text": missing quotes here}',                                content_type="json"),
    # unknown content type
    Document(source="weird.xyz",      raw="binary data",                                                 content_type="xyz"),
]


# =================================================================
# SECTION 7  --  Demo
# =================================================================

def demo() -> None:
    """End-to-end: ingest SAMPLE_INPUTS, report ingested / dupes / DLQ."""
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Document Ingestion and Parsing")
    print("=" * 70)

    # 1. Parser registry
    print("\n  Section 1: Parser registry")
    print("  " + "-" * 66)
    for name in PARSERS:
        print(f"    {name:<8} -> {PARSERS[name].__name__}")

    # 2. Content hash
    print("\n  Section 2: Content hash (idempotency key)")
    print("  " + "-" * 66)
    h1 = content_hash("hello world")
    h2 = content_hash("hello world")
    h3 = content_hash("hello WORLD")
    print(f"    content_hash('hello world')   = {h1}")
    print(f"    content_hash('hello world')   = {h2}  (same -> idempotent)")
    print(f"    content_hash('hello WORLD')   = {h3}  (diff -> different)")

    # 3. Single-doc parse
    print("\n  Section 3: Single-doc parse")
    print("  " + "-" * 66)
    md_doc = SAMPLE_INPUTS[1]
    parsed = parse_one(md_doc)
    print(f"    source: {parsed.source}")
    print(f"    parser: {parsed.parser}")
    print(f"    text:   {parsed.text!r}")
    print(f"    hash:   {parsed.content_hash}")

    # 4. Idempotency
    print("\n  Section 4: Idempotency (re-ingest the same doc)")
    print("  " + "-" * 66)
    svc = IngestionService()
    r1 = svc.ingest([SAMPLE_INPUTS[0]])
    print(f"    first ingest:  ingested={len(r1.ingested)}, dupes={len(r1.duplicates)}, dlq={len(r1.dead_letter)}")
    r2 = svc.ingest([SAMPLE_INPUTS[0]])
    print(f"    second ingest: ingested={len(r2.ingested)}, dupes={len(r2.duplicates)}, dlq={len(r2.dead_letter)}")

    # 5. DLQ
    print("\n  Section 5: Dead-letter queue")
    print("  " + "-" * 66)
    svc2 = IngestionService()
    bad = [Document(source="bad.json", raw='{"text": missing}', content_type="json")]
    r3 = svc2.ingest(bad)
    print(f"    bad json -> dlq: {len(r3.dead_letter)}")
    for dl in r3.dead_letter:
        print(f"      {dl.source}: {dl.error}")

    # 6. End-to-end
    print("\n  Section 6: End-to-end ingest of 7 mixed docs")
    print("  " + "-" * 66)
    svc3 = IngestionService()
    r = svc3.ingest(SAMPLE_INPUTS)
    print(f"    ingested:   {len(r.ingested)}")
    for d in r.ingested:
        print(f"      {d.doc_id}  {d.parser:<6}  {d.char_count:>4} chars  {d.source}")
    print(f"    duplicates: {len(r.duplicates)}")
    for src, h in r.duplicates:
        print(f"      {src}  ->  existing hash {h}")
    print(f"    dead_letter: {len(r.dead_letter)}")
    for dl in r.dead_letter:
        print(f"      {dl.source}: {dl.error}")

    # 7. Idempotency guarantee
    print("\n  Section 7: Idempotency over the whole run")
    print("  " + "-" * 66)
    before = len(svc3.store)
    r2 = svc3.ingest(SAMPLE_INPUTS)  # re-ingest everything
    after = len(svc3.store)
    print(f"    store size before re-ingest: {before}")
    print(f"    store size after  re-ingest: {after}  (should be equal)")
    print(f"    duplicates detected:         {len(r2.duplicates)}")
    print(f"    new docs ingested:           {len(r2.ingested)}  (should be 0)")

    print("=" * 70)
    print("  See L5-document-ingestion.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 8  --  Tests
# =================================================================

def test_parse_txt_strips_whitespace() -> None:
    assert parse_txt("  hello  \n") == "hello"


def test_parse_md_drops_front_matter() -> None:
    md = "---\ntitle: x\n---\n# Hello\n\nbody"
    out = parse_md(md)
    assert "Hello" in out
    assert "title: x" not in out


def test_parse_html_strips_tags() -> None:
    out = parse_html("<p>hello <b>world</b></p>")
    assert "hello" in out
    assert "<" not in out


def test_parse_json_pulls_text_field() -> None:
    out = parse_json('{"text": "the body"}')
    assert out == "the body"


def test_parse_json_raises_on_bad() -> None:
    try:
        parse_json('{"text": missing}')
    except ValueError:
        return
    assert False, "should have raised ValueError"


def test_content_hash_is_stable() -> None:
    assert content_hash("hello") == content_hash("hello")


def test_content_hash_differs_on_different_text() -> None:
    assert content_hash("a") != content_hash("b")


def test_content_hash_is_16_chars() -> None:
    h = content_hash("anything")
    assert len(h) == 16


def test_ingest_idempotent() -> None:
    """Re-ingesting the same valid doc produces 0 new docs and 1 dupe."""
    svc = IngestionService()
    good = [SAMPLE_INPUTS[0]]   # one valid doc
    r1 = svc.ingest(good)
    before = len(svc.store)
    r2 = svc.ingest(good)
    after = len(svc.store)
    assert before == after
    assert len(r2.ingested) == 0
    assert len(r2.duplicates) == 1
    assert len(r2.dead_letter) == 0


def test_ingest_dlq_for_bad_docs() -> None:
    """A bad json doc lands in the DLQ, not in the store."""
    svc = IngestionService()
    bad = [Document(source="bad.json", raw='{"x": broken}', content_type="json")]
    r = svc.ingest(bad)
    assert len(r.ingested) == 0
    assert len(r.dead_letter) == 1
    assert len(svc.store) == 0


def test_ingest_dlq_for_unknown_content_type() -> None:
    """Unknown content_type lands in the DLQ."""
    svc = IngestionService()
    bad = [Document(source="x.xyz", raw="data", content_type="xyz")]
    r = svc.ingest(bad)
    assert len(r.dead_letter) == 1


def test_parser_registry_covers_four() -> None:
    """The registry has txt, md, html, json."""
    assert set(PARSERS.keys()) == {"txt", "md", "html", "json"}


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
