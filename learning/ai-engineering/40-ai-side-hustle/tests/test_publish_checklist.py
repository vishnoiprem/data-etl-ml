"""test_publish_checklist.py — the publish script prints + writes the right data."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest


# Make the scripts/ dir importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import publish_checklist as pc  # noqa: E402


@pytest.fixture
def fake_products(tmp_path: Path) -> Path:
    """Build a fake output/products/ tree + url-map.json."""
    products = tmp_path / "products"
    (products / "alpha-product").mkdir(parents=True)
    (products / "alpha-product" / "deliverable.pdf").write_bytes(b"%PDF-1.4 fake")
    (products / "alpha-product" / "listing.md").write_text(
        "# Alpha Test\n\n**$9**\n\nThe alpha hook.\n\n## What you get\n- Item one\n"
    )
    (products / "beta-product").mkdir(parents=True)
    (products / "beta-product" / "deliverable.pdf").write_bytes(b"%PDF-1.4 fake")
    (products / "beta-product" / "listing.md").write_text(
        "# Beta Test\n\n**$19**\n\nThe beta hook.\n"
    )
    (tmp_path / "url-map.json").write_text(json.dumps({
        "alpha-product": "https://vishnoiprem.gumroad.com/l/alpha",
        "beta-product":  "https://vishnoiprem.gumroad.com/l/beta",
    }))
    return tmp_path


def test_main_prints_product_table(fake_products, monkeypatch, capsys):
    """The CLI prints a table with all 3 products' data."""
    monkeypatch.setattr(pc, "ROOT", fake_products)
    monkeypatch.setattr(pc, "PRODUCTS", fake_products / "products")
    monkeypatch.setattr(pc, "URL_MAP", fake_products / "url-map.json")
    monkeypatch.setattr(pc, "OUT", fake_products / "publish.md")
    rc = pc.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Alpha Test" in out
    assert "Beta Test" in out
    assert "$9" in out
    assert "$19" in out
    assert "vishnoiprem.gumroad.com" in out
    assert "publish.md" in out


def test_main_writes_publish_md(fake_products, monkeypatch):
    """The script writes output/publish.md with full descriptions inline."""
    monkeypatch.setattr(pc, "ROOT", fake_products)
    monkeypatch.setattr(pc, "PRODUCTS", fake_products / "products")
    monkeypatch.setattr(pc, "URL_MAP", fake_products / "url-map.json")
    out_path = fake_products / "publish.md"
    monkeypatch.setattr(pc, "OUT", out_path)
    pc.main()
    assert out_path.exists()
    text = out_path.read_text()
    # Has the product name
    assert "Alpha Test" in text
    # Has the description (the hook line)
    assert "The alpha hook" in text
    # Has the launch sequence reminder
    assert "Day 1" in text or "tweet-thread" in text


def test_main_returns_1_when_no_products(monkeypatch, capsys):
    """No products under output/products/ -> exit 1 with a clear error."""
    empty = Path("/tmp/empty-test-publish-checklist")
    empty.mkdir(exist_ok=True)
    monkeypatch.setattr(pc, "ROOT", empty)
    monkeypatch.setattr(pc, "PRODUCTS", empty / "products")
    monkeypatch.setattr(pc, "URL_MAP", empty / "url-map.json")
    rc = pc.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "No products" in err


def test_main_warns_when_pdf_missing(fake_products, monkeypatch, capsys):
    """A product without deliverable.pdf should still appear, with a warning."""
    # Remove alpha's PDF
    (fake_products / "products" / "alpha-product" / "deliverable.pdf").unlink()
    monkeypatch.setattr(pc, "ROOT", fake_products)
    monkeypatch.setattr(pc, "PRODUCTS", fake_products / "products")
    monkeypatch.setattr(pc, "URL_MAP", fake_products / "url-map.json")
    monkeypatch.setattr(pc, "OUT", fake_products / "publish.md")
    pc.main()
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "Alpha Test" in out
