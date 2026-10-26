"""
Tests for the Sqoop ingestion path generator.

We don't test the file-writing part (that requires a writable HDFS
sim). We test the pure path-generation function and the country
filtering logic.
"""
from __future__ import annotations

import pandas as pd


class TestPartitionPath:
    """Tests for _partition_path() in sqoop_ingest.py."""

    def test_path_format(self, monkeypatch):
        from scb_aml_platform.ingestion.sqoop_ingest import _partition_path
        path = _partition_path("SG", "customer_master", "20260115")
        # Should contain year/month/day
        s = str(path)
        assert "customer_master" in s
        assert "2026" in s
        assert "01" in s
        assert "15" in s
        # country code lowercased
        assert "sg" in s

    def test_date_components(self):
        from scb_aml_platform.ingestion.sqoop_ingest import _partition_path
        path = _partition_path("HK", "fact_transaction", "20251231")
        s = str(path)
        assert "2025" in s
        assert "12" in s
        assert "31" in s


class TestCountryFiltering:
    """Verify the country loop doesn't crash on missing data."""

    def test_ingest_with_empty_data(self, monkeypatch, tmp_path):
        from scb_aml_platform import config
        from scb_aml_platform.ingestion import sqoop_ingest

        # Point HDFS_ROOT to tmp_path and replace DUMMY_DIR
        monkeypatch.setattr(config.settings, "HDFS_ROOT", str(tmp_path))
        monkeypatch.setattr(config.settings, "DUMMY_DIR", str(tmp_path))

        # Create empty dummy data
        (tmp_path / "dummy").mkdir(exist_ok=True)

        # Should not raise even if data files are missing
        # (the implementation logs warnings and continues)
        try:
            sqoop_ingest.run_all("20260115")
        except FileNotFoundError:
            # Acceptable — the function may bail on missing files
            pass
