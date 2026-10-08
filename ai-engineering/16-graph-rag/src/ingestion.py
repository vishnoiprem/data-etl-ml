"""Markdown corpus loader + simple char-based chunker."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Doc:
    doc_id: str            # e.g. "onboarding.md"
    chunk_id: str          # "{doc_id}#0", "{doc_id}#1", ...
    text: str              # chunk content
    title: str = ""        # first H1 of the doc, if any


def _read_markdown(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return text, title


_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+")


def _split_sections(text: str) -> list[str]:
    """Split on H2/H3 headings; keep H1 with the first section."""
    parts = _HEADING_RE.split(text)
    if not parts:
        return [text]
    sections: list[str] = [parts[0]]
    for p in parts[1:]:
        sections.append(p)
    # Group: the first element is preamble; alternate [heading-with-rest...]
    # Simpler: just chunk by ~1200 chars per chunk, ~200 overlap
    return sections


def _chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # try to break on a paragraph boundary
        slice_ = text[start:end]
        if end < len(text):
            cut = slice_.rfind("\n\n")
            if cut > max_chars // 2:
                slice_ = slice_[:cut]
                end = start + cut
        chunks.append(slice_.strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def load_corpus(corpus_dir: Path) -> list[Doc]:
    """Load all .md files under `corpus_dir`, returning a flat list of chunks."""
    docs: list[Doc] = []
    paths = sorted(corpus_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No .md files found under {corpus_dir}")
    for path in paths:
        text, title = _read_markdown(path)
        chunks = _chunk_text(text)
        for i, chunk in enumerate(chunks):
            docs.append(
                Doc(
                    doc_id=path.name,
                    chunk_id=f"{path.name}#{i}",
                    text=chunk,
                    title=title,
                )
            )
    return docs


def write_jsonl(items: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            if hasattr(item, "__dataclass_fields__"):
                item = asdict(item)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
