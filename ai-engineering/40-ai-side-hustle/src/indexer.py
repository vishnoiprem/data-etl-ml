"""
indexer.py — Build output/INDEX.md after each run.

After a pass, the `output/` directory has a tree of generated assets
(articles, saas scaffolds, products, merch listings). Without a map
you have to dig around. This module walks the tree and writes a
single INDEX.md that lists everything in one place.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone


def build_index(output_dir: Path) -> Path:
    """Walk output_dir and write INDEX.md. Returns the path written."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sections: list[str] = []
    sections.append(f"# Output Index")
    sections.append("")
    sections.append(f"_Generated {datetime.now(timezone.utc).isoformat()}_")
    sections.append("")

    total_files = 0
    subdirs = sorted(output_dir.iterdir(), key=lambda p: p.name) if output_dir.exists() else []
    for sub in subdirs:
        if not sub.is_dir() or sub.name == "__pycache__":
            continue
        sections.append(f"## {sub.name}/")
        sections.append("")
        files = sorted(sub.rglob("*"))
        files = [f for f in files if f.is_file()]
        for f in files:
            rel = f.relative_to(output_dir)
            size = f.stat().st_size
            sections.append(f"- `{rel}` ({size} B)")
            total_files += 1
        sections.append("")

    if total_files == 0:
        sections.append("_No output yet. Run `make demo` to generate._")
        sections.append("")

    index_path = output_dir / "INDEX.md"
    index_path.write_text("\n".join(sections))
    return index_path
