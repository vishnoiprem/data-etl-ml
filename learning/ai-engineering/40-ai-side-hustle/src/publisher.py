"""
publisher.py — Local file publishers (mock CMS, mock Gumroad, mock blog).

Why mock?  Real publishers require API keys, accounts, and approval.
For the demo, we just write files to disk under `output/`. The same
function signatures are what a real publisher would expose, so the
swap is a one-import change.
"""

from __future__ import annotations

from pathlib import Path


def write_article(output_dir: Path, slug: str, keyword: str, body: str) -> str:
    """Write a markdown article to output/articles/<slug>.md.

    Returns the file URL (file:// scheme for local files).
    """
    articles_dir = output_dir / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    path = articles_dir / f"{slug}.md"
    # Add a front-matter block for downstream static-site generators
    frontmatter = (
        f"---\n"
        f"title: {keyword.title()}\n"
        f"keyword: {keyword}\n"
        f"---\n\n"
    )
    path.write_text(frontmatter + body)
    return f"file://{path}"


def write_file(root: Path, name: str, body: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(body)
    return path
