"""Document loaders.

Unified interface for loading text from various source formats.
Each loader returns a list of `Document` objects with text + metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from loguru import logger


@dataclass
class Document:
    """A loaded source document, before chunking."""
    doc_id: str           # stable id (e.g. file path or system id)
    text: str             # full document text
    source: str           # logical source: "policies", "runbooks", etc.
    title: str = ""
    metadata: dict = field(default_factory=dict)


def load_text_file(path: Path) -> Document:
    """Load a plain text or markdown file."""
    text = path.read_text(encoding="utf-8")
    return Document(
        doc_id=str(path),
        text=text,
        source=path.parent.name,
        title=path.stem.replace("_", " ").title(),
        metadata={"path": str(path), "size_bytes": path.stat().st_size},
    )


def load_pdf(path: Path) -> Document:
    """Load a PDF using pypdf. For scanned PDFs in production, prefer Textract."""
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return Document(
        doc_id=str(path),
        text=text,
        source=path.parent.name,
        title=path.stem.replace("_", " ").title(),
        metadata={"path": str(path), "pages": len(reader.pages)},
    )


_LOADERS = {
    ".txt": load_text_file,
    ".md": load_text_file,
    ".pdf": load_pdf,
}


def load_directory(root: Path) -> Iterable[Document]:
    """Walk a directory and yield Document objects for each supported file."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in _LOADERS]
    logger.info(f"Loading {len(files)} files from {root}")

    for path in files:
        try:
            yield _LOADERS[path.suffix.lower()](path)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
