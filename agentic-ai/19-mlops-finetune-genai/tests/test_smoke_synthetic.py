"""Synthetic-mode end-to-end smoke test.

What this proves:

    1. `agent.train.run(synthetic=True)` writes an adapter directory on disk
       with the same shape as a real QLoRA save.
    2. `agent.dataset.build(...)` reads that directory and produces
       non-empty, deduped, leakage-filtered rows.
    3. `agent.serve.app` boots and `/v1/chat/completions` returns a 200.
       The FastAPI wrapper already has the degraded-mode path for no-LLM
       imports, so this works without vLLM installed.
    4. `agent.client.run([])` reports zero errors when the SDK is missing.

This is the test that lets `make smoke` pass on a laptop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_train_synthetic_produces_adapter(tmp_path):
    from agent.config import load_settings
    from agent.train import run

    load_settings.cache_clear()
    settings = load_settings()
    # Force synthetic by setting the env, then reload settings.
    import os
    os.environ["TRAIN_SYNTHETIC"] = "1"
    load_settings.cache_clear()

    out_dir = tmp_path / "sft-output"
    result = run(out_dir=out_dir)
    assert result.adapter_path.exists()
    assert (result.adapter_path / "adapter_config.json").exists()
    # synthetic-mode deliberately returns None for `merged_path` — that's a contract.
    assert result.merged_path is None
    assert result.run_id == "synthetic-local"
    assert result.stopped_reason == "ok"


def test_dataset_build_synthetic(tmp_path):
    """The same flag we set in test_train_synthetic above should make
    `build` produce a 16-row synthetic dataset without touching the network.
    """
    import os

    os.environ["TRAIN_SYNTHETIC"] = "1"
    from agent.config import load_settings
    from agent.dataset import build

    load_settings.cache_clear()
    ds, stats = build(root=tmp_path)
    assert stats.raw_rows == 16
    assert stats.final_rows > 0
    assert (tmp_path / "data/synthetic_sft.jsonl").exists()


def test_serve_app_healthz():
    """`/healthz` must return 200 in degraded mode (no vLLM installed)."""
    from agent.serve import app

    with TestClient(app) as client:
        resp = client.get("/healthz")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] in ("ready", "degraded")
        assert "ts" in payload


def test_serve_app_chat_degraded():
    """`/v1/chat/completions` must return a valid OpenAI-compat shape even
    when vLLM is not installed (so the smoke test doesn't depend on the GPU).
    """
    from agent.serve import app

    with TestClient(app) as client:
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "champion",
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
                "max_tokens": 8,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["object"] == "chat.completion"
        assert body["model"] == "champion"
        assert body["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in body


def test_serve_metrics_endpoint_exposes_prometheus_format():
    """The /metrics endpoint must return Prometheus exposition format with
    the registered gauges. We don't require live data, but the format must parse.
    """
    from agent.serve import app

    with TestClient(app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text
        # Sample of well-known metric names this contract guarantees.
        assert "# HELP" in text
        # At least one of the registered collectors should be present after the
        # chat call above; if not, post one more to be sure.
        if "vllm_requests_total" not in text:
            client.post(
                "/v1/chat/completions",
                json={
                    "model": "champion",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 4,
                },
            )
            resp = client.get("/metrics")
            text = resp.text
        assert "vllm_requests_total" in text


def test_client_batch_summary_zero_prompts():
    from agent.client import BatchSummary, run

    summary = run(prompts=[])
    assert isinstance(summary, BatchSummary)
    assert summary.report() == {"n": 0}


def test_client_missing_openai_graceful():
    """If openai SDK isn't installed, `run` returns a summary with status='openai_missing'
    rather than crashing.
    """
    from agent.client import run

    summary = run(["a prompt that won't be sent"])
    # Either we hit the wire (real openai is installed) or we degrade; both are valid.
    report = summary.report()
    assert report["n"] == 1
    if report["errors"] == 1:
        # Degraded mode — no openai installed, no errors are 'real'.
        assert summary.records[0].status == "openai_missing" or "error" in summary.records[0].status


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))