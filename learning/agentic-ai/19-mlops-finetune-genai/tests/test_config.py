"""Tests for `agent.config` — validation and env-var precedence.

These are the tests that would have caught a mis-scoped env prefix: e.g. if
`TrainConfig` forgot `env_prefix="TRAIN_"`, setting `TRAIN_LR=1e-5` would
silently do nothing. That's a money bug, so it gets a test.
"""

from __future__ import annotations

import os

import pytest


class TestModelConfig:
    def test_default_model_name(self):
        from agent.config import ModelConfig

        assert ModelConfig().model_name == "meta-llama/Llama-3.1-8B-Instruct"

    def test_rejects_blank_model_name(self, monkeypatch):
        from agent.config import ModelConfig

        monkeypatch.setenv("MODEL_NAME", "   ")
        with pytest.raises(Exception):
            ModelConfig()

    def test_model_name_from_env(self, monkeypatch):
        from agent.config import ModelConfig

        monkeypatch.setenv("MODEL_NAME", "meta-llama/Llama-3.1-70B-Instruct")
        assert ModelConfig().model_name == "meta-llama/Llama-3.1-70B-Instruct"

    def test_huggingface_token_alias(self, monkeypatch):
        from agent.config import ModelConfig

        monkeypatch.setenv("HUGGINGFACE_TOKEN", "hf_test_token")
        assert ModelConfig().huggingface_token == "hf_test_token"


class TestTrainConfig:
    def test_defaults_match_readme(self):
        from agent.config import TrainConfig

        c = TrainConfig()
        assert c.lora_r == 16
        assert c.lora_alpha == 32
        assert c.max_seq_len == 2048
        assert c.seed == 42

    def test_env_prefix_is_train(self, monkeypatch):
        """The critical one: TRAIN_LR must actually reach TrainConfig.lr."""
        from agent.config import TrainConfig

        monkeypatch.setenv("TRAIN_LR", "1e-5")
        monkeypatch.setenv("TRAIN_LORA_R", "64")
        monkeypatch.setenv("TRAIN_EPOCHS", "3")
        c = TrainConfig()
        assert c.lr == pytest.approx(1e-5)
        assert c.lora_r == 64
        assert c.epochs == 3

    def test_unprefixed_env_does_not_leak_in(self, monkeypatch):
        """An LR set without the prefix must NOT be picked up."""
        from agent.config import TrainConfig

        monkeypatch.delenv("TRAIN_LR", raising=False)
        monkeypatch.setenv("LR", "1e-9")
        assert TrainConfig().lr == pytest.approx(2e-4)

    def test_synthetic_flag_from_env(self, monkeypatch):
        from agent.config import TrainConfig

        monkeypatch.setenv("TRAIN_SYNTHETIC", "1")
        assert TrainConfig().synthetic is True


class TestServeConfig:
    def test_defaults(self):
        from agent.config import ServeConfig

        c = ServeConfig()
        assert c.base_url == "http://localhost:8000/v1"
        assert c.adapter_alias == "champion"
        assert c.max_model_len == 8192

    def test_env_prefix_is_vllm(self, monkeypatch):
        from agent.config import ServeConfig

        monkeypatch.setenv("VLLM_BASE_URL", "http://gpu-box:8000/v1")
        monkeypatch.setenv("VLLM_MAX_MODEL_LEN", "16384")
        c = ServeConfig()
        assert c.base_url == "http://gpu-box:8000/v1"
        assert c.max_model_len == 16384


class TestMonitorConfig:
    def test_per_token_conversion(self):
        from agent.config import MonitorConfig

        c = MonitorConfig()
        assert c.cost_input_per_token == pytest.approx(0.18 / 1e6)
        assert c.cost_output_per_token == pytest.approx(0.18 / 1e6)

    def test_drift_threshold_default(self):
        from agent.config import MonitorConfig

        assert MonitorConfig().drift_threshold == 0.3


class TestGateConfig:
    def test_defaults(self):
        from agent.config import GateConfig

        c = GateConfig()
        assert c.max_train_usd == 200.0
        assert c.max_run_seconds == 7200
        assert c.max_retry == 3

    def test_env_prefix_is_gate(self, monkeypatch):
        from agent.config import GateConfig

        monkeypatch.setenv("GATE_MAX_TRAIN_USD", "50.0")
        assert GateConfig().max_train_usd == 50.0


class TestLoadSettings:
    def test_bundle_has_all_sections(self):
        from agent.config import load_settings

        s = load_settings()
        for attr in ("model", "train", "serve", "monitor", "gate"):
            assert hasattr(s, attr)

    def test_snapshot_is_flat_and_mlflow_safe(self):
        """MLflow `log_params` rejects nested dicts and Path objects."""
        from agent.config import load_settings

        snap = load_settings().snapshot()
        assert isinstance(snap, dict)
        assert all(isinstance(k, str) for k in snap)
        assert all(not isinstance(v, dict) for v in snap.values())
        # Paths must be stringified, else MLflow raises.
        for v in snap.values():
            assert not hasattr(v, "__fspath__") or isinstance(v, str)

    def test_snapshot_has_section_prefixes(self):
        from agent.config import load_settings

        keys = load_settings().snapshot().keys()
        assert any(k.startswith("TrainConfig.") for k in keys)
        assert any(k.startswith("ServeConfig.") for k in keys)

    def test_cache_clear_is_needed_for_env_change(self, monkeypatch):
        from agent.config import load_settings

        s1 = load_settings()
        monkeypatch.setenv("TRAIN_LORA_R", "8")
        assert load_settings().train.lora_r == s1.train.lora_r  # still cached
        load_settings.cache_clear()
        assert load_settings().train.lora_r == 8
        load_settings.cache_clear()


class TestEnvFileLocation:
    def test_env_path_points_at_project(self):
        from agent.config import PACKAGE_ROOT, env_path

        assert env_path() == PACKAGE_ROOT / ".env"
        assert PACKAGE_ROOT.name == "19-mlops-finetune-genai"

    def test_env_example_exists(self):
        from agent.config import PACKAGE_ROOT

        assert (PACKAGE_ROOT / ".env.example").exists()