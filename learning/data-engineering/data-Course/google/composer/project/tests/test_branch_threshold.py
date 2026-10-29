from __future__ import annotations
import pytest
from pipeline_logic import should_run_full_load

@pytest.mark.parametrize("row_count,threshold,expected", [
    (0, 100, False), (99, 100, False), (100, 100, False),
    (101, 100, True), (1_245, 100, True), (1_245, 1_000_000, False),
])
def test_should_run_full_load(row_count, threshold, expected):
    assert should_run_full_load(row_count, threshold) is expected

def test_threshold_boundary_is_strict():
    assert should_run_full_load(1000, 1000) is False
    assert should_run_full_load(1001, 1000) is True
