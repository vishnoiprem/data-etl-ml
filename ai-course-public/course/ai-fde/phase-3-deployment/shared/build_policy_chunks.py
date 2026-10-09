"""
build_policy_chunks.py — one-time script that chunks the style guide.

What it does
------------
Reads Phase 1's `style-guide.md` and produces a `policy_chunks.jsonl` file
where each line is one H2 section of the style guide, ready to be embedded
and retrieved by the RAG layer in `service/rag.py`.

This is the Phase 2 version of "the style guide is in the system prompt":
instead of pasting the whole 130-line file into every LLM call, we chunk
it, embed it (or hash-mock it in Phase 2), and retrieve only the relevant
section for the current email.

Why a one-time script
---------------------
- The style guide changes ~once a quarter, not every deploy.
- We want chunks to be stable across service restarts.
- The script is run manually when the style guide changes; the output is
  committed to the repo as a jsonl.

How to run
----------
    python3 shared/build_policy_chunks.py \\
        --style-guide ../phase-1-foundations/shared/style-guide.md \\
        --out shared/policy_chunks.jsonl

How Phase 3 will do it
----------------------
Phase 3 replaces this with an actual embedding model (text-embedding-3-small)
and stores chunks in a real vector DB (Pinecone, Qdrant, or pgvector). The
chunk IDs and metadata here are what the real system will index.

Reuse from Phase 1
------------------
- Reads `phase-1-foundations/shared/style-guide.md` (the source of truth).
- Output format is what `service/rag.py` loads at startup.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Pattern that matches an H2 (## ) heading and captures the heading text.
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def chunk_style_guide(text: str, source: str) -> list[dict]:
    """Split a markdown file by H2 sections.

    Each chunk is a dict: {"id", "section", "text", "source"}.
    The first H1 (file title) is included in the first chunk so the
    vector store has context for the document as a whole.
    """
    # Find all H2 positions in the file.
    h2_matches = list(_H2_RE.finditer(text))
    if not h2_matches:
        # No H2s: treat the whole file as one chunk.
        return [{
            "id": f"{Path(source).stem}#0",
            "section": "(whole document)",
            "text": text.strip(),
            "source": source,
        }]

    chunks: list[dict] = []
    for i, m in enumerate(h2_matches):
        start = m.start()
        end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(text)
        section = m.group(1).strip()
        # Include the H1 (everything before the first H2) in the first chunk
        # so the retriever has document context.
        if i == 0:
            # Find the H1 (# Title) at the top.
            h1_match = re.match(r"^#\s+.+?\n", text)
            prefix = text[:h1_match.end()] if h1_match else ""
            body = prefix + text[start:end]
        else:
            body = text[start:end]
        chunk_id = f"{Path(source).stem}#{i + 1}"
        chunks.append({
            "id": chunk_id,
            "section": section,
            "text": body.strip(),
            "source": source,
        })
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--style-guide",
        type=Path,
        default=Path(__file__).parent.parent.parent / "phase-1-foundations" / "shared" / "style-guide.md",
        help="Path to the style guide .md file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent / "policy_chunks.jsonl",
        help="Where to write the chunked jsonl",
    )
    args = parser.parse_args()

    if not args.style_guide.exists():
        print(f"ERROR: style guide not found at {args.style_guide}", file=sys.stderr)
        return 1

    text = args.style_guide.read_text(encoding="utf-8")
    chunks = chunk_style_guide(text, source=str(args.style_guide))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for chunk in chunks:
            fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"Wrote {len(chunks)} chunks to {args.out}")
    for c in chunks:
        preview = c["text"].splitlines()[0][:80]
        print(f"  {c['id']:30s}  {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
