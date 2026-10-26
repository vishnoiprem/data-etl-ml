"""
Tests for the Elasticsearch index manager.

Tests only the pure-Python helpers (no ES client required).
"""
from __future__ import annotations

import pandas as pd
import numpy as np


class TestDfToDocs:
    """Tests for _df_to_docs() in es_index_manager.py."""

    def test_basic_dataframe(self):
        from scb_aml_platform.elasticsearch.scripts.es_index_manager import _df_to_docs
        df = pd.DataFrame([
            {"id": 1, "name": "Alice", "score": 0.95},
            {"id": 2, "name": "Bob", "score": 0.42},
        ])
        docs = _df_to_docs(df)
        assert len(docs) == 2
        assert docs[0]["name"] == "Alice"
        assert docs[1]["score"] == 0.42

    def test_handles_nan(self):
        from scb_aml_platform.elasticsearch.scripts.es_index_manager import _df_to_docs
        df = pd.DataFrame([
            {"id": 1, "value": float("nan")},
        ])
        docs = _df_to_docs(df)
        assert docs[0]["value"] is None

    def test_handles_list_columns(self):
        from scb_aml_platform.elasticsearch.scripts.es_index_manager import _df_to_docs
        df = pd.DataFrame([
            {"id": 1, "tags": ["a", "b", "c"]},
        ])
        docs = _df_to_docs(df)
        assert docs[0]["tags"] == ["a", "b", "c"]

    def test_handles_numpy_array(self):
        from scb_aml_platform.elasticsearch.scripts.es_index_manager import _df_to_docs
        df = pd.DataFrame([
            {"id": 1, "vec": np.array([1.0, 2.0, 3.0])},
        ])
        docs = _df_to_docs(df)
        assert docs[0]["vec"] == [1.0, 2.0, 3.0]


class TestFileFallback:
    """Tests for save_to_file() — used when ES is unavailable."""

    def test_save_to_file_writes_json(self, tmp_path, monkeypatch):
        from scb_aml_platform.elasticsearch.scripts import es_index_manager
        # Redirect ES_DATA_DIR to tmp
        monkeypatch.setattr(
            es_index_manager, "ES_DATA_DIR", tmp_path, raising=False
        )
        docs = [{"id": 1, "name": "test"}]
        es_index_manager.save_to_file("test_index", docs)
        out = tmp_path / "test_index.json"
        assert out.exists()
        import json
        loaded = json.loads(out.read_text())
        assert loaded == docs
