"""Project configuration — pydantic-settings, loaded from env + .env."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_mode: str = Field(default="auto", description="auto | mock | real")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-5-haiku-latest")

    # Embeddings
    embed_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # Paths
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    sample_data_dir: Path = Field(default=PROJECT_ROOT / "sample_data")

    # Retrieval
    top_k_vector: int = 5
    top_k_bm25: int = 5
    top_k_graph: int = 5
    rrf_k: int = 60  # Reciprocal Rank Fusion constant (Cormack et al., 2009)
    graph_expand_depth: int = 2

    def index_path(self, name: str) -> Path:
        return self.data_dir / f"{name}.index"

    def chunks_path(self, name: str) -> Path:
        return self.data_dir / f"{name}.jsonl"

    def graph_path(self) -> Path:
        return self.data_dir / "graph.sqlite"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
    return _settings
