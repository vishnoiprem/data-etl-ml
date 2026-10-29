"""test_merch.py — Stream 4 (print-on-demand merch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ledger import Ledger
from router import StubRouter
from stream_merch import MerchIdea, run as run_merch


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    return Ledger(tmp_path / "test.db")


def test_merch_run_creates_one_folder_per_idea(out_dir: Path, ledger: Ledger):
    res = run_merch("ai engineers", StubRouter(), ledger, out_dir)
    assert len(res["ideas"]) >= 1
    merch_dir = out_dir / "merch"
    assert merch_dir.exists()
    # Each idea has at least a listing.md
    for sub in merch_dir.iterdir():
        assert (sub / "listing.md").exists()


def test_merch_run_records_projected_revenue(out_dir: Path, ledger: Ledger):
    res = run_merch("ai engineers", StubRouter(), ledger, out_dir)
    assert ledger.total("merch") > 0
    assert ledger.units_total("merch") >= len(res["ideas"])


def test_merch_run_no_record_keeps_ledger_empty(out_dir: Path, ledger: Ledger):
    run_merch("ai engineers", StubRouter(), ledger, out_dir, record_projected=False)
    assert ledger.total("merch") == 0
    # But merch folders still exist
    assert (out_dir / "merch").exists()


def test_merch_idea_projection_is_positive():
    """T-shirts and mugs should both project non-zero revenue."""
    shirt = MerchIdea(slogan="Hello, World 2.0", format="t-shirt",
                       audience="devs", designer_brief="...")
    mug = MerchIdea(slogan="Code. Sleep. Repeat.", format="mug",
                     audience="devs", designer_brief="...")
    assert shirt.projection.base > 0
    assert mug.projection.base > 0
    # Shirt royalty > mug royalty
    assert shirt.projection.base > mug.projection.base


def test_merch_idea_slug_is_filename_safe():
    m = MerchIdea(slogan="404 Sleep Not Found!!!", format="sticker",
                   audience="devs", designer_brief="...")
    assert "/" not in m.slug
    assert " " not in m.slug
    assert m.slug  # non-empty


def test_merch_run_resilient_to_router_failure(out_dir: Path, ledger: Ledger):
    class BoomRouter:
        name = "boom"
        def complete(self, *a, **kw): raise RuntimeError("nope")
        def json(self, *a, **kw): raise RuntimeError("nope")
    res = run_merch("ai", BoomRouter(), ledger, out_dir)  # type: ignore[arg-type]
    assert res.get("error")
    assert ledger.total() == 0


def test_ledger_accepts_merch_stream(ledger: Ledger):
    ledger.record("merch", 5.0)
    assert ledger.total("merch") == 5.0
