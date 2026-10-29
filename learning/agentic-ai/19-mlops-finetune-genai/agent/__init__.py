"""19. MLOps fine-tuning a GenAI model — end to end.

The package boundary mirrors the directory layout in the README:

    config     → pydantic-settings, single source of truth
    dataset    → HuggingFace loader + chat-template tokenization + quality filters
    train      → QLoRA SFT, MLflow autolog, register @Champion
    evaluate   → lm-eval-harness wrapper + per-task scores → MLflow
    gates      → pure-function budget/retry reasoning
    serve      → vLLM FastAPI wrapper (--enable-lora), /metrics, OpenAI-compat
    client     → OpenAI-compat client with retries + per-task cost
    monitor    → Prometheus + Evidently drift detector

Public surface is intentionally narrow — each module exposes a single
`run()` (or `build_*()`) entrypoint so the bash side stays one line per step.
"""

from agent.config import (
    ModelConfig,
    MonitorConfig,
    ServeConfig,
    TrainConfig,
    load_settings,
)

__all__ = [
    "ModelConfig",
    "TrainConfig",
    "ServeConfig",
    "MonitorConfig",
    "load_settings",
]
