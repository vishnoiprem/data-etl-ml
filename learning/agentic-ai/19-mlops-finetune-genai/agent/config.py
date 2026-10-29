"""agent.config — single source of truth for the entire pipeline.

Four pydantic-settings models, one `load_settings()` factory. Every other
module in this package imports `load_settings()` and never reads os.environ
directly. This is the only place shell / .env / defaults precedence is defined.

Why pydantic-settings instead of a hand-rolled dataclass:
- Env-var precedence matches the order in the README (shell > .env > defaults).
- Validation errors are reported at first import, not at first call site.
- `model_dump()` gives a JSON-friendly snapshot for MLflow `log_params`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class ModelConfig(BaseSettings):
    """The base model + the adapter slot name we publish at serve time."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=os.environ.get("ENV_FILE", str(PACKAGE_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model_name: str = Field(
        default="meta-llama/Llama-3.1-8B-Instruct",
        description="HuggingFace hub id of the base model.",
    )
    huggingface_token: Optional[str] = Field(default=None, alias="HUGGINGFACE_TOKEN")

    @field_validator("model_name")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("MODEL_NAME must be a non-empty string")
        return v.strip()


class TrainConfig(BaseSettings):
    """QLoRA + SFT knobs. The three that matter most: r/alpha, lr, max_seq_len."""

    model_config = SettingsConfigDict(
        env_prefix="TRAIN_",
        env_file=os.environ.get("ENV_FILE", str(PACKAGE_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lr: float = 2e-4
    epochs: int = 1
    batch: int = 4
    grad_accum: int = 4
    max_seq_len: int = 2048
    dataset_rows: int = 30000
    seed: int = 42
    synthetic: bool = Field(
        default=False,
        description="Use the 16-row synthetic JSONL instead of HF (CI + smoke).",
    )


class ServeConfig(BaseSettings):
    """vLLM-side knobs. `--enable-lora` plus the alias the client uses to pick the adapter."""

    model_config = SettingsConfigDict(
        env_prefix="VLLM_",
        env_file=os.environ.get("ENV_FILE", str(PACKAGE_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "http://localhost:8000/v1"
    api_key: str = "sk-no-auth-required"
    max_model_len: int = 8192
    adapter_alias: str = "champion"


class MonitorConfig(BaseSettings):
    """Prometheus port + drift detector threshold + per-token cost model."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=os.environ.get("ENV_FILE", str(PACKAGE_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    prometheus_port: int = 9090
    drift_threshold: float = 0.3
    drift_baseline_path: Path = Path("artifacts/drift_baseline.parquet")
    cost_input_usd_per_1m: float = 0.18
    cost_output_usd_per_1m: float = 0.18

    @property
    def cost_input_per_token(self) -> float:
        return self.cost_input_usd_per_1m / 1_000_000.0

    @property
    def cost_output_per_token(self) -> float:
        return self.cost_output_usd_per_1m / 1_000_000.0


class GateConfig(BaseSettings):
    """Hard stops. The training run will refuse to spend the next cent
    once either `max_train_usd` or `max_run_seconds` is crossed.
    """

    model_config = SettingsConfigDict(
        env_prefix="GATE_",
        env_file=os.environ.get("ENV_FILE", str(PACKAGE_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_train_usd: float = 200.0
    max_run_seconds: int = 7200
    max_retry: int = 3


@dataclass  # type: ignore[misc]
class _SettingsBundle:
    """One container so callers can write `s = load_settings(); s.train.lr`."""

    model: ModelConfig
    train: TrainConfig
    serve: ServeConfig
    monitor: MonitorConfig
    gate: GateConfig

    def snapshot(self) -> dict:
        """Flat dict suitable for `mlflow.log_params`. Nested keys get a `_` join."""
        snap: dict = {}
        for section in (self.model, self.train, self.serve, self.monitor, self.gate):
            for k, v in section.model_dump().items():
                if isinstance(v, Path):
                    v = str(v)
                snap[f"{section.__class__.__name__}.{k}"] = v
        return snap


@lru_cache(maxsize=1)
def load_settings() -> _SettingsBundle:
    """Construct and cache the settings bundle. Re-call `.cache_clear()` to pick up new env."""
    return _SettingsBundle(
        model=ModelConfig(),
        train=TrainConfig(),
        serve=ServeConfig(),
        monitor=MonitorConfig(),
        gate=GateConfig(),
    )


def env_path() -> Path:
    """Convenience for the bootstrap script — where to look for .env."""
    return PACKAGE_ROOT / ".env"
