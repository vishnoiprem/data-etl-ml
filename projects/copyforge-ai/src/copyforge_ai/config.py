"""Settings for CopyForge.

Everything the pipeline can be configured with lives here, so the
settings are in one place rather than scattered as environment-variable
reads across the modules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent

#: Where the sample drafts live.
DATA_DIR = PROJECT_ROOT / "data"

#: Where reports are written.
REPORT_DIR = PROJECT_ROOT / "reports"

#: The default model. A small instruct model is enough: the planner has
#: already decided what the block is, and the model only writes the
#: words.
DEFAULT_MODEL = "qwen2.5:7b-instruct"

#: The default Ollama host.
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

#: The environment variable that forces the deterministic stub.
DISABLE_ENV_VAR = "COPYFORGE_LLM_PROVIDER"


@dataclass(slots=True)
class Settings:
    """The settings for one run."""

    #: The router name: `stub` or `ollama`.
    provider: str = "stub"
    model: str = DEFAULT_MODEL
    host: str = DEFAULT_OLLAMA_HOST
    #: The target word count for the article.
    target_words: int = 1200
    #: The directory holding the sample drafts.
    data_dir: Path = DATA_DIR
    #: Where reports are written.
    report_dir: Path = REPORT_DIR
    #: The minimum score improvement the eval harness requires.
    min_score_delta: float = 5.0


def load_settings() -> Settings:
    """The settings, read from the environment."""
    provider = os.environ.get(DISABLE_ENV_VAR, "stub").strip().lower() or "stub"
    model = os.environ.get("COPYFORGE_OLLAMA_MODEL", DEFAULT_MODEL)
    host = os.environ.get("COPYFORGE_OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    try:
        target_words = int(os.environ.get("COPYFORGE_TARGET_WORDS", "1200"))
    except ValueError:
        target_words = 1200
    try:
        min_delta = float(os.environ.get("COPYFORGE_MIN_SCORE_DELTA", "5.0"))
    except ValueError:
        min_delta = 5.0

    return Settings(
        provider=provider,
        model=model,
        host=host,
        target_words=target_words,
        min_score_delta=min_delta,
    )
