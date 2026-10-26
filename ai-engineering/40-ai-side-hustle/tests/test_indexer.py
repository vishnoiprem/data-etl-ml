"""test_indexer.py — output/INDEX.md generator."""

from __future__ import annotations

from pathlib import Path

from indexer import build_index


def test_index_writes_file(tmp_path: Path):
    out = tmp_path / "output"
    out.mkdir()
    (out / "articles").mkdir()
    (out / "articles" / "a.md").write_text("hi")
    idx = build_index(out)
    assert idx.exists()
    text = idx.read_text()
    assert "Output Index" in text
    assert "articles" in text
    assert "a.md" in text


def test_index_handles_empty_output(tmp_path: Path):
    out = tmp_path / "output"
    idx = build_index(out)
    assert idx.exists()
    text = idx.read_text()
    assert "No output yet" in text


def test_index_lists_nested_files(tmp_path: Path):
    out = tmp_path / "output"
    (out / "products").mkdir(parents=True)
    (out / "products" / "x").mkdir()
    (out / "products" / "x" / "ebook.md").write_text("body")
    (out / "products" / "x" / "listing.md").write_text("body2")
    idx = build_index(out)
    text = idx.read_text()
    assert "ebook.md" in text
    assert "listing.md" in text


def test_index_handles_missing_output_dir(tmp_path: Path):
    """No output/ dir at all should still produce a valid INDEX.md."""
    out = tmp_path / "does-not-exist"
    idx = build_index(out)
    assert idx.exists()
    assert "No output yet" in idx.read_text()
