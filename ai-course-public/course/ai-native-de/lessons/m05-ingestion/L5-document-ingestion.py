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


def test_parse_txt_normalizes_line_endings() -> None:
    """Windows-style \\r\\n becomes \\n; trailing whitespace stripped."""
    out = parse_txt("hello\r\nworld\r\n  \n")
    assert out == "hello\nworld"
    assert "\r" not in out


def test_parse_md_strips_all_heading_levels() -> None:
    """All ATX heading levels (#, ##, ###) lose their leading hashes."""
    md = "# h1\n\n## h2\n\n### h3\n\nbody"
    out = parse_md(md)
    assert "h1" in out and "h2" in out and "h3" in out
    assert "#" not in out
    assert "title:" not in out


def test_parse_html_drops_scripts_and_styles() -> None:
    """Both <script> and <style> blocks are removed (content + tags)."""
    html = "<p>good</p><script>alert(1)</script><style>body{}</style><p>also good</p>"
    out = parse_html(html)
    assert "good" in out
    assert "alert" not in out
    assert "body{}" not in out
    assert "<" not in out


def test_parse_html_collapses_whitespace() -> None:
    """Run-on whitespace in HTML becomes single spaces."""
    out = parse_html("<p>hello</p>   <p>world</p>")
    assert "  " not in out
    assert "hello world" in out


def test_parse_json_falls_back_to_dump() -> None:
    """JSON without a 'text' field is dumped (not silently dropped)."""
    out = parse_json('{"a": 1, "b": [2, 3]}')
    assert '"a"' in out
    assert "1" in out


def test_content_hash_distinguishes_punctuation() -> None:
    """A trailing period changes the hash (so 'policy.' != 'policy')."""
    assert content_hash("policy.") != content_hash("policy")


def test_content_hash_handles_unicode() -> None:
    """Unicode text is hashed without raising (UTF-8 path is exercised)."""
    h1 = content_hash("café résumé")
    h2 = content_hash("café résumé")
    assert h1 == h2
    assert len(h1) == 16


def test_content_hash_handles_empty_string() -> None:
    """Empty string hashes to a valid 16-char string (not raise)."""
    h = content_hash("")
    assert len(h) == 16
    assert isinstance(h, str)


def test_ingested_doc_doc_id_equals_content_hash() -> None:
    """doc_id is the content_hash -- the doc is content-addressed."""
    svc = IngestionService()
    r = svc.ingest([SAMPLE_INPUTS[0]])
    d = r.ingested[0]
    assert d.doc_id == d.content_hash


def test_ingested_doc_byte_count_matches_raw() -> None:
    """byte_count is the byte length of the RAW input, not the parsed text."""
    svc = IngestionService()
    raw = "  Vacation policy: 20 days per year.  \n"
    r = svc.ingest([Document(source="x.txt", raw=raw, content_type="txt")])
    assert r.ingested[0].byte_count == len(raw.encode("utf-8"))


def test_dead_letter_preserves_attempt_count() -> None:
    """A DLQ entry records `attempts` so the operator can spot retry storms."""
    svc = IngestionService()
    bad = [Document(source="bad.json", raw='{"x": broken}', content_type="json")]
    r = svc.ingest(bad)
    assert len(r.dead_letter) == 1
    assert r.dead_letter[0].attempts == MAX_RETRIES + 1


def test_dead_letter_failed_at_is_isoformat() -> None:
    """failed_at is an ISO-8601 string (parseable + ends with offset)."""
    svc = IngestionService()
    bad = [Document(source="bad.json", raw='{"x": broken}', content_type="json")]
    r = svc.ingest(bad)
    ts = r.dead_letter[0].failed_at
    assert isinstance(ts, str)
    assert len(ts) >= 20
    # ISO-8601 datetimes have at least one '-' and one ':'
    assert "-" in ts and ":" in ts


def test_ingest_dedupe_by_content_not_source() -> None:
    """Two docs with the same TEXT (different sources) -> exactly 1 stored, 1 dupe."""
    svc = IngestionService()
    docs = [
        Document(source="a.txt", raw="same text", content_type="txt"),
        Document(source="b.txt", raw="same text", content_type="txt"),
    ]
    r = svc.ingest(docs)
    assert len(r.ingested) == 1
    assert len(r.duplicates) == 1
    assert len(svc.store) == 1


def test_ingest_preserves_ingestion_order_in_result() -> None:
    """The ingested[] list is in the same order as the input docs."""
    svc = IngestionService()
    docs = [
        Document(source=f"d{i}.txt", raw=f"text number {i}", content_type="txt")
        for i in range(5)
    ]
    r = svc.ingest(docs)
    assert [d.source for d in r.ingested] == [d.source for d in docs]


def test_ingest_mixed_success_and_failure() -> None:
    """A mixed batch: 2 success, 1 dupe, 1 fail -- 4 inputs, classified correctly."""
    svc = IngestionService()
    docs = [
        Document(source="a.txt", raw="alpha", content_type="txt"),     # success
        Document(source="b.txt", raw="beta",  content_type="txt"),     # success
        Document(source="a2.txt", raw="alpha", content_type="txt"),    # dupe of a
        Document(source="bad.json", raw="not json", content_type="json"),  # fail
    ]
    r = svc.ingest(docs)
    assert len(r.ingested) == 2
    assert len(r.duplicates) == 1
    assert len(r.dead_letter) == 1
    assert len(svc.store) == 2


def test_parser_registry_dispatch_is_deterministic() -> None:
    """Same content_type -> same parser -> same output (no randomness)."""
    raw = "# heading\n\nbody"
    p1 = PARSERS["md"](raw)
    p2 = PARSERS["md"](raw)
    assert p1 == p2


def test_parse_md_handles_no_front_matter() -> None:
    """Markdown without front-matter is parsed normally (no error)."""
    out = parse_md("# title\n\nbody paragraph")
    assert "title" in out
    assert "body paragraph" in out
    assert "---" not in out


def test_parse_html_lowercase_and_uppercase_tags() -> None:
    """Tags are stripped regardless of case (HTML is case-insensitive)."""
    out = parse_html("<P>hi</P><Div>x</Div>")
    assert "hi" in out and "x" in out
    assert "<" not in out.upper() or "P>" not in out.upper()


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
